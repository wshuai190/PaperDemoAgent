"""Tests for provider layer."""

import pytest
from unittest.mock import MagicMock, patch

from paper_demo_agent.providers.base import BaseLLMProvider, LLMResponse, ToolCall
from paper_demo_agent.providers.factory import create_provider, list_providers, PROVIDER_DEFAULTS


class TestToolCall:
    def test_fields(self):
        tc = ToolCall(id="call_1", name="write_file", arguments={"path": "app.py", "content": ""})
        assert tc.id == "call_1"
        assert tc.name == "write_file"
        assert tc.arguments["path"] == "app.py"


class TestLLMResponse:
    def test_defaults(self):
        r = LLMResponse(content="hello")
        assert r.tool_calls == []
        assert r.stop_reason == "end_turn"

    def test_with_tool_calls(self):
        tc = ToolCall(id="c1", name="write_file", arguments={})
        r = LLMResponse(content="", tool_calls=[tc], stop_reason="tool_use")
        assert len(r.tool_calls) == 1
        assert r.stop_reason == "tool_use"


class TestFactory:
    def test_list_providers(self):
        providers = list_providers()
        assert "anthropic" in providers
        assert "openai" in providers
        assert "gemini" in providers
        assert "deepseek" in providers
        assert "qwen" in providers
        assert "minimax" in providers

    def test_invalid_provider(self):
        with pytest.raises(ValueError, match="Unknown provider"):
            create_provider("nonexistent_provider", api_key="fake")

    def test_missing_api_key(self):
        # Use deepseek instead of anthropic — anthropic may find keys via
        # tool credential detection (Claude Code, OpenClaw, Aider).
        with pytest.raises(RuntimeError, match="API key not found"):
            import os
            env_key = "DEEPSEEK_API_KEY"
            old = os.environ.pop(env_key, None)
            try:
                create_provider("deepseek", api_key=None)
            finally:
                if old:
                    os.environ[env_key] = old

    @patch("paper_demo_agent.providers.anthropic_provider.AnthropicProvider.chat")
    def test_anthropic_provider_created(self, mock_chat):
        mock_chat.return_value = LLMResponse(content="hi")
        provider = create_provider("anthropic", api_key="fake-key")
        assert provider.__class__.__name__ == "AnthropicProvider"
        assert provider.api_key == "fake-key"

    def test_openai_provider_created(self):
        provider = create_provider("openai", api_key="fake-key")
        assert provider.__class__.__name__ == "OpenAIProvider"

    def test_deepseek_provider_created(self):
        provider = create_provider("deepseek", api_key="fake-key")
        assert provider.__class__.__name__ == "DeepSeekProvider"
        assert provider._base_url == "https://api.deepseek.com/v1"

    def test_qwen_provider_created(self):
        provider = create_provider("qwen", api_key="fake-key")
        assert provider.__class__.__name__ == "QwenProvider"

    def test_minimax_requires_group_id(self):
        with pytest.raises(RuntimeError, match="MINIMAX_GROUP_ID"):
            create_provider("minimax", api_key="fake-key")

    def test_minimax_provider_created(self):
        provider = create_provider("minimax", api_key="fake-key", group_id="group123")
        assert provider.__class__.__name__ == "MiniMaxProvider"
        assert provider._group_id == "group123"
