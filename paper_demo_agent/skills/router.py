"""Skill router — maps paper analysis to the appropriate skill."""

from typing import Dict, Optional, Type

from paper_demo_agent.paper.models import PaperAnalysis
from paper_demo_agent.skills.base import BaseSkill


class SkillRouter:
    """Routes a PaperAnalysis to the correct BaseSkill subclass."""

    def __init__(self):
        self._registry: Dict[str, Type[BaseSkill]] = {}
        self._load_defaults()

    def _load_defaults(self) -> None:
        from paper_demo_agent.skills.model_inference import ModelInferenceSkill
        from paper_demo_agent.skills.data_explorer import DataExplorerSkill
        from paper_demo_agent.skills.algorithm_visualizer import AlgorithmVisualizerSkill
        from paper_demo_agent.skills.framework_tutorial import FrameworkTutorialSkill
        from paper_demo_agent.skills.findings_dashboard import FindingsDashboardSkill
        from paper_demo_agent.skills.theoretical_explainer import TheoreticalExplainerSkill
        from paper_demo_agent.skills.survey_dashboard import SurveyDashboardSkill
        from paper_demo_agent.skills.general_qa import GeneralQASkill
        from paper_demo_agent.skills.flowchart_generator import FlowchartGeneratorSkill
        from paper_demo_agent.skills.streamlit_demo import StreamlitDemoSkill
        from paper_demo_agent.skills.readme_generator import ReadmeGeneratorSkill
        from paper_demo_agent.skills.blog_explainer import BlogExplainerSkill
        from paper_demo_agent.skills.graphviz_diagram import GraphvizDiagramSkill

        self.register("ModelInferenceSkill", ModelInferenceSkill)
        self.register("DataExplorerSkill", DataExplorerSkill)
        self.register("AlgorithmVisualizerSkill", AlgorithmVisualizerSkill)
        self.register("FrameworkTutorialSkill", FrameworkTutorialSkill)
        self.register("FindingsDashboardSkill", FindingsDashboardSkill)
        self.register("TheoreticalExplainerSkill", TheoreticalExplainerSkill)
        self.register("SurveyDashboardSkill", SurveyDashboardSkill)
        self.register("GeneralQASkill", GeneralQASkill)
        self.register("FlowchartGeneratorSkill", FlowchartGeneratorSkill)
        self.register("StreamlitDemoSkill", StreamlitDemoSkill)
        self.register("ReadmeGeneratorSkill", ReadmeGeneratorSkill)
        self.register("BlogExplainerSkill", BlogExplainerSkill)
        self.register("GraphvizDiagramSkill", GraphvizDiagramSkill)

    def register(self, name: str, skill_class: Type[BaseSkill]) -> None:
        self._registry[name] = skill_class

    # Skills that are form-specific and should NOT be used for other forms
    _FORM_LOCKED_SKILLS = {
        "FlowchartGeneratorSkill": {"flowchart"},
        "GraphvizDiagramSkill":    {"diagram_graphviz"},
        "StreamlitDemoSkill":      {"app_streamlit"},
        "ReadmeGeneratorSkill":    {"page_readme"},
        "BlogExplainerSkill":      {"page_blog"},
    }

    # Default skill to use per form when the analysis skill_hint is incompatible
    _FORM_DEFAULT_SKILLS = {
        "website":          "FrameworkTutorialSkill",
        "app":              "GeneralQASkill",
        "app_streamlit":    "StreamlitDemoSkill",
        "presentation":     "AlgorithmVisualizerSkill",
        "flowchart":        "FlowchartGeneratorSkill",
        "slides":           "TheoreticalExplainerSkill",
        "latex":            "TheoreticalExplainerSkill",
        "page_readme":      "ReadmeGeneratorSkill",
        "page_blog":        "BlogExplainerSkill",
        "diagram_graphviz": "GraphvizDiagramSkill",
    }

    def route(
        self,
        analysis: PaperAnalysis,
        override_skill: Optional[str] = None,
        demo_form: Optional[str] = None,
    ) -> BaseSkill:
        """Return the appropriate skill instance for a paper analysis."""
        form = demo_form or analysis.demo_form

        # Form-locked forms: always use their designated skill regardless of paper type
        if form == "flowchart":
            return self._registry["FlowchartGeneratorSkill"]()
        if form == "diagram_graphviz":
            return self._registry["GraphvizDiagramSkill"]()
        if form == "app_streamlit":
            return self._registry["StreamlitDemoSkill"]()
        if form == "page_readme":
            return self._registry["ReadmeGeneratorSkill"]()
        if form == "page_blog":
            return self._registry["BlogExplainerSkill"]()

        # slides / latex forms ALWAYS use TheoreticalExplainerSkill —
        # it has python-pptx 1.0.0 API and LaTeX/Beamer templates baked in.
        # Only an explicit user override_skill can change this.
        if form in ("slides", "latex"):
            if override_skill and override_skill in self._registry:
                return self._registry[override_skill]()
            return self._registry["TheoreticalExplainerSkill"]()

        skill_name = override_skill or analysis.skill_hint

        # Check form-lock: some skills (e.g. FlowchartGeneratorSkill) only work
        # with their designated form.  If the user overrode the form to something
        # else, skip the analysis hint and fall through to the paper_type map.
        if skill_name in self._registry:
            allowed_forms = self._FORM_LOCKED_SKILLS.get(skill_name)
            if allowed_forms is None or form in allowed_forms:
                return self._registry[skill_name]()
            # Skill is locked to a different form — fall through

        # Fallback by paper_type
        type_map = {
            "model":     "ModelInferenceSkill",
            "dataset":   "DataExplorerSkill",
            "algorithm": "AlgorithmVisualizerSkill",
            "framework": "FrameworkTutorialSkill",
            "empirical": "FindingsDashboardSkill",
            "theory":    "TheoreticalExplainerSkill",
            "survey":    "SurveyDashboardSkill",
        }
        fallback_name = type_map.get(analysis.paper_type, "GeneralQASkill")
        return self._registry[fallback_name]()

    def list_skills(self) -> Dict[str, str]:
        """Return a dict of skill name → description."""
        return {
            name: cls().description for name, cls in self._registry.items()
        }
