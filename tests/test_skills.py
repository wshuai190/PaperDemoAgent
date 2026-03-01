"""Tests for skill routing and base skill implementations."""

import pytest

from paper_demo_agent.paper.models import Paper, PaperAnalysis
from paper_demo_agent.skills.base import BaseSkill
from paper_demo_agent.skills.router import SkillRouter
from paper_demo_agent.skills.model_inference import ModelInferenceSkill
from paper_demo_agent.skills.general_qa import GeneralQASkill
from paper_demo_agent.skills.theoretical_explainer import TheoreticalExplainerSkill
from paper_demo_agent.skills.streamlit_demo import StreamlitDemoSkill
from paper_demo_agent.skills.readme_generator import ReadmeGeneratorSkill
from paper_demo_agent.skills.blog_explainer import BlogExplainerSkill
from paper_demo_agent.skills.graphviz_diagram import GraphvizDiagramSkill


def _make_analysis(paper_type="model", skill_hint="ModelInferenceSkill", demo_form="app", demo_type="user_demo", demo_subtype=""):
    return PaperAnalysis(
        paper_type=paper_type,
        contribution="A novel contribution",
        skill_hint=skill_hint,
        demo_form=demo_form,
        demo_type=demo_type,
        demo_subtype=demo_subtype,
        hf_model_query="transformer attention",
        required_keys=[],
        interaction_pattern="User inputs text",
        reasoning="Because reasons.",
    )


def _make_paper():
    return Paper(
        title="Test Paper",
        abstract="We present a new model.",
        full_text="Full text here.",
        sections={"Introduction": "Intro text."},
        source_type="arxiv",
        source="1706.03762",
    )


class TestSkillRouter:
    def setup_method(self):
        self.router = SkillRouter()

    def test_routes_model_to_inference(self):
        analysis = _make_analysis("model", "ModelInferenceSkill")
        skill = self.router.route(analysis)
        assert isinstance(skill, ModelInferenceSkill)

    def test_routes_by_paper_type_fallback(self):
        analysis = _make_analysis("theory", "UnknownSkill")
        skill = self.router.route(analysis)
        assert isinstance(skill, TheoreticalExplainerSkill)

    def test_fallback_to_general_qa(self):
        analysis = _make_analysis("other", "NotASkill")
        skill = self.router.route(analysis)
        assert isinstance(skill, GeneralQASkill)

    def test_override_skill(self):
        analysis = _make_analysis("model", "ModelInferenceSkill")
        skill = self.router.route(analysis, override_skill="GeneralQASkill")
        assert isinstance(skill, GeneralQASkill)

    def test_list_skills(self):
        from paper_demo_agent.skills.flowchart_generator import FlowchartGeneratorSkill
        skills = self.router.list_skills()
        assert "ModelInferenceSkill" in skills
        assert "GeneralQASkill" in skills
        assert "FlowchartGeneratorSkill" in skills
        assert "StreamlitDemoSkill" in skills
        assert "ReadmeGeneratorSkill" in skills
        assert "BlogExplainerSkill" in skills
        assert "GraphvizDiagramSkill" in skills
        assert len(skills) == 13

    # --- New category+subtype routing tests ---

    def test_routes_flowchart_form_locked(self):
        analysis = _make_analysis("algorithm", "AlgorithmVisualizerSkill", "flowchart")
        skill = self.router.route(analysis, demo_form="flowchart")
        from paper_demo_agent.skills.flowchart_generator import FlowchartGeneratorSkill
        assert isinstance(skill, FlowchartGeneratorSkill)

    def test_routes_app_streamlit_form_locked(self):
        analysis = _make_analysis("model", "ModelInferenceSkill", "app_streamlit")
        skill = self.router.route(analysis, demo_form="app_streamlit")
        assert isinstance(skill, StreamlitDemoSkill)

    def test_routes_page_readme_form_locked(self):
        analysis = _make_analysis("framework", "FrameworkTutorialSkill", "page_readme")
        skill = self.router.route(analysis, demo_form="page_readme")
        assert isinstance(skill, ReadmeGeneratorSkill)

    def test_routes_page_blog_form_locked(self):
        analysis = _make_analysis("theory", "TheoreticalExplainerSkill", "page_blog")
        skill = self.router.route(analysis, demo_form="page_blog")
        assert isinstance(skill, BlogExplainerSkill)

    def test_routes_diagram_graphviz_form_locked(self):
        analysis = _make_analysis("algorithm", "AlgorithmVisualizerSkill", "diagram_graphviz")
        skill = self.router.route(analysis, demo_form="diagram_graphviz")
        assert isinstance(skill, GraphvizDiagramSkill)

    def test_slides_routes_to_theoretical(self):
        analysis = _make_analysis("theory", "TheoreticalExplainerSkill", "slides")
        skill = self.router.route(analysis, demo_form="slides")
        assert isinstance(skill, TheoreticalExplainerSkill)

    def test_latex_routes_to_theoretical(self):
        analysis = _make_analysis("theory", "TheoreticalExplainerSkill", "latex")
        skill = self.router.route(analysis, demo_form="latex")
        assert isinstance(skill, TheoreticalExplainerSkill)


class TestModelInferenceSkill:
    def test_get_system_prompt(self):
        skill = ModelInferenceSkill()
        paper = _make_paper()
        analysis = _make_analysis()
        prompt = skill.get_system_prompt(paper, analysis, "app", "user_demo")
        assert "Gradio" in prompt
        assert paper.title in prompt

    def test_get_initial_message(self):
        skill = ModelInferenceSkill()
        paper = _make_paper()
        analysis = _make_analysis()
        msg = skill.get_initial_message(paper, analysis, "app", "user_demo")
        assert paper.title in msg


class TestTheoreticalExplainerSkill:
    def test_system_prompt_includes_revealjs(self):
        skill = TheoreticalExplainerSkill()
        paper = _make_paper()
        analysis = _make_analysis("theory", "TheoreticalExplainerSkill", "presentation", "theoretical")
        prompt = skill.get_system_prompt(paper, analysis, "presentation", "theoretical")
        assert "reveal.js" in prompt or "MathJax" in prompt


class TestStreamlitDemoSkill:
    def test_instantiation(self):
        skill = StreamlitDemoSkill()
        assert skill.name == "StreamlitDemoSkill"

    def test_system_prompt_includes_streamlit(self):
        skill = StreamlitDemoSkill()
        paper = _make_paper()
        analysis = _make_analysis("model", "StreamlitDemoSkill", "app_streamlit", "user_demo")
        prompt = skill.get_system_prompt(paper, analysis, "app_streamlit", "user_demo")
        assert "streamlit" in prompt.lower() or "Streamlit" in prompt


class TestReadmeGeneratorSkill:
    def test_instantiation(self):
        skill = ReadmeGeneratorSkill()
        assert skill.name == "ReadmeGeneratorSkill"

    def test_system_prompt_includes_markdown(self):
        skill = ReadmeGeneratorSkill()
        paper = _make_paper()
        analysis = _make_analysis("framework", "ReadmeGeneratorSkill", "page_readme", "findings")
        prompt = skill.get_system_prompt(paper, analysis, "page_readme", "findings")
        assert "README" in prompt or "Markdown" in prompt or "markdown" in prompt


class TestBlogExplainerSkill:
    def test_instantiation(self):
        skill = BlogExplainerSkill()
        assert skill.name == "BlogExplainerSkill"

    def test_system_prompt_includes_distill(self):
        skill = BlogExplainerSkill()
        paper = _make_paper()
        analysis = _make_analysis("theory", "BlogExplainerSkill", "page_blog", "theoretical")
        prompt = skill.get_system_prompt(paper, analysis, "page_blog", "theoretical")
        assert "distill" in prompt.lower() or "d-article" in prompt or "blog" in prompt.lower()


class TestGraphvizDiagramSkill:
    def test_instantiation(self):
        skill = GraphvizDiagramSkill()
        assert skill.name == "GraphvizDiagramSkill"

    def test_system_prompt_includes_graphviz(self):
        skill = GraphvizDiagramSkill()
        paper = _make_paper()
        analysis = _make_analysis("algorithm", "GraphvizDiagramSkill", "diagram_graphviz", "theoretical")
        prompt = skill.get_system_prompt(paper, analysis, "diagram_graphviz", "theoretical")
        assert "graphviz" in prompt.lower() or "Digraph" in prompt or "SVG" in prompt
