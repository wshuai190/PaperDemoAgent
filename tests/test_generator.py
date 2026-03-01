"""Tests for the generation loop and tools."""

import os
import pytest
import tempfile
from unittest.mock import MagicMock, patch

from paper_demo_agent.generation.tools import (
    tool_write_file, tool_read_file, tool_execute_python,
    dispatch_tool, _safe_path
)
from paper_demo_agent.generation.generator import (
    generate, _detect_main_file,
    _anthropic_assistant_message, _anthropic_tool_result_message,
    _openai_assistant_message, _openai_tool_result_message,
)
from paper_demo_agent.paper.models import Paper, PaperAnalysis, DemoResult
from paper_demo_agent.providers.base import LLMResponse, ToolCall


def _make_paper():
    return Paper(
        title="Test Paper",
        abstract="Abstract.",
        full_text="Full text.",
        sections={"Introduction": "Intro."},
        source_type="text",
        source="test",
    )


def _make_analysis(demo_form="app", demo_subtype=""):
    return PaperAnalysis(
        paper_type="other",
        contribution="A contribution.",
        skill_hint="GeneralQASkill",
        demo_form=demo_form,
        demo_type="user_demo",
        demo_subtype=demo_subtype,
        hf_model_query="test",
        required_keys=[],
        interaction_pattern="Q&A",
        reasoning="Because.",
    )


class TestTools:
    def test_write_and_read_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = tool_write_file(tmpdir, "app.py", "print('hello')")
            assert "Written" in result
            content = tool_read_file(tmpdir, "app.py")
            assert content == "print('hello')"

    def test_write_creates_subdirs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = tool_write_file(tmpdir, "static/style.css", "body {}")
            assert "Written" in result
            assert os.path.exists(os.path.join(tmpdir, "static", "style.css"))

    def test_read_nonexistent_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = tool_read_file(tmpdir, "nonexistent.py")
            assert "not found" in result

    def test_path_traversal_blocked(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(ValueError, match="escapes"):
                _safe_path(tmpdir, "../../etc/passwd")

    def test_execute_python_simple(self):
        result = tool_execute_python("print(1+1)")
        assert "2" in result

    def test_execute_python_error(self):
        result = tool_execute_python("raise ValueError('test error')")
        assert "test error" in result or "STDERR" in result

    def test_execute_python_timeout(self):
        result = tool_execute_python("import time; time.sleep(100)")
        assert "timed out" in result.lower()

    def test_dispatch_tool_write(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = dispatch_tool("write_file", {"path": "x.py", "content": "# test"}, tmpdir)
            assert "Written" in result

    def test_dispatch_tool_unknown(self):
        result = dispatch_tool("nonexistent_tool", {}, "/tmp")
        assert "Unknown tool" in result

    def test_dispatch_tool_missing_arg(self):
        result = dispatch_tool("write_file", {"path": "x.py"}, "/tmp")
        assert "Missing" in result or "Error" in result


class TestMessageFormats:
    """Tests for provider-specific message format helpers."""

    def setup_method(self):
        self.tc = ToolCall(id="call_1", name="write_file", arguments={"path": "app.py", "content": "# hi"})
        self.response_with_tools = LLMResponse(
            content="Let me write that.",
            tool_calls=[self.tc],
            stop_reason="tool_use",
        )
        self.response_text_only = LLMResponse(
            content="Done!",
            tool_calls=[],
            stop_reason="end_turn",
        )

    def test_anthropic_assistant_with_tools(self):
        msg = _anthropic_assistant_message(self.response_with_tools)
        assert msg["role"] == "assistant"
        assert isinstance(msg["content"], list)
        assert msg["content"][0] == {"type": "text", "text": "Let me write that."}
        assert msg["content"][1]["type"] == "tool_use"
        assert msg["content"][1]["id"] == "call_1"
        assert msg["content"][1]["input"] == {"path": "app.py", "content": "# hi"}

    def test_anthropic_assistant_text_only(self):
        msg = _anthropic_assistant_message(self.response_text_only)
        assert msg["role"] == "assistant"
        assert isinstance(msg["content"], list)
        assert len(msg["content"]) == 1
        assert msg["content"][0] == {"type": "text", "text": "Done!"}

    def test_anthropic_tool_result(self):
        msg = _anthropic_tool_result_message(self.tc, "Written 4 bytes")
        assert msg["role"] == "user"
        assert msg["content"][0]["type"] == "tool_result"
        assert msg["content"][0]["tool_use_id"] == "call_1"
        assert msg["content"][0]["content"] == "Written 4 bytes"

    def test_openai_assistant_with_tools(self):
        import json
        msg = _openai_assistant_message(self.response_with_tools)
        assert msg["role"] == "assistant"
        assert msg["content"] == "Let me write that."
        assert len(msg["tool_calls"]) == 1
        # arguments must be valid JSON string
        args = json.loads(msg["tool_calls"][0]["function"]["arguments"])
        assert args == {"path": "app.py", "content": "# hi"}

    def test_openai_assistant_no_tools(self):
        msg = _openai_assistant_message(self.response_text_only)
        assert msg["role"] == "assistant"
        assert "tool_calls" not in msg

    def test_openai_tool_result(self):
        msg = _openai_tool_result_message(self.tc, "Written 4 bytes")
        assert msg["role"] == "tool"
        assert msg["tool_call_id"] == "call_1"
        assert msg["content"] == "Written 4 bytes"

    def test_anthropic_messages_passed_to_provider(self):
        """Verify that the generator sends correct Anthropic messages with tool_use blocks."""
        import copy
        from paper_demo_agent.skills.general_qa import GeneralQASkill

        # Capture a snapshot of messages at call time (mock stores refs, not copies)
        captured_messages = []
        gradio_content = "import gradio as gr\napp = gr.Interface(lambda x: x, 'text', 'text')\napp.launch()"
        # Phase order: research(1 call end_turn) → build(write_file then end_turn) → polish(end_turn)
        responses = [
            LLMResponse(content="Research: found GitHub repo and prior work.", tool_calls=[], stop_reason="end_turn"),
            LLMResponse(content="Writing.", tool_calls=[
                ToolCall(id="c1", name="write_file", arguments={"path": "app.py", "content": gradio_content})
            ], stop_reason="tool_use"),
            LLMResponse(content="Done.", tool_calls=[], stop_reason="end_turn"),
            LLMResponse(content="Looks good.", tool_calls=[], stop_reason="end_turn"),
        ]
        response_iter = iter(responses)

        def capture_and_respond(**kwargs):
            captured_messages.append(copy.deepcopy(kwargs["messages"]))
            return next(response_iter)

        provider = MagicMock()
        provider.__class__.__name__ = "AnthropicProvider"
        provider.model = "claude-opus-4-6"
        provider.chat.side_effect = capture_and_respond

        skill = GeneralQASkill()
        paper = _make_paper()
        analysis = _make_analysis()

        with tempfile.TemporaryDirectory() as tmpdir:
            generate(provider=provider, skill=skill, paper=paper, analysis=analysis, output_dir=tmpdir)

        # With 3-phase architecture:
        # Call 0: research phase initial call (end_turn)
        # Call 1: build phase call 1 (write_file tool use)
        # Call 2: build phase call 2 (after tool result, end_turn) ← check THIS one
        # Call 3: polish phase call (end_turn)
        assert len(captured_messages) >= 3, f"Expected >=3 calls, got {len(captured_messages)}"

        # Find the build phase's second call — it should include the assistant message with tool_use blocks
        # It's the call where messages contain an "assistant" entry with tool_use content
        build_second_call = None
        for msgs in captured_messages:
            for m in msgs:
                if m.get("role") == "assistant" and isinstance(m.get("content"), list):
                    build_second_call = msgs
                    break
            if build_second_call:
                break

        assert build_second_call is not None, "No call found with assistant tool_use message"

        assistant_msgs = [m for m in build_second_call if m["role"] == "assistant"]
        assert len(assistant_msgs) == 1, f"Expected 1 assistant msg, got {len(assistant_msgs)}"

        content = assistant_msgs[0]["content"]
        assert isinstance(content, list)
        tool_use_blocks = [b for b in content if isinstance(b, dict) and b.get("type") == "tool_use"]
        assert len(tool_use_blocks) == 1
        assert tool_use_blocks[0]["id"] == "c1"
        assert tool_use_blocks[0]["name"] == "write_file"


class TestGenerator:
    def test_detect_main_file_python(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            open(os.path.join(tmpdir, "app.py"), "w").close()
            assert _detect_main_file(tmpdir, "app") == "app.py"

    def test_detect_main_file_html(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            open(os.path.join(tmpdir, "demo.html"), "w").close()
            assert _detect_main_file(tmpdir, "presentation") == "demo.html"

    def test_generate_end_turn_immediately(self):
        """Generator should return successfully when LLM sends end_turn immediately."""
        from paper_demo_agent.skills.general_qa import GeneralQASkill

        provider = MagicMock()
        provider.__class__.__name__ = "AnthropicProvider"
        provider.model = "claude-opus-4-6"
        provider.chat.return_value = LLMResponse(
            content="Done! I've created the demo.",
            tool_calls=[],
            stop_reason="end_turn",
        )

        skill = GeneralQASkill()
        paper = _make_paper()
        analysis = _make_analysis()

        with tempfile.TemporaryDirectory() as tmpdir:
            result = generate(
                provider=provider,
                skill=skill,
                paper=paper,
                analysis=analysis,
                output_dir=tmpdir,
            )
            assert isinstance(result, DemoResult)
            assert result.success is True

    def test_generate_with_tool_calls(self):
        """Generator correctly dispatches tool calls."""
        from paper_demo_agent.skills.general_qa import GeneralQASkill

        provider = MagicMock()
        provider.__class__.__name__ = "AnthropicProvider"
        provider.model = "claude-opus-4-6"

        gradio_content = "import gradio as gr\napp = gr.Interface(lambda x: x, 'text', 'text')\napp.launch()"
        # Phase order: research(end_turn) → build(write_file, end_turn) → polish(end_turn)
        provider.chat.side_effect = [
            LLMResponse(content="Research done.", tool_calls=[], stop_reason="end_turn"),
            LLMResponse(
                content="Let me write a file.",
                tool_calls=[ToolCall(
                    id="call_1",
                    name="write_file",
                    arguments={"path": "app.py", "content": gradio_content},
                )],
                stop_reason="tool_use",
            ),
            LLMResponse(content="Done!", tool_calls=[], stop_reason="end_turn"),
            LLMResponse(content="Looks good.", tool_calls=[], stop_reason="end_turn"),
        ]

        skill = GeneralQASkill()
        paper = _make_paper()
        analysis = _make_analysis()

        with tempfile.TemporaryDirectory() as tmpdir:
            result = generate(
                provider=provider,
                skill=skill,
                paper=paper,
                analysis=analysis,
                output_dir=tmpdir,
            )
            assert result.success is True
            assert os.path.exists(os.path.join(tmpdir, "app.py"))

    # --- New subtype _detect_main_file tests ---

    def test_detect_main_file_app_streamlit(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            open(os.path.join(tmpdir, "app.py"), "w").close()
            assert _detect_main_file(tmpdir, "app_streamlit") == "app.py"

    def test_detect_main_file_page_readme(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            open(os.path.join(tmpdir, "README.md"), "w").close()
            assert _detect_main_file(tmpdir, "page_readme") == "README.md"

    def test_detect_main_file_page_blog(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            open(os.path.join(tmpdir, "index.html"), "w").close()
            assert _detect_main_file(tmpdir, "page_blog") == "index.html"

    def test_detect_main_file_diagram_graphviz(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            open(os.path.join(tmpdir, "build.py"), "w").close()
            assert _detect_main_file(tmpdir, "diagram_graphviz") == "build.py"

    def test_detect_main_file_slides(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            open(os.path.join(tmpdir, "build.py"), "w").close()
            assert _detect_main_file(tmpdir, "slides") == "build.py"

    def test_detect_main_file_latex(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            open(os.path.join(tmpdir, "presentation.tex"), "w").close()
            assert _detect_main_file(tmpdir, "latex") == "presentation.tex"
