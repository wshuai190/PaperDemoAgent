"""Base class and shared helpers for all demo generation skills."""

from abc import ABC, abstractmethod
from paper_demo_agent.paper.models import Paper, PaperAnalysis


# ═══════════════════════════════════════════════════════════════════════════════
# FORM SPECIFICATIONS
# Each entry defines the exact contract the LLM must fulfil for that demo form.
# These are injected verbatim into every skill system prompt.
# ═══════════════════════════════════════════════════════════════════════════════

FORM_SPECS: dict[str, dict] = {
    "app": {
        "main_file": "app.py",
        "technology": "Gradio 5 (Python)",
        "description": "Interactive Python web app — HuggingFace Spaces quality",
        "stack": ["gradio>=5.0", "Python 3.10+"],
        "cdns": [],
        "must": [
            "Create `app.py` as the main file; first import must be `import gradio as gr`",
            "Use `gr.Blocks(theme=gr.themes.Soft())` as the root layout",
            "Add a header: paper title (large), authors, venue/year, arXiv link button",
            "Use tabbed layout: primary Demo tab + About tab with abstract and BibTeX block",
            "Include `gr.Examples()` with >=3 realistic, pre-loaded examples (click to try)",
            "Add custom CSS via `gr.Blocks(css=...)` for paper branding colors and fonts",
            "Stream model outputs — use `yield` in generator functions for long runs",
            "Handle errors gracefully: `gr.Error('...')` for model failures, timeouts",
            "Write `requirements.txt` with pinned versions for every dependency",
            "Write `README.md` formatted as a HuggingFace Space card (YAML front-matter + description)",
            "End with: `if __name__ == '__main__': demo.launch()`",
        ],
        "forbidden": [
            "Do NOT create HTML/CSS as the primary demo output",
            "Do NOT use Flask, FastAPI, Django, or any other web framework",
            "Do NOT use deprecated `gr.Interface()` as root — always `gr.Blocks()`",
            "Do NOT hardcode model weights — load from HuggingFace Hub with `from_pretrained()`",
        ],
        "quality_bar": "HuggingFace Spaces featured demos",
    },

    "presentation": {
        "main_file": "demo.html",
        "technology": "reveal.js 5.2.1 — single self-contained HTML file",
        "description": "Conference-quality HTML5 presentation slides",
        "stack": ["reveal.js 5.2.1", "KaTeX", "highlight.js"],
        "cdns": [
            "https://unpkg.com/reveal.js@5.2.1/dist/reveal.css",
            "https://unpkg.com/reveal.js@5.2.1/dist/theme/black.css",
            "https://unpkg.com/reveal.js@5.2.1/plugin/highlight/monokai.css",
            "https://unpkg.com/reveal.js@5.2.1/dist/reveal.js",
            "https://unpkg.com/reveal.js@5.2.1/plugin/highlight/highlight.js",
            "https://unpkg.com/reveal.js@5.2.1/plugin/math/math.js",
            "https://unpkg.com/reveal.js@5.2.1/plugin/notes/notes.js",
        ],
        "must": [
            "Create `demo.html` — one fully self-contained file, no external local assets",
            "Load reveal.js 5.2.1 from the exact CDN URLs listed above — never change versions",
            "Call `Reveal.initialize({ hash:true, transition:'slide', transitionSpeed:'fast', plugins:[RevealHighlight, RevealMath.KaTeX, RevealNotes] })`",
            "Build >=14 slides: Title, Motivation, Background, Method Overview, Method Detail x2-3, Key Results, Ablation, Demo Placeholder, Comparison, Limitations, Conclusion, Q&A",
            "Use `data-auto-animate` on consecutive related slides for smooth element transitions",
            "Every list slide uses `class='fragment'` — reveal bullets one at a time, NO bullet dumps",
            "Add `<aside class='notes'>` speaker notes on every content slide",
            "Create >=3 original inline SVG diagrams for the method/architecture sections",
            "Override theme via CSS vars: `--r-background-color`, `--r-main-font`, `--r-heading-color`, `--r-link-color`",
            "FONT SIZING: `--r-main-font-size: 28px` max for body text. Headings h1 36-40px, h2 30-34px, h3 24-28px. Bullet text 22-26px. NEVER exceed 40px for any element. Code blocks 16-18px",
            "Use a dark, branded color scheme (dark bg + vibrant accent matching the paper topic)",
            "All math uses KaTeX syntax inside `$$...$$` delimiters",
        ],
        "forbidden": [
            "Do NOT reference local CSS/JS files — CDN only",
            "Do NOT create app.py or any Python files",
            "Do NOT use impress.js, Slick, or other slide frameworks",
            "Do NOT put more than 5 bullet points on any single slide",
            "Do NOT use the default white theme — always customise the color scheme",
            "Do NOT set --r-main-font-size larger than 28px — oversized text looks unprofessional and overflows slides",
        ],
        "quality_bar": "NeurIPS / ICML / ICLR oral presentation slides",
    },

    "website": {
        "main_file": "index.html",
        "technology": "Static HTML5 / CSS3 / Vanilla JS — Nerfies / Distill.pub style",
        "description": "Professional research paper project page, opens directly in browser",
        "stack": ["HTML5", "CSS3 custom properties", "Vanilla JS ES2020+", "Inter font", "KaTeX"],
        "cdns": [
            "https://fonts.googleapis.com/css2?family=Inter:ital,opsz,wght@0,14..32,300..700;1,14..32,300..700&display=swap",
            "https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500&display=swap",
            "https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css",
            "https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js",
            "https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/contrib/auto-render.min.js",
        ],
        "must": [
            "Create `index.html` — one single file that opens with `file://` in any browser",
            "Use Inter (Google Fonts CDN) for all body text; JetBrains Mono for code",
            "STEP 0: Call `web_search('{paper title} arxiv')` to find the real arXiv URL — use it in hero buttons and citation. If not found, use '#' as placeholder but mark it clearly.",
            "Page structure: sticky-nav, hero, abstract, teaser, method, results, comparisons, citation, footer",
            "Hero section: paper title (large), author list with superscript affiliations, venue badge, year, action buttons [Paper] [Code] [Demo] [Video]",
            "Implement CSS custom properties: `--primary`, `--bg`, `--bg2`, `--text`, `--text2`, `--border`, `--accent`",
            "Support dark mode: `@media (prefers-color-scheme: dark)` + manual toggle button in nav",
            "Add IntersectionObserver scroll animations: sections fade + slide up as user scrolls",
            "BibTeX section: pre-formatted citation block + 'Copy BibTeX' button (clipboard API)",
            "Fully responsive: 320px to 1200px; CSS grid/flexbox layout, no horizontal overflow",
            "All math notation uses auto-rendered KaTeX (call `renderMathInElement(document.body)`)",
            "Use semantic HTML5: `<nav>`, `<main>`, `<section>`, `<article>`, `<figure>`, `<footer>`",
            "At least one rich interactive element: image comparison slider, results tab-switcher, or animated diagram",
            "Headings: letter-spacing -0.02em; body: line-height 1.65 — these exact values",
        ],
        "forbidden": [
            "Do NOT use React, Vue, Angular, Svelte, or ANY JavaScript framework",
            "Do NOT use Tailwind CDN — write plain CSS only",
            "Do NOT use Bootstrap or other CSS frameworks",
            "Do NOT create multiple HTML files — single `index.html` only",
            "Do NOT require any server — must work with `file://` protocol",
        ],
        "quality_bar": "nerfies.github.io / distill.pub / Instant NGP project page",
    },

    "flowchart": {
        "main_file": "index.html",
        "technology": "Interactive HTML diagram — Mermaid.js v11 ESM + Vanilla JS",
        "description": "Interactive flowchart explorer for paper methodology and algorithms",
        "stack": ["Mermaid.js v11", "HTML5/CSS3", "Vanilla JS ES2020+", "KaTeX", "Inter font"],
        "cdns": [
            "https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs  (use <script type=module>)",
            "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap",
            "https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css",
            "https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js",
        ],
        "must": [
            "Create `index.html` — one self-contained interactive diagram explorer",
            "Import Mermaid.js v11 as ESM with `startOnLoad: false` — render lazily per tab with `mermaid.run({nodes:[el]})`",
            "Each tab has its OWN panel div + its OWN .mermaid div — NEVER render all diagrams at once (causes collision)",
            "Tab switching calls `switchTab(id)`: hide all panels, show selected, lazy-render Mermaid for that tab only",
            "Include >=4 diagram tabs: (1) Full Pipeline/Architecture, (2) Training Algorithm, (3) Inference/Deployment Flow, (4) Key Concepts Map",
            "Every diagram node is CLICKABLE — click opens a right-side detail panel with: explanation, paper section ref, pseudocode",
            "Implement zoom (scroll wheel) and pan (drag) on the diagram canvas using CSS transform",
            "Search bar: typing highlights matching nodes; non-matching nodes dim to 20% opacity",
            "Consistent color coding: inputs=#3b82f6 (blue), transforms=#6366f1 (indigo), decisions=#f59e0b (amber), outputs=#22c55e (green), loss=#ef4444 (red)",
            "Step-by-step walkthrough mode: 'Next'/'Prev' buttons walk through nodes with synchronized detail panel",
            "Dark theme: --bg:#09090b, --bg2:#111113, --border:#27272a, --text:#fafafa",
            "Export buttons per diagram: 'Copy Mermaid Source' (clipboard) and 'Download SVG'",
            "Header with paper title, authors, arXiv link, and one-line description",
            "Legend panel explaining color-coding conventions",
        ],
        "forbidden": [
            "Do NOT use React Flow — it requires a build step",
            "Do NOT produce only static images — all diagrams must be interactive",
            "Do NOT create app.py or Python files as the primary output",
            "Do NOT use `<script src='mermaid.min.js'>` — use the ESM import syntax only",
        ],
        "quality_bar": "Netron app / NN-SVG / interactive GitHub architecture diagrams",
    },

    "slides": {
        "main_file": "build.py",
        "technology": "python-pptx 1.0.0 — generates presentation.pptx",
        "description": "Professional PowerPoint deck — opens in PowerPoint / LibreOffice / Keynote",
        "stack": ["python-pptx>=1.0.0", "httpx", "Pillow", "matplotlib"],
        "cdns": [],
        "must": [
            "Create `build.py` — Python script that runs python-pptx and saves `presentation.pptx`",
            "Set 16:9 widescreen: `prs.slide_width = Inches(13.33); prs.slide_height = Inches(7.5)`",
            "Dark theme: every slide background = `RGBColor(0x09, 0x09, 0x0b)`; body text = `RGBColor(0xfa, 0xfa, 0xfa)`",
            "Accent color `RGBColor(0x63, 0x66, 0xf1)` (#6366f1) for heading bars, chart series, border shapes",
            "Build >=12 slides: Title · Motivation · Background x2 · Method x3 · Results x2 · Example · Conclusion · Q&A",
            "Title slide: paper title 36-44pt bold centered (use 36pt if title >60 chars to avoid overflow), authors 22pt, venue+year 18pt, in white on dark bg. CRITICAL: if the title is long, use word_wrap=True and shrink font — NEVER let text overflow the slide edges",
            "Content slides: filled accent-color rectangle as header bar (top strip), white title text 24-28pt bold. Slide titles must be SHORT (max 50 chars) — use a concise phrase, not the full paper title",
            "FIGURES: Use the exact `extract_pdf_page(page=N, crop={...})` calls from the PDF Figure/Table Map — always crop to just the figure, never embed a full page",
            "TABLES: Use `add_table()` for ALL data tables — NEVER embed a table page as an image. NEVER simulate tables with rectangles or text boxes. Call `slide.shapes.add_table(n_rows, n_cols, left, top, width, height).table` and set cell fill/text/font on every cell",
            "CHARTS: Use `add_chart(XL_CHART_TYPE.BAR_CLUSTERED, ...)` with ALL numeric results for comparison slides",
            "BACKGROUNDS: Check if the paper's institution/company has brand guidelines; use a custom background image or gradient shape for slides that need it",
            "Add speaker notes to every slide: `slide.notes_slide.notes_text_frame.text = 'Notes here'`",
            "End build.py with: `prs.save('presentation.pptx'); print('Saved: presentation.pptx')`",
            "Write `requirements.txt`: python-pptx>=1.0.0",
            "Use `execute_python` to test-run build.py content and verify it saves without errors",
        ],
        "forbidden": [
            "Do NOT create HTML/CSS/JS as the primary output — python-pptx .pptx only",
            "Do NOT use COM automation (win32com) or Keynote AppleScript — python-pptx only",
            "Do NOT leave placeholder dummy content — all slides must use real paper information",
            "Do NOT use existing .potx template files — build slides completely from scratch",
            "Do NOT add logos or brand icons via add_picture() — Simple Icons / Font Awesome CDN files are SVG and python-pptx CANNOT handle SVG. Skip logos entirely; use colored accent rectangles or text labels instead",
            "Do NOT rename SVG files to .png/.jpg and try to open them — they are still SVG internally and will cause an error",
        ],
        "quality_bar": "NeurIPS / ICLR oral presentation deck",
    },

    "latex": {
        "main_file": "presentation.tex",
        "technology": "LaTeX Beamer — compile with `pdflatex presentation.tex` (run twice for refs)",
        "description": "Academic LaTeX/Beamer presentation — publication-quality typeset slides",
        "stack": ["LaTeX", "Beamer", "TikZ", "amsmath", "booktabs"],
        "cdns": [],
        "must": [
            "Create `presentation.tex` — a complete, standalone, compilable LaTeX Beamer document",
            "Use `\\documentclass[aspectratio=169,11pt]{beamer}` for widescreen 16:9",
            "Theme: `\\usetheme{metropolis}` (lowercase, mandatory — this is standard in every TeX Live 2020+ installation)",
            "Color: `\\definecolor{accent}{HTML}{6366f1}` + `\\setbeamercolor{frametitle}{fg=white,bg=accent}`",
            "Packages: `\\usepackage{amsmath,amssymb,tikz,booktabs,xcolor,hyperref,graphicx,colortbl,microtype}`",
            "Build >=12 frames: title, motivation, background x2, method x3, results x2, example, conclusion, Q&A",
            "Incremental reveals: `\\item<1->`, `\\item<2->` — never show all bullets at once on any frame",
            "All math in correct LaTeX: `$inline$` and `\\begin{equation}\\end{equation}` for display",
            "Results table: `\\begin{tabular}` with `\\toprule / \\midrule / \\bottomrule` (booktabs)",
            "FIGURES — use the exact `extract_pdf_page(page=N, crop={...})` calls provided in the PDF Figure/Table Map injected into your initial message — NEVER call extract_pdf_page() without the crop arg, and NEVER embed a full page as a figure",
            "Figure caption in frames: define `\\newcommand{\\figcap}[1]{\\par\\vspace{2pt}{\\scriptsize\\textit{#1}}}` in preamble and call `\\figcap{Your caption here}` — NEVER use `\\caption*` directly in a frame",
            "Architecture figure: TikZ `\\begin{tikzpicture}` with `\\node[draw,rounded corners]` and `\\draw[->]`",
            "Write `compile.sh`: `#!/bin/bash\\npdflatex presentation.tex\\npdflatex presentation.tex`",
            "Write `README.md` with compile command: `pdflatex presentation.tex` (run twice for cross-refs)",
        ],
        "forbidden": [
            "Do NOT use `\\documentclass{article}` — MUST be `beamer`",
            "Do NOT use `\\usetheme{Berlin}` or `\\usetheme{Madrid}` — use `\\usetheme{metropolis}` only",
            "Do NOT use `\\includegraphics` without first calling `extract_pdf_page` with the exact crop from the PDF map — always extract figures before referencing them",
            "Do NOT require external .sty files beyond standard CTAN distributions (metropolis, beamer, tikz, booktabs, etc. are all standard)",
            "Do NOT create Python or HTML files as primary output",
            "Do NOT use fontawesome5, fontawesome, or other icon packages that may not be installed — use text labels instead",
            "Do NOT use `\\caption*{...}` or `\\caption{...}` directly inside a Beamer frame — use `\\figcap{...}` instead",
            "Do NOT call extract_pdf_page() without a crop arg — always use the exact crop coordinates from the PDF Figure/Table Map",
            "Do NOT embed table pages as images — reproduce tables as LaTeX tabular code with booktabs",
        ],
        "must_extract_figures": True,  # signal to skill: always run extract_pdf_page in STEP 0
        "quality_bar": "ICML / ACL / CVPR oral talk Beamer slides",
    },

    "app_streamlit": {
        "main_file": "app.py",
        "technology": "Streamlit 1.30+ (Python)",
        "description": "Interactive Streamlit web app — deployable to HuggingFace Spaces or Streamlit Cloud",
        "stack": ["streamlit>=1.30", "Python 3.10+"],
        "cdns": [],
        "must": [
            "Create `app.py` as the main file; first import must be `import streamlit as st`",
            "Set page config first: `st.set_page_config(page_title='...', page_icon='...', layout='wide')`",
            "Add a header: paper title (st.title), authors, venue/year, arXiv link (st.link_button)",
            "Use `st.tabs()` or `st.sidebar` for navigation between demo sections",
            "Use `@st.cache_data` for data loading and `@st.cache_resource` for model loading",
            "Include interactive widgets: `st.slider`, `st.selectbox`, `st.text_input`, `st.file_uploader`",
            "Use `st.columns()` for multi-column layouts and `st.expander()` for collapsible sections",
            "Display charts via `st.plotly_chart()`, `st.pyplot()`, or `st.altair_chart()`",
            "Show progress for long operations: `st.progress()`, `st.spinner()`",
            "Handle errors gracefully with `st.error()` and `st.warning()`",
            "Write `requirements.txt` with pinned versions for every dependency",
            "Write `README.md` with YAML front-matter for HuggingFace Spaces (`sdk: streamlit`)",
        ],
        "forbidden": [
            "Do NOT create HTML/CSS as the primary demo output",
            "Do NOT use Flask, FastAPI, Django, Gradio, or any other web framework",
            "Do NOT use deprecated `st.cache` — use `@st.cache_data` or `@st.cache_resource`",
            "Do NOT call `st.set_page_config()` more than once or after other st commands",
        ],
        "quality_bar": "Streamlit Gallery featured apps",
    },

    "page_readme": {
        "main_file": "README.md",
        "technology": "GitHub Markdown + Mermaid diagrams",
        "description": "Publication-quality GitHub README — Papers With Code template",
        "stack": ["Markdown", "Mermaid code blocks", "shields.io badges"],
        "cdns": [],
        "must": [
            "Create `README.md` as the main file — a comprehensive, beautifully formatted README",
            "Start with paper title as H1, badges row (arXiv, Python version, license, stars)",
            "Use shields.io badges: `![Python](https://img.shields.io/badge/python-3.9+-blue)`",
            "Include arXiv badge: `[![arXiv](https://img.shields.io/badge/arXiv-XXXX.XXXXX-b31b1b.svg)](url)`",
            "Structure: Title+badges → Overview → Key Results → Quick Start → Method (with Mermaid diagram) → Citation",
            "Include at least one Mermaid diagram in a ```mermaid code block (architecture or pipeline)",
            "Use `<details><summary>` for collapsible sections (detailed results, full BibTeX, etc.)",
            "Include a comparison table with bold best results: `| Method | Acc | F1 |`",
            "Add BibTeX citation block in a ```bibtex code fence",
            "Use web_search to find the paper's arXiv URL and include it in badges and links",
        ],
        "forbidden": [
            "Do NOT create HTML files — output is pure Markdown only",
            "Do NOT create Python scripts as the primary output",
            "Do NOT use raw HTML tables when Markdown tables suffice",
            "Do NOT leave placeholder badge URLs — use real arXiv ID and paper metadata",
        ],
        "quality_bar": "Papers With Code top repositories",
    },

    "page_blog": {
        "main_file": "index.html",
        "technology": "Distill.pub v2 article template — single self-contained HTML file",
        "description": "Interactive research blog post — Distill.pub quality",
        "stack": ["Distill.pub template v2", "KaTeX 0.16.11", "D3.js v7", "HTML5/CSS3"],
        "cdns": [
            "https://distill.pub/template.v2.js",
            "https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css",
            "https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js",
            "https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/contrib/auto-render.min.js",
            "https://d3js.org/d3.v7.min.js",
        ],
        "must": [
            "Create `index.html` — one self-contained Distill-style article",
            "Include `<script src='https://distill.pub/template.v2.js'></script>` in <head>",
            "Use Distill components: `<d-front-matter>`, `<d-article>`, `<d-appendix>`, `<d-bibliography>`",
            "Front matter: title, description, authors with affiliations, date, DOI/arXiv link",
            "Article structure: Hook → Problem → Background → Approach → Key Results → Discussion → Conclusion",
            "Use `<d-cite>` for inline citations and `<d-bibliography>` for references",
            "Use `<d-figure>` for figures with captions, `<d-footnote>` for footnotes",
            "Include at least one interactive D3.js visualization embedded in a `<d-figure>`",
            "All math via KaTeX: `<d-math>` for inline, `<d-math block>` for display equations",
            "Use `<d-aside>` for margin notes explaining technical terms",
            "Mobile-responsive: content should read well on narrow screens",
            "Use web_search to find the paper's arXiv URL and author details",
        ],
        "forbidden": [
            "Do NOT use React, Vue, or any JavaScript framework",
            "Do NOT create Python files as the primary output",
            "Do NOT skip the Distill template script — it provides essential styling",
            "Do NOT use `<script src='mermaid.min.js'>` — use D3.js for visualizations instead",
        ],
        "quality_bar": "distill.pub published articles",
    },

    "diagram_graphviz": {
        "main_file": "build.py",
        "technology": "Python graphviz library → SVG + PNG publication-quality diagrams",
        "description": "Graphviz architecture diagrams — generates SVG/PNG files via Python",
        "stack": ["graphviz>=0.20", "Python 3.10+"],
        "cdns": [],
        "must": [
            "Create `build.py` — Python script that uses the graphviz library to generate diagrams",
            "First import: `from graphviz import Digraph` (or `Graph` for undirected)",
            "Generate at least 3 diagrams: (1) Overall architecture, (2) Training pipeline, (3) Key component detail",
            "Use consistent color scheme: inputs=#3b82f6, transforms=#6366f1, decisions=#f59e0b, outputs=#22c55e, loss=#ef4444",
            "Dark theme: `graph_attr={'bgcolor': '#09090b'}`, white text on colored nodes",
            "Use cluster subgraphs to group related components: `with dot.subgraph(name='cluster_X') as c:`",
            "Set layout attributes: `rankdir`, `ranksep`, `nodesep` for clean spacing",
            "Render to both SVG and PNG: `dot.render('diagram_name', format='svg', cleanup=True)`",
            "Also render PNG: `dot.render('diagram_name', format='png', cleanup=True)`",
            "End build.py with: print listing all generated files",
            "Write `requirements.txt`: graphviz>=0.20",
            "Write `README.md` with: install instructions, what each diagram shows, run command",
            "Use `execute_python` to test-run build.py and verify it generates files without errors",
        ],
        "forbidden": [
            "Do NOT create HTML/CSS/JS as the primary output — graphviz SVG/PNG only",
            "Do NOT use matplotlib for the diagrams — use the graphviz Python library",
            "Do NOT hardcode absolute paths — use relative paths for all outputs",
            "Do NOT forget to install graphviz system package note in README",
        ],
        "quality_bar": "Publication-quality architecture diagrams for ML papers",
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# BASE SKILL CLASS
# ═══════════════════════════════════════════════════════════════════════════════

class BaseSkill(ABC):
    """Abstract base for all paper demo generation skills."""

    name: str = "BaseSkill"
    description: str = "Base skill"

    @abstractmethod
    def get_system_prompt(
        self, paper: Paper, analysis: PaperAnalysis, demo_form: str, demo_type: str
    ) -> str:
        """Return the full system prompt for the LLM agent."""

    @abstractmethod
    def get_initial_message(
        self, paper: Paper, analysis: PaperAnalysis, demo_form: str, demo_type: str
    ) -> str:
        """Return the first user message that kicks off generation."""

    def get_polish_prompt(
        self,
        paper: Paper,
        analysis: PaperAnalysis,
        demo_form: str,
        demo_type: str,
        generated_files: list[str],
    ) -> str:
        """Return a quality-review / polish prompt for Phase 3."""
        spec = FORM_SPECS.get(demo_form, {})
        main_file = spec.get("main_file", "app.py")
        quality_bar = spec.get("quality_bar", "production quality")
        return f"""You have generated: {', '.join(generated_files[:12])}

Run a thorough QUALITY REVIEW and fix everything you find.

STEP 1 — Read {main_file} and audit for:
  • Broken or missing CDN links (verify they match the spec exactly)
  • Placeholder text: "TODO", "INSERT", "PLACEHOLDER", "[AUTHOR]" left unfilled
  • JavaScript errors: undefined variables, missing event listeners, broken async
  • CSS issues: overflow, broken layout at mobile widths, invisible text on dark bg

STEP 2 — Content completeness:
  • Paper title, authors, venue used correctly everywhere
  • All numerical results from the paper are present and accurate
  • No Lorem Ipsum or dummy data in final output

STEP 3 — Polish the visual design:
  • Typography consistent: Inter font, correct weights, sizes, letter-spacing
  • Color contrast: minimum 4.5:1 for body text (WCAG AA)
  • All hover/focus/active states implemented on interactive elements
  • Smooth transitions (200ms ease) on all state changes
  • Spacing uniform: 8px base grid

STEP 4 — Final check:
  • {main_file} opens without errors in a browser
  • README.md (if applicable) has correct run commands

Target quality: {quality_bar}
Rewrite any file that needs significant changes. Make it genuinely impressive."""

    def get_form_polish_prompt(
        self,
        paper: Paper,
        analysis: PaperAnalysis,
        demo_form: str,
        demo_type: str,
        generated_files: list[str],
    ) -> str:
        """Form-specific polish prompt — called for latex/slides/presentation/flowchart
        regardless of which skill generated the content, bypassing skill-level overrides."""
        flist = ', '.join(generated_files[:12])
        figures_available = [f for f in generated_files if f.startswith("figures/fig")]

        if demo_form == "latex":
            figs_line = (
                f"Pre-extracted figures available: {', '.join(figures_available)}\n"
                if figures_available else ""
            )
            return f"""QUALITY REVIEW for LaTeX Beamer presentation — files: {flist}

{figs_line}
Step 1 — Read presentation.tex and fix:
  • Does it use \\usetheme{{metropolis}} (NOT Berlin/Madrid)? Fix if wrong.
  • Are ALL pre-extracted figures used across the slides? Figures: {', '.join(figures_available)}
    Each figure should appear in a relevant slide — don't skip any without reason.
  • Does it have >=12 frames? Count them. Add missing slides if fewer.
  • Are ALL tables reproduced as LaTeX \\begin{{tabular}} code (not embedded images)?
  • Does every frame with bullets use \\item<1-> incremental reveals?
  • Is \\figcap{{...}} used for figure captions (NOT \\caption* in frames)?
  • Do all \\includegraphics use paths like figures/fig1.png?

Step 2 — LaTeX compilation check:
  • Run execute_python to parse presentation.tex and check for unmatched $, {{, }}
  • Verify no TikZ parameterized styles (#1) inside \\begin{{frame}}...\\end{{frame}}
  • Check that all \\includegraphics filenames exist in the figures/ list above

Step 3 — Content quality:
  • Paper title, real author names, venue, year on title slide
  • Real numeric results from the paper in the results frames (not "~X%" estimates)
  • All key paper contributions covered: at minimum motivation, method, results, conclusion

Fix everything found. Target: ICML oral talk quality Beamer slides."""

        elif demo_form == "slides":
            figs_line = (
                f"Pre-extracted figures available: {', '.join(figures_available)}\n"
                if figures_available else ""
            )
            return f"""QUALITY REVIEW for python-pptx presentation — files: {flist}

{figs_line}
Step 1 — Read build.py and fix:
  • Are ALL pre-extracted figures used? {', '.join(figures_available)}
    Use add_picture('figures/figN.png', ...) on the relevant results/method slides.
  • Are ALL tables created with add_table() (NOT embedded as images)?
  • Are there >=12 slides? Count slide additions. Add if fewer.
  • Does every slide have a header bar (accent rectangle) + white title text?
  • Are there speaker notes on every slide?
  • Does build.py end with prs.save('presentation.pptx')?

Step 2 — Run execute_python with the full build.py to verify it saves without errors

Step 3 — Content:
  • Paper title, authors, venue on title slide
  • Real numeric benchmark results (not placeholders)
  • Results slides must include actual paper numbers

Fix all issues. Target: NeurIPS oral presentation deck."""

        elif demo_form == "presentation":
            return f"""QUALITY REVIEW for reveal.js presentation — files: {flist}

Step 1 — Read demo.html and check:
  • Are there >=14 <section> elements? Count them. Add slides if fewer.
  • Does EVERY content <section> have <aside class='notes'>...</aside>? Add missing ones.
  • Is reveal.js loaded from unpkg.com/reveal.js@5.2.1 (exact version)?
  • Does Reveal.initialize() include plugins: RevealHighlight, RevealMath.KaTeX, RevealNotes?
  • Do all list slides use class='fragment' on their <li> items?
  • Are there >=3 inline SVG diagrams for method/architecture slides?
  • Are all CDN links in the file exactly as specified (no version changes)?

Step 2 — Content:
  • Real paper title, all authors, venue, year on title slide
  • Real numeric results from the paper (not "~X%" estimates)
  • BibTeX or citation on the last slide

Step 3 — Fix any broken slide structure

Target: NeurIPS/ICML oral presentation slides."""

        elif demo_form == "app_streamlit":
            return f"""QUALITY REVIEW for Streamlit app — files: {flist}

Step 1 — Read app.py and check:
  • Is st.set_page_config() called FIRST (before any other st commands)?
  • Are @st.cache_data and @st.cache_resource used for expensive operations?
  • Are there interactive widgets (sliders, selectboxes, text inputs)?
  • Is the paper title, authors, and venue displayed in the header?
  • Are there st.spinner() or st.progress() for long operations?

Step 2 — Content:
  • Real paper results are displayed (not placeholder data)
  • Charts/visualizations use real paper numbers
  • BibTeX or citation section included

Step 3 — Fix any missing requirements in requirements.txt

Target: Streamlit Gallery featured apps."""

        elif demo_form == "page_readme":
            return f"""QUALITY REVIEW for GitHub README — files: {flist}

Step 1 — Read README.md and check:
  • Does it start with H1 title and a row of shields.io badges?
  • Is the arXiv badge URL using the real arXiv ID (not placeholder XXXX)?
  • Is there at least one ```mermaid diagram block?
  • Are there <details><summary> collapsible sections?
  • Is there a comparison table with bold best results?
  • Is there a BibTeX citation in a ```bibtex code fence?

Step 2 — Content:
  • Paper overview accurately describes the contribution
  • Key results match the paper's reported numbers
  • Quick Start section has runnable commands

Step 3 — Fix any placeholder text or broken badge URLs

Target: Papers With Code top repositories."""

        elif demo_form == "page_blog":
            return f"""QUALITY REVIEW for Distill blog article — files: {flist}

Step 1 — Read index.html and check:
  • Is distill.pub template.v2.js included in <head>?
  • Is <d-front-matter> properly filled with authors, date, description?
  • Does <d-article> have proper section structure?
  • Are <d-cite> used for references with matching <d-bibliography>?
  • Is there at least one interactive D3.js visualization?
  • Are equations using <d-math> (not raw KaTeX)?

Step 2 — Content:
  • Article tells a coherent story from problem to solution
  • Key results from the paper are accurately presented
  • <d-aside> margin notes explain technical terms

Step 3 — Fix any broken Distill components

Target: distill.pub published article quality."""

        elif demo_form == "diagram_graphviz":
            return f"""QUALITY REVIEW for Graphviz diagrams — files: {flist}

Step 1 — Read build.py and check:
  • Does it import from graphviz (Digraph/Graph)?
  • Are there at least 3 separate diagrams generated?
  • Are colors consistent: inputs=#3b82f6, transforms=#6366f1, outputs=#22c55e?
  • Are cluster subgraphs used to group related components?
  • Does it render to both SVG and PNG formats?
  • Does it end with a print statement listing generated files?

Step 2 — Run execute_python with build.py to verify it works

Step 3 — Content:
  • Diagrams use real paper terminology and architecture
  • requirements.txt includes graphviz>=0.20
  • README.md has install and run instructions

Target: Publication-quality ML architecture diagrams."""

        else:
            # Fallback to generic polish for other forms
            return self.get_polish_prompt(paper, analysis, demo_form, demo_type, generated_files)

    # ─────────────────────────────────────────────────────────────────────
    # Shared helpers
    # ─────────────────────────────────────────────────────────────────────

    def _paper_summary(self, paper: Paper, analysis: PaperAnalysis) -> str:
        authors_list = getattr(paper, "authors", None)
        authors = ", ".join(authors_list) if authors_list else "Unknown"
        year = getattr(paper, "year", None) or ""
        lines = [
            f"Title:        {paper.title}",
            f"Authors:      {authors}" + (f" ({year})" if year else ""),
            f"Paper type:   {analysis.paper_type}",
            f"Contribution: {analysis.contribution}",
            f"Interaction:  {analysis.interaction_pattern}",
        ]
        if paper.abstract:
            lines.append(f"Abstract:     {paper.abstract[:500]}...")
        return "\n".join(lines)

    def _form_block(self, demo_form: str) -> str:
        """Generate the mandatory output-format constraint block."""
        spec = FORM_SPECS.get(demo_form)
        if not spec:
            return f"DEMO FORM: {demo_form}"

        must_text = "\n".join(f"  ✓  {m}" for m in spec["must"])
        forbidden_text = "\n".join(f"  ✗  {f}" for f in spec["forbidden"])
        cdns = spec.get("cdns", [])
        cdn_text = (
            "\n\nUSE THESE EXACT CDN LINKS (do not change versions or URLs):\n"
            + "\n".join(f"  {c}" for c in cdns)
        ) if cdns else ""

        return (
            f"╔══════════════════════════════════════════════════════════════════╗\n"
            f"║  MANDATORY OUTPUT FORMAT — {demo_form.upper():<37}║\n"
            f"║  Technology : {spec['technology'][:53]:<53}║\n"
            f"║  Main file  : {spec['main_file']:<53}║\n"
            f"║  Quality bar: {spec['quality_bar'][:53]:<53}║\n"
            f"╚══════════════════════════════════════════════════════════════════╝\n"
            f"\nYOU MUST DO ALL OF THE FOLLOWING:\n{must_text}"
            f"\n\nYOU MUST NOT DO ANY OF THE FOLLOWING:\n{forbidden_text}"
            f"{cdn_text}"
        )

    def _demo_type_guidance(self, demo_type: str) -> str:
        guidance = {
            "theoretical": (
                "━━ DEMO TYPE: THEORETICAL ━━\n"
                "Goal  → Explain the core ideas so a grad student outside this subfield understands them.\n"
                "Rules → Build intuition BEFORE formalism: concrete example first, then equations.\n"
                "        Every concept: Motivation → Plain-English Intuition → Formal Statement → Example → Impact.\n"
                "        Use diagrams, animations, step-by-step reveals — never walls of text.\n"
                "KPI   → A smart outsider reads it and says 'I finally understand this idea.'"
            ),
            "findings": (
                "━━ DEMO TYPE: FINDINGS ━━\n"
                "Goal  → Show empirical results so a reviewer can assess the paper's claims in 2 minutes.\n"
                "Rules → Hard-code ALL numeric results (tables, figures, ablations) from the paper.\n"
                "        Always show baselines alongside the proposed method — compare, never just show.\n"
                "        Use exact metric names and dataset names from the paper.\n"
                "KPI   → Reviewer understands what was gained over prior work at a glance."
            ),
            "user_demo": (
                "━━ DEMO TYPE: USER DEMO ━━\n"
                "Goal  → Let a non-technical person try the system and see value within 10 seconds.\n"
                "Rules → Pre-load 3+ realistic examples — first interaction is a single click, not an upload.\n"
                "        Show the model/system running on real inputs with real outputs.\n"
                "        Minimize friction: no account, no API key, no setup for the end user.\n"
                "KPI   → Non-technical person tries it, gets a result, and says 'wow, that is cool.'"
            ),
        }
        return guidance.get(demo_type, f"━━ DEMO TYPE: {demo_type.upper()} ━━")

    def _multistep_instructions(self, demo_form: str) -> str:
        """Numbered phase instructions injected into every skill system prompt."""
        steps = {
            "app": """━━ EXECUTION PLAN (follow in order, do not skip steps) ━━

Step 1 ── RESEARCH
  • Use web_search: find current Gradio 5 best practices, HF Space examples for this paper topic
  • Use search_huggingface: find official model/dataset on HuggingFace Hub
  • Note the model ID, license, and any required tokens

Step 2 ── REQUIREMENTS
  • Write requirements.txt FIRST with all dependencies and pinned versions
  • Include: gradio>=5.0, torch/transformers (if applicable), numpy, etc.

Step 3 ── SKELETON
  • Write app.py: all imports, gr.Blocks() layout, tab structure, UI components
  • Define all widgets, output areas, examples panel, about tab — placeholder logic OK here

Step 4 ── CORE LOGIC
  • Implement model loading (lazy-load on first call, not at import time)
  • Implement inference function(s) with streaming (yield) for long operations
  • Add gr.Progress() indicators; handle OOM, timeout, missing model errors with gr.Error()

Step 5 ── UX POLISH
  • Add gr.Examples() with >=3 realistic, click-to-run examples
  • About tab: abstract, method summary, BibTeX, arXiv/GitHub links
  • Custom CSS: Inter font, brand accent color, styled header

Step 6 ── TEST
  • execute_python: `import app` — must succeed with no errors
  • Test core function with a simple input
  • Verify requirements.txt lists every import used

Step 7 ── README
  • Write README.md as HuggingFace Space card (YAML front-matter + usage + citation)""",

            "presentation": """━━ EXECUTION PLAN (follow in order, do not skip steps) ━━

Step 1 ── RESEARCH
  • web_search: find this paper's official results, key tables, figures, and author details
  • DO NOT search for reveal.js CDN URLs — they are pre-baked in the form spec above

Step 2 ── OUTLINE
  • Plan every slide: title + 1-line content description
  • Sequence: Title → Motivation → Background → Method(x3) → Results(x2) → Demo → Comparison → Limits → Conclusion → Q&A

Step 3 ── SCAFFOLD
  • Write demo.html: CDN links, <head>, reveal.js structure, custom CSS color variables
  • Define theme override (--r-background-color, --r-heading-color, --r-link-color, etc.)

Step 4 ── CONTENT
  • Fill every slide with real paper content — NO Lorem Ipsum or placeholder text
  • Title slide: paper name, all authors, venue, year
  • Every slide: add <aside class='notes'> with speaker notes

Step 5 ── DIAGRAMS + ICONS
  • Draw >=3 inline SVG diagrams for method/architecture slides
  • Consistent colors, labeled arrows, font-size 14px minimum
  • ICONS: Use Font Awesome 6 CDN (already in reveal.js head) — zero downloads needed
    Examples: <i class="fa-solid fa-brain"></i>, <i class="fa-solid fa-database"></i>, <i class="fa-solid fa-gears"></i>
    For ML brand logos: <img src="https://cdn.simpleicons.org/pytorch/ffffff" height="20">
    DO NOT search flaticon.com — use Font Awesome classes directly

Step 6 ── ANIMATIONS
  • Add data-auto-animate to consecutive related slides
  • Add class='fragment' to bullet items (never show all bullets at once)

Step 7 ── POLISH
  • read_file demo.html → check Reveal.initialize() includes all plugins
  • Verify every CDN link; no slide has >5 bullets""",

            "website": """━━ EXECUTION PLAN (follow in order, do not skip steps) ━━

Step 1 ── RESEARCH
  • web_search: find the paper's official project page and author details
  • Find exact author names, affiliations, venue, year, arXiv ID

Step 2 ── ARCHITECTURE
  • Write a comment outline at the top of index.html listing all sections
  • Plan which sections need KaTeX, which need SVG, which need JS animations

Step 3 ── FOUNDATION
  • Write <head>: CDN links (Inter, JetBrains Mono, KaTeX), meta tags
  • Write full CSS: custom properties, reset, typography (Inter -0.02em headings, 1.65 body), dark mode, responsive grid

Step 4 ── HERO SECTION
  • Paper title (display size, bold), author list with affiliations, venue badge, year
  • Action buttons: [Paper] [Code] [Demo] [Video]
  • Teaser figure or animated key-result visualization
  • ICONS: Use Font Awesome 6 CDN — zero downloads needed
    Add to <head>: <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.6.0/css/all.min.css">
    Examples: <i class="fa-solid fa-brain"></i>, <i class="fa-solid fa-diagram-project"></i>
    For ML brand logos: <img src="https://cdn.simpleicons.org/pytorch/ffffff" height="20">
    DO NOT search flaticon.com — use Font Awesome classes directly

Step 5 ── CONTENT SECTIONS
  • Abstract (formatted prose, KaTeX for equations)
  • Method: overview SVG diagram + numbered steps
  • Results: card grid with metrics, comparison tables, gallery images

Step 6 ── INTERACTIVITY
  • IntersectionObserver scroll animations (fade + slide-up on entry)
  • BibTeX copy-to-clipboard
  • Dark/light mode toggle
  • At least one interactive element: comparison slider, result tab-switcher, or animated diagram

Step 7 ── RESPONSIVE + FINAL
  • @media queries for 320px, 768px, 1200px
  • renderMathInElement() call after DOM ready
  • Fix any overflow; verify file:// protocol works""",

            "flowchart": """━━ EXECUTION PLAN (follow in order, do not skip steps) ━━

Step 1 ── UNDERSTAND THE PAPER
  • Deeply read the paper: identify ALL components, data flows, decision points, algorithms
  • Extract: input/output types, model architecture layers, training loop, inference pipeline
  • Use web_search only for paper-specific info: official repo, benchmark results, architecture details

Step 2 ── DIAGRAM DESIGN
  • Identify 4 diagram views: (1) Full Pipeline, (2) Training Algorithm, (3) Inference Flow, (4) Key Concepts
  • Write out Mermaid source code for each diagram using paper's actual terminology
  • Plan all nodeDetails entries: title, description, section reference, pseudocode snippet

Step 3 ── SCAFFOLD
  • Write index.html: ESM Mermaid v11 import with startOnLoad:false, dark-theme CSS, tab nav
  • CRITICAL: Use the lazy per-tab rendering pattern from the system prompt above
  • Each tab gets its OWN panel div (panel-pipeline, panel-training, panel-inference, panel-concepts)
  • Each panel has its OWN diagram-canvas and detail-panel with unique IDs

Step 4 ── MERMAID DIAGRAMS
  • Implement all 4 diagrams with real paper content and custom themeVariables
  • Color coding: inputs=#3b82f6, transforms=#6366f1, decisions=#f59e0b, outputs=#22c55e, loss=#ef4444
  • Each .mermaid div is inside its own panel — NEVER share a canvas between tabs

Step 5 ── INTERACTIVITY
  • Use attachHandlers(panel) called AFTER mermaid.run() — NOT MutationObserver
  • Zoom/pan per canvas (CSS transform on the .mermaid div inside each panel)
  • Step-by-step walkthrough with Next/Prev buttons updates the detail panel for active tab

Step 6 ── CONTENT + ICONS
  • Fill every node's nodeDetails entry (title, desc, section, code) — no blank panels
  • ICONS: Use Font Awesome 6 CDN — zero downloads needed
    Add to <head>: <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.6.0/css/all.min.css">
    Examples: <i class="fa-solid fa-brain"></i>, <i class="fa-solid fa-layer-group"></i>, <i class="fa-solid fa-gears"></i>
    For ML brand logos: <img src="https://cdn.simpleicons.org/pytorch/ffffff" height="20">
    Use icons in diagram headers, legend, or section titles
    DO NOT search flaticon.com — use Font Awesome classes directly, zero web searches needed

Step 7 ── POLISH
  • Verify all 4 diagrams render; check dark theme contrast (4.5:1 minimum)
  • Test click, zoom, pan, search, walkthrough; verify SVG export works""",

            "slides": """━━ EXECUTION PLAN (follow in order, do not skip steps) ━━

Step 1 ── SETUP
  • install_package: python-pptx (run first)
  • Plan all slides: list every slide title + content type (title/bullets/chart/diagram)
  • Use web_search only for paper-specific info: author list, venue, benchmark numbers, diagrams

Step 2 ── FOUNDATION
  • Write build.py skeleton: imports, prs = Presentation(), set_dimensions(), helper functions
  • Helpers: set_dark_bg(slide), add_header_bar(slide, title), format_text(tf, text, size, bold)
  • Test imports: execute_python with just the import + Presentation() + save to /tmp/test.pptx

Step 3 ── BRANDING + TITLE SLIDES
  • Pick brand colors: accent #6366f1 (indigo) as default, or match the paper's institution primary color
  • Title slide: paper title (36-44pt bold, use smaller size for long titles), all authors (22pt), venue+year (18pt)
  • CRITICAL: if the title exceeds 60 characters, shrink font to 36pt and enable word_wrap=True to prevent overflow
  • Do NOT download institution logos as SVG — python-pptx cannot render SVGs. Use text-only branding

Step 4 ── CONTENT + METHOD SLIDES
  • Background slides: text boxes with bullet points (font 20pt, indent levels)
  • Method slides: use matplotlib to draw architecture diagram → save PNG → add_picture()
  • Every slide: colored header strip (accent BG rectangle), white title on top

Step 5 ── RESULTS SLIDES
  • Use add_chart(XL_CHART_TYPE.BAR_CLUSTERED, ...) with ChartData populated from paper numbers
  • Chart colors: series fills set to RGBColor(0x63, 0x66, 0xf1) (accent), plot area BG = dark

Step 6 ── EXECUTE + VERIFY
  • execute_python with full build.py content — verify it saves presentation.pptx without errors
  • If errors occur, fix python-pptx API calls and retry

Step 7 ── NOTES + FINAL
  • Add speaker notes to every slide
  • Write requirements.txt
  • read_file build.py to verify all slides present before finishing""",

            "latex": """━━ EXECUTION PLAN (follow in order, do not skip steps) ━━

Step 1 ── PLAN CONTENT
  • List every frame title + content type (math/table/tikz/bullets/code)
  • Extract all key equations and write LaTeX for them (use amsmath environments)
  • Use web_search only for paper-specific info: exact benchmark numbers, author affiliations

Step 2 ── PREAMBLE
  • Write complete LaTeX preamble: \\documentclass[aspectratio=169,11pt]{beamer}
  • Include all packages: amsmath, amssymb, tikz, booktabs, xcolor, hyperref, graphicx, listings
  • Define colors and theme overrides (accent color #6366f1)

Step 3 ── TITLE + INTRO FRAMES
  • \\maketitle frame; motivation frame with the core problem statement
  • Background frames: prerequisites with \\item<1-> incremental reveals

Step 4 ── METHOD FRAMES
  • Main method/algorithm frame: pseudocode using listings or algorithm2e
  • Architecture frame: TikZ diagram with \\node[draw,rounded corners,fill=accent!20] and \\draw[->]
  • Math frames: key equations with equation/align environments

Step 5 ── RESULTS FRAMES
  • Numeric results table: tabular with \\toprule/\\midrule/\\bottomrule
  • Comparison table: \\textbf{} to highlight best results in each column

Step 6 ── FINAL FRAMES + BUILD
  • Conclusion frame: 3 key takeaways with \\item<1->
  • Q&A frame
  • Write build.sh and README.md with pdflatex compile instructions
  • execute_python to syntax-check: search for unbalanced $, {, } using Python string parsing""",

            "app_streamlit": """━━ EXECUTION PLAN (follow in order, do not skip steps) ━━

Step 1 ── RESEARCH
  • Use web_search: find paper-specific results, author list, GitHub repo
  • Use search_huggingface: find official model/dataset on HuggingFace Hub
  • Note the model ID, license, and any required tokens

Step 2 ── REQUIREMENTS
  • Write requirements.txt FIRST: streamlit>=1.30, plus domain dependencies
  • Include: torch/transformers (if applicable), plotly, numpy, pandas, etc.

Step 3 ── PAGE CONFIG + LAYOUT
  • Write app.py: st.set_page_config() FIRST, then sidebar/tabs layout
  • Define page structure: sidebar for controls, main area for visualizations
  • Add paper title, authors, venue in the header area

Step 4 ── CORE LOGIC
  • Implement model loading with @st.cache_resource (lazy-load, not at import)
  • Implement data processing with @st.cache_data
  • Add interactive widgets: sliders, selectboxes, text inputs
  • Display results with st.plotly_chart() or st.pyplot()

Step 5 ── UX POLISH
  • Add st.expander() sections for detailed information
  • Include About section with abstract, BibTeX, links
  • Add st.spinner() for long operations

Step 6 ── TEST
  • execute_python: import streamlit — must succeed
  • Verify requirements.txt lists every import used

Step 7 ── README
  • Write README.md with HuggingFace Space YAML front-matter (sdk: streamlit)""",

            "page_readme": """━━ EXECUTION PLAN (follow in order, do not skip steps) ━━

Step 1 ── RESEARCH
  • web_search: find the paper's arXiv URL, GitHub repo, author details
  • web_search: find benchmark results, comparison numbers, key figures
  • Note exact arXiv ID for badge URLs

Step 2 ── HEADER + BADGES
  • Write README.md: H1 title, badge row (arXiv, Python, license)
  • Use real arXiv ID in badge URL: img.shields.io/badge/arXiv-XXXX.XXXXX-b31b1b.svg
  • Add 1-line description after badges

Step 3 ── OVERVIEW + KEY RESULTS
  • Write 2-3 paragraph overview of the paper's contribution
  • Add a key results table with bold best numbers
  • Include a teaser figure description or ASCII art

Step 4 ── METHOD + DIAGRAM
  • Write a ```mermaid code block showing the architecture/pipeline
  • Add Quick Start section with installation and usage commands
  • Include code examples in ```python blocks

Step 5 ── DETAILED SECTIONS
  • Use <details><summary> for collapsible sections (full results, ablations)
  • Add comparison table with prior work
  • Include requirements and dependencies

Step 6 ── CITATION + FOOTER
  • Add BibTeX in ```bibtex code fence
  • Add license section and acknowledgments
  • Final review: ensure all badge URLs are correct""",

            "page_blog": """━━ EXECUTION PLAN (follow in order, do not skip steps) ━━

Step 1 ── RESEARCH
  • web_search: find paper arXiv URL, author affiliations, venue
  • web_search: find key results and figures to reproduce
  • Note all author names and institutional affiliations

Step 2 ── TEMPLATE SETUP
  • Write index.html: include distill.pub template.v2.js in <head>
  • Add KaTeX and D3.js CDN links
  • Set up <d-front-matter> with authors, date, description

Step 3 ── ARTICLE STRUCTURE
  • Write <d-article> with sections: Introduction, Background, Method, Results, Discussion
  • Use <d-cite> for all paper references
  • Add <d-aside> margin notes for technical terms

Step 4 ── MATH + FIGURES
  • Add key equations using <d-math> (inline) and <d-math block> (display)
  • Create <d-figure> elements with descriptive captions
  • Use SVG diagrams for method illustrations

Step 5 ── INTERACTIVE D3 VISUALIZATION
  • Create at least one D3.js interactive visualization
  • Examples: interactive results chart, concept explorer, data distribution plot
  • Embed in <d-figure> with proper dimensions

Step 6 ── BIBLIOGRAPHY + POLISH
  • Add <d-bibliography> with all cited papers
  • Add <d-appendix> with additional details
  • Test that file opens correctly in browser""",

            "diagram_graphviz": """━━ EXECUTION PLAN (follow in order, do not skip steps) ━━

Step 1 ── UNDERSTAND THE PAPER
  • Deeply read the paper: identify ALL components, data flows, decision points
  • Extract: input/output types, model layers, training loop, inference pipeline
  • Use web_search for paper-specific info: official repo, architecture details

Step 2 ── PLAN DIAGRAMS
  • Plan 3 diagrams: (1) Overall architecture, (2) Training pipeline, (3) Key component
  • List all nodes and edges for each diagram
  • Decide layout direction (TB or LR) for each

Step 3 ── SETUP + FIRST DIAGRAM
  • install_package: graphviz
  • Write build.py skeleton: imports, color constants, helper functions
  • Implement first diagram (overall architecture) with cluster subgraphs

Step 4 ── REMAINING DIAGRAMS
  • Implement training pipeline diagram with loop structure
  • Implement key component detail diagram
  • Use consistent colors across all diagrams

Step 5 ── RENDER + VERIFY
  • Add render calls for both SVG and PNG formats
  • execute_python to test build.py — verify it generates files without errors
  • Fix any graphviz API issues

Step 6 ── DOCUMENTATION
  • Write requirements.txt: graphviz>=0.20
  • Write README.md: install instructions, diagram descriptions, run command
  • List all generated output files""",
        }
        return steps.get(demo_form, f"Follow logical steps to build a high-quality {demo_form} demo.")

    def _tool_usage_instructions(self) -> str:
        return """━━ TOOL USAGE RULES ━━

  web_search         Use for PAPER-SPECIFIC info: official results, author list, GitHub repo
                     NOT for library basics already documented in this system prompt
  search_huggingface Use to find official models/datasets for the paper
  extract_pdf_page   Render a PDF page (or cropped region) as PNG to embed in slides/demos
                     Required args: page (1-indexed integer)
                     Optional: dpi (default 150), crop ({x0,y0,x1,y1} as 0.0–1.0 fractions), filename
                     Examples:  extract_pdf_page(page=5)                  → full page 5
                                extract_pdf_page(page=7, crop={x0:0,y0:0.5,x1:1,y1:1})  → bottom half of page 7
                     Use this for: architecture diagrams, result tables, example figures from the paper
  download_file      Use to fetch images from URLs into the output directory
                     For ML brand logos only: download_file url=https://cdn.simpleicons.org/pytorch/ffffff filename=assets/pytorch.svg
                     For all other icons: use Font Awesome 6 CDN classes (zero downloads needed)
                     DO NOT search flaticon.com — it does not provide direct download URLs
  write_file         Use for every file you create (path relative to output dir)
  read_file          Use before rewriting any file to check current state
  execute_python     Use to test Python syntax/imports, validate build scripts, syntax-check output
  install_package    Use to install python-pptx, graphviz, matplotlib, etc. before use

  ALWAYS: Pre-baked CDN links are in the FORM_SPECS above — use them verbatim, never search for them.
          Write requirements.txt; read files before overwriting; verify build scripts with execute_python.
  NEVER:  Search for reveal.js/Mermaid/KaTeX CDN URLs — they are already provided above.
          Write placeholder code; skip requirements.txt; leave TODO items unfilled."""
