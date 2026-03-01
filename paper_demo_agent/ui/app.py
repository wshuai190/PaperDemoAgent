"""Gradio web interface for Paper Demo Agent — commercial-grade dark UI."""

import os
import time
import threading
import zipfile
from pathlib import Path
from typing import Iterator, Optional, Tuple

import gradio as gr

from paper_demo_agent import __version__
from paper_demo_agent.agent import PaperDemoAgent
from paper_demo_agent.keys.manager import KeyManager
from paper_demo_agent.providers.factory import PROVIDER_DEFAULTS, list_providers
from paper_demo_agent.generation.runner import DemoRunner

key_manager = KeyManager()

# ─────────────────────────────────────────────────────────────────────────────
# Gradio theme — module-level so launch() can reference it
# ─────────────────────────────────────────────────────────────────────────────
_THEME = gr.themes.Base(
    primary_hue=gr.themes.colors.indigo,
    secondary_hue=gr.themes.colors.slate,
    neutral_hue=gr.themes.colors.zinc,
    font=gr.themes.GoogleFont("Inter"),
    font_mono=gr.themes.GoogleFont("JetBrains Mono"),
).set(
    body_background_fill="#09090b",
    body_background_fill_dark="#09090b",
    body_text_color="#fafafa",
    body_text_color_dark="#fafafa",
    body_text_size="14px",
    block_background_fill="#111113",
    block_background_fill_dark="#111113",
    block_border_color="#27272a",
    block_border_color_dark="#27272a",
    block_label_text_color="#a1a1aa",
    block_label_text_color_dark="#a1a1aa",
    input_background_fill="#18181b",
    input_background_fill_dark="#18181b",
    input_border_color="#27272a",
    input_border_color_dark="#27272a",
    input_placeholder_color="#71717a",
    input_placeholder_color_dark="#71717a",
    button_primary_background_fill="#6366f1",
    button_primary_background_fill_dark="#6366f1",
    button_primary_background_fill_hover="#4f46e5",
    button_primary_background_fill_hover_dark="#4f46e5",
    button_primary_text_color="#ffffff",
    button_secondary_background_fill="#18181b",
    button_secondary_background_fill_dark="#18181b",
    button_secondary_text_color="#fafafa",
    button_secondary_border_color="#27272a",
    border_color_accent="#6366f1",
    shadow_drop="0 1px 3px rgba(0,0,0,0.4)",
)

# ── Output kind choices (what the user sees) ──────────────────────────────────
KIND_OPTIONS    = ["Auto", "App", "Presentation", "Page", "Diagram"]
APP_OPTIONS     = ["Auto", "Gradio (HF Space)", "Streamlit"]
PRES_OPTIONS    = ["Auto", "PowerPoint (.pptx)", "LaTeX / Beamer", "HTML Slides"]
PAGE_OPTIONS    = ["Auto", "Project Page", "GitHub README", "Blog Article"]
DIAGRAM_OPTIONS = ["Auto", "Interactive (Mermaid)", "Graphviz (SVG/PNG)"]
FOCUS_OPTIONS   = ["Auto", "Try the model", "Explore results", "Explain theory"]

KIND_META = {
    "Auto":         ("🤖", "Let the AI decide",
                     "AI reads the paper and picks the best output type automatically."),
    "App":          ("⚡", "Interactive app",
                     "Python web app users can run to try the paper's system. Choose Gradio or Streamlit below."),
    "Presentation": ("📊", "Slides deck",
                     "A presentation explaining the paper. Choose PowerPoint, LaTeX, or HTML slides below."),
    "Page":         ("🌐", "Static page / document",
                     "A static page or document. Choose project page, GitHub README, or blog article below."),
    "Diagram":      ("🗺️", "Visual diagram",
                     "Architecture or pipeline diagram. Choose interactive Mermaid or static Graphviz below."),
}

APP_META = {
    "Auto":              "AI picks the best app framework for this paper.",
    "Gradio (HF Space)": "Gradio 5 Python app — deploy to HuggingFace Spaces. Best for model inference demos.",
    "Streamlit":         "Streamlit app — interactive widgets, dashboards, data exploration.",
}

PRES_META = {
    "Auto":                "AI picks the best slides format for this paper.",
    "PowerPoint (.pptx)":  "python-pptx — dark theme, charts, logos. Opens in PowerPoint / LibreOffice / Keynote.",
    "LaTeX / Beamer":      "Beamer + Metropolis theme — TikZ diagrams, booktabs tables. Compile with pdflatex.",
    "HTML Slides":         "reveal.js 5 — animated slides with KaTeX math, SVG diagrams, speaker notes.",
}

PAGE_META = {
    "Auto":           "AI picks the best page format for this paper.",
    "Project Page":   "Nerfies / Distill.pub-style website — hero, method, results, BibTeX. Opens in any browser.",
    "GitHub README":  "Publication-quality README.md — badges, Mermaid diagrams, comparison tables, BibTeX.",
    "Blog Article":   "Distill.pub interactive blog article — D3.js visualizations, KaTeX math, citations.",
}

DIAGRAM_META = {
    "Auto":                 "AI picks the best diagram format for this paper.",
    "Interactive (Mermaid)": "Interactive Mermaid.js flowchart — clickable nodes, zoom/pan, step-by-step walkthrough.",
    "Graphviz (SVG/PNG)":    "Python graphviz → publication-quality SVG/PNG architecture diagrams.",
}

FOCUS_META = {
    "Auto":            "AI picks the demo style based on the paper's contribution.",
    "Try the model":   "Hands-on — users interact with the model/system directly, click examples.",
    "Explore results": "Results-first — reproduces benchmarks, ablation tables, comparisons.",
    "Explain theory":  "Educational — explains concepts, architecture, math with animations.",
}

# ── Example papers for one-click try ──────────────────────────────────────────
EXAMPLE_PAPERS = [
    ("Attention Is All You Need", "1706.03762"),
    ("ResNet",                    "1512.03385"),
    ("BERT",                      "1810.04805"),
    ("Diffusion Models Beat GANs","2105.05233"),
    ("LoRA",                      "2106.09685"),
    ("Chain-of-Thought",          "2201.11903"),
]


def _resolve_form_type(kind: str, app_format: str, pres_format: str,
                       page_format: str, diagram_format: str, demo_focus: str):
    """Map user-friendly UI selections → internal (form, type) strings."""
    from paper_demo_agent.paper.models import resolve_form_key

    if kind in ("Auto", ""):
        return None, None
    if kind == "App":
        app_map = {
            "Auto":              (None, None),
            "Gradio (HF Space)": ("app", None),
            "Streamlit":         ("app_streamlit", None),
        }
        form, _ = app_map.get(app_format, (None, None))
        if form is None:
            form = resolve_form_key("app")
        focus_map = {
            "Auto":            None,
            "Try the model":   "user_demo",
            "Explore results": "findings",
            "Explain theory":  "theoretical",
        }
        return form, focus_map.get(demo_focus, None)
    if kind == "Presentation":
        fmt_map = {
            "Auto":               None,
            "PowerPoint (.pptx)": "slides",
            "LaTeX / Beamer":     "latex",
            "HTML Slides":        "presentation",
        }
        return fmt_map.get(pres_format, None), None
    if kind == "Page":
        page_map = {
            "Auto":          None,
            "Project Page":  "website",
            "GitHub README": "page_readme",
            "Blog Article":  "page_blog",
        }
        return page_map.get(page_format, None), None
    if kind == "Diagram":
        diag_map = {
            "Auto":                  None,
            "Interactive (Mermaid)":  "flowchart",
            "Graphviz (SVG/PNG)":     "diagram_graphviz",
        }
        return diag_map.get(diagram_format, None), None
    return None, None

# ─────────────────────────────────────────────────────────────────────────────
# CSS — Vercel / Linear inspired dark theme + animations
# ─────────────────────────────────────────────────────────────────────────────
CSS = """
/* ── Fonts ────────────────────────────────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

/* ── CSS Custom Properties ─────────────────────────────────────────────────── */
:root {
  --pda-bg:       #09090b;
  --pda-bg2:      #111113;
  --pda-bg3:      #18181b;
  --pda-border:   #27272a;
  --pda-border2:  #3f3f46;
  --pda-text:     #fafafa;
  --pda-text2:    #a1a1aa;
  --pda-text3:    #71717a;
  --pda-accent:   #6366f1;
  --pda-accent-h: #4f46e5;
  --pda-accent-s: rgba(99,102,241,0.12);
  --pda-green:    #22c55e;
  --pda-amber:    #f59e0b;
  --pda-red:      #ef4444;
  --pda-font:     'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  --pda-mono:     'JetBrains Mono', 'Fira Code', 'SF Mono', Consolas, monospace;
  --pda-radius:   8px;
  --pda-radius-lg:12px;
  --pda-shadow:   0 1px 3px rgba(0,0,0,0.4), 0 1px 2px rgba(0,0,0,0.3);
  --pda-shadow-lg:0 8px 32px rgba(0,0,0,0.5);
}

/* ── Keyframe Animations ───────────────────────────────────────────────────── */
@keyframes hero-gradient {
  0%   { background-position: 0% 50%; }
  50%  { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}

@keyframes logo-shimmer {
  0%   { background-position: -200% center; }
  100% { background-position: 200% center; }
}

@keyframes badge-in {
  from { opacity: 0; transform: translateY(8px); }
  to   { opacity: 1; transform: translateY(0); }
}

@keyframes page-fade-in {
  from { opacity: 0; transform: translateY(12px); }
  to   { opacity: 1; transform: translateY(0); }
}

@keyframes glow-pulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(99,102,241,0); }
  50%      { box-shadow: 0 0 20px 4px rgba(99,102,241,0.25); }
}

@keyframes pulse-pill {
  0%, 100% { box-shadow: 0 0 0 0 rgba(99,102,241,0); }
  50%      { box-shadow: 0 0 0 4px rgba(99,102,241,0.2); }
}

@keyframes success-shine {
  0%   { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to   { transform: rotate(360deg); }
}

@keyframes tab-slide-in {
  from { opacity: 0; transform: translateX(-8px); }
  to   { opacity: 1; transform: translateX(0); }
}

/* ── Global Reset ───────────────────────────────────────────────────────────── */
*, *::before, *::after { box-sizing: border-box; }

body,
.gradio-container,
.main,
#component-0 {
  background: var(--pda-bg) !important;
  color: var(--pda-text) !important;
  font-family: var(--pda-font) !important;
  font-size: 14px !important;
  line-height: 1.6 !important;
  letter-spacing: -0.01em !important;
  animation: page-fade-in 0.6s ease-out !important;
}

/* ── Panel / Container overrides ──────────────────────────────────────────── */
.gr-panel, .panel, fieldset,
.block, .form,
.svelte-1f354aw, .svelte-vt1mxs,
[data-testid="block"] {
  background: var(--pda-bg2) !important;
  border: 1px solid var(--pda-border) !important;
  border-radius: var(--pda-radius) !important;
}

/* ── Inputs ─────────────────────────────────────────────────────────────────── */
input, textarea, select,
.gr-text-input input,
.gr-text-input textarea,
.gr-dropdown select {
  background: var(--pda-bg3) !important;
  border: 1px solid var(--pda-border) !important;
  color: var(--pda-text) !important;
  font-family: var(--pda-font) !important;
  font-size: 14px !important;
  border-radius: 6px !important;
  padding: 8px 12px !important;
  transition: border-color 150ms ease !important;
}
input:focus, textarea:focus, select:focus {
  border-color: var(--pda-accent) !important;
  outline: none !important;
  box-shadow: 0 0 0 2px var(--pda-accent-s) !important;
}
input::placeholder, textarea::placeholder { color: var(--pda-text3) !important; }

/* ── Labels ─────────────────────────────────────────────────────────────────── */
label, .label-wrap span, .block label span {
  color: var(--pda-text2) !important;
  font-size: 12px !important;
  font-weight: 500 !important;
  letter-spacing: 0.04em !important;
  text-transform: uppercase !important;
}

/* ── Buttons ─────────────────────────────────────────────────────────────────── */
.gr-button, button {
  font-family: var(--pda-font) !important;
  font-size: 13px !important;
  font-weight: 500 !important;
  letter-spacing: -0.01em !important;
  border-radius: 6px !important;
  cursor: pointer !important;
  transition: all 150ms ease !important;
}
.gr-button:active, button:active {
  transform: scale(0.97) !important;
}
.gr-button.primary, button.primary, .primary {
  background: var(--pda-accent) !important;
  border: 1px solid var(--pda-accent) !important;
  color: #fff !important;
  padding: 10px 20px !important;
}
.gr-button.primary:hover, button.primary:hover, .primary:hover {
  background: var(--pda-accent-h) !important;
  border-color: var(--pda-accent-h) !important;
  transform: translateY(-1px) !important;
  box-shadow: 0 4px 12px rgba(99,102,241,0.35) !important;
}
.gr-button.secondary, button.secondary, .secondary {
  background: var(--pda-bg3) !important;
  border: 1px solid var(--pda-border) !important;
  color: var(--pda-text) !important;
  padding: 8px 16px !important;
}
.gr-button.secondary:hover, button.secondary:hover {
  border-color: var(--pda-border2) !important;
  background: #222226 !important;
}

/* ── Tabs ───────────────────────────────────────────────────────────────────── */
.tab-nav, .tabs > div:first-child {
  background: var(--pda-bg2) !important;
  border-bottom: 1px solid var(--pda-border) !important;
  padding: 0 4px !important;
}
.tab-nav button, .tabs > div:first-child button {
  background: transparent !important;
  border: none !important;
  color: var(--pda-text2) !important;
  font-size: 13px !important;
  font-weight: 500 !important;
  padding: 10px 16px !important;
  border-bottom: 2px solid transparent !important;
  border-radius: 0 !important;
  text-transform: none !important;
  letter-spacing: normal !important;
  transition: color 150ms ease, border-color 150ms ease !important;
}
.tab-nav button.selected, .tabs > div:first-child button.selected,
.tab-nav button[aria-selected="true"] {
  color: var(--pda-text) !important;
  border-bottom-color: var(--pda-accent) !important;
  background: transparent !important;
}
.tab-nav button:hover:not(.selected) {
  color: var(--pda-text) !important;
}
.tabitem {
  animation: tab-slide-in 0.3s ease-out !important;
}

/* ── Accordion / Details ─────────────────────────────────────────────────────── */
details > summary {
  background: var(--pda-bg3) !important;
  border: 1px solid var(--pda-border) !important;
  border-radius: 6px !important;
  color: var(--pda-text) !important;
  font-size: 13px !important;
  font-weight: 500 !important;
  padding: 10px 14px !important;
  cursor: pointer !important;
}
details[open] > summary { border-bottom-left-radius: 0 !important; border-bottom-right-radius: 0 !important; }

/* ── Dropdowns ───────────────────────────────────────────────────────────────── */
.dropdown-arrow, svg.dropdown-icon { color: var(--pda-text2) !important; }
ul.options, .choices__list--dropdown {
  background: var(--pda-bg3) !important;
  border: 1px solid var(--pda-border) !important;
  border-radius: 6px !important;
}
ul.options li, .choices__item {
  color: var(--pda-text) !important;
  font-size: 13px !important;
  padding: 8px 12px !important;
}
ul.options li:hover, .choices__item--highlighted {
  background: var(--pda-accent-s) !important;
  color: var(--pda-accent) !important;
}

/* ── Markdown ────────────────────────────────────────────────────────────────── */
.prose, .md, .markdown-body,
[data-testid="markdown"] {
  color: var(--pda-text) !important;
  font-family: var(--pda-font) !important;
  font-size: 14px !important;
  line-height: 1.7 !important;
}
.prose h1, .prose h2, .prose h3,
.md h1, .md h2, .md h3 {
  color: var(--pda-text) !important;
  font-weight: 600 !important;
  letter-spacing: -0.02em !important;
}
.prose code, .md code, code {
  font-family: var(--pda-mono) !important;
  font-size: 12px !important;
  background: var(--pda-bg3) !important;
  padding: 2px 6px !important;
  border-radius: 4px !important;
  color: #c4b5fd !important;
}
.prose pre, .md pre {
  background: var(--pda-bg3) !important;
  border: 1px solid var(--pda-border) !important;
  border-radius: 8px !important;
  padding: 16px !important;
}
a { color: var(--pda-accent) !important; text-decoration: none !important; }
a:hover { text-decoration: underline !important; }
hr { border-color: var(--pda-border) !important; margin: 20px 0 !important; }

/* ── File upload ─────────────────────────────────────────────────────────────── */
.upload-container, [data-testid="file"],
.file-preview {
  background: var(--pda-bg3) !important;
  border: 1.5px dashed var(--pda-border) !important;
  border-radius: var(--pda-radius) !important;
  color: var(--pda-text2) !important;
  transition: border-color 150ms ease !important;
}
.upload-container:hover, [data-testid="file"]:hover {
  border-color: var(--pda-accent) !important;
}

/* ── Hero header ─────────────────────────────────────────────────────────────── */
#pda-header {
  background: linear-gradient(135deg,
    #0d0d10 0%, #111128 25%, #1a0d2e 50%, #111128 75%, #0d0d10 100%) !important;
  background-size: 400% 400% !important;
  animation: hero-gradient 8s ease infinite !important;
  border-bottom: 1px solid var(--pda-border) !important;
  padding: 36px 40px 30px !important;
  margin-bottom: 0 !important;
  position: relative;
  overflow: hidden;
}
#pda-header::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  background: radial-gradient(rgba(99,102,241,0.15) 1px, transparent 1px);
  background-size: 24px 24px;
  pointer-events: none;
  opacity: 0.5;
}
#pda-header::after {
  content: '';
  position: absolute;
  top: -80px; right: -80px;
  width: 350px; height: 350px;
  background: radial-gradient(circle, rgba(99,102,241,0.12) 0%, transparent 70%);
  pointer-events: none;
}
#pda-header h1 {
  font-size: 28px !important;
  font-weight: 700 !important;
  letter-spacing: -0.03em !important;
  margin: 0 0 4px !important;
  line-height: 1.2 !important;
  position: relative;
  background: linear-gradient(90deg, #fff 0%, #a5b4fc 40%, #818cf8 60%, #fff 100%);
  background-size: 200% auto;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  animation: logo-shimmer 6s linear infinite;
}
#pda-header .tagline {
  font-size: 15px;
  color: var(--pda-text2);
  margin: 0 0 18px;
  font-weight: 400;
  position: relative;
}
#pda-header .tagline em {
  color: #a5b4fc;
  font-style: normal;
  font-weight: 500;
}
#pda-header .badges {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  position: relative;
}
.pda-badge {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 11px;
  font-weight: 500;
  letter-spacing: 0.02em;
  opacity: 0;
  animation: badge-in 0.5s ease forwards;
}
.pda-badge:nth-child(1) { animation-delay: 0.3s; }
.pda-badge:nth-child(2) { animation-delay: 0.5s; }
.pda-badge:nth-child(3) { animation-delay: 0.7s; }
.pda-badge:nth-child(4) { animation-delay: 0.9s; }
.pda-badge-accent { background: rgba(99,102,241,0.15); color: #a5b4fc; border: 1px solid rgba(99,102,241,0.25); }
.pda-badge-green  { background: rgba(34,197,94,0.12);  color: #86efac; border: 1px solid rgba(34,197,94,0.2); }
.pda-badge-neutral{ background: var(--pda-bg3); color: var(--pda-text2); border: 1px solid var(--pda-border); }

/* ── Example paper buttons ──────────────────────────────────────────────────── */
.example-papers {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  margin: 8px 0 4px;
}
.example-btn {
  padding: 5px 12px !important;
  font-size: 12px !important;
  font-weight: 500 !important;
  background: var(--pda-bg3) !important;
  border: 1px solid var(--pda-border) !important;
  border-radius: 20px !important;
  color: var(--pda-text2) !important;
  cursor: pointer !important;
  transition: all 200ms ease !important;
  white-space: nowrap !important;
}
.example-btn:hover {
  border-color: var(--pda-accent) !important;
  color: #a5b4fc !important;
  background: rgba(99,102,241,0.08) !important;
  transform: translateY(-1px) !important;
}

/* ── Form selector cards ─────────────────────────────────────────────────────── */
#form-cards, #type-cards {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin: 4px 0;
}
.pda-card {
  flex: 1;
  min-width: 110px;
  padding: 12px 14px;
  background: var(--pda-bg3);
  border: 1.5px solid var(--pda-border);
  border-radius: var(--pda-radius);
  cursor: pointer;
  transition: all 150ms ease;
  user-select: none;
}
.pda-card:hover { border-color: var(--pda-border2); background: #1d1d22; }
.pda-card.active {
  border-color: var(--pda-accent);
  background: var(--pda-accent-s);
  box-shadow: 0 0 0 1px var(--pda-accent);
}
.pda-card .icon { font-size: 18px; margin-bottom: 4px; }
.pda-card .name { font-size: 12px; font-weight: 600; color: var(--pda-text); }
.pda-card .desc { font-size: 11px; color: var(--pda-text2); margin-top: 2px; line-height: 1.4; }

/* ── Terminal / progress ────────────────────────────────────────────────────── */
#pda-progress textarea,
.pda-terminal,
.pda-log-tabs textarea {
  font-family: var(--pda-mono) !important;
  font-size: 12px !important;
  line-height: 1.7 !important;
  background: #020204 !important;
  color: #d4d4d8 !important;
  border: 1px solid var(--pda-border) !important;
  border-radius: var(--pda-radius) !important;
  padding: 14px 16px !important;
  max-height: 420px !important;
  overflow-y: auto !important;
}

/* ── Log phase tabs ─────────────────────────────────────────────────────────── */
.pda-log-tabs .tab-nav,
.pda-log-tabs .tabs > div:first-child {
  background: #020204 !important;
  border: 1px solid var(--pda-border) !important;
  border-bottom: none !important;
  border-radius: var(--pda-radius) var(--pda-radius) 0 0 !important;
  padding: 0 !important;
}
.pda-log-tabs .tab-nav button,
.pda-log-tabs .tabs > div:first-child button {
  font-family: var(--pda-mono) !important;
  font-size: 11px !important;
  font-weight: 500 !important;
  padding: 6px 14px !important;
  color: var(--pda-text3) !important;
  border-bottom: 2px solid transparent !important;
}
.pda-log-tabs .tab-nav button.selected,
.pda-log-tabs .tabs > div:first-child button.selected,
.pda-log-tabs .tab-nav button[aria-selected="true"] {
  color: #a5b4fc !important;
  border-bottom-color: var(--pda-accent) !important;
}
.pda-log-tabs .tabitem {
  animation: none !important;
}

/* ── Phase status pills ──────────────────────────────────────────────────────── */
#pda-phase-status {
  display: flex;
  gap: 6px;
  padding: 10px 0;
  font-size: 12px;
  color: var(--pda-text2);
  font-family: var(--pda-mono);
  flex-wrap: wrap;
  align-items: center;
}
.phase-pill {
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 11px;
  font-weight: 500;
  background: var(--pda-bg3);
  border: 1px solid var(--pda-border);
  color: var(--pda-text3);
  transition: all 200ms ease;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}
.phase-pill.active {
  background: rgba(99,102,241,0.15);
  border-color: var(--pda-accent);
  color: #a5b4fc;
  animation: pulse-pill 1.5s ease infinite;
}
.phase-pill.done {
  background: rgba(34,197,94,0.1);
  border-color: rgba(34,197,94,0.25);
  color: #86efac;
}
.phase-arrow {
  color: var(--pda-text3);
  font-size: 10px;
}
.phase-timer {
  margin-left: auto;
  font-size: 12px;
  color: var(--pda-text2);
  font-family: var(--pda-mono);
  padding: 3px 10px;
  background: var(--pda-bg3);
  border-radius: 20px;
  border: 1px solid var(--pda-border);
}

/* ── Generated files panel ───────────────────────────────────────────────────── */
#pda-files-panel {
  background: var(--pda-bg2) !important;
  border: 1px solid var(--pda-border) !important;
  border-radius: var(--pda-radius-lg) !important;
  padding: 16px !important;
}
.file-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 13px;
  font-family: var(--pda-mono);
  color: var(--pda-text);
  border: 1px solid transparent;
  transition: all 150ms ease;
  cursor: default;
}
.file-item:hover {
  background: var(--pda-bg3);
  border-color: var(--pda-border);
  transform: translateX(4px);
}
.file-size { font-size: 11px; color: var(--pda-text2); margin-left: auto; }

/* ── Settings panel ──────────────────────────────────────────────────────────── */
.key-row {
  display: grid;
  grid-template-columns: 180px 1fr auto;
  gap: 8px;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid var(--pda-border);
}
.key-row:last-child { border-bottom: none; }
.key-name { font-size: 12px; font-weight: 600; color: var(--pda-text2); font-family: var(--pda-mono); }
.key-status-dot {
  width: 6px; height: 6px;
  border-radius: 50%;
  display: inline-block;
  margin-right: 4px;
}
.key-status-dot.set { background: var(--pda-green); }
.key-status-dot.unset { background: var(--pda-border2); }

/* ── Help section ────────────────────────────────────────────────────────────── */
.help-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 12px;
  margin-top: 12px;
}
.help-card {
  background: var(--pda-bg3);
  border: 1px solid var(--pda-border);
  border-radius: var(--pda-radius);
  padding: 16px;
  transition: border-color 200ms ease, transform 200ms ease;
}
.help-card:hover {
  border-color: var(--pda-border2);
  transform: translateY(-2px);
}
.help-card h4 { font-size: 13px; font-weight: 600; color: var(--pda-text); margin: 0 0 8px; }
.help-card p  { font-size: 12px; color: var(--pda-text2); margin: 0; line-height: 1.6; }

/* ── Success / Error banners ────────────────────────────────────────────────── */
.pda-success-banner {
  background: linear-gradient(90deg,
    rgba(34,197,94,0.08) 0%, rgba(34,197,94,0.12) 50%, rgba(34,197,94,0.08) 100%) !important;
  background-size: 200% 100% !important;
  animation: success-shine 3s linear infinite !important;
  border: 1px solid rgba(34,197,94,0.25) !important;
  border-radius: var(--pda-radius) !important;
  padding: 14px 18px !important;
  color: #86efac !important;
  font-size: 13px !important;
}
.pda-error-banner {
  background: rgba(239,68,68,0.08) !important;
  border: 1px solid rgba(239,68,68,0.2) !important;
  border-radius: var(--pda-radius) !important;
  padding: 12px 16px !important;
  color: #fca5a5 !important;
  font-size: 13px !important;
}

/* ── Generate button glow ───────────────────────────────────────────────────── */
#pda-generate-btn button.primary {
  animation: glow-pulse 3s ease infinite !important;
  font-size: 15px !important;
  padding: 12px 24px !important;
  font-weight: 600 !important;
  letter-spacing: -0.01em !important;
}
#pda-generate-btn button.primary:hover {
  animation: none !important;
}

/* ── Scrollbars ──────────────────────────────────────────────────────────────── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: var(--pda-bg); }
::-webkit-scrollbar-thumb { background: var(--pda-border2); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--pda-text3); }

/* ── Mobile Responsive ───────────────────────────────────────────────────────── */
@media (max-width: 768px) {
  #pda-header {
    padding: 24px 20px 22px !important;
  }
  #pda-header h1 {
    font-size: 22px !important;
  }
  #pda-header .tagline {
    font-size: 13px;
  }
  .pda-badge {
    font-size: 10px;
    padding: 3px 8px;
  }
  #pda-phase-status {
    flex-wrap: wrap;
    gap: 4px;
  }
  .phase-pill {
    font-size: 10px;
    padding: 3px 8px;
  }
  .phase-arrow {
    display: none;
  }
  .help-grid {
    grid-template-columns: 1fr;
  }
  .key-row {
    grid-template-columns: 1fr;
    gap: 4px;
  }
  .example-papers {
    gap: 4px;
  }
  .example-btn {
    font-size: 11px !important;
    padding: 4px 8px !important;
  }
}

/* ── Misc ─────────────────────────────────────────────────────────────────────── */
.footer { display: none !important; }
.svelte-1rjryqp { background: transparent !important; }
"""

# ── Viewport meta tag for mobile ──────────────────────────────────────────────
HEAD = '<meta name="viewport" content="width=device-width, initial-scale=1.0">'

# ── JS for typing effect on tagline ───────────────────────────────────────────
JS_ON_LOAD = """
() => {
  const el = document.getElementById('pda-tagline');
  if (!el) return;
  const text = el.getAttribute('data-text') || el.textContent;
  el.textContent = '';
  el.style.borderRight = '2px solid #a5b4fc';
  let i = 0;
  const type = () => {
    if (i < text.length) {
      el.textContent += text[i];
      i++;
      setTimeout(type, 28);
    } else {
      setTimeout(() => { el.style.borderRight = 'none'; }, 1200);
    }
  };
  setTimeout(type, 600);
}
"""


# ─────────────────────────────────────────────────────────────────────────────
# Phase detection for progress stepper
# ─────────────────────────────────────────────────────────────────────────────

_PHASES = [
    ("Parse",    ["Parsing paper", "Fetching from arXiv", "Extracting text", "Reading PDF"]),
    ("Analyze",  ["Analyzing paper", "Paper type:", "Recommended form:", "classification"]),
    ("Research", ["Research phase", "Searching for", "web_search", "research iteration"]),
    ("Build",    ["Build phase", "build iteration", "Code generation", "write_file", "Writing file"]),
    ("Polish",   ["Polish phase", "polish iteration", "Quality review", "Reviewing"]),
    ("Validate", ["Validate phase", "validation", "Checking output", "form-compliance"]),
]


def _detect_phase(text: str) -> int:
    """Return the index of the current phase (0-5) based on progress text."""
    last = 0
    lower = text.lower()
    for i, (_, keywords) in enumerate(_PHASES):
        for kw in keywords:
            if kw.lower() in lower:
                last = i
    return last


# ── Phase markers emitted by generator.py ────────────────────────────────────
# These exact strings mark phase transitions in the progress stream.
_PHASE_MARKERS = [
    (0, ["Parsing paper", "Fetching from arXiv", "Extracting text", "Reading PDF",
         "Provider :", "Skill    :"]),
    (1, ["Analyzing paper", "Paper type:", "Recommended form:", "classification",
         "Analyzing "]),
    (2, ["━━ Phase 1", "Research", "research iteration", "Searching for"]),
    (3, ["━━ Phase 2", "Build", "build iteration", "━━ Phase 1b"]),
    (4, ["━━ Phase 3", "Polish", "polish iteration"]),
    (5, ["validation", "Validate", "form-compliance", "auto-correction",
         "Form validation"]),
]


def _classify_line(line: str) -> int:
    """Classify a single progress line into a phase index (0-5).

    Returns the phase index for lines that contain a phase marker.
    Returns -1 for lines that don't trigger a phase change.
    """
    for phase_idx, markers in _PHASE_MARKERS:
        for marker in markers:
            if marker in line:
                return phase_idx
    return -1


def _split_progress_by_phase(progress_buf: list[str]) -> tuple[list[str], int]:
    """Split accumulated progress lines into per-phase buckets.

    Returns (phase_buckets, current_phase) where phase_buckets is a list of
    6 strings (one per phase), and current_phase is the latest active phase.
    """
    buckets: list[list[str]] = [[] for _ in range(6)]
    current = 0

    full_text = "".join(progress_buf)
    for line in full_text.splitlines(keepends=True):
        detected = _classify_line(line)
        if detected >= 0:
            current = detected
        buckets[current].append(line)

    return ["".join(b) for b in buckets], current


def _phase_html(current_phase: int, elapsed_secs: float, running: bool = True) -> str:
    """Build the visual phase stepper HTML."""
    parts = []
    for i, (name, _) in enumerate(_PHASES):
        if i < current_phase:
            parts.append(f'<span class="phase-pill done">&#10003; {name}</span>')
        elif i == current_phase and running:
            parts.append(f'<span class="phase-pill active">&#9679; {name}</span>')
        elif i == current_phase and not running:
            parts.append(f'<span class="phase-pill done">&#10003; {name}</span>')
        else:
            parts.append(f'<span class="phase-pill">{name}</span>')

        if i < len(_PHASES) - 1:
            parts.append('<span class="phase-arrow">&#8594;</span>')

    mins = int(elapsed_secs) // 60
    secs = int(elapsed_secs) % 60
    time_str = f"{mins}:{secs:02d}"

    if running:
        parts.append(f'<span class="phase-timer">&#8635; {time_str}</span>')
    else:
        parts.append(f'<span class="phase-timer">&#10003; {time_str}</span>')

    return f'<div id="pda-phase-status">{"".join(parts)}</div>'


# ─────────────────────────────────────────────────────────────────────────────
# Header HTML
# ─────────────────────────────────────────────────────────────────────────────
def _header_html() -> str:
    return f"""
<div id="pda-header">
  <h1>&#9670; Paper Demo Agent</h1>
  <p class="tagline" id="pda-tagline"
     data-text="Turn any scientific paper into a live interactive demo — in minutes.">Turn any scientific paper into a live interactive demo — in minutes.</p>
  <div class="badges">
    <span class="pda-badge pda-badge-accent">v{__version__}</span>
    <span class="pda-badge pda-badge-green">6 providers &middot; 15 skills</span>
    <span class="pda-badge pda-badge-neutral">10 output formats</span>
    <span class="pda-badge pda-badge-neutral">pip install paper-demo-agent</span>
  </div>
</div>"""


# ─────────────────────────────────────────────────────────────────────────────
# Provider helpers
# ─────────────────────────────────────────────────────────────────────────────

def _default_models() -> list[str]:
    first = list(PROVIDER_DEFAULTS.values())[0]
    return first.get("models", ["claude-opus-4-6"])


def _fetch_live_models(provider: str) -> Optional[list]:
    """Try to fetch the current model list from the provider's API. Returns None on failure."""
    info = PROVIDER_DEFAULTS.get(provider, {})
    key, _ = key_manager.get_with_source(info.get("key_env", ""))
    try:
        if provider == "gemini":
            from paper_demo_agent.providers.gemini_provider import GeminiProvider
            return GeminiProvider(api_key=key or None).list_models_live()
        if provider == "openai" and key:
            from paper_demo_agent.providers.openai_provider import OpenAIProvider
            return OpenAIProvider(api_key=key).list_models_live()
    except Exception:
        pass
    return None


def _get_models_for_provider(provider: str) -> dict:
    info = PROVIDER_DEFAULTS.get(provider, {})
    static_models = info.get("models", [])
    default = info.get("default_model", static_models[0] if static_models else "")

    live = _fetch_live_models(provider)
    if live:
        best_default = default if default in live else live[0]
        return gr.update(choices=live, value=best_default)

    return gr.update(choices=static_models, value=default)


# ─────────────────────────────────────────────────────────────────────────────
# HuggingFace auth helpers
# ─────────────────────────────────────────────────────────────────────────────

def _hf_login(token: str) -> str:
    if not token or not token.strip():
        return "⚠ Please enter a HuggingFace token."
    try:
        from huggingface_hub import login, whoami
        login(token=token.strip(), add_to_git_credential=False)
        info = whoami()
        username = info.get("name", "unknown")
        key_manager.set("HUGGINGFACE_TOKEN", token.strip())
        return f"✓ Logged in as **{username}**. Token saved to local config."
    except Exception as exc:
        return f"✗ Login failed: {exc}"


def _hf_logout() -> str:
    try:
        from huggingface_hub import logout
        logout()
        return "✓ Logged out of HuggingFace."
    except Exception as exc:
        return f"✗ Logout error: {exc}"


def _check_hf_status() -> str:
    try:
        from huggingface_hub import whoami
        info = whoami()
        return f"✓ Signed in as **{info.get('name', 'unknown')}**"
    except Exception:
        return "◦ Not signed in"


# ─────────────────────────────────────────────────────────────────────────────
# Key management helpers
# ─────────────────────────────────────────────────────────────────────────────

def _save_key(name: str, value: str) -> str:
    if not value or not value.strip():
        return f"✗ Empty value — nothing saved."
    try:
        key_manager.set(name.upper(), value.strip())
        return f"✓ {name.upper()} saved (••••••••)"
    except Exception as exc:
        return f"✗ Error: {exc}"


def _ok_html(msg: str) -> str:
    return f'<div class="pda-success-banner">✓ {msg}</div>'

def _error_html(msg: str) -> str:
    return f'<div class="pda-error-banner">✗ {msg}</div>'

def _info_html(msg: str) -> str:
    return f'<p style="font-size:13px;color:var(--pda-text2)">{msg}</p>'


def _key_status_html() -> str:
    """Build an HTML status panel showing which keys are set and where they came from."""
    status_all = key_manager.all_status_with_sources()

    _b = 'border-radius:10px;font-size:10px;padding:1px 7px;font-weight:500'
    SOURCE_BADGE = {
        "saved":       (f'<span style="background:rgba(99,102,241,0.15);color:#a5b4fc;'
                        f'border:1px solid rgba(99,102,241,0.3);{_b}">saved locally</span>'),
        "env":         (f'<span style="background:rgba(34,197,94,0.12);color:#86efac;'
                        f'border:1px solid rgba(34,197,94,0.2);{_b}">env var</span>'),
        "adc":         (f'<span style="background:rgba(251,191,36,0.12);color:#fcd34d;'
                        f'border:1px solid rgba(251,191,36,0.2);{_b}">gcloud ADC</span>'),
        "claude-code": (f'<span style="background:rgba(251,146,60,0.12);color:#fdba74;'
                        f'border:1px solid rgba(251,146,60,0.2);{_b}">Claude Code</span>'),
        "codex":       (f'<span style="background:rgba(16,185,129,0.12);color:#6ee7b7;'
                        f'border:1px solid rgba(16,185,129,0.2);{_b}">OpenAI Codex</span>'),
        "aider":       (f'<span style="background:rgba(168,85,247,0.12);color:#d8b4fe;'
                        f'border:1px solid rgba(168,85,247,0.2);{_b}">Aider</span>'),
        None:          ('<span style="color:var(--pda-text3);font-size:11px">not configured</span>'),
    }

    rows = []
    for key_name, info in status_all.items():
        source = info["source"]
        masked = info["masked"]
        is_set = source is not None
        dot = f'<span class="key-status-dot {"set" if is_set else "unset"}"></span>'
        badge = SOURCE_BADGE.get(source, SOURCE_BADGE[None])
        val_display = (f'<span style="font-family:var(--pda-mono);font-size:11px;'
                       f'color:var(--pda-text2)">{masked}</span>  ' if masked else "")
        rows.append(
            f'<div class="key-row">'
            f'<span class="key-name">{key_name}</span>'
            f'<span style="font-size:12px;color:var(--pda-text2)">{info["label"]}</span>'
            f'<span style="font-size:12px">{dot}{val_display}{badge}</span>'
            f'</div>'
        )
    return f'<div style="padding:4px 0">{"".join(rows)}</div>'


def _tool_detect_html() -> str:
    """Show which third-party AI tools were found and what credentials they provide."""
    rows = []

    # Claude Code → ANTHROPIC_API_KEY
    token = key_manager.detect_claude_code()
    if token:
        rows.append(("Claude Code", "~/.claude/.credentials.json", "ANTHROPIC_API_KEY", "••••••••", True))
    else:
        rows.append(("Claude Code", "~/.claude/.credentials.json", "ANTHROPIC_API_KEY", None, False))

    # OpenAI Codex → OPENAI_API_KEY
    key = key_manager.detect_openai_codex()
    if key:
        rows.append(("OpenAI Codex CLI", "~/.codex/auth.json", "OPENAI_API_KEY", "••••••••", True))
    else:
        rows.append(("OpenAI Codex CLI", "~/.codex/auth.json", "OPENAI_API_KEY", None, False))

    # Aider → multiple keys
    aider_keys = key_manager.detect_aider()
    if aider_keys:
        for env_name, val in aider_keys.items():
            rows.append(("Aider", "~/.aider.conf.yml", env_name, "••••••••" if val else None, bool(val)))
    else:
        rows.append(("Aider", "~/.aider.conf.yml", "ANTHROPIC/OPENAI keys", None, False))

    parts = []
    for tool, path, provides, masked, found in rows:
        dot_cls = "set" if found else "unset"
        dot = f'<span class="key-status-dot {dot_cls}"></span>'
        status = (
            f'<span style="font-family:var(--pda-mono);font-size:11px;color:var(--pda-text2)">'
            f'{masked}</span>'
            if found else
            '<span style="color:var(--pda-text3);font-size:11px">not found</span>'
        )
        parts.append(
            f'<div class="key-row">'
            f'<span class="key-name" style="min-width:130px">{tool}</span>'
            f'<span style="font-size:11px;color:var(--pda-text3);font-family:var(--pda-mono)'
            f';min-width:200px">{path}</span>'
            f'<span style="font-size:11px;color:var(--pda-text2);min-width:140px">{provides}</span>'
            f'<span style="font-size:12px">{dot}{status}</span>'
            f'</div>'
        )
    return f'<div style="padding:4px 0">{"".join(parts)}</div>'


def _adc_status_html() -> str:
    """Build an HTML snippet showing the current Google ADC / Gemini auth status."""
    has_key = bool(key_manager.get("GOOGLE_API_KEY"))
    has_adc = key_manager.detect_gemini_adc()

    if has_key:
        badge = ('<span style="background:rgba(99,102,241,0.15);color:#a5b4fc;'
                 'border:1px solid rgba(99,102,241,0.3);border-radius:10px;'
                 'font-size:11px;padding:2px 9px;font-weight:500">API key saved</span>')
        msg = "Gemini will use the saved <code>GOOGLE_API_KEY</code>."
    elif has_adc:
        badge = ('<span style="background:rgba(34,197,94,0.12);color:#86efac;'
                 'border:1px solid rgba(34,197,94,0.2);border-radius:10px;'
                 'font-size:11px;padding:2px 9px;font-weight:500">✓ gcloud ADC active</span>')
        msg = "Credentials found at <code>~/.config/gcloud/application_default_credentials.json</code>. No API key needed."
    else:
        badge = ('<span style="background:rgba(239,68,68,0.1);color:#fca5a5;'
                 'border:1px solid rgba(239,68,68,0.2);border-radius:10px;'
                 'font-size:11px;padding:2px 9px;font-weight:500">not configured</span>')
        msg = "Set <code>GOOGLE_API_KEY</code> below, or run <code>gcloud auth application-default login</code>."

    return (
        f'<div style="display:flex;align-items:center;gap:10px;padding:8px 0;'
        f'font-size:12px;color:var(--pda-text2)">'
        f'{badge}'
        f'<span>{msg}</span>'
        f'</div>'
    )


# ─────────────────────────────────────────────────────────────────────────────
# File utilities
# ─────────────────────────────────────────────────────────────────────────────

def _file_icon(name: str) -> str:
    ext = Path(name).suffix.lower()
    icons = {
        ".py": "🐍", ".html": "🌐", ".css": "🎨", ".js": "⚡",
        ".md": "📝", ".txt": "📄", ".json": "📦", ".svg": "🖼️",
        ".png": "🖼️", ".jpg": "🖼️", ".jpeg": "🖼️",
        ".tex": "📐", ".pptx": "📊", ".sh": "⚙️",
    }
    return icons.get(ext, "📄")


def _files_html(output_dir: str) -> str:
    if not output_dir or not Path(output_dir).exists():
        return "<p style='color:var(--pda-text2);font-size:13px'>No files generated yet.</p>"
    files = sorted(Path(output_dir).rglob("*"), key=lambda f: f.name)
    files = [f for f in files if f.is_file()]
    if not files:
        return "<p style='color:var(--pda-text2);font-size:13px'>Output directory is empty.</p>"
    items = []
    for f in files[:30]:
        size = f.stat().st_size
        size_str = f"{size/1024:.1f} KB" if size >= 1024 else f"{size} B"
        rel = f.relative_to(output_dir)
        icon = _file_icon(f.name)
        items.append(
            f'<div class="file-item">'
            f'<span>{icon}</span>'
            f'<span style="font-size:12px">{rel}</span>'
            f'<span class="file-size">{size_str}</span>'
            f'</div>'
        )
    total = sum(f.stat().st_size for f in files) / 1024
    header = (
        f'<div style="display:flex;justify-content:space-between;align-items:center;'
        f'margin-bottom:8px;padding-bottom:8px;border-bottom:1px solid var(--pda-border)">'
        f'<span style="font-size:12px;font-weight:600;color:var(--pda-text)">{len(files)} file(s)</span>'
        f'<span style="font-size:11px;color:var(--pda-text2)">{total:.1f} KB total</span>'
        f'</div>'
    )
    return f'<div id="pda-files-panel">{header}{"".join(items)}</div>'


def _file_preview_choices(output_dir: str) -> list[str]:
    if not output_dir or not Path(output_dir).exists():
        return []
    files = sorted(f for f in Path(output_dir).rglob("*") if f.is_file())
    return [str(f.relative_to(output_dir)) for f in files[:30]]


def _read_file_preview(output_dir: str, filename: str) -> str:
    if not output_dir or not filename:
        return ""
    try:
        content = (Path(output_dir) / filename).read_text(encoding="utf-8", errors="replace")
        ext = Path(filename).suffix.lower().lstrip(".")
        lang_map = {"py": "python", "js": "javascript", "html": "html",
                    "css": "css", "md": "markdown", "json": "json", "txt": "text",
                    "tex": "latex", "sh": "bash"}
        lang = lang_map.get(ext, "text")
        # Cap at 300 lines for readability
        lines = content.splitlines()
        truncated = len(lines) > 300
        shown = "\n".join(lines[:300])
        note = f"\n\n… truncated ({len(lines)} lines total)" if truncated else ""
        return f"```{lang}\n{shown}{note}\n```"
    except Exception as e:
        return f"Could not read file: {e}"


def _make_zip(output_dir: str) -> Optional[str]:
    if not output_dir or not Path(output_dir).exists():
        return None
    zip_path = str(Path(output_dir).parent / (Path(output_dir).name + ".zip"))
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in Path(output_dir).rglob("*"):
            if f.is_file():
                zf.write(f, f.relative_to(output_dir))
    return zip_path


# ─────────────────────────────────────────────────────────────────────────────
# Generation
# ─────────────────────────────────────────────────────────────────────────────

_PHASE_LABELS = [p[0] for p in _PHASES]   # ["Parse", "Analyze", ...]


def _run_generate(
    source: str,
    pdf_file,
    provider: str,
    model: str,
    api_key: str,
    output_kind: str,
    app_format: str,
    pres_format: str,
    page_format: str,
    diagram_format: str,
    demo_focus: str,
    max_iter: int,
) -> Iterator[tuple]:
    """Generator that yields per-phase log tabs + stepper + status.

    Tuple layout:
        (log_parse, log_analyze, log_research, log_build, log_polish, log_validate,
         active_tab, phase_html, status_html, files_html, result_state)
    """

    empty_logs = ("",) * 6

    def _state(logs, active_tab, phase_html, status_html, files_html, result=None):
        return logs + (gr.Tabs(selected=active_tab), phase_html, status_html,
                       files_html, result)

    # ── Input validation ─────────────────────────────────────────
    actual_source = None
    if pdf_file:
        actual_source = pdf_file if isinstance(pdf_file, str) else pdf_file.name
    elif source and source.strip():
        src = source.strip()
        if src.lower().startswith("arxiv:"):
            src = src[6:].strip()
        actual_source = src

    if not actual_source:
        err = '<div class="pda-error-banner">✗ Provide an arXiv ID, URL, or upload a PDF.</div>'
        yield _state(empty_logs, 0, "", err, "", None)
        return

    api_key_clean = api_key.strip() if api_key else None
    form_val, type_val = _resolve_form_type(
        output_kind, app_format, pres_format, page_format, diagram_format, demo_focus
    )
    model_val = model if model else None

    progress_buf = []
    running_status = '<div class="pda-badge pda-badge-accent" style="animation:none;opacity:1">&#8635; Running&hellip;</div>'
    output_dir_ref = [None]
    start_time = time.time()

    def on_progress(text: str):
        progress_buf.append(text)

    phase_html = _phase_html(0, 0.0, running=True)
    init_logs = ("Starting generation…\n",) + ("",) * 5
    yield _state(init_logs, 0, phase_html, running_status, "", None)

    try:
        agent = PaperDemoAgent(provider=provider, model=model_val, api_key=api_key_clean)

        result_ref = [None]
        error_ref = [None]

        def _run():
            try:
                result_ref[0] = agent.run(
                    source=actual_source,
                    output_dir=None,
                    demo_form=form_val,
                    demo_type=type_val,
                    max_iter=max_iter,
                    on_progress=on_progress,
                )
                if result_ref[0].output_dir:
                    output_dir_ref[0] = result_ref[0].output_dir
            except Exception as exc:
                error_ref[0] = str(exc)

        thread = threading.Thread(target=_run, daemon=True)
        thread.start()

        last_len = 0
        while thread.is_alive():
            thread.join(timeout=0.4)
            current_text = "".join(progress_buf)
            if len(current_text) > last_len:
                last_len = len(current_text)
                elapsed = time.time() - start_time
                buckets, current_phase = _split_progress_by_phase(progress_buf)
                phase_html = _phase_html(current_phase, elapsed, running=True)
                files_out = _files_html(output_dir_ref[0]) if output_dir_ref[0] else ""
                yield _state(tuple(buckets), current_phase, phase_html,
                             running_status, files_out, None)

        thread.join()
        elapsed = time.time() - start_time
        buckets, final_phase_idx = _split_progress_by_phase(progress_buf)

        if error_ref[0]:
            final_phase = _phase_html(final_phase_idx, elapsed, running=False)
            err_html = f'<div class="pda-error-banner">✗ {error_ref[0]}</div>'
            yield _state(tuple(buckets), final_phase_idx, final_phase, err_html, "", None)
            return

        result = result_ref[0]
        if not result or not result.success:
            err_msg = (result.error if result else "Unknown error")
            final_phase = _phase_html(final_phase_idx, elapsed, running=False)
            err_html = f'<div class="pda-error-banner">✗ Generation failed: {err_msg}</div>'
            yield _state(tuple(buckets), final_phase_idx, final_phase, err_html, "", None)
            return

        # Success
        out_path = Path(result.output_dir)
        out_files = [f for f in out_path.rglob("*") if f.is_file()]
        total_kb = sum(f.stat().st_size for f in out_files) / 1024
        mins = int(elapsed) // 60
        secs = int(elapsed) % 60
        time_str = f"{mins}:{secs:02d}"

        final_phase = _phase_html(5, elapsed, running=False)
        success_html = (
            f'<div class="pda-success-banner">'
            f'<strong>&#10003; Demo generated successfully</strong><br>'
            f'<span style="font-size:12px;color:#bbf7d0">'
            f'{len(out_files)} files &middot; {total_kb:.1f} KB &middot; {time_str} elapsed &middot; '
            f'<code>{result.demo_form}</code> / <code>{result.demo_type}</code></span><br>'
            f'<span style="font-size:11px;color:var(--pda-text2);font-family:var(--pda-mono)">'
            f'$ {result.run_command}</span>'
            f'</div>'
        )
        files_html = _files_html(result.output_dir)
        yield _state(tuple(buckets), final_phase_idx, final_phase,
                     success_html, files_html, result)

    except Exception as exc:
        elapsed = time.time() - start_time
        buckets, phase_idx = _split_progress_by_phase(progress_buf)
        final_phase = _phase_html(phase_idx, elapsed, running=False)
        err_html = f'<div class="pda-error-banner">✗ {exc}</div>'
        yield _state(tuple(buckets), phase_idx, final_phase, err_html, "", None)


# ─────────────────────────────────────────────────────────────────────────────
# Build UI
# ─────────────────────────────────────────────────────────────────────────────

def build_ui() -> gr.Blocks:

    with gr.Blocks() as demo:
        # State
        result_state = gr.State(None)
        output_dir_state = gr.State("")

        # ── Hero header ──────────────────────────────────────────────
        gr.HTML(_header_html())

        # ── Main tabs ────────────────────────────────────────────────
        with gr.Tabs():

            # ╔══════════════════════════════════════════╗
            # ║  Tab 1: Generate                        ║
            # ╚══════════════════════════════════════════╝
            with gr.TabItem("⚡ Generate"):
                with gr.Row(equal_height=False):

                    # ── Left column: inputs ─────────────────────────
                    with gr.Column(scale=5, min_width=380):

                        gr.Markdown("### Paper Input")
                        with gr.Row():
                            source_input = gr.Textbox(
                                placeholder="arXiv ID (1706.03762) · arXiv URL · or paste abstract…",
                                label="arXiv ID / URL / Text",
                                lines=2,
                                scale=3,
                            )
                            pdf_input = gr.File(
                                label="Upload PDF",
                                file_types=[".pdf"],
                                scale=2,
                            )

                        # ── Example papers ──────────────────────────
                        gr.HTML('<p style="font-size:11px;color:var(--pda-text3);margin:4px 0 2px;'
                                'text-transform:uppercase;letter-spacing:0.05em;font-weight:500">'
                                'Try an example</p>')
                        with gr.Row(elem_classes="example-papers"):
                            example_btns = []
                            for name, arxiv_id in EXAMPLE_PAPERS:
                                btn = gr.Button(
                                    name,
                                    variant="secondary",
                                    size="sm",
                                    elem_classes="example-btn",
                                )
                                example_btns.append((btn, arxiv_id))

                        gr.Markdown("### LLM Provider")
                        with gr.Row():
                            provider_dd = gr.Dropdown(
                                choices=list_providers(),
                                value="anthropic",
                                label="Provider",
                                scale=1,
                            )
                            model_dd = gr.Dropdown(
                                choices=_default_models(),
                                value=_default_models()[0] if _default_models() else None,
                                label="Model",
                                allow_custom_value=True,
                                scale=2,
                            )
                            api_key_input = gr.Textbox(
                                placeholder="API key (or set in Settings tab)",
                                label="API Key",
                                type="password",
                                scale=2,
                            )

                        gr.Markdown("### Output")
                        output_kind_dd = gr.Dropdown(
                            choices=KIND_OPTIONS,
                            value="Auto",
                            label="What to make",
                        )
                        kind_info = gr.HTML(
                            f'<p style="font-size:12px;color:var(--pda-text2);margin:4px 0 0">'
                            f'{KIND_META["Auto"][2]}</p>'
                        )

                        # App sub-row — only visible when kind = App
                        with gr.Row(visible=False) as app_format_row:
                            app_format_dd = gr.Dropdown(
                                choices=APP_OPTIONS,
                                value="Auto",
                                label="App framework",
                                scale=2,
                            )
                            app_format_info = gr.HTML(
                                f'<p style="font-size:12px;color:var(--pda-text2);'
                                f'margin:4px 0 0;align-self:flex-end">'
                                f'{APP_META["Auto"]}</p>',
                                scale=3,
                            )

                        # Presentation sub-row — only visible when kind = Presentation
                        with gr.Row(visible=False) as pres_format_row:
                            pres_format_dd = gr.Dropdown(
                                choices=PRES_OPTIONS,
                                value="Auto",
                                label="Slides format",
                                scale=2,
                            )
                            pres_format_info = gr.HTML(
                                f'<p style="font-size:12px;color:var(--pda-text2);'
                                f'margin:4px 0 0;align-self:flex-end">'
                                f'{PRES_META["Auto"]}</p>',
                                scale=3,
                            )

                        # Page sub-row — only visible when kind = Page
                        with gr.Row(visible=False) as page_format_row:
                            page_format_dd = gr.Dropdown(
                                choices=PAGE_OPTIONS,
                                value="Auto",
                                label="Page type",
                                scale=2,
                            )
                            page_format_info = gr.HTML(
                                f'<p style="font-size:12px;color:var(--pda-text2);'
                                f'margin:4px 0 0;align-self:flex-end">'
                                f'{PAGE_META["Auto"]}</p>',
                                scale=3,
                            )

                        # Diagram sub-row — only visible when kind = Diagram
                        with gr.Row(visible=False) as diagram_format_row:
                            diagram_format_dd = gr.Dropdown(
                                choices=DIAGRAM_OPTIONS,
                                value="Auto",
                                label="Diagram type",
                                scale=2,
                            )
                            diagram_format_info = gr.HTML(
                                f'<p style="font-size:12px;color:var(--pda-text2);'
                                f'margin:4px 0 0;align-self:flex-end">'
                                f'{DIAGRAM_META["Auto"]}</p>',
                                scale=3,
                            )

                        # Demo focus sub-row — visible when kind = App
                        with gr.Row(visible=False) as demo_focus_row:
                            demo_focus_dd = gr.Dropdown(
                                choices=FOCUS_OPTIONS,
                                value="Auto",
                                label="Demo focus",
                                scale=2,
                            )
                            demo_focus_info = gr.HTML(
                                f'<p style="font-size:12px;color:var(--pda-text2);'
                                f'margin:4px 0 0;align-self:flex-end">'
                                f'{FOCUS_META["Auto"]}</p>',
                                scale=3,
                            )

                        with gr.Accordion("Advanced", open=False):
                            max_iter_sl = gr.Slider(
                                minimum=8, maximum=60, value=25, step=1,
                                label="Max agent iterations (Phase 2 budget)",
                            )

                        generate_btn = gr.Button(
                            "◆  Generate Demo", variant="primary", size="lg",
                            elem_id="pda-generate-btn",
                        )

                    # ── Right column: progress + output ─────────────
                    with gr.Column(scale=7, min_width=440):

                        status_html = gr.HTML(
                            '<p style="font-size:13px;color:var(--pda-text2)">Ready.</p>'
                        )

                        phase_html_component = gr.HTML(
                            '<div id="pda-phase-status"></div>'
                        )

                        # Per-phase log tabs
                        log_boxes = []
                        with gr.Tabs(elem_classes="pda-log-tabs") as log_tabs:
                            for idx, phase_name in enumerate(_PHASE_LABELS):
                                with gr.TabItem(phase_name, id=idx):
                                    tb = gr.Textbox(
                                        label=None,
                                        show_label=False,
                                        lines=14,
                                        max_lines=400,
                                        interactive=False,
                                        elem_id=f"pda-log-{phase_name.lower()}",
                                    )
                                    log_boxes.append(tb)

                        files_html = gr.HTML(
                            '<p style="font-size:13px;color:var(--pda-text2)">Generated files will appear here.</p>'
                        )

                        with gr.Row():
                            download_btn  = gr.Button("⬇ Download ZIP", variant="secondary")
                            open_btn      = gr.Button("↗ Open Demo",    variant="secondary")
                            download_file = gr.File(label="ZIP", visible=False)

                        with gr.Accordion("File Preview", open=True):
                            file_picker = gr.Dropdown(
                                choices=[],
                                label="Select a file to preview",
                                interactive=True,
                            )
                            file_preview = gr.Markdown(
                                value="",
                                label="Content",
                            )

            # ╔══════════════════════════════════════════╗
            # ║  Tab 2: Settings & Keys                 ║
            # ╚══════════════════════════════════════════╝
            with gr.TabItem("⚙ Settings & Keys"):
                gr.HTML("""
<div style="max-width:700px">
  <h3 style="font-size:16px;font-weight:600;color:var(--pda-text);margin:0 0 4px">Credentials</h3>
  <p style="font-size:13px;color:var(--pda-text2);margin:0 0 20px">
    Keys are saved to <code>~/.paper-demo-agent/config.json</code> and never sent
    anywhere except the chosen LLM provider. Environment variables are detected automatically.
  </p>
</div>""")

                key_status_display = gr.HTML(_key_status_html())

                gr.HTML('<div style="height:1px;background:var(--pda-border);margin:16px 0"></div>')

                # ── API Keys for all providers ───────────────────────────────
                gr.HTML("""
<div style="max-width:700px;margin-bottom:10px">
  <h4 style="font-size:14px;font-weight:600;color:var(--pda-text);margin:0 0 6px">
    API Keys
  </h4>
  <p style="font-size:12px;color:var(--pda-text2);margin:0 0 4px;line-height:1.6">
    Get keys from your provider's dashboard:
    <a href="https://console.anthropic.com" target="_blank"
       style="color:var(--pda-accent);text-decoration:none">Anthropic</a> ·
    <a href="https://platform.openai.com/api-keys" target="_blank"
       style="color:var(--pda-accent);text-decoration:none">OpenAI</a> ·
    <a href="https://aistudio.google.com/apikey" target="_blank"
       style="color:var(--pda-accent);text-decoration:none">Google AI Studio</a> ·
    <a href="https://platform.deepseek.com" target="_blank"
       style="color:var(--pda-accent);text-decoration:none">DeepSeek</a> ·
    <a href="https://dashscope.aliyuncs.com" target="_blank"
       style="color:var(--pda-accent);text-decoration:none">Qwen/DashScope</a> ·
    <a href="https://www.minimaxi.com" target="_blank"
       style="color:var(--pda-accent);text-decoration:none">MiniMax</a>
  </p>
</div>""")

                with gr.Row():
                    key_name_dd = gr.Dropdown(
                        choices=[
                            "ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GOOGLE_API_KEY",
                            "DEEPSEEK_API_KEY", "QWEN_API_KEY", "MINIMAX_API_KEY",
                            "MINIMAX_GROUP_ID", "HUGGINGFACE_TOKEN",
                        ],
                        value="ANTHROPIC_API_KEY",
                        label="Key name",
                    )
                    key_value_input = gr.Textbox(
                        placeholder="Paste key value here…",
                        label="Value",
                        type="password",
                    )
                    save_key_btn = gr.Button("Save", variant="primary")
                key_save_msg = gr.HTML("")

                gr.HTML('<div style="height:1px;background:var(--pda-border);margin:16px 0"></div>')

                # ── Auto-detected tools (collapsed) ──────────────────────────
                with gr.Accordion("Auto-detected Tools", open=False):
                    gr.HTML("""
<div style="max-width:700px;margin-bottom:10px">
  <p style="font-size:12px;color:var(--pda-text2);margin:0 0 10px;line-height:1.6">
    Paper Demo Agent scans for credentials left by other AI tools on your machine.
    If detected, they are used automatically — no copy-pasting needed.
  </p>
</div>""")
                    tool_detect_display = gr.HTML(_tool_detect_html())
                    with gr.Row():
                        refresh_tools_btn = gr.Button("↻ Refresh Detected Tools", variant="secondary", size="sm")

                # ── Google / Gemini auth (collapsed) ─────────────────────────
                with gr.Accordion("Google / Gemini Authentication", open=False):
                    gr.HTML("""
<div style="max-width:700px;margin-bottom:10px">
  <p style="font-size:12px;color:var(--pda-text2);margin:0 0 12px;line-height:1.6">
    Gemini supports two auth methods — an <strong>API key</strong> (set above) <em>or</em>
    <strong>Application Default Credentials</strong> (ADC) via the <code>gcloud</code> CLI.
    ADC means no key to copy-paste: sign in once with your Google account and you're done.
  </p>
</div>""")

                    adc_status_display = gr.HTML(_adc_status_html())

                    gr.HTML("""
<div style="background:var(--pda-bg3);border:1px solid var(--pda-border);border-radius:8px;
            padding:14px 16px;margin:10px 0 6px;max-width:640px">
  <div style="font-size:10px;color:var(--pda-text3);margin-bottom:8px;font-weight:600;
              text-transform:uppercase;letter-spacing:0.06em">
    Install gcloud (if needed)
  </div>
  <code style="font-size:12px;color:var(--pda-text2);display:block;margin-bottom:12px">
    brew install --cask google-cloud-sdk
  </code>
  <div style="font-size:10px;color:var(--pda-text3);margin-bottom:8px;font-weight:600;
              text-transform:uppercase;letter-spacing:0.06em">
    Authenticate with your Google account
  </div>
  <code style="font-size:13px;color:#86efac;font-weight:600;display:block;margin-bottom:8px">
    gcloud auth application-default login
  </code>
  <div style="font-size:11px;color:var(--pda-text3);line-height:1.5">
    This opens a browser to sign in with Google. Paper Demo Agent detects the
    credentials automatically — no key needed. Click <strong>Refresh</strong> after signing in.
  </div>
</div>""")

                    check_adc_btn = gr.Button("↻ Refresh ADC Status", variant="secondary", size="sm")

                gr.HTML('<div style="height:1px;background:var(--pda-border);margin:16px 0"></div>')

                # ── HuggingFace login ────────────────────────────────────────
                gr.HTML("""
<div style="max-width:700px;margin-bottom:8px">
  <h4 style="font-size:14px;font-weight:600;color:var(--pda-text);margin:0 0 4px">
    HuggingFace
  </h4>
  <p style="font-size:12px;color:var(--pda-text2);margin:0;line-height:1.6">
    Required for gated models. Get a token at
    <a href="https://huggingface.co/settings/tokens" target="_blank"
       style="color:var(--pda-accent);text-decoration:none">huggingface.co/settings/tokens</a>.
  </p>
</div>""")
                hf_status = gr.HTML(_check_hf_status())
                with gr.Row():
                    hf_token_input = gr.Textbox(
                        placeholder="hf_…",
                        label="HuggingFace Token",
                        type="password",
                        scale=3,
                    )
                    hf_login_btn  = gr.Button("Login",  variant="primary", scale=1)
                    hf_logout_btn = gr.Button("Logout", variant="secondary", scale=1)
                hf_login_msg = gr.HTML("")

            # ╔══════════════════════════════════════════╗
            # ║  Tab 3: Help & Examples                 ║
            # ╚══════════════════════════════════════════╝
            with gr.TabItem("❓ Help"):
                gr.HTML("""
<div style="max-width:800px">

<h3 style="font-size:16px;font-weight:600;color:var(--pda-text);margin:0 0 16px">Quick Start</h3>

<div class="help-grid">
  <div class="help-card">
    <h4>1. Set an API Key</h4>
    <p>Go to the Settings tab and paste your Anthropic, OpenAI, or other provider key.
       Keys persist across sessions.</p>
  </div>
  <div class="help-card">
    <h4>2. Enter a Paper</h4>
    <p>Paste an arXiv ID (e.g. <code>1706.03762</code>), a full arXiv URL, or upload
       a PDF from your disk. Or click an example paper.</p>
  </div>
  <div class="help-card">
    <h4>3. Choose What to Make</h4>
    <p>Leave as <em>Auto</em> to let the agent decide, or pick Presentation / Demo App /
       Project Page / Diagram. Sub-options appear for the chosen category.</p>
  </div>
  <div class="help-card">
    <h4>4. Download or Open</h4>
    <p>After generation, download the ZIP or click "Open Demo" to launch it
       directly in your browser.</p>
  </div>
</div>

<h3 style="font-size:16px;font-weight:600;color:var(--pda-text);margin:24px 0 16px">Output Categories</h3>
<div class="help-grid">
  <div class="help-card">
    <h4>⚡ App</h4>
    <p><strong>Gradio</strong> (HF Space) or <strong>Streamlit</strong> — interactive Python apps.
       Focus: <em>Try the model</em>, <em>Explore results</em>, or <em>Explain theory</em>.</p>
  </div>
  <div class="help-card">
    <h4>📊 Presentation</h4>
    <p><strong>PowerPoint</strong> (.pptx), <strong>LaTeX/Beamer</strong> (pdflatex), or
       <strong>HTML Slides</strong> (reveal.js with KaTeX math and animations).</p>
  </div>
  <div class="help-card">
    <h4>🌐 Page</h4>
    <p><strong>Project Page</strong> (Nerfies-style), <strong>GitHub README</strong> (badges + Mermaid), or
       <strong>Blog Article</strong> (Distill.pub with D3.js visualizations).</p>
  </div>
  <div class="help-card">
    <h4>🗺️ Diagram</h4>
    <p><strong>Interactive Mermaid</strong> (clickable flowcharts) or
       <strong>Graphviz</strong> (publication-quality SVG/PNG architecture diagrams).</p>
  </div>
</div>

<h3 style="font-size:16px;font-weight:600;color:var(--pda-text);margin:24px 0 12px">CLI Usage</h3>
<pre style="background:var(--pda-bg3);border:1px solid var(--pda-border);border-radius:8px;padding:16px;font-size:12px;color:#d4d4d8;font-family:var(--pda-mono)">
# Basic usage
paper-demo-agent demo 1706.03762

# With category
paper-demo-agent demo arxiv:2312.11805 --form page --provider openai

# With category + subtype
paper-demo-agent demo paper.pdf --form app --subtype streamlit
paper-demo-agent demo paper.pdf --form presentation --subtype beamer
paper-demo-agent demo paper.pdf --form page --subtype readme
paper-demo-agent demo paper.pdf --form diagram --subtype graphviz

# Key management
paper-demo-agent key set ANTHROPIC_API_KEY sk-ant-...
paper-demo-agent providers
</pre>

</div>""")

        # ── Event wiring ──────────────────────────────────────────────

        # Example paper buttons → populate source input
        for btn, arxiv_id in example_btns:
            btn.click(
                fn=lambda aid=arxiv_id: aid,
                inputs=None,
                outputs=source_input,
            )

        # Provider → model update
        provider_dd.change(
            fn=_get_models_for_provider,
            inputs=provider_dd,
            outputs=model_dd,
        )

        # Output kind → show/hide sub-rows + update info text
        def _on_kind_change(kind):
            meta = KIND_META.get(kind, KIND_META["Auto"])
            info = (
                f'<p style="font-size:12px;color:var(--pda-text2);margin:4px 0 0">'
                f'{meta[0]} <strong>{meta[1]}</strong> — {meta[2]}</p>'
            )
            show_app  = (kind == "App")
            show_pres = (kind == "Presentation")
            show_page = (kind == "Page")
            show_diag = (kind == "Diagram")
            show_focus = (kind == "App")
            return (
                gr.update(visible=show_app),
                gr.update(visible=show_pres),
                gr.update(visible=show_page),
                gr.update(visible=show_diag),
                gr.update(visible=show_focus),
                info,
            )

        output_kind_dd.change(
            fn=_on_kind_change,
            inputs=output_kind_dd,
            outputs=[app_format_row, pres_format_row, page_format_row,
                     diagram_format_row, demo_focus_row, kind_info],
        )

        # App format → update description
        def _on_app_format_change(fmt):
            desc = APP_META.get(fmt, APP_META["Auto"])
            return f'<p style="font-size:12px;color:var(--pda-text2);margin:4px 0 0">{desc}</p>'

        app_format_dd.change(
            fn=_on_app_format_change,
            inputs=app_format_dd,
            outputs=app_format_info,
        )

        # Presentation format → update format description
        def _on_pres_format_change(fmt):
            desc = PRES_META.get(fmt, PRES_META["Auto"])
            return f'<p style="font-size:12px;color:var(--pda-text2);margin:4px 0 0">{desc}</p>'

        pres_format_dd.change(
            fn=_on_pres_format_change,
            inputs=pres_format_dd,
            outputs=pres_format_info,
        )

        # Page format → update description
        def _on_page_format_change(fmt):
            desc = PAGE_META.get(fmt, PAGE_META["Auto"])
            return f'<p style="font-size:12px;color:var(--pda-text2);margin:4px 0 0">{desc}</p>'

        page_format_dd.change(
            fn=_on_page_format_change,
            inputs=page_format_dd,
            outputs=page_format_info,
        )

        # Diagram format → update description
        def _on_diagram_format_change(fmt):
            desc = DIAGRAM_META.get(fmt, DIAGRAM_META["Auto"])
            return f'<p style="font-size:12px;color:var(--pda-text2);margin:4px 0 0">{desc}</p>'

        diagram_format_dd.change(
            fn=_on_diagram_format_change,
            inputs=diagram_format_dd,
            outputs=diagram_format_info,
        )

        # Demo focus → update focus description
        def _on_focus_change(focus):
            desc = FOCUS_META.get(focus, FOCUS_META["Auto"])
            return f'<p style="font-size:12px;color:var(--pda-text2);margin:4px 0 0">{desc}</p>'

        demo_focus_dd.change(
            fn=_on_focus_change,
            inputs=demo_focus_dd,
            outputs=demo_focus_info,
        )

        # Generate button — also update file picker after generation
        # Output layout from _run_generate:
        #   (log0, log1, log2, log3, log4, log5,  ← 6 per-phase textboxes
        #    log_tabs,                              ← Tabs selected
        #    phase_html, status_html, files_html,   ← HTML components
        #    result_state)                           ← State
        gen_outputs = log_boxes + [log_tabs, phase_html_component,
                                   status_html, files_html, result_state]

        def _run_generate_and_update_picker(*args):
            last = None
            for update in _run_generate(*args):
                last = update
                yield update + (gr.update(),)
            # After generation completes, populate file picker from result state
            if last and last[-1] is not None:
                result = last[-1]
                choices = _file_preview_choices(result.output_dir)
                value = choices[0] if choices else None
                yield last + (gr.update(choices=choices, value=value),)

        generate_btn.click(
            fn=_run_generate_and_update_picker,
            inputs=[
                source_input, pdf_input,
                provider_dd, model_dd, api_key_input,
                output_kind_dd, app_format_dd, pres_format_dd,
                page_format_dd, diagram_format_dd, demo_focus_dd, max_iter_sl,
            ],
            outputs=gen_outputs + [file_picker],
        )

        # File preview
        def _on_file_pick(filename, result):
            if result is None or not filename:
                return ""
            return _read_file_preview(result.output_dir, filename)

        file_picker.change(
            fn=_on_file_pick,
            inputs=[file_picker, result_state],
            outputs=file_preview,
        )

        # Download ZIP
        def _on_download(result):
            if result is None:
                return gr.update(visible=False)
            zip_path = _make_zip(result.output_dir)
            if zip_path:
                return gr.update(value=zip_path, visible=True)
            return gr.update(visible=False)

        download_btn.click(fn=_on_download, inputs=result_state, outputs=download_file)

        # Open demo
        def _on_open(result):
            if result is None:
                return gr.update(value=_info_html("No demo generated yet."))
            try:
                runner = DemoRunner(result.output_dir, result.main_file, result.demo_form)
                runner.run(open_browser=True)
                form_msg = {
                    "app":              "Gradio app launching — browser will open at localhost:7861",
                    "app_streamlit":    "Streamlit app launching — browser will open at localhost:8501",
                    "presentation":     "Opened in browser",
                    "website":          "Opened in browser",
                    "flowchart":        "Opened in browser",
                    "slides":           "Generating .pptx and opening in PowerPoint / LibreOffice…",
                    "latex":            "Opened .tex file — compile with: pdflatex presentation.tex",
                    "page_readme":      "Opened README.md in default viewer",
                    "page_blog":        "Opened in browser",
                    "diagram_graphviz": "Generating diagrams and opening SVG…",
                }.get(result.demo_form, "Opening demo…")
                return gr.update(value=_ok_html(form_msg))
            except Exception as exc:
                return gr.update(value=_error_html(f"Could not open demo: {exc}"))

        open_btn.click(fn=_on_open, inputs=result_state, outputs=status_html)

        # Key management
        def _do_save_key(name, value):
            msg = _save_key(name, value)
            return msg, _key_status_html()

        save_key_btn.click(
            fn=_do_save_key,
            inputs=[key_name_dd, key_value_input],
            outputs=[key_save_msg, key_status_display],
        )

        # ADC status refresh
        check_adc_btn.click(
            fn=lambda: (_adc_status_html(), _key_status_html()),
            inputs=None,
            outputs=[adc_status_display, key_status_display],
        )

        # Tool credential refresh
        refresh_tools_btn.click(
            fn=lambda: (_tool_detect_html(), _key_status_html()),
            inputs=None,
            outputs=[tool_detect_display, key_status_display],
        )

        # HuggingFace login/logout
        hf_login_btn.click(fn=_hf_login, inputs=hf_token_input, outputs=hf_login_msg)
        hf_logout_btn.click(fn=_hf_logout, inputs=None, outputs=hf_login_msg)

    return demo


# ─────────────────────────────────────────────────────────────────────────────
# Public launch entry point
# ─────────────────────────────────────────────────────────────────────────────

def _kill_port(port: int) -> None:
    """Kill any process currently holding the given TCP port (macOS / Linux)."""
    import signal
    import subprocess
    try:
        result = subprocess.run(
            ["lsof", "-ti", f"tcp:{port}"],
            capture_output=True, text=True, timeout=5,
        )
        pids = [int(p) for p in result.stdout.split() if p.strip().isdigit()]
        for pid in pids:
            try:
                import os
                os.kill(pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
        if pids:
            import time as _time
            _time.sleep(1.0)   # give the process a moment to release the port
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass   # lsof not available — skip silently


def launch(
    host: str = "0.0.0.0",
    port: int = 7860,
    share: bool = False,
    open_browser: bool = True,
    auth: Optional[Tuple[str, str]] = None,
) -> None:
    _kill_port(port)
    demo = build_ui()

    # Allow Gradio to serve generated demo files (ZIPs, etc.) from these dirs
    allowed = [
        str(Path.cwd()),
        str(Path.cwd() / "demos"),
    ]

    demo.launch(
        server_name=host,
        server_port=port,
        share=share,
        inbrowser=open_browser,
        auth=auth,
        favicon_path=None,
        css=CSS,
        js=JS_ON_LOAD,
        head=HEAD,
        theme=_THEME,
        allowed_paths=allowed,
    )
