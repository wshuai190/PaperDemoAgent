"""Tests for provider layer."""

import json
import pytest
from unittest.mock import MagicMock, patch

from paper_demo_agent.providers.base import BaseLLMProvider, LLMResponse, ToolCall
from paper_demo_agent.providers.factory import create_provider, list_providers, PROVIDER_DEFAULTS
from paper_demo_agent.providers.gemini_provider import GeminiProvider
from paper_demo_agent.providers.openai_provider import OpenAIProvider


class TestToolCall:
    def test_fields(self):
        tc = ToolCall(id="call_1", name="write_file", arguments={"path": "app.py", "content": ""})
        assert tc.id == "call_1"
        assert tc.name == "write_file"
        assert tc.arguments["path"] == "app.py"
        assert tc.metadata == {}


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


class TestGeminiProvider:
    def test_resolved_model_name_supports_cli_auto_aliases(self):
        provider = GeminiProvider(api_key="fake", model="auto-gemini-2.5")
        assert provider._resolved_model_name() == "gemini-2.5-pro"

        provider = GeminiProvider(api_key="fake", model="auto-gemini-3")
        provider._live_models_cache = ["gemini-3.1-pro-preview", "gemini-3-flash-preview"]
        assert provider._resolved_model_name() == "gemini-3.1-pro-preview"

    def test_messages_to_gemini_normalizes_rest_parts(self):
        provider = GeminiProvider(api_key=json.dumps({"token": "oauth-token", "projectId": "proj"}))
        messages = [
            {
                "role": "user",
                "content": [
                    {"inline_data": {"mime_type": "application/pdf", "data": "ZmFrZQ=="}},
                    {"type": "text", "text": "Analyze this paper"},
                ],
            },
            {"role": "tool", "name": "write_file", "content": "ok"},
        ]

        converted = provider._messages_to_gemini(messages)

        assert converted[0]["parts"][0] == {
            "inlineData": {"mime_type": "application/pdf", "data": "ZmFrZQ=="}
        }
        assert converted[0]["parts"][1] == {"text": "Analyze this paper"}
        assert converted[1]["parts"][0] == {
            "functionResponse": {"name": "write_file", "response": {"result": "ok"}}
        }

    def test_messages_to_gemini_handles_anthropic_tool_history(self):
        provider = GeminiProvider(api_key=json.dumps({"token": "oauth-token"}))
        messages = [
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "tool_use",
                        "id": "call_1",
                        "name": "web_search",
                        "input": {"query": "attention is all you need"},
                    }
                ],
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": "call_1",
                        "content": "Search results here",
                    }
                ],
            },
        ]

        converted = provider._messages_to_gemini(messages)

        assert converted[0] == {
            "role": "model",
            "parts": [{"functionCall": {"name": "web_search", "args": {"query": "attention is all you need"}}}],
        }
        assert converted[1] == {
            "role": "user",
            "parts": [{"functionResponse": {"name": "web_search", "response": {"result": "Search results here"}}}],
        }

    def test_messages_to_gemini_replays_thought_signature(self):
        provider = GeminiProvider(api_key=json.dumps({"token": "oauth-token"}))
        messages = [
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "tool_use",
                        "id": "call_1",
                        "name": "web_search",
                        "input": {"query": "chain of thought prompting"},
                        "metadata": {"thoughtSignature": "sig-123"},
                    }
                ],
            },
        ]

        converted = provider._messages_to_gemini(messages)

        assert converted[0] == {
            "role": "model",
            "parts": [{
                "functionCall": {
                    "name": "web_search",
                    "args": {"query": "chain of thought prompting"},
                    "thoughtSignature": "sig-123",
                }
            }],
        }

    def test_messages_to_gemini_merges_consecutive_tool_results(self):
        provider = GeminiProvider(api_key=json.dumps({"token": "oauth-token"}))
        messages = [
            {
                "role": "assistant",
                "content": [
                    {"type": "tool_use", "id": "call_1", "name": "web_search", "input": {"query": "a"}},
                    {"type": "tool_use", "id": "call_2", "name": "search_huggingface", "input": {"query": "b"}},
                ],
            },
            {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "call_1", "content": "result a"}]},
            {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "call_2", "content": "result b"}]},
        ]

        converted = provider._messages_to_gemini(messages)

        assert converted[0]["role"] == "model"
        assert len(converted[0]["parts"]) == 2
        assert converted[1] == {
            "role": "user",
            "parts": [
                {"functionResponse": {"name": "web_search", "response": {"result": "result a"}}},
                {"functionResponse": {"name": "search_huggingface", "response": {"result": "result b"}}},
            ],
        }

    def test_chat_rest_uses_project_and_session_id(self, monkeypatch):
        provider = GeminiProvider(
            api_key=json.dumps({"token": "oauth-token", "projectId": "paperdemoagent"}),
            model="gemini-2.5-flash",
        )
        captured = {}

        class DummyResponse:
            status_code = 200
            text = "ok"

            @staticmethod
            def json():
                return {"response": {"candidates": [{"content": {"parts": [{"text": "done"}]}}]}}

        class DummyClient:
            def __init__(self, *args, **kwargs):
                pass

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def post(self, url, json=None, headers=None):
                captured["url"] = url
                captured["json"] = json
                captured["headers"] = headers
                return DummyResponse()

        monkeypatch.setattr("httpx.Client", DummyClient)

        response = provider.chat_with_pdf(
            messages=[{"role": "user", "content": "Analyze this paper"}],
            pdf_bytes=b"%PDF-1.4 fake",
            system="system prompt",
            max_tokens=256,
        )

        assert response.content == "done"
        assert captured["url"] == "https://cloudcode-pa.googleapis.com/v1internal:generateContent"
        assert captured["headers"]["Authorization"] == "Bearer oauth-token"
        assert captured["json"]["project"] == "paperdemoagent"
        assert captured["json"]["model"] == "gemini-2.5-flash"
        assert captured["json"]["request"]["session_id"] == provider._session_id
        assert "enabled_credit_types" not in captured["json"]
        assert captured["json"]["request"]["systemInstruction"] == {
            "parts": [{"text": "system prompt"}]
        }
        assert captured["json"]["request"]["contents"][0]["parts"][0]["inlineData"]["mime_type"] == "application/pdf"

    def test_chat_rest_retries_without_invalid_project(self, monkeypatch):
        provider = GeminiProvider(
            api_key=json.dumps({"token": "oauth-token", "projectId": "paperdemoagent"}),
            model="gemini-2.5-flash",
        )
        calls = []

        class DummyResponse:
            def __init__(self, status_code, body):
                self.status_code = status_code
                self._body = body
                self.text = json.dumps(body)

            def json(self):
                return self._body

        class DummyClient:
            def __init__(self, *args, **kwargs):
                pass

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def post(self, url, json=None, headers=None):
                calls.append(json)
                if len(calls) == 1:
                    return DummyResponse(
                        403,
                        {
                            "error": {
                                "message": "Permission denied on resource project paperdemoagent.",
                                "details": [{"reason": "CONSUMER_INVALID"}],
                            }
                        },
                    )
                return DummyResponse(
                    200,
                    {"response": {"candidates": [{"content": {"parts": [{"text": "done"}]}}]}},
                )

        monkeypatch.setattr("httpx.Client", DummyClient)

        response = provider.chat(
            messages=[{"role": "user", "content": "hello"}],
            system="system prompt",
            max_tokens=64,
        )

        assert response.content == "done"
        assert len(calls) == 2
        assert calls[0]["project"] == "paperdemoagent"
        assert "project" not in calls[1]

    def test_chat_rest_loads_code_assist_project_before_generate(self, monkeypatch):
        provider = GeminiProvider(
            api_key=json.dumps({"token": "oauth-token"}),
            model="gemini-2.5-flash",
        )
        calls = []

        class DummyResponse:
            def __init__(self, status_code, body):
                self.status_code = status_code
                self._body = body
                self.text = json.dumps(body)

            def json(self):
                return self._body

        class DummyClient:
            def __init__(self, *args, **kwargs):
                pass

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def post(self, url, json=None, headers=None):
                calls.append((url, json))
                if url.endswith(":loadCodeAssist"):
                    return DummyResponse(
                        200,
                        {
                            "allowedTiers": [{"id": "free-tier", "name": "Free", "isDefault": True}],
                        },
                    )
                if url.endswith(":onboardUser"):
                    return DummyResponse(
                        200,
                        {
                            "done": True,
                            "response": {
                                "cloudaicompanionProject": {"id": "server-project"},
                            },
                        },
                    )
                if url.endswith(":generateContent"):
                    return DummyResponse(
                        200,
                        {"response": {"candidates": [{"content": {"parts": [{"text": "done"}]}}]}},
                    )
                raise AssertionError(f"Unexpected POST URL: {url}")

            def get(self, url, headers=None):
                raise AssertionError(f"Unexpected GET URL: {url}")

        monkeypatch.setattr("httpx.Client", DummyClient)

        response = provider.chat(
            messages=[{"role": "user", "content": "hello"}],
            system="system prompt",
            max_tokens=64,
        )

        assert response.content == "done"
        assert calls[0][0].endswith(":loadCodeAssist")
        assert calls[1][0].endswith(":onboardUser")
        assert calls[2][0].endswith(":generateContent")
        assert calls[2][1]["project"] == "server-project"

    def test_parse_rest_response_preserves_thought_signature(self):
        provider = GeminiProvider(api_key=json.dumps({"token": "oauth-token"}))

        response = provider._parse_rest_response({
            "candidates": [{
                "content": {
                    "parts": [{
                        "functionCall": {
                            "name": "web_search",
                            "args": {"query": "chain of thought"},
                            "thoughtSignature": "sig-123",
                        }
                    }]
                }
            }]
        })

        assert response.stop_reason == "tool_use"
        assert len(response.tool_calls) == 1
        assert response.tool_calls[0].metadata == {"thoughtSignature": "sig-123"}


class TestOpenAIProvider:
    def test_chat_clamps_gpt_4o_mini_max_tokens(self, monkeypatch):
        provider = OpenAIProvider(api_key="fake-key", model="gpt-4o-mini")
        captured = {}

        class DummyCompletions:
            def create(self, **kwargs):
                captured.update(kwargs)
                message = MagicMock(content="done", tool_calls=None)
                choice = MagicMock(message=message, finish_reason="stop")
                return MagicMock(choices=[choice])

        class DummyChat:
            completions = DummyCompletions()

        class DummyClient:
            chat = DummyChat()

        monkeypatch.setattr(provider, "_client", lambda: DummyClient())

        response = provider.chat(
            messages=[{"role": "user", "content": "hello"}],
            max_tokens=32768,
        )

        assert response.content == "done"
        assert captured["model"] == "gpt-4o-mini"
        assert captured["max_tokens"] == 16384
        assert "max_completion_tokens" not in captured

    def test_chat_uses_completion_tokens_for_gpt_5(self, monkeypatch):
        provider = OpenAIProvider(api_key="fake-key", model="gpt-5.2")
        captured = {}

        class DummyCompletions:
            def create(self, **kwargs):
                captured.update(kwargs)
                message = MagicMock(content="done", tool_calls=None)
                choice = MagicMock(message=message, finish_reason="stop")
                return MagicMock(choices=[choice])

        class DummyChat:
            completions = DummyCompletions()

        class DummyClient:
            chat = DummyChat()

        monkeypatch.setattr(provider, "_client", lambda: DummyClient())

        response = provider.chat(
            messages=[{"role": "user", "content": "hello"}],
            max_tokens=8192,
        )

        assert response.content == "done"
        assert captured["model"] == "gpt-5.2"
        assert captured["max_completion_tokens"] == 16384
        assert "max_tokens" not in captured
