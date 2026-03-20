"""Paper analyzer — uses an LLM to classify a paper and recommend a demo form/type/skill."""

import json
import re
from typing import Optional

from paper_demo_agent.paper.models import Paper, PaperAnalysis, resolve_form_key
from paper_demo_agent.providers.base import BaseLLMProvider


_ANALYSIS_SYSTEM = """You are an expert at reading scientific papers and deciding what kind of interactive demo would best showcase them.

You will be given the content of a paper. Analyze it and return a JSON object with these fields:

{
  "paper_type": "<model|dataset|algorithm|framework|survey|empirical|theory|other>",
  "authors": ["<list of author full names, e.g. 'John Smith', 'Jane Doe'>"],
  "year": <publication year as integer, e.g. 2024>,
  "contribution": "<one sentence describing the core contribution>",
  "skill_hint": "<recommended skill class: ModelInferenceSkill|DataExplorerSkill|AlgorithmVisualizerSkill|FrameworkTutorialSkill|FindingsDashboardSkill|TheoreticalExplainerSkill|SurveyDashboardSkill|GeneralQASkill|FlowchartGeneratorSkill|StreamlitDemoSkill|ReadmeGeneratorSkill|BlogExplainerSkill|GraphvizDiagramSkill>",
  "demo_form": "<app|presentation|page|diagram>",
  "demo_subtype": "<gradio|streamlit|revealjs|beamer|pptx|project|readme|blog|mermaid|graphviz>",
  "demo_type": "<theoretical|findings|user_demo>",
  "hf_model_query": "<a Hugging Face Hub search query to find a relevant model or dataset>",
  "required_keys": ["<list of API key names needed, e.g. HUGGINGFACE_TOKEN>"],
  "interaction_pattern": "<brief description of how users will interact with the demo>",
  "reasoning": "<2-3 sentences explaining why you chose this form and type>"
}

CATEGORY + SUBTYPE GUIDE:
  app (interactive applications):
    - gradio (default): Gradio 5 Python app → HuggingFace Spaces
    - streamlit: Streamlit app with interactive widgets and dashboards
  presentation (slide-based):
    - revealjs (default): reveal.js 5.2.1 HTML slides — web-based sharing
    - beamer: LaTeX Beamer — publication-quality typeset slides with math
    - pptx: python-pptx PowerPoint deck — opens in PowerPoint/LibreOffice
  page (static pages / documents):
    - project (default): Nerfies/Distill.pub project page — hero, method, results, BibTeX
    - readme: GitHub README with shields.io badges, Mermaid diagrams, comparison tables
    - blog: Distill.pub interactive blog article with D3.js visualizations
  diagram (visual diagrams):
    - mermaid (default): Interactive Mermaid.js flowchart explorer — clickable, zoomable
    - graphviz: Python graphviz → SVG/PNG publication-quality architecture diagrams

Decision guidelines:
- New ML model with live inference → ModelInferenceSkill, app/gradio, user_demo
- New dataset → DataExplorerSkill, app/gradio, user_demo
- New algorithm / method with clear steps → AlgorithmVisualizerSkill, diagram/mermaid, theoretical
- New framework / library → FrameworkTutorialSkill, page/project, user_demo
- Survey / review paper → SurveyDashboardSkill, page/project, findings
- Theory / math paper → TheoreticalExplainerSkill, presentation/beamer, theoretical
- Empirical study → FindingsDashboardSkill, page/project, findings
- Complex architecture / pipeline → FlowchartGeneratorSkill, diagram/mermaid, theoretical
- Conference talk / overview → TheoreticalExplainerSkill, presentation/pptx, theoretical
- Paper needing web sharing → presentation/revealjs
- Paper with dashboard/data exploration → StreamlitDemoSkill, app/streamlit, user_demo
- Paper needing quick documentation → ReadmeGeneratorSkill, page/readme, findings
- Paper needing deep explainer → BlogExplainerSkill, page/blog, theoretical
- Paper with static architecture visualization → GraphvizDiagramSkill, diagram/graphviz, theoretical
- Anything else → GeneralQASkill, app/gradio, user_demo

Return ONLY valid JSON, no markdown fences.

EXAMPLES of good classifications:
- "Attention Is All You Need" (new architecture) → paper_type: model, skill: TheoreticalExplainerSkill, form: presentation/revealjs
- "BERT" (pretrained model) → paper_type: model, skill: ModelInferenceSkill, form: app/gradio
- "SQuAD" (benchmark dataset) → paper_type: dataset, skill: DataExplorerSkill, form: app/gradio
"""


class PaperAnalyzer:
    """Analyzes a paper using an LLM to recommend demo form and type."""

    def __init__(self, provider: BaseLLMProvider):
        self.provider = provider

    def analyze(self, paper: Paper) -> PaperAnalysis:
        """Analyze a paper and return a PaperAnalysis.

        If the provider supports native PDF input and the paper has raw bytes,
        the PDF is sent directly (preserving figures, tables, equations).
        Otherwise falls back to extracted text.
        """
        messages = [{"role": "user", "content": "Please analyze this paper:"}]

        if paper.pdf_bytes and self.provider.supports_native_pdf:
            # PDF mode needs more tokens — the model describes figures/tables before producing JSON
            response = self.provider.chat_with_pdf(
                messages=messages,
                pdf_bytes=paper.pdf_bytes,
                system=_ANALYSIS_SYSTEM,
                max_tokens=8192,
            )
        else:
            context = paper.get_context(max_chars=12000)
            messages = [{"role": "user", "content": f"Please analyze this paper:\n\n{context}"}]
            response = self.provider.chat(
                messages=messages,
                system=_ANALYSIS_SYSTEM,
                max_tokens=8192,
            )

        raw = response.content.strip()
        data = self._parse_json(raw)

        # Parse year safely (LLM may return string or int)
        raw_year = data.get("year")
        year = None
        if raw_year is not None:
            try:
                year = int(raw_year)
            except (ValueError, TypeError):
                pass

        # Resolve the two-level (category, subtype) → internal composite key
        raw_form = data.get("demo_form", "app")
        raw_subtype = data.get("demo_subtype", "")
        composite_key = resolve_form_key(raw_form, raw_subtype or None)
        # If resolve_form_key returns None (shouldn't happen), fall back to raw_form
        resolved_form = composite_key or raw_form

        return PaperAnalysis(
            paper_type=data.get("paper_type", "other"),
            contribution=data.get("contribution", ""),
            skill_hint=data.get("skill_hint", "GeneralQASkill"),
            demo_form=resolved_form,
            demo_type=data.get("demo_type", "user_demo"),
            hf_model_query=data.get("hf_model_query", paper.title),
            required_keys=data.get("required_keys", []),
            interaction_pattern=data.get("interaction_pattern", ""),
            reasoning=data.get("reasoning", ""),
            authors=data.get("authors", []),
            year=year,
            demo_subtype=raw_subtype,
        )

    def _parse_json(self, text: str) -> dict:
        """Extract JSON from LLM response, handling markdown fences."""
        # Strip markdown fences if present
        clean = re.sub(r"```(?:json)?\s*", "", text).strip().rstrip("`").strip()
        try:
            return json.loads(clean)
        except json.JSONDecodeError:
            # Try extracting a JSON object
            m = re.search(r"\{.*\}", clean, re.DOTALL)
            if m:
                try:
                    return json.loads(m.group(0))
                except json.JSONDecodeError:
                    pass
            # Log truncated raw response for debugging, then return safe defaults
            import sys
            preview = text[:500].replace("\n", " ")
            print(f"[analyzer] JSON parse failed. Raw response preview: {preview!r}", file=sys.stderr)
            return {
                "paper_type": "other",
                "contribution": "Unknown",
                "skill_hint": "GeneralQASkill",
                "demo_form": "app",
                "demo_subtype": "gradio",
                "demo_type": "user_demo",
                "hf_model_query": "",
                "required_keys": [],
                "interaction_pattern": "User interacts with a Q&A interface about the paper",
                "reasoning": "Could not parse LLM analysis; using fallback.",
            }
