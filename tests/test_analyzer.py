"""Tests for paper analyzer."""

import json
import pytest
from unittest.mock import MagicMock

from paper_demo_agent.analysis.analyzer import PaperAnalyzer
from paper_demo_agent.paper.models import Paper, PaperAnalysis
from paper_demo_agent.providers.base import LLMResponse


def _make_paper(title="Test Paper", paper_type="model"):
    return Paper(
        title=title,
        abstract="We present a new transformer-based model.",
        full_text="Full text...",
        sections={"Introduction": "We present..."},
        source_type="arxiv",
        source="1706.03762",
    )


def _make_provider(response_json: dict):
    provider = MagicMock()
    provider.chat.return_value = LLMResponse(
        content=json.dumps(response_json),
        tool_calls=[],
        stop_reason="end_turn",
    )
    return provider


class TestPaperAnalyzer:
    def test_analyze_returns_analysis(self):
        response = {
            "paper_type": "model",
            "contribution": "A new attention mechanism",
            "skill_hint": "ModelInferenceSkill",
            "demo_form": "app",
            "demo_subtype": "gradio",
            "demo_type": "user_demo",
            "hf_model_query": "transformer attention",
            "required_keys": ["HUGGINGFACE_TOKEN"],
            "interaction_pattern": "User inputs text, model returns attended output",
            "reasoning": "This is an ML model paper, best shown as an interactive inference demo.",
        }
        provider = _make_provider(response)
        analyzer = PaperAnalyzer(provider)
        analysis = analyzer.analyze(_make_paper())

        assert isinstance(analysis, PaperAnalysis)
        assert analysis.paper_type == "model"
        assert analysis.demo_form == "app"  # composite key for (app, gradio) is "app"
        assert analysis.demo_type == "user_demo"
        assert analysis.skill_hint == "ModelInferenceSkill"

    def test_analyze_new_subtype_streamlit(self):
        response = {
            "paper_type": "model",
            "contribution": "A dashboard tool",
            "skill_hint": "StreamlitDemoSkill",
            "demo_form": "app",
            "demo_subtype": "streamlit",
            "demo_type": "user_demo",
            "hf_model_query": "dashboard",
            "required_keys": [],
            "interaction_pattern": "User explores data",
            "reasoning": "Streamlit is better for data dashboards.",
        }
        provider = _make_provider(response)
        analyzer = PaperAnalyzer(provider)
        analysis = analyzer.analyze(_make_paper())

        assert isinstance(analysis, PaperAnalysis)
        assert analysis.demo_form == "app_streamlit"  # composite key
        assert analysis.demo_subtype == "streamlit"

    def test_analyze_diagram_graphviz(self):
        response = {
            "paper_type": "algorithm",
            "contribution": "A pipeline architecture",
            "skill_hint": "GraphvizDiagramSkill",
            "demo_form": "diagram",
            "demo_subtype": "graphviz",
            "demo_type": "theoretical",
            "hf_model_query": "",
            "required_keys": [],
            "interaction_pattern": "View architecture diagram",
            "reasoning": "Publication-quality diagram needed.",
        }
        provider = _make_provider(response)
        analyzer = PaperAnalyzer(provider)
        analysis = analyzer.analyze(_make_paper())

        assert isinstance(analysis, PaperAnalysis)
        assert analysis.demo_form == "diagram_graphviz"  # composite key
        assert analysis.demo_subtype == "graphviz"

    def test_parse_json_with_fences(self):
        analyzer = PaperAnalyzer(MagicMock())
        raw = '```json\n{"paper_type": "model", "contribution": "test", "skill_hint": "ModelInferenceSkill", "demo_form": "app", "demo_subtype": "gradio", "demo_type": "user_demo", "hf_model_query": "test", "required_keys": [], "interaction_pattern": "test", "reasoning": "test"}\n```'
        result = analyzer._parse_json(raw)
        assert result["paper_type"] == "model"
        assert result["demo_subtype"] == "gradio"

    def test_parse_json_invalid_returns_defaults(self):
        analyzer = PaperAnalyzer(MagicMock())
        result = analyzer._parse_json("not valid json at all !!!!")
        assert result["paper_type"] == "other"
        assert result["skill_hint"] == "GeneralQASkill"
