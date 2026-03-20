"""Canonical section structures for each demo form.

These lists define the ideal section order for each output type.
They are injected into every skill's system prompt via BaseSkill._tool_usage_instructions()
so the model always knows the expected structure without per-skill duplication.
"""
from __future__ import annotations


PRESENTATION_STRUCTURE: list[str] = [
    "Title",
    "Overview",
    "Problem",
    "Key Insight",
    "Architecture (with diagrams)",
    "Architecture Details",
    "Training",
    "Results (charts)",
    "Analysis",
    "Comparison",
    "Limitations",
    "Conclusion",
]
"""Ideal slide order for a research paper presentation (e.g. reveal.js or PPTX)."""

WEBSITE_STRUCTURE: list[str] = [
    "Hero",
    "TL;DR",
    "Problem",
    "Method (interactive diagram)",
    "Results (Chart.js)",
    "Demo",
    "Citation",
]
"""Ideal section order for a paper project-page website."""

BLOG_STRUCTURE: list[str] = [
    "Hook",
    "Background",
    "Problem",
    "Key Insight",
    "How It Works (diagrams)",
    "Results",
    "Implications",
    "References",
]
"""Ideal section order for a blog-post explainer."""
