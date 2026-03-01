"""Data models for Paper Demo Agent."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


# ═══════════════════════════════════════════════════════════════════════════════
# Two-level category + subtype taxonomy
# ═══════════════════════════════════════════════════════════════════════════════

FORM_CATEGORIES = ["app", "presentation", "page", "diagram"]

CATEGORY_SUBTYPES: Dict[str, List[str]] = {
    "app":          ["gradio", "streamlit"],
    "presentation": ["revealjs", "beamer", "pptx"],
    "page":         ["project", "readme", "blog"],
    "diagram":      ["mermaid", "graphviz"],
}

CATEGORY_DEFAULTS: Dict[str, str] = {
    "app": "gradio",
    "presentation": "revealjs",
    "page": "project",
    "diagram": "mermaid",
}

# (category, subtype) → internal flat key used in FORM_SPECS, _RESEARCH_QUERIES, etc.
COMPOSITE_KEY: Dict[tuple, str] = {
    ("app", "gradio"):            "app",
    ("app", "streamlit"):         "app_streamlit",
    ("presentation", "revealjs"): "presentation",
    ("presentation", "beamer"):   "latex",
    ("presentation", "pptx"):     "slides",
    ("page", "project"):          "website",
    ("page", "readme"):           "page_readme",
    ("page", "blog"):             "page_blog",
    ("diagram", "mermaid"):       "flowchart",
    ("diagram", "graphviz"):      "diagram_graphviz",
}


def resolve_form_key(category: Optional[str], subtype: Optional[str] = None) -> Optional[str]:
    """Resolve a (category, subtype) pair to the internal flat form key.

    If category is None, returns None (auto-detect).
    If subtype is None, uses the default subtype for the category.
    """
    if category is None:
        return None
    sub = subtype or CATEGORY_DEFAULTS.get(category, "")
    return COMPOSITE_KEY.get((category, sub), category)


@dataclass
class Paper:
    """Represents a parsed scientific paper."""
    title: str
    abstract: str
    full_text: str
    sections: Dict[str, str]
    source_type: str    # "arxiv" | "pdf" | "url" | "text"
    source: str         # original input (URL, file path, or text snippet)
    authors: List[str] = field(default_factory=list)
    year: Optional[int] = None
    arxiv_id: Optional[str] = None
    pdf_bytes: Optional[bytes] = None   # Raw PDF bytes for multimodal providers (capped at 20 MB)

    def get_context(self, max_chars: int = 12000) -> str:
        """Return paper content suitable for LLM context window."""
        parts = []
        if self.title:
            parts.append(f"Title: {self.title}")
        if self.authors:
            parts.append(f"Authors: {', '.join(self.authors)}")
        if self.year:
            parts.append(f"Year: {self.year}")
        if self.abstract:
            parts.append(f"\nAbstract:\n{self.abstract}")

        # Add sections selectively until limit
        if self.sections:
            parts.append("\nSections:")
            for name, content in self.sections.items():
                chunk = f"\n## {name}\n{content}"
                if sum(len(p) for p in parts) + len(chunk) > max_chars:
                    parts.append(f"\n## {name}\n[truncated]")
                    break
                parts.append(chunk)
        elif self.full_text:
            remaining = max_chars - sum(len(p) for p in parts)
            if remaining > 500:
                parts.append(f"\nFull text (excerpt):\n{self.full_text[:remaining]}")

        return "\n".join(parts)


@dataclass
class PaperAnalysis:
    """Analysis result from examining a paper."""
    paper_type: str       # "model"|"dataset"|"algorithm"|"framework"|"survey"|"empirical"|"theory"|"other"
    contribution: str     # One-sentence summary of the core contribution
    skill_hint: str       # Recommended skill class name
    demo_form: str        # "app"|"presentation"|"page"|"diagram" (category)
    demo_type: str        # "theoretical"|"findings"|"user_demo"
    hf_model_query: str   # Search query for Hugging Face Hub
    required_keys: List[str]          # API keys needed for the demo
    interaction_pattern: str          # How users will interact with the demo
    reasoning: str        # LLM's reasoning for these choices
    authors: List[str] = field(default_factory=list)   # LLM-extracted authors
    year: Optional[int] = None                         # LLM-extracted year
    demo_subtype: str = ""  # e.g. "gradio"|"streamlit"|"revealjs"|"beamer"|"pptx" etc.

    def to_dict(self) -> dict:
        return {
            "paper_type": self.paper_type,
            "contribution": self.contribution,
            "skill_hint": self.skill_hint,
            "demo_form": self.demo_form,
            "demo_subtype": self.demo_subtype,
            "demo_type": self.demo_type,
            "hf_model_query": self.hf_model_query,
            "required_keys": self.required_keys,
            "interaction_pattern": self.interaction_pattern,
            "reasoning": self.reasoning,
        }


@dataclass
class DemoResult:
    """Result of demo generation."""
    demo_form: str        # internal composite key (e.g. "app", "app_streamlit", "page_readme")
    demo_type: str        # "theoretical"|"findings"|"user_demo"
    output_dir: str       # Absolute path to generated files
    main_file: str        # e.g. "app.py", "demo.html", "index.html"
    dependencies: List[str]
    run_command: str
    success: bool
    error: Optional[str] = None
    demo_subtype: str = ""  # original subtype for display purposes

    def to_dict(self) -> dict:
        return {
            "demo_form": self.demo_form,
            "demo_subtype": self.demo_subtype,
            "demo_type": self.demo_type,
            "output_dir": self.output_dir,
            "main_file": self.main_file,
            "dependencies": self.dependencies,
            "run_command": self.run_command,
            "success": self.success,
            "error": self.error,
        }
