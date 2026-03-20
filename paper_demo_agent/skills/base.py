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
  • Verify all CDN URLs are correct pinned versions (no 'latest', no wrong versions)
  • Check all figures from figures/ directory are referenced in the output
  • Verify dark theme consistency — no white or near-white backgrounds anywhere
  • Check all interactive elements work: buttons respond, sliders update, links point somewhere valid

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

Step 4 — Universal checks:
  • Verify all CDN URLs are correct pinned versions
  • Check all figures from figures/ directory are referenced
  • Verify dark theme consistency (no white backgrounds)
  • Check all interactive elements work (buttons, sliders, links)

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

Step 3 — Universal checks:
  • Verify all CDN URLs are correct pinned versions
  • Check all figures from figures/ directory are referenced
  • Verify dark theme consistency (no white backgrounds)
  • Check all interactive elements work (buttons, sliders, links)

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

Step 4 — Universal checks:
  • Verify all CDN URLs are correct pinned versions (reveal.js@5.2.1, etc.)
  • Check all figures from figures/ directory are referenced
  • Verify dark theme consistency (no white backgrounds)
  • Check all interactive elements work (buttons, fragments, links)

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

Step 4 — Universal checks:
  • Verify all CDN URLs are correct pinned versions
  • Check all figures from figures/ directory are referenced
  • Verify dark theme consistency (no white backgrounds in custom CSS)
  • Check all interactive widgets work (sliders update, buttons respond)

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

Step 4 — Universal checks:
  • Verify all CDN URLs are correct pinned versions (shields.io badges, etc.)
  • Check all figures referenced in README actually exist in figures/
  • Verify dark-mode friendly content (avoid raw white image backgrounds)
  • Check all code fences have language specifiers and are syntactically valid

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

Step 4 — Universal checks:
  • Verify all CDN URLs are correct pinned versions (distill template.v2.js, d3, etc.)
  • Check all figures from figures/ directory are referenced in the article
  • Verify dark theme consistency (article body: no white/light hardcoded backgrounds)
  • Check all interactive D3 visualizations respond to user interaction

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

Step 4 — Universal checks:
  • Verify all CDN URLs / pip package versions are correct
  • Check all figures referenced in README exist in the output directory
  • Verify dark theme consistency in SVG output (bg: #09090b for wrappers)
  • Check all generated diagrams render without errors (run execute_python again)

Target: Publication-quality ML architecture diagrams."""

        else:
            # Fallback to generic polish for other forms
            return self.get_polish_prompt(paper, analysis, demo_form, demo_type, generated_files)

    # ─────────────────────────────────────────────────────────────────────
    # Shared helpers
    # ─────────────────────────────────────────────────────────────────────

    @classmethod
    def _cdn_urls(cls) -> dict[str, str]:
        """Return a dict of verified CDN URLs, keyed by library name.

        All URLs have been tested and are known-good at the pinned version.
        Inject these into skill prompts via _tool_usage_instructions() to avoid
        the agent wasting iterations searching for or guessing CDN links.
        """
        return {
            # ── Fonts ────────────────────────────────────────────────────────
            "inter_font": (
                "https://fonts.googleapis.com/css2?family=Inter:"
                "ital,opsz,wght@0,14..32,300..700;1,14..32,300..700&display=swap"
            ),
            "jetbrains_mono": (
                "https://fonts.googleapis.com/css2?family=JetBrains+Mono:"
                "wght@400;500&display=swap"
            ),
            # ── Math ─────────────────────────────────────────────────────────
            "katex_css": "https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css",
            "katex_js": "https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js",
            "katex_auto_render": (
                "https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/contrib/auto-render.min.js"
            ),
            # ── Presentation ─────────────────────────────────────────────────
            "revealjs_css": "https://unpkg.com/reveal.js@5.2.1/dist/reveal.css",
            "revealjs_theme_black": "https://unpkg.com/reveal.js@5.2.1/dist/theme/black.css",
            "revealjs_highlight_css": (
                "https://unpkg.com/reveal.js@5.2.1/plugin/highlight/monokai.css"
            ),
            "revealjs_js": "https://unpkg.com/reveal.js@5.2.1/dist/reveal.js",
            "revealjs_highlight_js": (
                "https://unpkg.com/reveal.js@5.2.1/plugin/highlight/highlight.js"
            ),
            "revealjs_math_js": "https://unpkg.com/reveal.js@5.2.1/plugin/math/math.js",
            "revealjs_notes_js": "https://unpkg.com/reveal.js@5.2.1/plugin/notes/notes.js",
            # ── Diagrams ─────────────────────────────────────────────────────
            "mermaid_esm": (
                "https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs"
                "  <!-- use <script type=module> -->"
            ),
            # ── Data / Viz ────────────────────────────────────────────────────
            "d3_v7": "https://d3js.org/d3.v7.min.js",
            # ── Publishing ────────────────────────────────────────────────────
            "distill_template": "https://distill.pub/template.v2.js",
        }

    def _graphics_reference(self) -> str:
        """Return the GRAPHICS_REFERENCE string for injection into prompts."""
        from paper_demo_agent.graphics import GRAPHICS_REFERENCE
        return GRAPHICS_REFERENCE

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

    def _figure_integration_note(self, demo_form: str) -> str:
        """Return figure extraction guidance for forms that embed visual content."""
        if demo_form in ("slides", "latex"):
            return """━━ FIGURE & TABLE INTEGRATION (MANDATORY for slides/latex) ━━
  BEFORE writing any slides, extract key figures from the paper PDF:
  1. extract_pdf_page(page=N) for architecture diagrams, result charts, example figures
  2. Use full-page PNGs directly — only crop if a figure occupies a small region
  3. Embed with add_picture (pptx) or \\includegraphics (LaTeX)
  4. ALWAYS reproduce tables as structured data (add_table / tabular) — NEVER embed table images
  5. Use \\figcap{} for LaTeX captions (NOT \\caption* in frames)
"""
        elif demo_form == "presentation":
            return """━━ FIGURE & TABLE INTEGRATION (recommended for presentations) ━━
  Consider extracting key figures from the paper PDF as reference:
  1. extract_pdf_page(page=N) for architecture diagrams, key result figures
  2. Use extracted images as REFERENCE to create inline SVG diagrams (don't embed the PNG)
  3. Reproduce all data tables as styled HTML <table> elements
  4. Create inline SVG charts for visual comparisons
"""
        elif demo_form in ("page_readme",):
            return """━━ FIGURE INTEGRATION (recommended for README) ━━
  Extract key figures from the paper PDF:
  1. extract_pdf_page(page=1) for teaser/overview figure
  2. extract_pdf_page for architecture diagram and key results
  3. Embed with <p align="center"><img src="figures/..." width="80%"></p>
  4. Add italicized captions below each figure
"""
        return ""

    def _multistep_instructions(self, demo_form: str) -> str:
        """Numbered phase instructions injected into every skill system prompt."""
        steps = {
            "app": """━━ EXECUTION PLAN (follow in order, do not skip steps) ━━

Step 1 ── FIND MODEL
  • Use search_huggingface: find official model/dataset on HuggingFace Hub
  • Note the model ID, license, and any required tokens

Step 2 ── WRITE app.py (ONE SHOT)
  • Write the COMPLETE app.py in a single write_file call — all imports, layout, logic
  • gr.Blocks(theme=gr.themes.Soft()) root, tabbed layout (Demo + About)
  • Lazy-load model on first call (not at import time), streaming with yield
  • gr.Examples() with >=3 realistic examples, error handling with gr.Error()
  • Custom CSS: Inter font, brand accent color, styled header
  • About tab: abstract, method summary, BibTeX, arXiv/GitHub links

Step 3 ── REQUIREMENTS + README
  • Write requirements.txt with all pinned dependencies
  • Write README.md as HuggingFace Space card
  • DONE — do NOT self-verify. Polish phase handles review.""",

            "presentation": """━━ EXECUTION PLAN (follow in order, do not skip steps) ━━

Step 0 ── EXTRACT FIGURES (optional but recommended)
  • If the paper has key architecture diagrams, result charts, or example figures:
    extract_pdf_page(page=N) for 2-4 key pages. Use extracted PNGs as reference
    when creating your own inline SVG diagrams (trace the structure, don't embed the PNG).
  • For result tables: READ the numbers from the paper and hard-code them in HTML tables.

Step 1 ── PLAN
  • Plan every slide: title + 1-line content description
  • Sequence: Title → Motivation → Background → Method(x3) → Results(x2) → Demo → Comparison → Limits → Conclusion → Q&A

Step 2 ── WRITE demo.html (ONE SHOT)
  • Write the COMPLETE demo.html in a single write_file call
  • CDN links from form spec, custom CSS theme override, reveal.js structure
  • Every slide: real paper content (no placeholders), <aside class='notes'> speaker notes
  • >=3 inline SVG diagrams for method/architecture slides
  • Icons: Font Awesome 6 CDN + cdn.simpleicons.org for ML logos — zero downloads
  • Animations: data-auto-animate on related slides, class='fragment' on bullets
  • Reveal.initialize() with all plugins: RevealHighlight, RevealMath.KaTeX, RevealNotes

Step 3 ── DONE
  • Do NOT read_file to verify. Do NOT web_search for CDN URLs. Polish phase handles review.""",

            "website": """━━ EXECUTION PLAN (follow in order, do not skip steps) ━━

Step 0 ── RESEARCH & EXTRACT (do this first)
  • web_search for the paper's arXiv URL — use it in hero buttons and citation
  • If the paper has a striking teaser or architecture figure:
    extract_pdf_page(page=N) to reference when creating your own SVG diagrams
  • Parse key numeric results from the paper text for the results section

Step 1 ── PLAN
  • Plan all sections: Hero, Abstract, Method, Results, Citation
  • Note which sections need KaTeX, SVG, or JS animations

Step 2 ── WRITE index.html (ONE SHOT)
  • Write the COMPLETE index.html in a single write_file call
  • <head>: CDN links from form spec (Inter, JetBrains Mono, KaTeX, Font Awesome 6)
  • Full CSS: custom properties, dark theme, responsive grid, typography
  • Hero: paper title, authors with affiliations, venue badge, action buttons
  • Content: abstract (KaTeX for equations), method (SVG diagram), results (card grid, tables)
  • Interactivity: IntersectionObserver scroll anims, BibTeX copy, dark/light toggle
  • Responsive: @media queries for 320px, 768px, 1200px
  • renderMathInElement() after DOM ready
  • Icons: Font Awesome 6 classes + cdn.simpleicons.org for ML logos — zero downloads

Step 3 ── DONE
  • Do NOT read_file to verify. Do NOT web_search for CDN URLs. Polish phase handles review.""",

            "flowchart": """━━ EXECUTION PLAN (follow in order, do not skip steps) ━━

Step 1 ── PLAN DIAGRAMS
  • Read the paper deeply: identify ALL components, data flows, decision points
  • Plan 4 diagram views: (1) Full Pipeline, (2) Training, (3) Inference, (4) Key Concepts
  • Plan all nodeDetails entries: title, description, section reference, pseudocode

Step 2 ── WRITE index.html (ONE SHOT)
  • Write the COMPLETE index.html in a single write_file call
  • ESM Mermaid v11 import with startOnLoad:false, dark-theme CSS, tab nav
  • Each tab: OWN panel div + OWN diagram-canvas + OWN detail-panel (unique IDs)
  • 4 Mermaid diagrams with real paper content, custom themeVariables
  • Color coding: inputs=#3b82f6, transforms=#6366f1, decisions=#f59e0b, outputs=#22c55e, loss=#ef4444
  • Interactivity: attachHandlers(panel) AFTER mermaid.run(), zoom/pan, walkthrough
  • Every nodeDetails entry filled — no blank panels
  • Icons: Font Awesome 6 CDN + cdn.simpleicons.org for ML logos — zero downloads

Step 3 ── DONE
  • Do NOT read_file to verify. Do NOT web_search for CDN URLs. Polish phase handles review.""",

            "slides": """━━ EXECUTION PLAN (follow in order, do not skip steps) ━━

━━ SLIDE DECK PHILOSOPHY ━━
A great presentation tells a STORY, not a data dump. Think like a keynote speaker:
  • 16-20 slides maximum (never >22). Audience attention drops after 20 minutes.
  • Structure: Title → Why (motivation) → What (method, 3-4 slides) → So What (2-3 key results) → Conclusion → Q&A
  • Only 2-3 results tables/charts — pick the MOST IMPORTANT ones that prove the paper's claim.
  • NEVER include hyperparameter tables, appendix tables, or training config tables.
  • Tables must be STRUCTURED: proper multi-column add_table() with typed data, NOT text dumps.
  • Prefer charts over tables when comparing numbers (charts are visual, tables are boring).
  • Every slide should have a "takeaway" — if it doesn't advance the story, cut it.

Step 1 ── PLAN (pick 16-20 slides)
  • Outline every slide: title + content type + 1-line takeaway
  • Select ONLY 2-3 key results tables from the paper (main comparison, ablation, scaling)
  • SKIP: hyperparameter configs, training details, appendix tables, per-dataset breakdowns
  • For each table: manually extract the numbers and hard-code them as Python lists/tuples

Step 2 ── WRITE build.py (ONE SHOT)
  • Write the COMPLETE build.py in a single write_file call
  • Include: imports, helpers (set_dark_bg, add_header_bar, add_text_box, add_bullet_list, add_results_table)
  • Title slide: paper title (36-44pt, shrink if >60 chars), all authors, venue+year
  • Content slides: bullet points with meaningful text (not raw PDF text!)
  • Method: use matplotlib to draw architecture diagram → BytesIO → add_picture()
  • Results: HARD-CODE numbers as Python data. Use add_results_table() for structured comparison.
    Use add_chart() for visual comparisons. NEVER parse PDF text at runtime.
  • CRITICAL: do NOT use .style property on charts. Set colors via series.format.fill directly.
  • CRITICAL: do NOT use pdfplumber, fitz, or any PDF parser to extract table text.
    All data must be manually extracted and hard-coded as clean Python data structures.
  • Speaker notes: meaningful narration per slide, not "Discuss key takeaways from table N."
  • Pre-extracted figures (figures/fig*.png) can be embedded with add_picture()

Step 3 ── EXECUTE
  • Run: execute_python(open('build.py').read()) — NEVER use subprocess
  • If errors: read_file build.py, fix the specific line, write_file, re-execute

Step 4 ── REQUIREMENTS + DONE
  • Write requirements.txt: python-pptx>=1.0.0, matplotlib (if used)
  • DONE — do NOT self-verify. Polish phase handles review.""",

            "latex": """━━ EXECUTION PLAN (follow in order, do not skip steps) ━━

Step 1 ── PLAN
  • List every frame title + content type (math/table/tikz/bullets/code)
  • Extract all key equations from the paper

Step 2 ── WRITE presentation.tex (ONE SHOT)
  • Write the COMPLETE presentation.tex in a single write_file call
  • Preamble: \\documentclass[aspectratio=169,11pt]{beamer} + all packages
  • Theme: \\usetheme{metropolis} with accent color #6366f1
  • Title + Intro frames, method frames (TikZ diagrams, pseudocode), math frames
  • Results: \\toprule/\\midrule/\\bottomrule tables, \\textbf{} for best numbers
  • Conclusion + Q&A frames

Step 3 ── BUILD SCRIPT + DONE
  • Write build.sh: pdflatex compile instructions
  • Write requirements.txt if any Python dependencies used
  • DONE — do NOT self-verify. Polish phase handles review.""",

            "app_streamlit": """━━ EXECUTION PLAN (follow in order, do not skip steps) ━━

Step 1 ── FIND MODEL
  • Use search_huggingface: find official model/dataset
  • Note the model ID, license, and any required tokens

Step 2 ── WRITE app.py (ONE SHOT)
  • Write the COMPLETE app.py in a single write_file call
  • st.set_page_config() FIRST, sidebar/tabs layout, paper header
  • Model loading with @st.cache_resource, data with @st.cache_data
  • Interactive widgets, st.plotly_chart()/st.pyplot() for results
  • About section with abstract, BibTeX, links

Step 3 ── REQUIREMENTS + README
  • Write requirements.txt: streamlit>=1.30 + all dependencies
  • Write README.md with HF Space YAML (sdk: streamlit)
  • DONE — do NOT self-verify. Polish phase handles review.""",

            "page_readme": """━━ EXECUTION PLAN (follow in order, do not skip steps) ━━

Step 1 ── WRITE README.md (ONE SHOT)
  • Write the COMPLETE README.md in a single write_file call
  • H1 title, badge row (arXiv, Python, license) with real arXiv ID
  • 2-3 paragraph overview, key results table, teaser figure
  • ```mermaid architecture diagram, Quick Start, code examples
  • <details><summary> collapsible sections for full results, ablations
  • BibTeX in ```bibtex fence, license, acknowledgments

Step 2 ── DONE
  • Do NOT self-verify. Polish phase handles review.""",

            "page_blog": """━━ EXECUTION PLAN (follow in order, do not skip steps) ━━

Step 1 ── WRITE index.html (ONE SHOT)
  • Write the COMPLETE index.html in a single write_file call
  • <head>: distill.pub template.v2.js, KaTeX, D3.js CDN links
  • <d-front-matter> with authors, affiliations, date
  • <d-article>: Introduction, Background, Method, Results, Discussion
  • <d-cite> references, <d-aside> margin notes, <d-math> equations
  • <d-figure> with captions, SVG diagrams for method
  • At least one D3.js interactive visualization
  • <d-bibliography> + <d-appendix>

Step 2 ── DONE
  • Do NOT self-verify. Polish phase handles review.""",

            "diagram_graphviz": """━━ EXECUTION PLAN (follow in order, do not skip steps) ━━

Step 1 ── PLAN
  • Identify ALL components, data flows, decision points from the paper
  • Plan 3 diagrams: (1) Overall architecture, (2) Training pipeline, (3) Key component

Step 2 ── WRITE build.py (ONE SHOT)
  • Write the COMPLETE build.py in a single write_file call
  • Imports, color constants, helper functions
  • All 3 diagrams with cluster subgraphs, consistent colors
  • Render calls for both SVG and PNG formats

Step 3 ── EXECUTE
  • Run: execute_python(open('build.py').read()) — NEVER use subprocess
  • If errors: fix and re-execute

Step 4 ── REQUIREMENTS + DONE
  • Write requirements.txt: graphviz>=0.20
  • Write README.md: install instructions, run command
  • DONE — do NOT self-verify. Polish phase handles review.""",
        }
        return steps.get(demo_form, f"Follow logical steps to build a high-quality {demo_form} demo.")

    def _tool_usage_instructions(self) -> str:
        cdn = self._cdn_urls()
        cdn_block = "\n".join(f"    {k:<28} {v}" for k, v in cdn.items())
        from paper_demo_agent.skills.templates import (
            PRESENTATION_STRUCTURE, WEBSITE_STRUCTURE, BLOG_STRUCTURE,
        )
        pres_steps = "\n".join(f"    {i+1:2}. {s}" for i, s in enumerate(PRESENTATION_STRUCTURE))
        web_steps  = "\n".join(f"    {i+1:2}. {s}" for i, s in enumerate(WEBSITE_STRUCTURE))
        blog_steps = "\n".join(f"    {i+1:2}. {s}" for i, s in enumerate(BLOG_STRUCTURE))
        return f"""━━ VERIFIED CDN URLS (use verbatim — do NOT search for alternatives) ━━
{cdn_block}

━━ MATH RENDERING (KaTeX) ━━

  For ANY mathematical equations, use KaTeX. Include these in your HTML <head>:
    <link rel="stylesheet" href="{cdn['katex_css']}">
    <script src="{cdn['katex_js']}"></script>
    <script src="{cdn['katex_auto_render']}"></script>
  Then call on DOMContentLoaded:
    document.addEventListener('DOMContentLoaded', () => renderMathInElement(document.body, {{
      delimiters: [
        {{left: '\\\\[', right: '\\\\]', display: true}},
        {{left: '\\\\(', right: '\\\\)', display: false}}
      ]
    }}));
  Inline math:   \\( f(x) = e^x \\)
  Display math:  \\[ \\mathcal{{L}} = -\\log p(y|x) \\]
  This is CRITICAL for papers with equations — the demo must render them beautifully.
  For reveal.js: use RevealMath.KaTeX plugin (already in CDN list above); delimiters are $$...$$

━━ SECTION STRUCTURES (follow these in order — adapt to paper content) ━━

  Presentation:
{pres_steps}

  Website / Project Page:
{web_steps}

  Blog Post:
{blog_steps}

━━ TOOL USAGE RULES ━━

  web_search         Use for PAPER-SPECIFIC info: official results, author list, GitHub repo
                     NOT for library basics already documented in this system prompt
  search_huggingface Use to find official models/datasets for the paper
  extract_pdf_page   Render a PDF page (or cropped region) as PNG to embed in slides/demos
                     Required args: page (1-indexed integer)
                     Optional: dpi (default 150), crop ({{x0,y0,x1,y1}} as 0.0–1.0 fractions), filename
                     Examples:  extract_pdf_page(page=5)                  → full page 5
                                extract_pdf_page(page=7, crop={{x0:0,y0:0.5,x1:1,y1:1}})  → bottom half of page 7
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
          Write requirements.txt; read files before overwriting.
  NEVER:  Search for reveal.js/Mermaid/KaTeX CDN URLs — they are already provided above.
          Write placeholder code; skip requirements.txt; leave TODO items unfilled.
          Use subprocess to run scripts — always use execute_python directly.

━━ GRAPHICS TOOLKIT (use instead of writing SVG from scratch) ━━

  You have access to pre-built graphics components via:
    from paper_demo_agent.graphics import *

  Or call them directly via the render_svg tool:
    render_svg(expr="pipeline_flow(['Input','Model','Output'], title='Inference')")

  ARCHITECTURE DIAGRAMS (SVG, returns complete <svg> string):
    encoder_decoder(enc_layers, dec_layers)       Transformer encoder-decoder
    transformer_block(num_heads, d_model, d_ff)   Single transformer block with residuals
    cnn_architecture(layers_config)               CNN with conv/pool/fc layers (featuremap style)
    rnn_cell(cell_type='lstm')                    LSTM or GRU cell with gates
    residual_block(num_layers=2)                  ResNet skip-connection block (2=BasicBlock, 3=Bottleneck)
    multi_head_attention_detail(num_heads, d_k, d_v) Detailed MHA with Q/K/V projections
    gan_architecture(gen_layers, disc_layers)     Generator vs Discriminator with fake-image arrow
    pipeline_flow(steps, title='')                Left-to-right pipeline (any # of steps)
    comparison_diagram(method_a, method_b, ...)   Side-by-side comparison
    attention_visualization(ql, kl, weights=None) Attention weight heatmap (SVG)

  CHART TEMPLATES (returns HTML/JS code to embed in HTML files):
    bar_chart_js(data, labels, title, highlight_idx=0)           Chart.js bar chart
    line_chart_js(data_series, labels, title, y_label='Value')   Chart.js multi-line (training curves)
    radar_chart_js(metrics, scores_dict, title)                  Chart.js radar / spider chart
    d3_grouped_bar(data, group_labels, series_labels, title)     D3.js grouped bars
    heatmap_d3(matrix, row_labels, col_labels, title)            D3.js heatmap (attention / confusion)
    metric_dashboard_html(metrics_dict)                          Grid of metric cards with deltas
    comparison_table_html(headers, rows, highlight_row=0)        Styled results table
    results_card_html(metric, value, delta, delta_label='vs SOTA') Single metric card

  MERMAID PATTERNS (returns Mermaid v11 string for <pre class="mermaid">):
    mermaid_pipeline(steps)                       LR flowchart pipeline
    mermaid_training_loop(steps=None)             Standard training loop with loop-back arrow
    mermaid_comparison(a_steps, b_steps, labels)  Side-by-side method comparison subgraphs
    mermaid_architecture(components, connections) TD architecture with subgraphs
    mermaid_sequence(actors, messages)            Sequence diagram

  TIKZ TEMPLATES (for LaTeX/Beamer):
    tikz_flow_diagram(steps, title='')
    tikz_block_diagram(blocks, connections)
    tikz_encoder_decoder(enc_layers, dec_layers)
    tikz_comparison_table(headers, rows, highlight_row=0)

  RULE: When you need an architecture diagram or chart, USE THESE FIRST.
        Do NOT write raw SVG path data from scratch — the toolkit produces better output faster.

━━ ERROR RECOVERY PATTERNS ━━

  write_file FAILS (content too large):
    → Split the file into logical parts. For HTML: write a base file with <script src="data.js">,
      then write data.js separately. For Python: extract data constants into a data.py module.
    → For extremely large HTML files (>50KB): move inline CSS to style.css, inline JS to script.js,
      and large data arrays to data.js — then write_file each separately.
    → NEVER truncate content to fit — split intelligently instead.

  web_search RETURNS NOTHING USEFUL:
    → Try alternative queries: use the paper's full title, then first author + year,
      then key method name + "arxiv" or "github".
    → If still nothing: proceed WITHOUT the info. Use data from the paper PDF itself.
      Mark any missing links with '#' and a visible comment like "[arXiv link pending]".
    → NEVER invent URLs or DOIs — use '#' placeholder and note it clearly.

  CDN LINK FAILS (404, timeout, CORS error):
    → All CDN links in this prompt are pre-vetted. If one fails at runtime:
      1. Try the EXACT same URL (typos are the #1 cause).
      2. For unpkg.com: try cdn.jsdelivr.net equivalent (and vice versa).
      3. NEVER switch to a different library version — the patterns above are version-specific.
    → For Font Awesome: if CDN is blocked, use inline SVG icons as a last resort.

  extract_pdf_page FAILS or returns blank:
    → The page number may be wrong (PDF page != printed page). Try page±1.
    → If the PDF is encrypted or corrupted: skip figure extraction for that page,
      describe the figure in text instead, and note "[Figure could not be extracted]".
    → NEVER call extract_pdf_page in a loop over all pages — target specific pages only.

  execute_python FAILS:
    → Read the error traceback carefully. Common causes:
      - Missing import → add install_package call first
      - File not found → check path is relative to output dir
      - Syntax error → fix the specific line, don't rewrite the whole file
    → After fixing, re-run ONLY the failing script — don't re-run everything.

━━ EFFICIENCY RULES (save iterations & tokens) ━━
  • Do NOT verify output during build — the Polish phase handles quality review.
  • Do NOT call list_files or read_file just to check your own work mid-build.
  • Do NOT web_search for library docs, CDN URLs, or API syntax — everything is pre-baked above.
  • When running build scripts: use execute_python(open('build.py').read()) — never subprocess.
  • Minimize iterations: write the complete file in one write_file call, then move on.

━━ CRITICAL FILE SIZE RULE ━━
  NEVER write a file longer than 300 lines in a single write_file call.
  If a file would exceed 300 lines, you MUST write it in MULTIPLE calls — split intelligently:

  FOR WEBSITE / BLOG / APP FORMS (multi-file):
    Step 1 → write styles.css   (all CSS — typically 100-200 lines)
    Step 2 → write script.js    (all JavaScript — typically 100-300 lines)
    Step 3 → write index.html   (skeleton referencing styles.css + script.js)
    Step 4 → overwrite sections of index.html if content is still incomplete

  FOR PRESENTATION FORM (single self-contained demo.html):
    The main file MUST be demo.html — do NOT create separate CSS/JS files.
    Write demo.html in chunks: first call writes the skeleton (head, first 5 slides),
    second call overwrites with more slides appended — each write_file ≤300 lines.
    reveal.js REQUIRES inline <style> and <script> in the same HTML file.

  FOR PYTHON FORMS: extract large data into data.py, helpers into helpers.py.
  FOR LATEX: split appendix into appendix.tex and \\input{{appendix}} from main file.

  NEVER truncate content to force it under the limit — split intelligently instead.
  NEVER attempt to write a 500+ line file in one shot — it WILL be truncated and the tool call will fail.
  PRIORITY: Always write the main file FIRST (even as a skeleton), then add supporting files."""
