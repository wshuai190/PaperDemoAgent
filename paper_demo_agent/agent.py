"""PaperDemoAgent — the main orchestrator."""

from pathlib import Path
from typing import Callable, Optional

from paper_demo_agent import config as cfg
from paper_demo_agent.analysis.analyzer import PaperAnalyzer
from paper_demo_agent.generation.generator import generate
from paper_demo_agent.paper.models import DemoResult, Paper, PaperAnalysis, resolve_form_key
from paper_demo_agent.paper.parser import PaperParser
from paper_demo_agent.providers.base import BaseLLMProvider
from paper_demo_agent.providers.factory import create_provider
from paper_demo_agent.skills.router import SkillRouter


class PaperDemoAgent:
    """
    High-level agent that turns a scientific paper into a live demo.

    Usage:
        agent = PaperDemoAgent(provider="anthropic")
        result = agent.run("arxiv:1706.03762")
        print(result.run_command)
    """

    def __init__(
        self,
        provider: str = "anthropic",
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        **provider_kwargs,
    ):
        """
        Initialize the agent.

        Args:
            provider: Provider name ("anthropic", "openai", "deepseek", "qwen", "gemini", "minimax")
            model: Model override (uses provider default if not specified)
            api_key: API key override (uses config/env if not specified)
            **provider_kwargs: Extra args for the provider (e.g. group_id for MiniMax)
        """
        self._provider_name = provider
        self._model = model
        self._api_key = api_key
        self._provider_kwargs = provider_kwargs
        self._llm: Optional[BaseLLMProvider] = None

        self.parser = PaperParser()
        self.router = SkillRouter()

    @property
    def llm(self) -> BaseLLMProvider:
        if self._llm is None:
            self._llm = create_provider(
                self._provider_name,
                api_key=self._api_key,
                model=self._model,
                **self._provider_kwargs,
            )
        return self._llm

    def parse(self, source: str) -> Paper:
        """Parse a paper from an arXiv ID/URL, local PDF, or text."""
        return self.parser.parse(source)

    def parse_pdf_bytes(self, data: bytes, filename: str = "upload.pdf") -> Paper:
        """Parse a PDF from raw bytes (for file upload)."""
        return self.parser.parse_pdf_bytes(data, filename)

    def analyze(self, paper: Paper) -> PaperAnalysis:
        """Analyze a paper to determine the best demo form and type."""
        analyzer = PaperAnalyzer(self.llm)
        return analyzer.analyze(paper)

    def run(
        self,
        source: str,
        output_dir: Optional[str] = None,
        demo_form: Optional[str] = None,
        demo_type: Optional[str] = None,
        demo_subtype: Optional[str] = None,
        max_iter: int = 25,
        on_progress: Optional[Callable[[str], None]] = None,
    ) -> DemoResult:
        """
        Full pipeline: parse → analyze → route → generate.

        Args:
            source: arXiv ID/URL, local PDF path, or raw text
            output_dir: Where to write generated files (auto-generated if not set)
            demo_form: Override category ("app"|"presentation"|"page"|"diagram")
                       or legacy flat key ("app"|"website"|"flowchart"|etc.)
            demo_type: Override type ("theoretical"|"findings"|"user_demo")
            demo_subtype: Override subtype (e.g. "streamlit", "beamer", "readme")
            max_iter: Max agentic iterations
            on_progress: Callback for streaming progress text

        Returns:
            DemoResult with output paths and run command
        """
        def _emit(text: str) -> None:
            if on_progress:
                on_progress(text)

        # Resolve (category, subtype) → composite key early
        # If demo_form is already a composite key (backward compat), pass through
        if demo_form and demo_subtype:
            resolved_form = resolve_form_key(demo_form, demo_subtype)
        elif demo_form:
            resolved_form = resolve_form_key(demo_form) or demo_form
        else:
            resolved_form = None

        # Step 1: Parse paper
        _emit(f"Fetching paper: {source}\n")
        paper = self.parse(source)
        _emit(f"Paper fetched: \"{paper.title}\"\n")

        # Step 2: Analyze
        _emit("Analyzing paper...\n")
        analysis = self.analyze(paper)

        # Backfill paper metadata from LLM analysis (local PDFs lack this)
        self._backfill_metadata(paper, analysis)

        _emit(
            f"Analysis: {analysis.paper_type} paper | "
            f"Form: {analysis.demo_form} | Type: {analysis.demo_type}\n"
        )
        _emit(f"Reasoning: {analysis.reasoning}\n\n")

        # Step 3: Route to skill (pass resolved composite key)
        skill = self.router.route(analysis, demo_form=resolved_form)
        _emit(f"Skill selected: {skill.name}\n\n")

        # Step 4: Determine output dir
        if not output_dir:
            title_slug = "".join(
                c if c.isalnum() else "_" for c in paper.title[:40]
            ).strip("_").lower()
            out = cfg.get_output_dir(title_slug or "demo")
        else:
            out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)

        _emit(f"Output directory: {out}\n\n")

        # Step 5: Generate
        result = generate(
            provider=self.llm,
            skill=skill,
            paper=paper,
            analysis=analysis,
            output_dir=str(out),
            demo_form=resolved_form,
            demo_type=demo_type,
            max_iter=max_iter,
            on_progress=on_progress,
        )

        return result

    @staticmethod
    def _backfill_metadata(paper: Paper, analysis: PaperAnalysis) -> None:
        """Fill in paper.authors and paper.year from LLM analysis if missing."""
        llm_authors = getattr(analysis, "authors", None) or []
        llm_year = getattr(analysis, "year", None)
        if not paper.authors and llm_authors:
            paper.authors = llm_authors
        if not paper.year and llm_year:
            paper.year = llm_year

    def run_from_pdf(
        self,
        pdf_data: bytes,
        filename: str = "upload.pdf",
        **kwargs,
    ) -> DemoResult:
        """
        Convenience: run from raw PDF bytes.
        Useful for UI file uploads.
        """
        paper = self.parse_pdf_bytes(pdf_data, filename)

        def _emit(text: str) -> None:
            if kwargs.get("on_progress"):
                kwargs["on_progress"](text)

        # Resolve (category, subtype) → composite key
        raw_form = kwargs.get("demo_form")
        raw_subtype = kwargs.get("demo_subtype")
        if raw_form and raw_subtype:
            resolved_form = resolve_form_key(raw_form, raw_subtype)
        elif raw_form:
            resolved_form = resolve_form_key(raw_form) or raw_form
        else:
            resolved_form = None

        _emit(f"Paper loaded from upload: \"{paper.title}\"\n")
        analysis = self.analyze(paper)
        self._backfill_metadata(paper, analysis)
        _emit(f"Analysis: {analysis.paper_type} | Form: {analysis.demo_form}\n\n")

        skill = self.router.route(analysis, demo_form=resolved_form)
        _emit(f"Skill: {skill.name}\n\n")

        title_slug = "".join(
            c if c.isalnum() else "_" for c in paper.title[:40]
        ).strip("_").lower()
        out = cfg.get_output_dir(title_slug or "demo")
        out.mkdir(parents=True, exist_ok=True)

        return generate(
            provider=self.llm,
            skill=skill,
            paper=paper,
            analysis=analysis,
            output_dir=str(out),
            demo_form=resolved_form,
            demo_type=kwargs.get("demo_type"),
            max_iter=kwargs.get("max_iter", 25),
            on_progress=kwargs.get("on_progress"),
        )
