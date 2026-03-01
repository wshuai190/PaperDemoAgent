"""Anthropic Claude provider."""

import base64
import json
from typing import Dict, Iterator, List, Optional

from paper_demo_agent.providers.base import BaseLLMProvider, LLMResponse, ToolCall


class AnthropicProvider(BaseLLMProvider):
    """LLM provider for Anthropic Claude models."""

    MODELS = [
        "claude-opus-4-6",
        "claude-sonnet-4-6",
        "claude-haiku-4-5-20251001",
        "claude-3-5-sonnet-20241022",
        "claude-3-5-haiku-20241022",
    ]

    @property
    def default_model(self) -> str:
        return "claude-opus-4-6"

    def list_models(self) -> List[str]:
        return self.MODELS

    @property
    def supports_native_pdf(self) -> bool:
        return True

    def chat_with_pdf(
        self,
        messages: List[Dict],
        pdf_bytes: bytes,
        system: str = "",
        tools: Optional[List[Dict]] = None,
        max_tokens: int = 8192,
    ) -> LLMResponse:
        """Inject the PDF as an Anthropic document block before the first user message."""
        b64 = base64.standard_b64encode(pdf_bytes).decode()
        pdf_block = {
            "type": "document",
            "source": {"type": "base64", "media_type": "application/pdf", "data": b64},
        }
        augmented = list(messages)
        first_user = next((i for i, m in enumerate(augmented) if m["role"] == "user"), None)
        if first_user is not None:
            orig = augmented[first_user]
            content = orig["content"]
            if isinstance(content, str):
                content = [{"type": "text", "text": content}]
            augmented[first_user] = {"role": "user", "content": [pdf_block] + list(content)}
        return self.chat(augmented, system=system, tools=tools, max_tokens=max_tokens)

    def _client(self):
        try:
            import anthropic
        except ImportError:
            raise ImportError("anthropic package is required: pip install anthropic")
        return anthropic.Anthropic(api_key=self.api_key)

    def _convert_tools(self, tools: List[Dict]) -> List[Dict]:
        """Convert generic tool defs to Anthropic format."""
        converted = []
        for t in tools:
            converted.append({
                "name": t["name"],
                "description": t.get("description", ""),
                "input_schema": t.get("parameters", t.get("input_schema", {"type": "object", "properties": {}})),
            })
        return converted

    def _parse_response(self, response) -> LLMResponse:
        content_text = ""
        tool_calls = []
        for block in response.content:
            if block.type == "text":
                content_text += block.text
            elif block.type == "tool_use":
                tool_calls.append(ToolCall(
                    id=block.id,
                    name=block.name,
                    arguments=block.input if isinstance(block.input, dict) else json.loads(block.input),
                ))

        stop_reason = "tool_use" if tool_calls else "end_turn"
        if response.stop_reason == "max_tokens":
            stop_reason = "max_tokens"

        return LLMResponse(
            content=content_text,
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
        kwargs = dict(
            model=self.model,
            max_tokens=max_tokens,
            messages=messages,
        )
        if system:
            kwargs["system"] = system
        if tools:
            kwargs["tools"] = self._convert_tools(tools)

        response = client.messages.create(**kwargs)
        return self._parse_response(response)

    def stream_chat(
        self,
        messages: List[Dict],
        system: str = "",
        tools: Optional[List[Dict]] = None,
        max_tokens: int = 8192,
    ) -> Iterator[str]:
        client = self._client()
        kwargs = dict(
            model=self.model,
            max_tokens=max_tokens,
            messages=messages,
        )
        if system:
            kwargs["system"] = system
        if tools:
            kwargs["tools"] = self._convert_tools(tools)

        with client.messages.stream(**kwargs) as stream:
            for text in stream.text_stream:
                yield text
