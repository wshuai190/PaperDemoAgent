"""MiniMax provider (OpenAI-compatible REST API)."""

import json
from typing import Dict, Iterator, List, Optional

from paper_demo_agent.providers.base import BaseLLMProvider, LLMResponse, ToolCall


class MiniMaxProvider(BaseLLMProvider):
    """LLM provider for MiniMax models."""

    MODELS = [
        "abab6.5-chat",
        "abab6.5s-chat",
        "abab5.5-chat",
    ]

    BASE_URL = "https://api.minimax.chat/v1"

    def __init__(self, api_key: str, group_id: str, model: Optional[str] = None):
        self._group_id = group_id
        super().__init__(api_key, model)

    @property
    def default_model(self) -> str:
        return "abab6.5-chat"

    def list_models(self) -> List[str]:
        return self.MODELS

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _url(self, path: str) -> str:
        return f"{self.BASE_URL}/{path}?GroupId={self._group_id}"

    def _convert_tools(self, tools: List[Dict]) -> List[Dict]:
        converted = []
        for t in tools:
            converted.append({
                "type": "function",
                "function": {
                    "name": t["name"],
                    "description": t.get("description", ""),
                    "parameters": t.get("parameters", {"type": "object", "properties": {}}),
                },
            })
        return converted

    def _build_payload(
        self,
        messages: List[Dict],
        system: str = "",
        tools: Optional[List[Dict]] = None,
        max_tokens: int = 8192,
        stream: bool = False,
    ) -> Dict:
        msgs = []
        if system:
            msgs.append({"role": "system", "content": system})
        msgs.extend(messages)

        payload: Dict = {
            "model": self.model,
            "messages": msgs,
            "max_tokens": max_tokens,
            "stream": stream,
        }
        if tools:
            payload["tools"] = self._convert_tools(tools)
            payload["tool_choice"] = "auto"
        return payload

    def _parse_choice(self, choice: Dict) -> LLMResponse:
        msg = choice.get("message", {})
        content = msg.get("content", "")
        tool_calls = []
        for tc in msg.get("tool_calls", []) or []:
            fn = tc.get("function", {})
            args = fn.get("arguments", {})
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except json.JSONDecodeError:
                    args = {}
            tool_calls.append(ToolCall(
                id=tc.get("id", f"call_{len(tool_calls)}"),
                name=fn.get("name", ""),
                arguments=args,
            ))
        finish = choice.get("finish_reason", "stop")
        if tool_calls:
            stop_reason = "tool_use"
        elif finish == "length":
            stop_reason = "max_tokens"
        else:
            stop_reason = "end_turn"

        return LLMResponse(content=content, tool_calls=tool_calls, stop_reason=stop_reason)

    def chat(
        self,
        messages: List[Dict],
        system: str = "",
        tools: Optional[List[Dict]] = None,
        max_tokens: int = 8192,
    ) -> LLMResponse:
        try:
            import httpx
        except ImportError:
            raise ImportError("httpx is required: pip install httpx")

        payload = self._build_payload(messages, system, tools, max_tokens)
        response = httpx.post(
            self._url("text/chatcompletion_v2"),
            headers=self._headers(),
            json=payload,
            timeout=120,
        )
        response.raise_for_status()
        data = response.json()
        choice = data["choices"][0]
        return self._parse_choice(choice)

    def stream_chat(
        self,
        messages: List[Dict],
        system: str = "",
        tools: Optional[List[Dict]] = None,
        max_tokens: int = 8192,
    ) -> Iterator[str]:
        try:
            import httpx
        except ImportError:
            raise ImportError("httpx is required: pip install httpx")

        payload = self._build_payload(messages, system, tools, max_tokens, stream=True)
        with httpx.stream(
            "POST",
            self._url("text/chatcompletion_v2"),
            headers=self._headers(),
            json=payload,
            timeout=120,
        ) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if line.startswith("data: "):
                    chunk = line[6:]
                    if chunk.strip() == "[DONE]":
                        break
                    try:
                        data = json.loads(chunk)
                        delta = data["choices"][0].get("delta", {})
                        if delta.get("content"):
                            yield delta["content"]
                    except (json.JSONDecodeError, KeyError):
                        continue
