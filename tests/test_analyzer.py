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

    def test_year_parsed_as_int(self):
        response = {
            "paper_type": "model",
            "contribution": "Test",
            "skill_hint": "ModelInferenceSkill",
            "demo_form": "app",
            "demo_subtype": "gradio",
            "demo_type": "user_demo",
            "hf_model_query": "",
            "required_keys": [],
            "interaction_pattern": "",
            "reasoning": "",
            "year": "2024",  # string from LLM
            "authors": ["Alice", "Bob"],
        }
        provider = _make_provider(response)
        analysis = PaperAnalyzer(provider).analyze(_make_paper())
        assert analysis.year == 2024
        assert isinstance(analysis.year, int)


class TestAdaptSkillHintForForm:
    """Tests for PaperAnalyzer.adapt_skill_hint_for_form()."""

    def _make_analysis(self, skill_hint: str, demo_form: str = "app") -> PaperAnalysis:
        return PaperAnalysis(
            paper_type="model",
            contribution="A new model",
            skill_hint=skill_hint,
            demo_form=demo_form,
            demo_type="user_demo",
            demo_subtype="",
            hf_model_query="",
            required_keys=[],
            interaction_pattern="",
            reasoning="",
        )

    def _make_analyzer(self) -> PaperAnalyzer:
        return PaperAnalyzer(MagicMock())

    def test_overrides_app_skill_to_presentation(self):
        """When form is 'presentation', skill should become TheoreticalExplainerSkill."""
        analysis = self._make_analysis("ModelInferenceSkill", "app")
        result = self._make_analyzer().adapt_skill_hint_for_form(analysis, "presentation")
        assert result.skill_hint == "TheoreticalExplainerSkill"

    def test_overrides_app_skill_to_slides(self):
        """When form is 'slides' (pptx), skill should become TheoreticalExplainerSkill."""
        analysis = self._make_analysis("ModelInferenceSkill", "app")
        result = self._make_analyzer().adapt_skill_hint_for_form(analysis, "slides")
        assert result.skill_hint == "TheoreticalExplainerSkill"

    def test_overrides_model_to_readme(self):
        """When form is 'page_readme', skill should become ReadmeGeneratorSkill."""
        analysis = self._make_analysis("ModelInferenceSkill", "app")
        result = self._make_analyzer().adapt_skill_hint_for_form(analysis, "page_readme")
        assert result.skill_hint == "ReadmeGeneratorSkill"

    def test_overrides_to_blog(self):
        analysis = self._make_analysis("FindingsDashboardSkill", "website")
        result = self._make_analyzer().adapt_skill_hint_for_form(analysis, "page_blog")
        assert result.skill_hint == "BlogExplainerSkill"

    def test_overrides_to_flowchart(self):
        analysis = self._make_analysis("ModelInferenceSkill", "app")
        result = self._make_analyzer().adapt_skill_hint_for_form(analysis, "flowchart")
        assert result.skill_hint == "FlowchartGeneratorSkill"

    def test_overrides_to_graphviz(self):
        analysis = self._make_analysis("ModelInferenceSkill", "app")
        result = self._make_analyzer().adapt_skill_hint_for_form(analysis, "diagram_graphviz")
        assert result.skill_hint == "GraphvizDiagramSkill"

    def test_does_not_override_already_correct_skill(self):
        """TheoreticalExplainerSkill + presentation → no change."""
        analysis = self._make_analysis("TheoreticalExplainerSkill", "presentation")
        result = self._make_analyzer().adapt_skill_hint_for_form(analysis, "presentation")
        assert result.skill_hint == "TheoreticalExplainerSkill"

    def test_agnostic_skill_not_overridden(self):
        """GeneralQASkill is agnostic — keep it even if form implies something else."""
        analysis = self._make_analysis("GeneralQASkill", "app")
        result = self._make_analyzer().adapt_skill_hint_for_form(analysis, "presentation")
        assert result.skill_hint == "GeneralQASkill"

    def test_unknown_form_returns_unchanged(self):
        """Unknown form override → no change to skill_hint."""
        analysis = self._make_analysis("ModelInferenceSkill", "app")
        result = self._make_analyzer().adapt_skill_hint_for_form(analysis, "unknown_form_xyz")
        assert result.skill_hint == "ModelInferenceSkill"

    def test_other_fields_preserved(self):
        """adapt_skill_hint_for_form should only change skill_hint."""
        analysis = self._make_analysis("ModelInferenceSkill", "app")
        analysis_with_contribution = PaperAnalysis(
            paper_type="model",
            contribution="Important contribution",
            skill_hint="ModelInferenceSkill",
            demo_form="app",
            demo_type="user_demo",
            demo_subtype="gradio",
            hf_model_query="bert model",
            required_keys=["HF_TOKEN"],
            interaction_pattern="User inputs text",
            reasoning="It's a model",
        )
        result = self._make_analyzer().adapt_skill_hint_for_form(
            analysis_with_contribution, "presentation"
        )
        assert result.contribution == "Important contribution"
        assert result.hf_model_query == "bert model"
        assert result.required_keys == ["HF_TOKEN"]
        assert result.demo_subtype == "gradio"
        assert result.skill_hint == "TheoreticalExplainerSkill"  # changed
