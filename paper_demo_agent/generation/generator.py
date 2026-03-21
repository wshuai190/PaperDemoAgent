"""Multi-phase agentic generator loop — produces demo files using tools.

Phase 1 — RESEARCH  (2-3 iterations): web_search for paper-specific info (results, repos, metadata).
Phase 2 — BUILD     (up to max_iter):  write all files, implement logic, add interactivity.
Phase 3 — POLISH    (up to 3 iters):   read-review-fix cycle for quality and correctness.
Post    — VALIDATE  (up to 8 iters):   form-compliance check + auto-correction if needed.
"""
from __future__ import annotations


import base64
import concurrent.futures
import json
import os
import re
import time
from pathlib import Path
from typing import Callable, List, Optional

from paper_demo_agent.paper.models import DemoResult, Paper, PaperAnalysis
from paper_demo_agent.providers.base import BaseLLMProvider, LLMResponse, ToolCall
from paper_demo_agent.skills.base import BaseSkill, FORM_SPECS
from paper_demo_agent.generation.tools import TOOLS, dispatch_tool


def _chat_with_retry(
    provider: BaseLLMProvider,
    messages: list,
    system: str,
    tools: list,
    max_tokens: int,
    on_emit: Callable,
    max_retries: int = 4,
) -> LLMResponse:
    """Call provider.chat() and retry on rate-limit (429) errors with backoff.

    Parses the retry_delay from the error message when available, otherwise
    uses exponential backoff (15s → 30s → 60s → 120s).
    """
    backoff = 15
    for attempt in range(max_retries + 1):
        try:
            return provider.chat(
                messages=messages, system=system, tools=tools, max_tokens=max_tokens
            )
        except Exception as exc:
            msg = str(exc)
            is_rate_limit = (
                "429" in msg
                or "quota" in msg.lower()
                or "rate limit" in msg.lower()
                or "resource_exhausted" in msg.lower()
                or "ResourceExhausted" in type(exc).__name__
            )
            if not is_rate_limit or attempt >= max_retries:
                raise

            # Try to extract suggested retry delay from the error message
            delay_match = re.search(r"retry.*?(\d+(?:\.\d+)?)\s*s", msg, re.IGNORECASE)
            wait = float(delay_match.group(1)) + 2 if delay_match else backoff
            wait = min(wait, 120)
            on_emit(
                f"  ⏳ Rate limit hit — waiting {wait:.0f}s then retrying "
                f"(attempt {attempt + 1}/{max_retries})…\n"
            )
            time.sleep(wait)
            backoff = min(backoff * 2, 120)
    raise RuntimeError("Max retries exceeded")  # unreachable but satisfies type checkers


# ─────────────────────────────────────────────────────────────────────────────
# Provider-specific message builders
# ─────────────────────────────────────────────────────────────────────────────

def _anthropic_assistant_message(response: LLMResponse) -> dict:
    """Build the assistant message for Anthropic's API.
    Content MUST be a list containing both text blocks and tool_use blocks.
    """
    content_blocks = []
    if response.content:
        content_blocks.append({"type": "text", "text": response.content})
    for tc in response.tool_calls:
        block = {
            "type": "tool_use",
            "id": tc.id,
            "name": tc.name,
            "input": tc.arguments,
        }
        if tc.metadata:
            block["metadata"] = tc.metadata
        content_blocks.append(block)
    if not content_blocks:
        return {"role": "assistant", "content": ""}
    return {"role": "assistant", "content": content_blocks}


def _anthropic_tool_result_message(tool_call: ToolCall, result: str) -> dict:
    return {
        "role": "user",
        "content": [{
            "type": "tool_result",
            "tool_use_id": tool_call.id,
            "content": result,
        }],
    }


def _openai_assistant_message(response: LLMResponse) -> dict:
    """Build assistant message with JSON-stringified tool_calls for OpenAI-compatible APIs."""
    msg: dict = {"role": "assistant", "content": response.content or ""}
    if response.tool_calls:
        msg["tool_calls"] = [
            {
                "id": tc.id,
                "type": "function",
                "function": {
                    "name": tc.name,
                    "arguments": json.dumps(tc.arguments),  # must be JSON string, not Python repr
                },
            }
            for tc in response.tool_calls
        ]
    return msg


def _openai_tool_result_message(tool_call: ToolCall, result: str) -> dict:
    return {
        "role": "tool",
        "tool_call_id": tool_call.id,
        "content": result,
    }


def _is_openai_format(provider: BaseLLMProvider) -> bool:
    return provider.__class__.__name__ in (
        "OpenAIProvider", "DeepSeekProvider", "QwenProvider", "MiniMaxProvider"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Output detection helpers
# ─────────────────────────────────────────────────────────────────────────────

def _detect_main_file(output_dir: str, demo_form: str) -> str:
    base = Path(output_dir)
    candidates = {
        "app":              ["app.py", "main.py", "demo.py", "streamlit_app.py"],
        "app_streamlit":    ["app.py", "streamlit_app.py", "main.py"],
        "presentation":     ["demo.html", "slides.html", "index.html"],
        "website":          ["index.html", "demo.html"],
        "flowchart":        ["index.html", "diagram.html", "flowchart.html"],
        "slides":           ["build.py", "generate.py", "presentation.pptx"],
        "latex":            ["presentation.tex", "slides.tex", "talk.tex"],
        "page_readme":      ["README.md", "readme.md"],
        "page_blog":        ["index.html", "article.html"],
        "diagram_graphviz": ["build.py", "generate.py"],
    }
    for name in candidates.get(demo_form, ["app.py", "index.html"]):
        if (base / name).exists():
            return name
    # Fallback by extension
    if demo_form in ("slides", "diagram_graphviz"):
        for ext in ["*.pptx", "*.py"]:
            found = sorted(base.glob(ext))
            if found:
                return found[0].name
    elif demo_form == "latex":
        found = sorted(base.glob("*.tex"))
        if found:
            return found[0].name
    elif demo_form == "page_readme":
        found = sorted(base.glob("*.md"))
        if found:
            return found[0].name
    expected_ext = ".py" if demo_form in ("app", "app_streamlit", "slides", "diagram_graphviz") else ".html"
    if demo_form == "page_readme":
        expected_ext = ".md"
    for ext in [f"*{expected_ext}", "*.py", "*.html", "*.md"]:
        found = sorted(base.glob(ext))
        if found:
            return found[0].name
    return "app.py"


def _detect_dependencies(output_dir: str) -> List[str]:
    req_file = Path(output_dir) / "requirements.txt"
    if req_file.exists():
        return [
            l.strip()
            for l in req_file.read_text().splitlines()
            if l.strip() and not l.startswith("#")
        ]
    return []


def _build_run_command(output_dir: str, main_file: str, demo_form: str) -> str:
    name = main_file.lower()
    if name.endswith(".tex"):
        return f"cd {output_dir} && pdflatex {main_file}  # run twice for refs"
    elif name.endswith(".pptx"):
        return f"open {os.path.join(output_dir, main_file)}  # opens in PowerPoint / LibreOffice"
    elif name.endswith(".md"):
        full = os.path.join(output_dir, main_file)
        return f"open {full}   # or view on GitHub"
    elif name.endswith(".py"):
        try:
            content = (Path(output_dir) / main_file).read_text(errors="ignore")
        except OSError:
            content = ""
        if "streamlit" in content or demo_form == "app_streamlit":
            return f"cd {output_dir} && streamlit run {main_file}"
        if demo_form in ("slides", "diagram_graphviz"):
            return f"cd {output_dir} && pip install -r requirements.txt && python {main_file}"
        return f"cd {output_dir} && python {main_file}"
    elif name.endswith(".html"):
        full = os.path.join(output_dir, main_file)
        return f"open {full}   # or: python -m http.server 8000 (in {output_dir})"
    return f"cd {output_dir} && python {main_file}"


# ─────────────────────────────────────────────────────────────────────────────
# Form validation
# ─────────────────────────────────────────────────────────────────────────────

def _auto_validate_files(output_dir: str, form: str) -> str:
    """Run tool_validate_output on the main generated files and consolidate issues.

    Returns a non-empty string describing all issues found, or empty string if
    everything is clean.  Only checks file types that the validator supports
    (.html, .py, .js).
    """
    from paper_demo_agent.generation.tools import tool_validate_output

    base = Path(output_dir)

    # Collect files to check — prefer main entry points, then all HTML/PY/JS
    spec = FORM_SPECS.get(form, {})
    main_file = spec.get("main_file", "")
    priority: List[str] = [main_file] if main_file else []

    html_files = sorted(str(f.relative_to(base)) for f in base.glob("*.html"))
    py_files   = sorted(str(f.relative_to(base)) for f in base.glob("*.py"))
    js_files   = sorted(str(f.relative_to(base)) for f in base.glob("*.js"))

    # Build deduped list: priority first, then up to 3 of each type
    seen: set = set()
    to_check: List[str] = []
    for p in priority + html_files[:3] + py_files[:2] + js_files[:2]:
        if p and p not in seen:
            seen.add(p)
            to_check.append(p)

    all_issues: List[str] = []
    for rel_path in to_check:
        if not (base / rel_path).exists():
            continue
        result = tool_validate_output(output_dir, rel_path)
        if result and result != "No issues found" and not result.startswith("Validation not supported"):
            all_issues.append(f"[{rel_path}]\n{result}")

    return "\n\n".join(all_issues)


def _validate_form_output(output_dir: str, demo_form: str) -> tuple[bool, str]:
    """Check that the generated files match the expected form."""
    base = Path(output_dir)
    files = [f for f in base.rglob("*") if f.is_file()]

    if demo_form == "app":
        py_files = [f for f in files if f.suffix == ".py"]
        if not py_files:
            return False, (
                "Expected a Gradio app (app.py) but no .py files were generated. "
                "You must create app.py as the main file."
            )
        for f in py_files:
            content = f.read_text(errors="ignore")
            if "gradio" in content or "streamlit" in content:
                return True, ""
        return False, (
            f"Generated {[f.name for f in py_files]} but none import gradio or streamlit. "
            "app.py must be a Gradio application (import gradio as gr)."
        )

    elif demo_form == "presentation":
        html_files = [f for f in files if f.suffix == ".html"]
        if not html_files:
            return False, (
                "Expected a reveal.js HTML presentation (demo.html) but no .html files found. "
                "You must create demo.html using reveal.js from CDN."
            )
        for f in html_files:
            content = f.read_text(errors="ignore")
            if "reveal.js" in content or "Reveal.initialize" in content or "reveal.min.js" in content:
                return True, ""
        return False, (
            f"Generated {[f.name for f in html_files]} but none use reveal.js. "
            "demo.html must load reveal.js from CDN and call Reveal.initialize()."
        )

    elif demo_form in ("website", "flowchart"):
        html_files = [f for f in files if f.suffix == ".html"]
        if not html_files:
            return False, (
                f"Expected an HTML file (index.html) for {demo_form} but none found. "
                "You must create index.html."
            )
        if demo_form == "flowchart":
            for f in html_files:
                content = f.read_text(errors="ignore")
                if "mermaid" in content.lower():
                    return True, ""
            return False, (
                f"Generated {[f.name for f in html_files]} but none use Mermaid.js. "
                "index.html must import Mermaid.js v11 and define at least one diagram."
            )
        return True, ""

    elif demo_form == "slides":
        # Accept .pptx output OR build.py that generates it
        pptx_files = [f for f in files if f.suffix == ".pptx"]
        if pptx_files:
            return True, ""
        py_files = [f for f in files if f.suffix == ".py"]
        if not py_files:
            return False, (
                "Expected build.py (python-pptx script) or presentation.pptx but neither found. "
                "Create build.py that imports python-pptx and saves presentation.pptx."
            )
        for f in py_files:
            content = f.read_text(errors="ignore")
            if "pptx" in content or "Presentation" in content:
                return True, ""
        return False, (
            f"Generated {[f.name for f in py_files]} but none import python-pptx. "
            "build.py must use python-pptx to create presentation.pptx."
        )

    elif demo_form == "latex":
        tex_files = [f for f in files if f.suffix == ".tex"]
        if not tex_files:
            return False, (
                "Expected presentation.tex (LaTeX Beamer) but no .tex files found. "
                "Create presentation.tex using \\documentclass[aspectratio=169]{beamer}."
            )
        for f in tex_files:
            content = f.read_text(errors="ignore")
            if "beamer" in content.lower() or "\\documentclass" in content:
                return True, ""
        return False, (
            f"Generated {[f.name for f in tex_files]} but none use Beamer. "
            "presentation.tex must use \\documentclass[aspectratio=169,11pt]{beamer}."
        )

    elif demo_form == "app_streamlit":
        py_files = [f for f in files if f.suffix == ".py"]
        if not py_files:
            return False, (
                "Expected a Streamlit app (app.py) but no .py files were generated. "
                "You must create app.py with `import streamlit as st`."
            )
        for f in py_files:
            content = f.read_text(errors="ignore")
            if "streamlit" in content:
                return True, ""
        return False, (
            f"Generated {[f.name for f in py_files]} but none import streamlit. "
            "app.py must be a Streamlit application (import streamlit as st)."
        )

    elif demo_form == "page_readme":
        md_files = [f for f in files if f.suffix == ".md"]
        if not md_files:
            return False, (
                "Expected README.md but no .md files found. "
                "You must create README.md as the main output."
            )
        return True, ""

    elif demo_form == "page_blog":
        html_files = [f for f in files if f.suffix == ".html"]
        if not html_files:
            return False, (
                "Expected index.html (Distill blog article) but no .html files found. "
                "You must create index.html using the Distill.pub template."
            )
        for f in html_files:
            content = f.read_text(errors="ignore")
            if "distill" in content.lower() or "d-article" in content:
                return True, ""
        return False, (
            f"Generated {[f.name for f in html_files]} but none use Distill template. "
            "index.html must include distill.pub template.v2.js and use <d-article>."
        )

    elif demo_form == "diagram_graphviz":
        # Accept SVG/PNG output OR build.py that generates them
        svg_files = [f for f in files if f.suffix in (".svg", ".png")]
        if svg_files:
            return True, ""
        py_files = [f for f in files if f.suffix == ".py"]
        if not py_files:
            return False, (
                "Expected build.py (graphviz script) or SVG/PNG output but neither found. "
                "Create build.py that imports graphviz and renders diagrams."
            )
        for f in py_files:
            content = f.read_text(errors="ignore")
            if "graphviz" in content or "Digraph" in content or "Graph(" in content:
                return True, ""
        return False, (
            f"Generated {[f.name for f in py_files]} but none import graphviz. "
            "build.py must use the graphviz library to generate SVG/PNG diagrams."
        )

    return True, ""  # Unknown form: skip validation


def _correction_message(form: str, error: str) -> str:
    spec = FORM_SPECS.get(form, {})
    main_file = spec.get("main_file", "app.py")
    technology = spec.get("technology", "")
    must_text = "\n".join(f"  • {m}" for m in spec.get("must", [])[:6])
    cdns = spec.get("cdns", [])
    cdn_text = "\n".join(f"  {c}" for c in cdns[:4]) if cdns else ""

    msg = (
        f"FORM VALIDATION FAILED: {error}\n\n"
        f"You generated the wrong output format. Fix this NOW:\n\n"
        f"Required form      : {form}\n"
        f"Required technology: {technology}\n"
        f"Required main file : {main_file}\n\n"
        f"WHAT YOU MUST DO (top requirements):\n{must_text}\n"
    )
    if cdn_text:
        msg += f"\nCDN LINKS TO USE:\n{cdn_text}\n"
    msg += f"\nDelete incorrect files and create {main_file} using {technology}. Do it now."
    return msg


# ─────────────────────────────────────────────────────────────────────────────
# Phase helpers
# ─────────────────────────────────────────────────────────────────────────────


_PDF_SURVEY_SCRIPT = """
import re, sys, json
try:
    import fitz
except ImportError:
    print("PyMuPDF not available -- skipping survey")
    sys.exit(0)

import os
pdf_path = os.path.join("{output_dir}", "paper.pdf")
if not os.path.exists(pdf_path):
    print("paper.pdf not found -- skipping survey")
    sys.exit(0)

doc = fitz.open(pdf_path)
print(f"Total pages: {len(doc)}")
print()

for i, page in enumerate(doc):
    pw = page.rect.width
    ph = page.rect.height
    blocks = sorted(page.get_text("blocks"), key=lambda b: b[1])

    # Find figure/table captions with y positions
    captions = []
    for blk in blocks:
        text = blk[4].strip().replace("\\n", " ")
        m = re.match(r'^(Fig(?:ure)?[.\\s]+\\d+|Table[\\s]+\\d+)[:\\.]?\\s*(.{0,60})', text, re.IGNORECASE)
        if m:
            captions.append({'label': m.group(1).strip(), 'desc': m.group(2)[:50],
                             'y0': blk[1], 'y1': blk[3]})

    if not captions:
        continue

    print(f"Page {i+1}:")

    # Sort captions by position; deduplicate by label (keep first occurrence)
    seen_labels = set()
    unique_captions = []
    for cap in sorted(captions, key=lambda c: c['y0']):
        if cap['label'] not in seen_labels:
            seen_labels.add(cap['label'])
            unique_captions.append(cap)
    captions = unique_captions

    # Build list of non-caption text blocks for finding figure boundaries
    caption_y0s = {c['y0'] for c in captions}
    body_blocks = [
        b for b in blocks
        if b[1] not in caption_y0s
        and not re.match(r'^(Fig(?:ure)?[.\\s]+\\d+|Table[\\s]+\\d+)', b[4].strip(), re.IGNORECASE)
    ]

    page_top = ph * 0.04
    prev_end = page_top
    for cap in captions:
        label, desc = cap['label'], cap['desc'][:50]
        is_table = label.lower().startswith('table')

        if is_table:
            print(f"  {label}: {desc}")
            print(f"  → [TABLE] Reproduce as LaTeX tabular / pptx add_table() — do NOT embed as image")
        else:
            # Find crop top: last body-text block ending above this caption
            fig_top = prev_end
            for bb in body_blocks:
                if bb[3] < cap['y0'] - 5:
                    fig_top = bb[3]
                elif bb[1] >= cap['y0']:
                    break
            # Ensure minimum crop height (12% of page)
            min_crop = ph * 0.12
            if (cap['y1'] - fig_top) < min_crop:
                fig_top = max(page_top, cap['y0'] - min_crop)
            fig_y0 = max(0.0, round((fig_top - 3) / ph, 3))
            fig_y1 = min(1.0, round((cap['y1'] + 5) / ph, 3))
            crop_str = json.dumps({'x0': 0.0, 'y0': fig_y0, 'x1': 1.0, 'y1': fig_y1})
            print(f"  {label}: {desc}")
            print(f"  → extract_pdf_page(page={i+1}, crop={crop_str})")
        prev_end = cap['y1']
    print()

print("CRITICAL RULES FOR FIGURE EXTRACTION:")
print("1. Use the exact extract_pdf_page(page=N, crop=...) call shown — NEVER omit the crop arg")
print("2. TABLE lines: reproduce in code (LaTeX tabular or pptx add_table()) — NEVER embed as image")
print("3. Only extract pages listed above — skip all other pages")
"""


def _run_pdf_survey(output_dir: str, on_emit: Callable) -> str:
    """Scan paper.pdf to find which pages contain figures and tables.

    Returns a structured summary string to inject into the Build initial message.
    Used by latex and slides forms so the agent has a precise paper map before writing code.
    """
    from paper_demo_agent.generation.tools import tool_execute_python

    pdf_path = Path(output_dir) / "paper.pdf"
    if not pdf_path.exists():
        return ""

    script = _PDF_SURVEY_SCRIPT.replace('"{output_dir}"', repr(output_dir))
    on_emit("  ↳ Scanning paper.pdf for figure/table locations…\n")
    result = tool_execute_python(script, output_dir=output_dir)
    on_emit(f"    → {result[:300]}\n")

    if "not available" in result or "not found" in result:
        return ""

    return (
        "\n\n─── PDF FIGURE/TABLE MAP (from paper.pdf scan) ───\n"
        + result.strip()
        + "\n─── END PDF MAP ───\n"
        "USE THE EXACT extract_pdf_page() CALLS SHOWN ABOVE — copy them verbatim.\n"
        "DO NOT call extract_pdf_page() without a crop arg. DO NOT embed tables as images.\n"
    )


# ---------------------------------------------------------------------------
# Figure extraction helpers — Docling (primary) + heuristic fallback
# ---------------------------------------------------------------------------

import threading

# Module-level Docling preloader — starts loading the heavy model in the
# background so it's warm by the time we need it for figure extraction.
_docling_converter = None      # will hold the DocumentConverter once ready
_docling_lock = threading.Lock()
_docling_preload_done = threading.Event()


def _preload_docling() -> None:
    """Load the Docling converter in a background thread (call once)."""
    global _docling_converter
    try:
        from docling.datamodel.base_models import InputFormat
        from docling.datamodel.pipeline_options import PdfPipelineOptions
        from docling.document_converter import DocumentConverter, PdfFormatOption

        pipeline_options = PdfPipelineOptions()
        pipeline_options.images_scale = 2.0
        pipeline_options.generate_picture_images = True

        with _docling_lock:
            _docling_converter = DocumentConverter(
                format_options={
                    InputFormat.PDF: PdfFormatOption(
                        pipeline_options=pipeline_options,
                    ),
                }
            )
    except Exception:
        pass  # docling not installed — _docling_converter stays None
    finally:
        _docling_preload_done.set()


def start_docling_preload() -> None:
    """Kick off background preload (idempotent — safe to call multiple times)."""
    if _docling_preload_done.is_set():
        return  # already loaded or failed
    t = threading.Thread(target=_preload_docling, daemon=True)
    t.start()


def _get_docling_converter(timeout: float = 120):
    """Wait for the preloaded converter, or load inline if preload wasn't started."""
    if not _docling_preload_done.is_set():
        # Preload wasn't kicked off — load synchronously
        _preload_docling()
    else:
        _docling_preload_done.wait(timeout=timeout)
    return _docling_converter


def _docling_extract(
    pdf_path: str,
    all_captions: dict,
    figures_dir: "Path",
    on_emit: Callable,
) -> tuple:
    """Use Docling's deep-learning layout model to extract figures and tables.

    Returns (figures_list, tables_markdown_str).
    """
    from docling_core.types.doc import PictureItem, TableItem

    converter = _get_docling_converter()
    if converter is None:
        raise RuntimeError("Docling converter not available")

    conv_res = converter.convert(pdf_path)

    # Build ordered list of figure captions for sequential matching
    fig_cap_list: list[dict] = []
    for _page_idx, caps in sorted(all_captions.items()):
        fig_cap_list.extend(caps)

    # ── Extract figures ───────────────────────────────────────────────
    extracted: list[tuple] = []
    pic_idx = 0
    for element, _level in conv_res.document.iterate_items():
        if not isinstance(element, PictureItem):
            continue
        pic_idx += 1
        img = element.get_image(conv_res.document)
        if img is None:
            continue

        fig_num = len(extracted) + 1
        fname = f"fig{fig_num}.png"
        img.save(str(figures_dir / fname), "PNG")

        # Match with known caption (sequential — Docling order matches PDF order)
        label = f"Figure {pic_idx}"
        desc, page_num = "", 0
        if pic_idx <= len(fig_cap_list):
            c = fig_cap_list[pic_idx - 1]
            label, desc = c["label"], c["desc"]

        on_emit(f"  ↳ Extracted {fname}: {label} — {desc[:40]}\n")
        extracted.append((fname, label, desc, page_num))

    # ── Extract tables as structured markdown ─────────────────────────
    table_lines: list[str] = []
    tbl_idx = 0
    for element, _level in conv_res.document.iterate_items():
        if not isinstance(element, TableItem):
            continue
        tbl_idx += 1
        try:
            md = element.export_to_markdown()
        except Exception:
            continue
        rows = md.strip().split("\n")
        n_rows = len([r for r in rows if r.startswith("|")]) - 1  # minus separator
        table_lines.append(f"\n### Table {tbl_idx} ({n_rows} data rows)")
        table_lines.append(md.strip())

    tables_md = "\n".join(table_lines) if table_lines else ""
    if tables_md:
        on_emit(f"  ↳ Extracted {tbl_idx} structured tables\n")

    return extracted, tables_md


def _heuristic_extract(
    doc,
    all_captions: dict,
    figures_dir: "Path",
    on_emit: Callable,
) -> list:
    """Fallback: extract figures using text-block and drawing heuristics."""
    import fitz

    extracted: list[tuple] = []

    for page_idx, caps in sorted(all_captions.items()):
        page = doc[page_idx]
        ph, pw = page.rect.height, page.rect.width
        page_top = ph * 0.04

        for cap in sorted(caps, key=lambda c: c["y0"]):
            label, desc = cap["label"], cap["desc"]

            # Default: crop 25% of page height above caption, full width
            min_crop = ph * 0.25
            fig_top = max(page_top, cap["y0"] - min_crop)
            y0 = max(0.0, (fig_top - 5) / ph)
            y1 = min(1.0, (cap["y1"] + 8) / ph)

            clip = fitz.Rect(0, y0 * ph, pw, y1 * ph)
            mat = fitz.Matrix(200 / 72, 200 / 72)
            pix = page.get_pixmap(matrix=mat, clip=clip)

            img_bytes = pix.tobytes("png")
            if len(img_bytes) < 5000:
                pix = page.get_pixmap(matrix=mat)

            fig_idx = len(extracted) + 1
            fname = f"fig{fig_idx}.png"
            pix.save(str(figures_dir / fname))

            on_emit(f"  ↳ Extracted {fname}: {label} — {desc[:40]}\n")
            extracted.append((fname, label, desc, page_idx + 1))

    return extracted


def _pre_extract_figures(
    output_dir: str,
    on_emit: Callable,
    provider: Optional["BaseLLMProvider"] = None,
) -> str:
    """Pre-extract all figures from paper.pdf before the Build phase.

    Primary strategy: Docling deep-learning layout model (precise figure crops).
    Fallback: heuristic text/drawing analysis (no extra dependencies).

    Returns a summary string listing all pre-extracted files.
    """
    pdf_path = Path(output_dir) / "paper.pdf"
    if not pdf_path.exists():
        return ""

    try:
        import fitz  # PyMuPDF
    except ImportError:
        on_emit("  ↳ PyMuPDF not available — skipping figure pre-extraction\n")
        return ""

    figures_dir = Path(output_dir) / "figures"
    figures_dir.mkdir(exist_ok=True)

    doc = fitz.open(str(pdf_path))

    # ── Step 1: Scan all pages for figure/table captions ──────────────
    all_captions: dict[int, list[dict]] = {}  # page_idx → caption list
    tables: list[tuple] = []  # (label, desc, page_num)

    for i, page in enumerate(doc):
        blocks = sorted(page.get_text("blocks"), key=lambda b: b[1])
        captions = []
        seen: set[str] = set()
        for blk in blocks:
            text = blk[4].strip().replace("\n", " ")
            m = re.match(
                r'^(Fig(?:ure)?[\.\s]+\d+|Table[\s]+\d+)[:\.]?\s*(.{0,60})',
                text, re.IGNORECASE,
            )
            if m:
                lbl = m.group(1).strip()
                if lbl not in seen:
                    seen.add(lbl)
                    captions.append({"label": lbl, "desc": m.group(2)[:60],
                                     "y0": blk[1], "y1": blk[3]})
        if captions:
            fig_caps = [c for c in captions if not c["label"].lower().startswith("table")]
            tbl_caps = [c for c in captions if c["label"].lower().startswith("table")]
            for tc in tbl_caps:
                tables.append((tc["label"], tc["desc"], i + 1))
            if fig_caps:
                all_captions[i] = fig_caps

    if not all_captions and not tables:
        doc.close()
        return ""

    # ── Step 2: Try Docling deep-learning extraction ─────────────────
    extracted: list[tuple] = []  # (filename, label, desc, page_num)
    tables_md = ""  # structured table markdown from Docling

    if all_captions:
        try:
            on_emit("  ↳ Using Docling layout model for precise figure extraction\n")
            extracted, tables_md = _docling_extract(
                str(pdf_path), all_captions, figures_dir, on_emit,
            )
        except Exception as exc:
            on_emit(f"  ↳ Docling unavailable ({exc}), using heuristic fallback\n")
            extracted = _heuristic_extract(doc, all_captions, figures_dir, on_emit)

    doc.close()

    if not extracted and not tables and not tables_md:
        return ""

    lines = ["\n\n─── PRE-EXTRACTED FIGURES (ready to use — do NOT call extract_pdf_page) ───"]
    lines.append("All figures already saved to the figures/ directory:\n")

    for fname, label, desc, pgnum in extracted:
        lines.append(f"  figures/{fname}  ←  {label}: {desc[:50]}")

    lines.append("\nUSAGE:")
    lines.append("  LaTeX:   \\includegraphics[width=\\textwidth]{figures/fig1.png}")
    lines.append("  pptx:    slide.shapes.add_picture('figures/fig1.png', left, top, width, height)")
    lines.append("  HTML:    <img src=\"figures/fig1.png\" ...>")
    lines.append("\nMANDATORY: Include ALL figures listed above in appropriate slides.")
    lines.append("  Every figN.png must appear somewhere — do not skip any figure without reason.")
    lines.append("  Assign each figure to the most relevant slide (results, method, architecture, etc.)")
    lines.append("\nDO NOT call extract_pdf_page() — figures are already extracted.")

    # ── Tables: inject structured data so the agent can hard-code values ──
    if tables_md:
        lines.append("\n─── STRUCTURED TABLE DATA (from paper — use these exact values) ───")
        lines.append("Hard-code these numbers directly in your code. Do NOT parse the PDF at runtime.")
        lines.append("Include only the 2-3 most important results tables in the presentation.")
        lines.append(tables_md)
        lines.append("─── END TABLE DATA ───")
    elif tables:
        lines.append("\nTABLES — reproduce these as code (do NOT embed as images):")
        for label, desc, pgnum in tables:
            lines.append(f"  Page {pgnum}: {label}: {desc[:60]}")

    lines.append("\n─── END PRE-EXTRACTED CONTENT ───")

    return "\n".join(lines)


def _extract_prior_work(paper) -> str:
    """Extract references to foundational prior work from the paper text."""
    # Look for related work / background sections
    related_sections = []
    for name, content in (paper.sections or {}).items():
        lower = name.lower()
        if any(kw in lower for kw in ("related", "background", "prior", "previous", "foundation")):
            related_sections.append(content[:2000])
    # Fallback: check abstract for "builds on", "extends", "based on" patterns
    if not related_sections and paper.abstract:
        related_sections.append(paper.abstract)
    return "\n".join(related_sections)[:3000]


def _run_research_phase(
    provider: BaseLLMProvider,
    paper,
    output_dir: str,
    use_openai_fmt: bool,
    on_emit: Callable,
    max_iter: int = 3,
) -> str:
    """Phase 1: find official resources + foundational prior work context."""
    prior_work_text = _extract_prior_work(paper)
    arxiv_hint = f" (arXiv: {paper.arxiv_id})" if paper.arxiv_id else ""

    system = (
        f"You are a research assistant. Your job is to gather context about the paper "
        f"\"{paper.title}\"{arxiv_hint} by searching the web. You have TWO tasks:\n\n"
        f"TASK 1 — OFFICIAL RESOURCES: Find the paper's GitHub repository, project page, "
        f"HuggingFace model/dataset, and arXiv page. One or two web_search calls should suffice.\n\n"
        f"TASK 2 — FOUNDATIONAL PRIOR WORK: Based on the paper's related work (provided below), "
        f"identify the 1-3 most important predecessor papers that this work builds on. "
        f"Search for those papers to get a brief summary of what they do — this helps the demo "
        f"builder understand the bigger picture.\n\n"
        f"DO NOT search for library docs, CDN URLs, or code examples — those are pre-baked.\n"
        f"DO NOT write any files."
    )

    initial_parts = [
        f"Research the paper: \"{paper.title}\"{arxiv_hint}\n",
        "STEP 1: Search for the paper's official resources (GitHub, project page, HuggingFace, arXiv).",
        "STEP 2: Read the prior work excerpt below and identify 1-3 key foundational papers. "
        "Search for those to summarize what they contribute and how this paper builds on them.\n",
    ]
    if prior_work_text:
        initial_parts.append(f"─── PRIOR WORK EXCERPT ───\n{prior_work_text}\n─── END EXCERPT ───\n")
    else:
        initial_parts.append(
            f"No related-work section was extracted. Use the abstract to infer key prior work:\n"
            f"{paper.abstract[:1500]}\n"
        )
    initial_parts.append(
        "Report your findings as:\n"
        "  - OFFICIAL LINKS: arXiv, GitHub, project page, HuggingFace (if any)\n"
        "  - FOUNDATIONAL PAPERS: for each, one sentence on what it does and how this paper extends it"
    )
    initial = "\n".join(initial_parts)

    messages: list[dict] = [{"role": "user", "content": initial}]
    findings: list[str] = []

    for _ in range(max_iter):
        response = _chat_with_retry(
            provider, messages, system, TOOLS, 2048, on_emit
        )
        if response.content:
            preview = response.content[:400].replace("\n", " ")
            on_emit(f"  ↳ {preview}…\n" if len(response.content) > 400 else f"  ↳ {response.content}\n")
            findings.append(response.content)

        if not response.tool_calls or response.stop_reason == "end_turn":
            break

        if use_openai_fmt:
            messages.append(_openai_assistant_message(response))
        else:
            messages.append(_anthropic_assistant_message(response))

        for tc in response.tool_calls:
            arg_preview = str(list(tc.arguments.values())[:1])[:60]
            on_emit(f"  ◆ {tc.name}({arg_preview})\n")
            result = dispatch_tool(tc.name, tc.arguments, output_dir)

            # Fallback: if search_huggingface returns empty results, try web_search
            if tc.name == "search_huggingface" and (
                not result.strip()
                or "no results" in result.lower()
                or "0 results" in result.lower()
                or result.strip() in ("{}", "[]", "No results found", "")
            ):
                query_val = tc.arguments.get("query", paper.title)
                fallback_query = f"site:huggingface.co {query_val}"
                on_emit(f"    ↳ search_huggingface returned empty — trying web_search fallback\n")
                fallback_result = dispatch_tool(
                    "web_search", {"query": fallback_query}, output_dir
                )
                result = f"[HuggingFace web fallback for '{query_val}']\n{fallback_result}"

            on_emit(f"    → {result[:150]}\n")
            if use_openai_fmt:
                messages.append(_openai_tool_result_message(tc, result))
            else:
                messages.append(_anthropic_tool_result_message(tc, result))

    return "\n\n".join(findings)


# ─────────────────────────────────────────────────────────────────────────────
# Form-specific iteration budgets (optimization #5)
# ─────────────────────────────────────────────────────────────────────────────

FORM_BUDGETS = {
    "page_readme":      {"build": 6,  "polish": 2},
    "diagram_graphviz":  {"build": 6,  "polish": 2},
    "flowchart":        {"build": 8,  "polish": 2},
    "presentation":     {"build": 15, "polish": 3},
    "website":          {"build": 12, "polish": 3},
    "page_blog":        {"build": 14, "polish": 3},
    "slides":           {"build": 14, "polish": 3},
    "latex":            {"build": 14, "polish": 3},
    "app":              {"build": 12, "polish": 3},
    "app_streamlit":    {"build": 12, "polish": 3},
}

# Forms that typically produce large files and benefit from skeleton-first writing
_LARGE_FILE_FORMS = frozenset([
    "presentation", "website", "page_blog", "latex", "slides",
])

_SKELETON_FIRST_MESSAGE_SPLIT = (
    "For this output, organize your files cleanly:\n"
    "  1. styles.css  — all CSS\n"
    "  2. script.js   — all JavaScript\n"
    "  3. index.html  — references styles.css + script.js via <link> and <script> tags\n"
    "Write the MAIN file (index.html) FIRST, even as a skeleton, then add supporting files.\n"
    "This ensures the demo is always in a working state."
)

_SKELETON_FIRST_MESSAGE_SINGLE = (
    "For this presentation, write demo.html as a SINGLE self-contained file.\n"
    "Do NOT create separate styles.css or script.js — reveal.js requires inline <style> and <script>.\n"
    "Do NOT create slides_part2.html or slide_parts/ — ALL slides go in ONE demo.html file.\n\n"
    "If the file is very large, use write_file for the first chunk (head + first slides),\n"
    "then append_file to add more slides. The last append MUST close all tags.\n"
    "START WRITING demo.html NOW."
)

# Single-file forms where CSS/JS must be inline (no external files)
_SINGLE_FILE_FORMS = frozenset(["presentation", "latex"])

# Tools that are safe to run in parallel (no side effects on shared state)
_PARALLEL_SAFE_TOOLS = frozenset([
    "web_search", "search_huggingface", "read_file", "list_files",
    "write_file", "append_file", "download_file", "validate_output",
])
# Tools with side effects that must run sequentially
_SEQUENTIAL_TOOLS = frozenset(["execute_python", "install_package"])


def _can_parallelize(tool_calls: list) -> bool:
    """Check if a set of tool calls can safely be executed in parallel."""
    names = {tc.name for tc in tool_calls}
    # Any sequential tool in the batch → run all sequentially
    if names & _SEQUENTIAL_TOOLS:
        return False
    # All tools must be parallel-safe
    if not names.issubset(_PARALLEL_SAFE_TOOLS):
        return False
    # write_file calls must target different files
    write_paths = [tc.arguments.get("path") for tc in tool_calls if tc.name == "write_file"]
    if len(write_paths) != len(set(write_paths)):
        return False
    return True


# ─────────────────────────────────────────────────────────────────────────────
# Context compaction (optimization #2)
# ─────────────────────────────────────────────────────────────────────────────

def _compact_messages(messages: list, keep_first: int = 1, keep_last: int = 6) -> list:
    """Compact old messages to reduce context size while preserving working memory.

    - Keeps messages[0:keep_first] unchanged (initial prompt)
    - Keeps messages[-keep_last:] unchanged (recent context)
    - For middle messages: truncates tool results to first 100 chars,
      and strips tool_use input details from assistant messages.
    """
    if len(messages) <= keep_first + keep_last:
        return messages

    head = messages[:keep_first]
    tail = messages[-keep_last:]
    middle = messages[keep_first:-keep_last]

    compacted = []
    for msg in middle:
        role = msg.get("role", "")
        content = msg.get("content")

        if role == "tool":
            # OpenAI format tool result — truncate content
            truncated = dict(msg)
            if isinstance(content, str) and len(content) > 100:
                truncated["content"] = content[:100] + "...[truncated]"
            compacted.append(truncated)

        elif role == "user" and isinstance(content, list):
            # Anthropic format tool_result blocks — truncate content
            new_blocks = []
            for block in content:
                if isinstance(block, dict) and block.get("type") == "tool_result":
                    block = dict(block)
                    c = block.get("content", "")
                    if isinstance(c, str) and len(c) > 100:
                        block["content"] = c[:100] + "...[truncated]"
                new_blocks.append(block)
            compacted.append({**msg, "content": new_blocks})

        elif role == "assistant" and isinstance(content, list):
            # Anthropic format — keep text blocks, strip tool_use input details
            new_blocks = []
            for block in content:
                if isinstance(block, dict) and block.get("type") == "tool_use":
                    # Keep id/name for message continuity, but clear bulky input
                    new_blocks.append({
                        "type": "tool_use",
                        "id": block.get("id", ""),
                        "name": block.get("name", ""),
                        "input": {},
                    })
                else:
                    new_blocks.append(block)
            compacted.append({**msg, "content": new_blocks})

        elif role == "assistant" and "tool_calls" in msg:
            # OpenAI format — strip function arguments from tool_calls
            stripped = dict(msg)
            stripped["tool_calls"] = [
                {**tc, "function": {**tc["function"], "arguments": "{}"}}
                for tc in msg["tool_calls"]
            ]
            compacted.append(stripped)

        else:
            compacted.append(msg)

    return head + compacted + tail


_SEARCH_TOOL_NAMES = {"web_search", "search_huggingface"}
_MAX_SEARCH_ONLY_ITERS = 2  # after this many consecutive search-only iters, force writing


def _run_loop(
    provider: BaseLLMProvider,
    messages: list,
    system: str,
    output_dir: str,
    use_openai_fmt: bool,
    on_emit: Callable,
    max_iter: int,
    phase_label: str = "",
) -> list:
    """Run a generic agentic loop; returns the updated messages list."""
    is_build = phase_label.startswith("build")
    search_only_iters = 0  # consecutive iters with only search calls, no write_file
    consecutive_write_failures = 0  # consecutive iters where write_file failed
    skeleton_injected = False  # track whether skeleton-first hint was injected

    # Determine the demo form from the phase label for skeleton-first logic
    build_form = phase_label.replace("build-", "").replace("build", "").strip().rstrip("-") or ""

    for iteration in range(max_iter):
        # Context compaction: after every 4 iterations, compact old messages (optimization #2)
        if len(messages) > 20 and iteration > 0 and iteration % 4 == 0:
            before_len = len(messages)
            messages = _compact_messages(messages, keep_first=1, keep_last=6)
            if len(messages) < before_len:
                on_emit(f"  ↳ Compacted context: {before_len} → {len(messages)} messages\n")

        on_emit(f"  [{phase_label}iter {iteration + 1}] calling model...\n")
        # Adaptive token budget: early build iterations are planning/searching
        # (8 192 is plenty); later iterations write large files (need 16 384).
        if is_build and iteration < 2:
            _max_tokens = 8192
        else:
            _max_tokens = 16384
        response = _chat_with_retry(
            provider, messages, system, TOOLS, _max_tokens, on_emit
        )

        if response.content:
            on_emit(response.content)

        if response.stop_reason == "end_turn" or not response.tool_calls:
            if response.content:
                messages.append({"role": "assistant", "content": response.content})

            # If no files have been written yet, the model stalled — nudge it once
            has_files = any(True for _ in Path(output_dir).rglob("*") if Path(_).is_file())
            if not has_files and iteration < max_iter - 1:
                spec = FORM_SPECS.get(phase_label.strip("- ").lower().split()[0] if phase_label else "", {})
                main = spec.get("main_file", "index.html")
                tech = spec.get("technology", "")
                extra = ""
                if main == "build.py":
                    extra = " Write the full python-pptx script; it must save presentation.pptx."
                elif main == "presentation.tex":
                    extra = " Write the full LaTeX Beamer document starting with \\documentclass[aspectratio=169,11pt]{beamer}."
                nudge = (
                    f"You haven't written any files yet. "
                    f"Stop planning and start immediately: use write_file to create {main!r} right now. "
                    f"Write the complete file content in one shot.{extra}"
                )
                on_emit(f"  ↻ Nudging: no files yet — prompting to write {main}\n")
                messages.append({"role": "user", "content": nudge})
                continue

            break

        if use_openai_fmt:
            messages.append(_openai_assistant_message(response))
        else:
            messages.append(_anthropic_assistant_message(response))

        # NOTE: nudge messages are injected AFTER tool results below,
        # because Anthropic API requires tool_results immediately after tool_use.
        _pending_nudge: Optional[str] = None

        # Check if main file exists — nudge model EVERY iteration until it writes the main file
        if is_build and iteration >= 1:
            from paper_demo_agent.skills.base import FORM_SPECS as _FS
            _spec = _FS.get(build_form, {})
            _main_file = _spec.get("main_file", "index.html")
            _main_path = Path(output_dir) / _main_file
            _all_files = [f.name for f in Path(output_dir).rglob("*") if f.is_file() and f.name != "paper.pdf"]
            _non_main = [f for f in _all_files if f != _main_file]
            _has_support = len(_non_main) > 0  # any file besides the main file
            _has_main = _main_path.exists()

            if _has_support and not _has_main:
                urgency = "CRITICAL" if iteration >= 3 else "URGENT"
                iters_left = max_iter - iteration - 1
                _pending_nudge = (
                    f"{urgency}: You have written supporting files ({', '.join(f for f in _all_files if f != 'paper.pdf')}) "
                    f"but NOT the main file '{_main_file}'. You have {iters_left} iterations left. "
                    f"Write '{_main_file}' NOW using write_file — this is your TOP PRIORITY. "
                    f"Reference your existing CSS/JS files with <link> and <script> tags. "
                    f"Without '{_main_file}', the demo is COMPLETELY BROKEN and all your work is wasted."
                )
                on_emit(f"  ↳ {urgency}: supporting files exist but no {_main_file} ({iters_left} iters left)\n")

        # Track whether this iteration is search-only (build phase only)
        tool_names = {tc.name for tc in response.tool_calls}
        has_write = "write_file" in tool_names
        all_search = tool_names.issubset(_SEARCH_TOOL_NAMES)

        if is_build and all_search and not has_write:
            search_only_iters += 1
        else:
            search_only_iters = 0

        # Parallel tool execution (optimization #4): run parallelizable tools concurrently
        write_failed_this_iter = False
        if len(response.tool_calls) > 1 and _can_parallelize(response.tool_calls):
            on_emit(f"  ↳ Executing {len(response.tool_calls)} tools in parallel\n")
            results = {}
            with concurrent.futures.ThreadPoolExecutor(max_workers=len(response.tool_calls)) as executor:
                future_to_tc = {
                    executor.submit(dispatch_tool, tc.name, tc.arguments, output_dir): tc
                    for tc in response.tool_calls
                }
                for future in concurrent.futures.as_completed(future_to_tc):
                    tc = future_to_tc[future]
                    try:
                        results[tc.id] = future.result()
                    except Exception as e:
                        results[tc.id] = f"Tool error ({tc.name}): {e}"
            # Append results in original order to preserve message sequence
            for tc in response.tool_calls:
                result = results[tc.id]
                on_emit(f"\n  ◆ {tc.name}({', '.join(list(tc.arguments.keys())[:3])})\n")
                on_emit(f"    → {result[:200]}\n")
                if use_openai_fmt:
                    messages.append(_openai_tool_result_message(tc, result))
                else:
                    messages.append(_anthropic_tool_result_message(tc, result))
                if tc.name == "write_file" and "Missing required argument" in result:
                    write_failed_this_iter = True
        else:
            for tc in response.tool_calls:
                on_emit(f"\n  ◆ {tc.name}({', '.join(list(tc.arguments.keys())[:3])})\n")
                result = dispatch_tool(tc.name, tc.arguments, output_dir)
                on_emit(f"    → {result[:200]}\n")
                if use_openai_fmt:
                    messages.append(_openai_tool_result_message(tc, result))
                else:
                    messages.append(_anthropic_tool_result_message(tc, result))
                if tc.name == "write_file" and "Missing required argument" in result:
                    write_failed_this_iter = True

        # Inject the pending main-file nudge AFTER all tool results
        # (must come after tool_results to satisfy Anthropic API ordering)
        if _pending_nudge is not None:
            messages.append({"role": "user", "content": _pending_nudge})
            _pending_nudge = None

        # Track consecutive write_file failures (typically from max_tokens truncation)
        if write_failed_this_iter:
            consecutive_write_failures += 1
        else:
            consecutive_write_failures = 0

        # After repeated write_file failures, tell the model to split the file
        if consecutive_write_failures >= 2:
            nudge = (
                "Your write_file calls are failing because the content is too large and gets truncated. "
                "SPLIT your approach: first write a skeleton version of the file with placeholder sections, "
                "then use additional write_file calls to overwrite with the complete content. "
                "Alternatively, break the content into a main file and separate helper files (e.g. styles.css, script.js). "
                "Do NOT attempt to write the entire file in one massive call again."
            )
            on_emit(f"  ↻ write_file failed {consecutive_write_failures}x — advising split strategy\n")
            messages.append({"role": "user", "content": nudge})
            consecutive_write_failures = 0

        # After too many consecutive search-only iters, force the model to write
        if is_build and search_only_iters >= _MAX_SEARCH_ONLY_ITERS:
            spec = FORM_SPECS.get(build_form or "website", {})
            main = spec.get("main_file", "index.html")
            nudge = (
                "STOP SEARCHING. You have spent too many iterations on web_search without writing any files. "
                "The Research phase already gathered what you need — those findings are in your context above. "
                f"You MUST use write_file to create {main!r} RIGHT NOW in this next response. "
                "Write the complete file content in a single write_file call. No more web_search calls."
            )
            on_emit(f"  ↻ Search limit hit ({search_only_iters} consecutive) — forcing write\n")
            messages.append({"role": "user", "content": nudge})
            search_only_iters = 0  # reset so we don't nudge every iteration

        # Last-resort: 2 iterations before max, if no main file exists, give a FINAL WARNING
        if is_build and iteration == max_iter - 2:
            _spec_lr = _FS.get(build_form, {})
            _main_lr = _spec_lr.get("main_file", "index.html")
            if not (Path(output_dir) / _main_lr).exists():
                _files_lr = [f.name for f in Path(output_dir).rglob("*") if f.is_file() and f.name != "paper.pdf"]
                last_resort = (
                    f"🚨 FINAL WARNING: You are about to run out of iterations and '{_main_lr}' DOES NOT EXIST. "
                    f"You have written: {', '.join(_files_lr) if _files_lr else 'nothing'}. "
                    f"In your NEXT response, you MUST write '{_main_lr}' or ALL your work is lost. "
                    f"Write a complete, working file — even if it means a simpler version. "
                    f"Do NOT search, do NOT plan — WRITE THE FILE NOW."
                )
                on_emit(f"  🚨 FINAL WARNING: {_main_lr} missing with 2 iterations left!\n")
                messages.append({"role": "user", "content": last_resort})
    else:
        on_emit(f"  [{phase_label}] max iterations reached.\n")

    return messages


# ─────────────────────────────────────────────────────────────────────────────
# Main entry point
# ─────────────────────────────────────────────────────────────────────────────

def generate(
    provider: BaseLLMProvider,
    skill: BaseSkill,
    paper: Paper,
    analysis: PaperAnalysis,
    output_dir: str,
    demo_form: Optional[str] = None,
    demo_type: Optional[str] = None,
    max_iter: int = 25,
    on_progress: Optional[Callable[[str], None]] = None,
) -> DemoResult:
    """
    Run the multi-phase agentic generation loop.

    Phases:
      1. Research  — find official links + foundational prior work (2-3 iters)
      2. Build     — write all demo files (up to max_iter - 8 iters)
      3. Polish    — read-review-fix quality pass (up to 3 iters)
      (post) Validate — form compliance check + auto-correction if needed
    """
    form  = demo_form or analysis.demo_form
    dtype = demo_type or analysis.demo_type

    os.makedirs(output_dir, exist_ok=True)

    # Save the paper PDF to output_dir so extract_pdf_page can access it
    if getattr(paper, "pdf_bytes", None):
        pdf_dest = Path(output_dir) / "paper.pdf"
        pdf_dest.write_bytes(paper.pdf_bytes)

    system  = skill.get_system_prompt(paper, analysis, form, dtype)
    use_oai = _is_openai_format(provider)

    def _emit(text: str) -> None:
        if on_progress and text:
            on_progress(text)

    _emit(f"\nProvider : {provider.__class__.__name__} ({provider.model})\n")
    _emit(f"Skill    : {skill.name}  |  Form: {form}  |  Type: {dtype}\n\n")

    # Start preloading the Docling model in the background so it's warm
    # by the time we need it for figure extraction after the research phase.
    if form in ("latex", "slides", "presentation", "page_blog"):
        start_docling_preload()

    try:
        # ── Phase 1: Research ─────────────────────────────────────────────
        _emit("━━ Phase 1 / 3 — Research ━━\n")
        research_notes = _run_research_phase(
            provider=provider,
            paper=paper,
            output_dir=output_dir,
            use_openai_fmt=use_oai,
            on_emit=_emit,
            max_iter=2,  # capped at 2 — avoids token waste on search loops
        )

        # ── Phase 1b: Figure Pre-extraction (forms that embed PDF figures) ───
        pdf_survey = ""
        if form in ("latex", "slides", "presentation", "page_blog"):
            _emit("\n━━ Phase 1b — Figure Pre-extraction ━━\n")
            pdf_survey = _pre_extract_figures(output_dir, _emit, provider=provider)
            if not pdf_survey:
                # Fallback to text-only survey if PyMuPDF unavailable
                pdf_survey = _run_pdf_survey(output_dir, _emit)

        # ── Phase 2: Build ────────────────────────────────────────────────
        _emit("\n━━ Phase 2 / 3 — Build ━━\n")
        initial = skill.get_initial_message(paper, analysis, form, dtype)
        if research_notes.strip():
            initial += (
                "\n\n─── RESEARCH FINDINGS (Phase 1) — OFFICIAL LINKS & PRIOR WORK CONTEXT ───\n"
                + research_notes[:12000]
                + "\n─── END RESEARCH ───"
            )
        if pdf_survey:
            initial += pdf_survey

        # Inject skeleton-first hint BEFORE iteration 0 for large-file forms (Priority 1 fix)
        if form in _LARGE_FILE_FORMS:
            if form in _SINGLE_FILE_FORMS:
                # Presentation/LaTeX: single self-contained file, no external CSS/JS
                initial += "\n\n" + _SKELETON_FIRST_MESSAGE_SINGLE
            else:
                # Website/blog/app: recommend file organization
                initial += "\n\n" + _SKELETON_FIRST_MESSAGE_SPLIT

        messages: list[dict] = [{"role": "user", "content": initial}]

        # Form-specific iteration budgets (optimization #5)
        budget = FORM_BUDGETS.get(form, {"build": max(4, max_iter - 6), "polish": 3})
        build_iters = min(budget["build"], max_iter)
        polish_iters = min(budget["polish"], max(1, max_iter - build_iters))
        _emit(f"  Budget: build={build_iters}, polish={polish_iters} (form={form})\n")

        messages = _run_loop(
            provider=provider,
            messages=messages,
            system=system,
            output_dir=output_dir,
            use_openai_fmt=use_oai,
            on_emit=_emit,
            max_iter=build_iters,
            phase_label=f"build-{form}-" if form else "build-",
        )

        # ── Phase 3: Polish ───────────────────────────────────────────────
        _emit("\n━━ Phase 3 / 3 — Polish ━━\n")
        generated_files = [
            str(Path(f).relative_to(output_dir))
            for f in Path(output_dir).rglob("*") if f.is_file()
        ]
        if generated_files:
            # For structural forms use form-specific polish (bypasses skill overrides)
            if form in ("latex", "slides", "presentation", "app_streamlit",
                         "page_readme", "page_blog", "diagram_graphviz"):
                polish_prompt = skill.get_form_polish_prompt(
                    paper, analysis, form, dtype, generated_files
                )
            else:
                polish_prompt = skill.get_polish_prompt(
                    paper, analysis, form, dtype, generated_files
                )
            messages.append({"role": "user", "content": polish_prompt})
            messages = _run_loop(
                provider=provider,
                messages=messages,
                system=system,
                output_dir=output_dir,
                use_openai_fmt=use_oai,
                on_emit=_emit,
                max_iter=polish_iters,
                phase_label="polish-",
            )

        _emit("\n✓ Generation complete.\n")

        # ── Post-Polish: Auto-Validation (HTML/JS/Python quality) ────────
        _emit("\n━━ Post-Polish Validation ━━\n")
        val_issues = _auto_validate_files(output_dir, form)
        if val_issues:
            _emit(f"  ⚠ Validation issues found — requesting auto-fix...\n")
            autofix_msg = (
                "VALIDATION ISSUES FOUND — Fix ALL of these before finishing:\n\n"
                + val_issues
                + "\n\nFix every issue listed above:\n"
                "  • Correct CDN URLs to exact pinned versions\n"
                "  • Ensure all figures from figures/ directory are referenced\n"
                "  • Fix any unclosed tags, broken relative paths, or JS errors\n"
                "  • Verify dark theme consistency (no white/light backgrounds)\n"
                "  • Check all interactive elements (buttons, sliders, links) work\n"
            )
            messages.append({"role": "user", "content": autofix_msg})
            messages = _run_loop(
                provider=provider,
                messages=messages,
                system=system,
                output_dir=output_dir,
                use_openai_fmt=use_oai,
                on_emit=_emit,
                max_iter=2,
                phase_label="autofix-",
            )
            # Re-validate after fix
            remaining = _auto_validate_files(output_dir, form)
            if remaining:
                _emit(f"  ⚠ Some issues remain after auto-fix:\n{remaining[:600]}\n")
            else:
                _emit("  ✓ All validation issues resolved.\n")
        else:
            _emit("  ✓ Validation passed — no issues found.\n")

        # ── Post-generation: Form Validation ─────────────────────────────
        is_valid, validation_error = _validate_form_output(output_dir, form)
        if not is_valid:
            _emit(f"\n⚠ Form validation failed: {validation_error}\n")
            _emit("  Requesting auto-correction...\n\n")
            correction = _correction_message(form, validation_error)
            messages.append({"role": "user", "content": correction})

            messages = _run_loop(
                provider=provider,
                messages=messages,
                system=system,
                output_dir=output_dir,
                use_openai_fmt=use_oai,
                on_emit=_emit,
                max_iter=8,
                phase_label="fix-",
            )

            is_valid, validation_error = _validate_form_output(output_dir, form)
            if is_valid:
                _emit("✓ Form validation passed after correction.\n")
            else:
                _emit(f"⚠ Still incorrect after correction: {validation_error}\n")

    except Exception as exc:
        _emit(f"\n[error] {exc}\n")
        return DemoResult(
            demo_form=form,
            demo_type=dtype,
            output_dir=output_dir,
            main_file="app.py",
            dependencies=[],
            run_command="",
            success=False,
            error=str(exc),
        )

    main_file = _detect_main_file(output_dir, form)
    deps      = _detect_dependencies(output_dir)
    run_cmd   = _build_run_command(output_dir, main_file, form)

    return DemoResult(
        demo_form=form,
        demo_type=dtype,
        output_dir=output_dir,
        main_file=main_file,
        dependencies=deps,
        run_command=run_cmd,
        success=True,
    )
