"""Anthropic Claude provider."""

import base64
import json
from typing import Dict, Iterator, List, Optional

from paper_demo_agent.providers.base import BaseLLMProvider, LLMResponse, ToolCall


class AnthropicProvider(BaseLLMProvider):
    """LLM provider for Anthropic Claude models.

    Supports both API key auth (x-api-key header) and OAuth/setup-token auth
    (Authorization: Bearer header). OAuth tokens are auto-detected from the key
    prefix: sk-ant-oat01-* tokens use Bearer auth, standard sk-ant-api* tokens
    use API key auth.
    """

    MODELS = [
        "claude-opus-4-6",
        "claude-sonnet-4-6",
        "claude-haiku-4-5-20251001",
        "claude-3-5-sonnet-20241022",
        "claude-3-5-haiku-20241022",
    ]

    # Token prefixes that indicate OAuth / setup-token (Bearer auth)
    OAUTH_TOKEN_PREFIXES = ("sk-ant-oat01-",)

    @property
    def default_model(self) -> str:
        return "claude-opus-4-6"

    def list_models(self) -> List[str]:
        return self.MODELS

    @property
    def supports_native_pdf(self) -> bool:
        return True

    @property
    def _is_oauth_token(self) -> bool:
        """Check if the API key is actually an OAuth/setup-token."""
        if not self.api_key:
            return False
        return any(self.api_key.startswith(p) for p in self.OAUTH_TOKEN_PREFIXES)

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

    # Claude Code identity headers required for OAuth tokens
    _CLAUDE_CODE_VERSION = "2.1.62"
    _OAUTH_BETA_FEATURES = "claude-code-20250219,oauth-2025-04-20,fine-grained-tool-streaming-2025-05-14,interleaved-thinking-2025-05-14,prompt-caching-2024-07-31"

    def _client(self):
        try:
            import anthropic
        except ImportError:
            raise ImportError("anthropic package is required: pip install anthropic")

        if self._is_oauth_token:
            # OAuth / setup-token: use Bearer auth with Claude Code identity headers.
            # The API requires these headers to accept OAuth tokens — it must
            # believe the request comes from Claude Code.
            return anthropic.Anthropic(
                api_key=None,
                auth_token=self.api_key,
                default_headers={
                    "anthropic-beta": self._OAUTH_BETA_FEATURES,
                    "user-agent": f"claude-cli/{self._CLAUDE_CODE_VERSION}",
                    "x-app": "cli",
                    "anthropic-dangerous-direct-browser-access": "true",
                },
            )
        else:
            return anthropic.Anthropic(
                api_key=self.api_key,
                default_headers={
                    "anthropic-beta": "prompt-caching-2024-07-31",
                },
            )

    def _convert_tools(self, tools: List[Dict]) -> List[Dict]:
        """Convert generic tool defs to Anthropic format.

        Marks the last tool with cache_control to enable prompt caching
        for tool definitions (they're static across all iterations).
        """
        converted = []
        for i, t in enumerate(tools):
            tool_def = {
                "name": t["name"],
                "description": t.get("description", ""),
                "input_schema": t.get("parameters", t.get("input_schema", {"type": "object", "properties": {}})),
            }
            # Cache control on last tool — caches all tools + system prompt
            if i == len(tools) - 1:
                tool_def["cache_control"] = {"type": "ephemeral"}
            converted.append(tool_def)
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

    # System prompt prefix required for OAuth tokens
    _CLAUDE_CODE_SYSTEM = "You are Claude Code, Anthropic's official CLI for Claude."

    def _build_system_kwarg(self, system: str = ""):
        """Build the system kwarg for the API call.

        For OAuth tokens, returns a list of text blocks with cache_control
        on the last block. This enables Anthropic prompt caching — the system
        prompt (which is large and static across iterations) is cached on the
        first call and reused on subsequent calls, saving ~90% of input tokens
        on multi-iteration generation loops.

        For API keys, also uses block format with cache_control when the system
        prompt is large enough to benefit (>1024 tokens ≈ 4KB).
        """
        if self._is_oauth_token:
            blocks = [{"type": "text", "text": self._CLAUDE_CODE_SYSTEM}]
            if system:
                # Mark the last block as cacheable — Anthropic caches everything
                # up to and including the block with cache_control
                blocks.append({
                    "type": "text",
                    "text": system,
                    "cache_control": {"type": "ephemeral"},
                })
            return blocks

        # For API key auth: use block format with caching if prompt is large enough
        if system and len(system) > 4000:
            return [{
                "type": "text",
                "text": system,
                "cache_control": {"type": "ephemeral"},
            }]
        return system if system else None

    def chat(
        self,
        messages: List[Dict],
        system: str = "",
        tools: Optional[List[Dict]] = None,
        max_tokens: int = 8192,
    ) -> LLMResponse:
        """Use streaming internally to avoid Anthropic's 10-min server timeout.

        The API requires streaming for requests that take >10 min. With large
        max_tokens (32K) + tool use, responses can exceed that. By streaming
        and collecting the final message, we get the full response without
        timeouts while keeping the same return type.
        """
        client = self._client()
        system_kwarg = self._build_system_kwarg(system)
        kwargs = dict(
            model=self.model,
            max_tokens=max_tokens,
            messages=messages,
        )
        if system_kwarg:
            kwargs["system"] = system_kwarg
        if tools:
            kwargs["tools"] = self._convert_tools(tools)

        # Stream and collect the final message to avoid server timeout
        with client.messages.stream(**kwargs) as stream:
            response = stream.get_final_message()
        return self._parse_response(response)

    def stream_chat(
        self,
        messages: List[Dict],
        system: str = "",
        tools: Optional[List[Dict]] = None,
        max_tokens: int = 8192,
    ) -> Iterator[str]:
        client = self._client()
        system_kwarg = self._build_system_kwarg(system)
        kwargs = dict(
            model=self.model,
            max_tokens=max_tokens,
            messages=messages,
        )
        if system_kwarg:
            kwargs["system"] = system_kwarg
        if tools:
            kwargs["tools"] = self._convert_tools(tools)

        with client.messages.stream(**kwargs) as stream:
            for text in stream.text_stream:
                yield text
