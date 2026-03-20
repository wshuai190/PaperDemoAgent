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

SKILL SELECTION — choose the BEST skill for the paper's PURPOSE, not just its topic:
  ModelInferenceSkill       → paper introduces a NEW model the user should be able to RUN
                              (e.g. GPT-3, BERT, Stable Diffusion, DALL-E, Whisper)
  DataExplorerSkill         → paper introduces a NEW dataset to explore interactively
                              (e.g. SQuAD, LAION, The Pile, MS MARCO)
  AlgorithmVisualizerSkill  → paper introduces an ALGORITHM with clear sequential steps
                              (e.g. RAFT, beam search, k-means, attention mechanism walkthrough)
  FrameworkTutorialSkill    → paper describes a LIBRARY or FRAMEWORK users install and use
                              (e.g. Hugging Face Transformers, LangChain, PyTorch Lightning)
  FindingsDashboardSkill    → paper reports EMPIRICAL RESULTS (benchmarks, ablations, comparisons)
                              (e.g. "Scaling Laws for LLMs", evaluation papers, ablation studies)
  TheoreticalExplainerSkill → paper proposes a NEW ARCHITECTURE or deep THEORETICAL insight
                              (e.g. Transformer, attention mechanism, VAE, diffusion process)
  SurveyDashboardSkill      → paper is a SURVEY or REVIEW covering many related works
  FlowchartGeneratorSkill   → paper describes a COMPLEX PIPELINE or WORKFLOW best shown as a diagram
  StreamlitDemoSkill        → paper needs an INTERACTIVE DASHBOARD with many sliders/charts
  ReadmeGeneratorSkill      → paper needs a clean GITHUB README for a code release
  BlogExplainerSkill        → paper needs a NARRATIVE EXPLAINER for a general audience
  GraphvizDiagramSkill      → paper has a STATIC ARCHITECTURE that reads best as a clean SVG
  GeneralQASkill            → paper doesn't fit above; generic interactive Q&A interface

EXAMPLES of correct vs wrong skill choices:
  CORRECT: "Attention Is All You Need" → TheoreticalExplainerSkill (deep architecture paper)
  WRONG:   "Attention Is All You Need" → FlowchartGeneratorSkill (it's not primarily a pipeline)

  CORRECT: "GPT-3" (Language Models are Few-Shot Learners) → ModelInferenceSkill (runnable model)
  WRONG:   "GPT-3" → TheoreticalExplainerSkill (it does have theory, but the key demo is inference)

  CORRECT: "Scaling Laws for Neural LMs" → FindingsDashboardSkill (empirical charts and results)
  WRONG:   "Scaling Laws" → ModelInferenceSkill (no runnable model to demo)

  CORRECT: "SQuAD" → DataExplorerSkill (it's a dataset)
  WRONG:   "SQuAD" → ModelInferenceSkill (it's not a model)

FORM SELECTION — also choose the right form:
  presentation/revealjs  Best for: architecture papers, theoretical papers, conference talks
  presentation/pptx      Best for: papers that will be presented in PowerPoint/LibreOffice
  app/gradio             Best for: models with live inference, datasets with interactive search
  page/project           Best for: published research with hero/results/bibtex format
  page/blog              Best for: papers needing a narrative explanation for broad audiences
  diagram/mermaid        Best for: algorithmic pipelines, training loops, step-by-step processes
  diagram/graphviz       Best for: static architecture diagrams (cleaner than mermaid for this)

Return ONLY valid JSON, no markdown fences.

CONCRETE CLASSIFICATION EXAMPLES (follow these patterns):
  "Attention Is All You Need" (Transformer architecture, 2017)
    → paper_type: model, skill_hint: TheoreticalExplainerSkill, demo_form: presentation, demo_subtype: revealjs
    → reasoning: "Foundational architecture paper; a reveal.js slide deck with SVG transformer
                  diagram and attention visualization best captures the conceptual innovation."

  "BERT: Pre-training of Deep Bidirectional Transformers" (2019)
    → paper_type: model, skill_hint: ModelInferenceSkill, demo_form: app, demo_subtype: gradio
    → reasoning: "BERT is a pretrained model with live inference possible via HF; Gradio app
                  best demonstrates masked-LM and classification capabilities."

  "SQuAD: 100,000+ Questions for Machine Comprehension of Text" (2016)
    → paper_type: dataset, skill_hint: DataExplorerSkill, demo_form: app, demo_subtype: gradio
    → reasoning: "Dataset paper; Gradio app lets users browse passages, view annotations."

  "Language Models are Few-Shot Learners" (GPT-3, 2020)
    → paper_type: model, skill_hint: ModelInferenceSkill, demo_form: app, demo_subtype: gradio
    → reasoning: "GPT-3 is all about few-shot prompting; a Gradio app lets users interactively
                  try few-shot examples across tasks."

  "Scaling Laws for Neural Language Models" (2020)
    → paper_type: empirical, skill_hint: FindingsDashboardSkill, demo_form: page, demo_subtype: project
    → reasoning: "Empirical paper about scaling curves; a project page with Chart.js/D3 plots
                  of the scaling law charts best communicates the findings."

  "Denoising Diffusion Probabilistic Models" (DDPM, 2020)
    → paper_type: model, skill_hint: TheoreticalExplainerSkill, demo_form: presentation, demo_subtype: revealjs
    → reasoning: "Deep theoretical contribution (noising/denoising process); a reveal.js deck
                  with animated diffusion process diagrams explains the math intuitively."
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

        skill_hint = data.get("skill_hint", "GeneralQASkill")

        return PaperAnalysis(
            paper_type=data.get("paper_type", "other"),
            contribution=data.get("contribution", ""),
            skill_hint=skill_hint,
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

    def adapt_skill_hint_for_form(
        self,
        analysis: "PaperAnalysis",
        form_override: str,
    ) -> "PaperAnalysis":
        """Adapt skill_hint to match a user-specified form override.

        When the user explicitly sets --form (e.g. --form slides), the analyzer's
        automatic skill_hint may not match the requested form. For example, the
        analyzer may pick 'app' for "Attention Is All You Need" but the user wants
        'slides'. This method overrides skill_hint to the best skill for the
        requested form, preserving all other analysis fields.

        Args:
            analysis: The PaperAnalysis returned by analyze()
            form_override: The composite form key (e.g. 'slides', 'presentation', 'website')

        Returns:
            A new PaperAnalysis with skill_hint adapted to the override form.
        """
        # Map from composite form key → best-fit skill class name
        _FORM_SKILL_MAP = {
            "presentation":  "TheoreticalExplainerSkill",
            "slides":        "TheoreticalExplainerSkill",   # pptx
            "latex":         "TheoreticalExplainerSkill",   # beamer
            "website":       "FrameworkTutorialSkill",      # project page
            "page_readme":   "ReadmeGeneratorSkill",
            "page_blog":     "BlogExplainerSkill",
            "flowchart":     "FlowchartGeneratorSkill",
            "diagram_graphviz": "GraphvizDiagramSkill",
            "app":           "ModelInferenceSkill",
            "app_streamlit": "StreamlitDemoSkill",
        }
        adapted_hint = _FORM_SKILL_MAP.get(form_override, analysis.skill_hint)

        # If the LLM's choice was already correct (or more specific), keep it
        # — only override when there's a clear form→skill mapping conflict.
        current_hint = analysis.skill_hint

        # Skills that are form-agnostic (work well across all forms)
        _AGNOSTIC_SKILLS = {
            "TheoreticalExplainerSkill",
            "GeneralQASkill",
        }

        # If the current skill is agnostic or already correct, don't override
        if current_hint == adapted_hint or current_hint in _AGNOSTIC_SKILLS:
            return analysis

        import dataclasses
        return dataclasses.replace(analysis, skill_hint=adapted_hint)

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
