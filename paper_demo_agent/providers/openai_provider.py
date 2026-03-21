"""OpenAI-compatible provider (also handles DeepSeek and Qwen via base_url override)."""

import json
from typing import Dict, Iterator, List, Optional

from paper_demo_agent.providers.base import BaseLLMProvider, LLMResponse, ToolCall


class OpenAIProvider(BaseLLMProvider):
    """LLM provider for OpenAI GPT models."""

    # Known chat-completions output caps for non-reasoning models that reject
    # larger max_tokens values during write-heavy build iterations.
    _MAX_OUTPUT_TOKENS = {
        "gpt-4o": 16384,
        "gpt-4o-mini": 16384,
    }

    MODELS = [
        "gpt-5.2", "gpt-5.2-pro",
        "gpt-5.1", "gpt-5",
        "gpt-4.1", "gpt-4.1-mini",
        "o3", "o4-mini",
    ]

    def __init__(self, api_key: str, model: Optional[str] = None, base_url: Optional[str] = None):
        self._base_url = base_url
        super().__init__(api_key, model)

    @property
    def default_model(self) -> str:
        return "gpt-5.2"

    def list_models(self) -> List[str]:
        return self.MODELS

    # Models to show in UI dropdown (no dated snapshots like gpt-4o-2024-08-06)
    _CURATED_MODELS = {
        "gpt-5.2", "gpt-5.2-pro",
        "gpt-5.1", "gpt-5", "gpt-5-pro",
        "gpt-4.1", "gpt-4.1-mini",
        "gpt-4o", "gpt-4o-mini",
        "o3", "o3-pro", "o4-mini",
    }

    def list_models_live(self) -> Optional[List[str]]:
        """Fetch curated chat/reasoning models from the OpenAI API (no dated snapshots)."""
        if not self.api_key:
            return None
        try:
            client = self._client()
            all_ids = {m.id for m in client.models.list()}
            # Only show curated models that actually exist on this account
            available = [m for m in self.MODELS if m in all_ids]
            # Also include any curated models we didn't list statically
            for m in sorted(all_ids, reverse=True):
                if m in self._CURATED_MODELS and m not in available:
                    available.append(m)
            return available if available else None
        except Exception:
            return None

    def _client(self):
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("openai package is required: pip install openai")
        kwargs = {"api_key": self.api_key}
        if self._base_url:
            kwargs["base_url"] = self._base_url
        return OpenAI(**kwargs)

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

    def _parse_response(self, response) -> LLMResponse:
        choice = response.choices[0]
        msg = choice.message
        content = msg.content or ""
        tool_calls = []

        if msg.tool_calls:
            for tc in msg.tool_calls:
                args = tc.function.arguments
                if isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except json.JSONDecodeError:
                        args = {}
                tool_calls.append(ToolCall(
                    id=tc.id,
                    name=tc.function.name,
                    arguments=args,
                ))

        finish = choice.finish_reason
        if tool_calls:
            stop_reason = "tool_use"
        elif finish == "length":
            stop_reason = "max_tokens"
        else:
            stop_reason = "end_turn"

        return LLMResponse(
            content=content,
            tool_calls=tool_calls,
            stop_reason=stop_reason,
            raw=response,
        )

    def chat(
        self,
        messages: List[Dict],
        system: str = "",
        tools: Optional[List[Dict]] = None,
        max_tokens: int = 8192,
    ) -> LLMResponse:
        client = self._client()
        msgs = []
        if system:
            msgs.append({"role": "system", "content": system})
        msgs.extend(messages)

        # gpt-5 and o-series models use max_completion_tokens instead of max_tokens.
        # They also need a larger budget since reasoning tokens count against the limit.
        token_key = "max_completion_tokens" if self._uses_completion_tokens() else "max_tokens"
        token_val = self._effective_token_budget(max_tokens)
        kwargs = dict(model=self.model, messages=msgs, **{token_key: token_val})
        if tools:
            kwargs["tools"] = self._convert_tools(tools)
            kwargs["tool_choice"] = "auto"

        response = client.chat.completions.create(**kwargs)
        return self._parse_response(response)

    def _uses_completion_tokens(self) -> bool:
        """Return True for models that require max_completion_tokens instead of max_tokens."""
        m = self.model.lower()
        return m.startswith("o1") or m.startswith("o3") or m.startswith("o4") or m.startswith("gpt-5")

    def _effective_token_budget(self, requested_max_tokens: int) -> int:
        """Clamp token budget to what the selected model actually accepts."""
        if self._uses_completion_tokens():
            return max(requested_max_tokens, 16384)
        model_name = self.model.lower()
        cap = self._MAX_OUTPUT_TOKENS.get(model_name)
        if cap is not None:
            return min(requested_max_tokens, cap)
        return requested_max_tokens

    def stream_chat(
        self,
        messages: List[Dict],
        system: str = "",
        tools: Optional[List[Dict]] = None,
        max_tokens: int = 8192,
    ) -> Iterator[str]:
        client = self._client()
        msgs = []
        if system:
            msgs.append({"role": "system", "content": system})
        msgs.extend(messages)

        token_key = "max_completion_tokens" if self._uses_completion_tokens() else "max_tokens"
        token_val = self._effective_token_budget(max_tokens)
        kwargs = dict(model=self.model, messages=msgs, **{token_key: token_val}, stream=True)
        if tools:
            kwargs["tools"] = self._convert_tools(tools)
            kwargs["tool_choice"] = "auto"

        for chunk in client.chat.completions.create(**kwargs):
            delta = chunk.choices[0].delta
            if delta.content:
                yield delta.content


class DeepSeekProvider(OpenAIProvider):
    """DeepSeek provider (OpenAI-compatible API)."""

    MODELS = ["deepseek-chat", "deepseek-reasoner"]

    def __init__(self, api_key: str, model: Optional[str] = None):
        super().__init__(
            api_key=api_key,
            model=model,
            base_url="https://api.deepseek.com/v1",
        )

    @property
    def default_model(self) -> str:
        return "deepseek-chat"

    def list_models(self) -> List[str]:
        return self.MODELS


class QwenProvider(OpenAIProvider):
    """Qwen (Alibaba) provider (OpenAI-compatible API)."""

    MODELS = [
        "qwen-plus",
        "qwen-turbo",
        "qwen-max",
        "qwen2.5-72b-instruct",
    ]

    def __init__(self, api_key: str, model: Optional[str] = None):
        super().__init__(
            api_key=api_key,
            model=model,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )

    @property
    def default_model(self) -> str:
        return "qwen-plus"

    def list_models(self) -> List[str]:
        return self.MODELS
