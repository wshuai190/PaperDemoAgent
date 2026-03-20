"""Agent tools for the demo generation loop."""
from __future__ import annotations


import json
import os
import re
import shutil
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Dict, List, Optional


# Tool definitions (generic format, converted per-provider by the provider layer)
TOOLS: List[Dict] = [
    {
        "name": "list_files",
        "description": "List all files currently in the output directory with their names and sizes. Call this to see what you have already generated.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "write_file",
        "description": (
            "Write content to a file in the output directory. Paths are relative to the output directory. "
            "Limit: 400 lines for split files (CSS/JS), 800 lines for main files (demo.html, index.html). "
            "For presentations: write demo.html with first slides, then use append_file to add more slides."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Relative file path (e.g. 'app.py' or 'static/style.css')",
                },
                "content": {
                    "type": "string",
                    "description": "The file content to write",
                },
            },
            "required": ["path", "content"],
        },
    },
    {
        "name": "append_file",
        "description": (
            "Append content to an existing file. Use this to incrementally build up large files like "
            "demo.html — write the first chunk with write_file, then add more sections with append_file. "
            "The file must already exist. Max combined size: 1200 lines."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Relative file path to append to",
                },
                "content": {
                    "type": "string",
                    "description": "Content to append to the end of the file",
                },
            },
            "required": ["path", "content"],
        },
    },
    {
        "name": "read_file",
        "description": "Read the content of a file in the output directory.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Relative file path to read",
                },
            },
            "required": ["path"],
        },
    },
    {
        "name": "search_huggingface",
        "description": "Search Hugging Face Hub for models or datasets relevant to a paper.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query (e.g. paper title or model name)",
                },
                "type": {
                    "type": "string",
                    "description": "What to search for: 'model' or 'dataset'",
                    "enum": ["model", "dataset"],
                },
                "limit": {
                    "type": "integer",
                    "description": "Max results to return (default: 5)",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "install_package",
        "description": "Install a Python package using pip.",
        "parameters": {
            "type": "object",
            "properties": {
                "package": {
                    "type": "string",
                    "description": "Package name or pip spec (e.g. 'gradio' or 'torch>=2.0')",
                },
            },
            "required": ["package"],
        },
    },
    {
        "name": "execute_python",
        "description": "Execute Python code in a subprocess (30 second timeout). Use to validate generated code.",
        "parameters": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "Python code to execute",
                },
            },
            "required": ["code"],
        },
    },
    {
        "name": "web_search",
        "description": "Search the web for documentation, examples, or API references.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "extract_pdf_page",
        "description": (
            "Render a page from the paper's PDF as a PNG image and save it to the output directory. "
            "Use this to extract figures, result tables, architecture diagrams, and charts from the paper "
            "to embed directly in slides or presentations. "
            "Supports cropping to a sub-region using relative coordinates (0.0 = top/left, 1.0 = bottom/right). "
            "The paper PDF is automatically available as 'paper.pdf' in the output directory."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "page": {
                    "type": "integer",
                    "description": "Page number (1-indexed)",
                },
                "dpi": {
                    "type": "integer",
                    "description": "Resolution in DPI (default: 150; use 200+ for high quality)",
                },
                "crop": {
                    "type": "object",
                    "description": (
                        "Optional crop box as relative coordinates. "
                        "x0/y0 = top-left corner, x1/y1 = bottom-right corner (all 0.0–1.0). "
                        "Example: crop a figure in the bottom half: {\"x0\":0.0,\"y0\":0.5,\"x1\":1.0,\"y1\":1.0}"
                    ),
                    "properties": {
                        "x0": {"type": "number"},
                        "y0": {"type": "number"},
                        "x1": {"type": "number"},
                        "y1": {"type": "number"},
                    },
                },
                "filename": {
                    "type": "string",
                    "description": "Output filename (default: figures/page_{page}.png)",
                },
            },
            "required": ["page"],
        },
    },
    {
        "name": "extract_tables",
        "description": (
            "Extract table-like text structures from a PDF page and return them as JSON. "
            "Returns a list of tables: [{headers: [...], rows: [[...], ...]}, ...]. "
            "Use this to get numerical results, comparison tables, or ablation data — "
            "then render as an HTML table or Chart.js bar chart."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "pdf_path": {
                    "type": "string",
                    "description": "Relative path to the PDF file (e.g. 'paper.pdf')",
                },
                "page": {
                    "type": "integer",
                    "description": "Page number (1-indexed)",
                },
            },
            "required": ["pdf_path", "page"],
        },
    },
    {
        "name": "extract_figure",
        "description": (
            "Extract a specific figure/diagram region from a PDF page using fractional coordinates. "
            "x1/y1 = top-left corner, x2/y2 = bottom-right corner (all 0.0–1.0 fractions of page size). "
            "Saves the cropped region as a PNG to the figures/ directory. "
            "Use this to precisely isolate a figure when you know its location on the page."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "pdf_path": {
                    "type": "string",
                    "description": "Relative path to the PDF file (e.g. 'paper.pdf')",
                },
                "page": {
                    "type": "integer",
                    "description": "Page number (1-indexed)",
                },
                "x1": {"type": "number", "description": "Left edge fraction (0.0–1.0)"},
                "y1": {"type": "number", "description": "Top edge fraction (0.0–1.0)"},
                "x2": {"type": "number", "description": "Right edge fraction (0.0–1.0)"},
                "y2": {"type": "number", "description": "Bottom edge fraction (0.0–1.0)"},
                "dpi": {
                    "type": "integer",
                    "description": "Render resolution in DPI (default: 200 for crisp figures)",
                },
                "filename": {
                    "type": "string",
                    "description": "Output filename (default: figures/figure_p{page}_....png)",
                },
            },
            "required": ["pdf_path", "page", "x1", "y1", "x2", "y2"],
        },
    },
    {
        "name": "list_pdf_pages",
        "description": (
            "Return the total page count and a brief text snippet from each page of a PDF. "
            "Use this to find which page contains a specific figure, table, or result you want to extract."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "pdf_path": {
                    "type": "string",
                    "description": "Relative path to the PDF file (default: 'paper.pdf')",
                },
            },
            "required": [],
        },
    },
    {
        "name": "render_svg",
        "description": (
            "Evaluate a Python expression using the graphics primitives module "
            "and return the resulting SVG string. Available functions include: "
            "rounded_box, arrow, flow_arrow, layer_stack, parallel_blocks, "
            "connection_lines, dashed_box, svg_wrapper, encoder_decoder, "
            "transformer_block, pipeline_flow, comparison_diagram, "
            "attention_visualization. See GRAPHICS_REFERENCE for full docs."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "expr": {
                    "type": "string",
                    "description": (
                        "Python expression that calls graphics functions and returns an SVG string. "
                        "Example: pipeline_flow(['Input','Encode','Decode'], title='Pipeline')"
                    ),
                },
            },
            "required": ["expr"],
        },
    },
    {
        "name": "download_file",
        "description": (
            "Download a file from a URL and save it to the output directory. "
            "Use this to fetch logos (SVG/PNG), fonts, icons, images, or other assets "
            "needed by your demo. Returns the saved filename."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The URL to download from",
                },
                "filename": {
                    "type": "string",
                    "description": "Local filename to save as (relative to output dir, e.g. 'assets/logo.svg')",
                },
            },
            "required": ["url", "filename"],
        },
    },
    {
        "name": "validate_output",
        "description": (
            "Validate a generated file for common issues. "
            "For HTML: checks unclosed tags, empty src/href, missing doctype, broken relative paths. "
            "For Python: checks syntax via ast.parse. "
            "For JS: checks matching braces/brackets/parens. "
            "Returns a list of issues found, or 'No issues found'."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Relative file path to validate (e.g. 'index.html', 'app.py')",
                },
            },
            "required": ["path"],
        },
    },
]


def tool_list_files(output_dir: str) -> str:
    base = Path(output_dir)
    files = [f for f in base.rglob("*") if f.is_file()]
    if not files:
        return "Output directory is empty — no files generated yet."
    lines = []
    total_bytes = 0
    for f in sorted(files):
        size = f.stat().st_size
        total_bytes += size
        rel = f.relative_to(base)
        size_str = f"{size / 1024:.1f} KB" if size >= 1024 else f"{size} B"
        lines.append(f"  {rel}  ({size_str})")
    lines.append(f"\n{len(files)} file(s)  |  {total_bytes / 1024:.1f} KB total")
    return "\n".join(lines)


def _safe_path(output_dir: str, relative_path: str) -> Path:
    """Resolve a relative path safely within output_dir."""
    base = Path(output_dir).resolve()
    target = (base / relative_path).resolve()
    if not str(target).startswith(str(base)):
        raise ValueError(f"Path escapes output directory: {relative_path!r}")
    return target


_WRITE_FILE_MAX_LINES = 300
_WRITE_FILE_HARD_MAX = 800  # absolute max for single-file forms
_WRITE_FILE_SPLIT_MAX = 400  # max for files that should be split (CSS, JS, etc.)

# Single-file forms where the main file is allowed to be larger
_SINGLE_FILE_MAIN = {"demo.html", "presentation.tex", "main.tex", "index.html"}


def tool_write_file(output_dir: str, path: str, content: str) -> str:
    line_count = content.count("\n") + 1
    filename = Path(path).name

    is_main = filename in _SINGLE_FILE_MAIN
    max_allowed = _WRITE_FILE_HARD_MAX if is_main else _WRITE_FILE_SPLIT_MAX

    if line_count > max_allowed:
        return (
            f"ERROR: File too large ({line_count} lines, max {max_allowed}). "
            + (f"Write in multiple calls: first write the skeleton, then use read_file + write_file to append more content."
               if is_main else
               f"Split into separate files (CSS, JS, HTML).")
        )
    # Write the file
    target = _safe_path(output_dir, path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    msg = f"Written {len(content)} bytes to {path}"
    if line_count > _WRITE_FILE_MAX_LINES:
        msg += f" (NOTE: {line_count} lines — large but accepted for main file)"
    return msg


def tool_read_file(output_dir: str, path: str) -> str:
    target = _safe_path(output_dir, path)
    if not target.exists():
        return f"Error: file not found: {path}"
    try:
        return target.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        size = target.stat().st_size
        return f"Error: {path} is a binary file ({size} bytes) and cannot be read as text."


def tool_append_file(output_dir: str, path: str, content: str) -> str:
    """Append content to an existing file. Useful for building up large files incrementally."""
    target = _safe_path(output_dir, path)
    if not target.exists():
        return f"Error: file not found: {path}. Use write_file to create it first."
    existing = target.read_text(encoding="utf-8")
    combined = existing + content
    combined_lines = combined.count("\n") + 1
    if combined_lines > 1200:
        return (
            f"ERROR: Combined file would be {combined_lines} lines (max 1200). "
            f"The file is getting too large."
        )
    target.write_text(combined, encoding="utf-8")
    return f"Appended {len(content)} bytes to {path} (total: {len(combined)} bytes, {combined_lines} lines)"


def tool_search_huggingface(query: str, type: str = "model", limit: int = 5) -> str:
    # LLMs sometimes send floats for integer params — islice() requires int
    limit = max(1, min(int(limit), 20))
    items = []
    hf_error: Optional[str] = None

    try:
        from huggingface_hub import HfApi
        api = HfApi()

        if type == "dataset":
            results = list(api.list_datasets(search=query, limit=limit))
            items = [
                {"id": r.id, "downloads": getattr(r, "downloads", 0), "likes": getattr(r, "likes", 0)}
                for r in results
            ]
        else:
            # Try sort="downloads" first; fall back to no sort if unsupported
            try:
                results = list(api.list_models(search=query, limit=limit, sort="downloads"))
            except Exception:
                results = list(api.list_models(search=query, limit=limit))
            items = [
                {"id": r.id, "downloads": getattr(r, "downloads", 0), "likes": getattr(r, "likes", 0)}
                for r in results
            ]
    except Exception as e:
        hf_error = str(e)

    if items:
        return json.dumps(items, indent=2)

    # Fallback: web_search with site:huggingface.co so the agent still finds
    # relevant models/datasets even when the Hub API returns nothing.
    prefix = (
        f"HuggingFace API error: {hf_error}"
        if hf_error
        else f"HuggingFace API returned no results for {query!r}"
    )
    fallback_query = f"site:huggingface.co {query}"
    fallback_result = tool_web_search(fallback_query)
    return f"{prefix}. Web search fallback (site:huggingface.co):\n\n{fallback_result}"


def _ensure_graphviz_binary() -> str:
    """Install the Graphviz system binary (dot) if not already present."""
    if shutil.which("dot"):
        return ""
    import platform
    system = platform.system()
    if system == "Darwin":
        cmd = ["brew", "install", "graphviz"]
    elif system == "Linux":
        cmd = ["apt-get", "install", "-y", "graphviz"]
    else:
        return " (WARNING: Graphviz system binary 'dot' not found — install it manually)"
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode == 0:
            return " + system binary 'dot' installed"
        return f" (WARNING: could not install system graphviz: {result.stderr[:200]})"
    except Exception as e:
        return f" (WARNING: could not install system graphviz: {e})"


def tool_install_package(package: str) -> str:
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", package, "-q"],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode == 0:
            extra = ""
            # graphviz Python package needs the system binary (dot) to render
            if "graphviz" in package.lower():
                extra = _ensure_graphviz_binary()
            return f"Installed: {package}{extra}"
        return f"Install failed: {result.stderr[:500]}"
    except subprocess.TimeoutExpired:
        return f"Install timed out: {package}"
    except Exception as e:
        return f"Install error: {e}"


def tool_execute_python(code: str, output_dir: Optional[str] = None) -> str:
    """Execute Python code in the output directory so relative paths work correctly."""
    try:
        result = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            timeout=60,    # increased: pptx/matplotlib generation takes longer
            cwd=output_dir,  # run in output dir so prs.save('x.pptx') lands in the right place
        )
        output = result.stdout[:3000]
        if result.returncode != 0:
            output += f"\nSTDERR:\n{result.stderr[:1500]}"
        return output or "(no output — script ran successfully)"
    except subprocess.TimeoutExpired:
        return "Execution timed out (60s)"
    except Exception as e:
        return f"Execution error: {e}"


def tool_extract_pdf_page(
    output_dir: str,
    page: int,
    dpi: int = 150,
    crop: Optional[Dict[str, float]] = None,
    filename: Optional[str] = None,
) -> str:
    """Render a PDF page (or cropped region) as PNG for use in slides."""
    try:
        import fitz  # PyMuPDF
    except ImportError:
        return "Error: PyMuPDF not installed. Run: pip install pymupdf"

    pdf_path = Path(output_dir) / "paper.pdf"
    if not pdf_path.exists():
        return (
            "Error: paper.pdf not found in output directory. "
            "The PDF was not available for this paper source (URL or text input). "
            "Try using web_search or download_file to get figures instead."
        )

    try:
        doc = fitz.open(str(pdf_path))
        total_pages = len(doc)
        if page < 1 or page > total_pages:
            return f"Error: page {page} out of range (paper has {total_pages} pages, 1-indexed)"

        pg = doc[page - 1]
        mat = fitz.Matrix(dpi / 72, dpi / 72)

        if crop:
            rect = pg.rect
            w, h = rect.width, rect.height
            clip = fitz.Rect(
                crop.get("x0", 0.0) * w,
                crop.get("y0", 0.0) * h,
                crop.get("x1", 1.0) * w,
                crop.get("y1", 1.0) * h,
            )
            pix = pg.get_pixmap(matrix=mat, clip=clip)
        else:
            pix = pg.get_pixmap(matrix=mat)

        out_filename = filename or f"figures/page_{page}.png"
        target = _safe_path(output_dir, out_filename)
        target.parent.mkdir(parents=True, exist_ok=True)
        pix.save(str(target))

        size_str = f"{pix.width}×{pix.height}px"
        crop_note = (
            f" [cropped: x0={crop['x0']:.2f} y0={crop['y0']:.2f} x1={crop['x1']:.2f} y1={crop['y1']:.2f}]"
            if crop else ""
        )
        return f"Saved {out_filename} ({size_str}{crop_note})"
    except Exception as e:
        return f"extract_pdf_page error: {e}"


def tool_extract_figure(
    output_dir: str,
    pdf_path: str,
    page: int,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    dpi: int = 200,
    filename: Optional[str] = None,
) -> str:
    """Extract a specific figure region from a PDF page using fractional coords."""
    try:
        import fitz  # PyMuPDF
    except ImportError:
        return "Error: PyMuPDF not installed. Run: pip install pymupdf"

    full_path = _safe_path(output_dir, pdf_path)
    if not full_path.exists():
        return f"Error: PDF not found: {pdf_path}"

    try:
        doc = fitz.open(str(full_path))
        total_pages = len(doc)
        if page < 1 or page > total_pages:
            return f"Error: page {page} out of range (PDF has {total_pages} pages, 1-indexed)"

        pg = doc[page - 1]
        rect = pg.rect
        w, h = rect.width, rect.height
        clip = fitz.Rect(x1 * w, y1 * h, x2 * w, y2 * h)
        mat = fitz.Matrix(dpi / 72, dpi / 72)
        pix = pg.get_pixmap(matrix=mat, clip=clip)

        out_filename = filename or f"figures/figure_p{page}_{x1:.2f}_{y1:.2f}_{x2:.2f}_{y2:.2f}.png"
        target = _safe_path(output_dir, out_filename)
        target.parent.mkdir(parents=True, exist_ok=True)
        pix.save(str(target))

        size_str = f"{pix.width}×{pix.height}px"
        return f"Saved {out_filename} ({size_str}, {dpi}dpi, crop=[{x1:.2f},{y1:.2f},{x2:.2f},{y2:.2f}])"
    except Exception as e:
        return f"extract_figure error: {e}"


def tool_extract_tables(output_dir: str, pdf_path: str, page: int) -> str:
    """Extract table-like structures from a PDF page and return them as JSON.

    Uses PyMuPDF block extraction: identifies rows by clustering text blocks
    that share the same y-coordinate band, then groups into columns by x position.
    Returns JSON: [{headers: [...], rows: [[...], ...]}, ...]
    """
    try:
        import fitz  # PyMuPDF
    except ImportError:
        return "Error: PyMuPDF not installed. Run: pip install pymupdf"

    full_path = _safe_path(output_dir, pdf_path)
    if not full_path.exists():
        return f"Error: PDF not found: {pdf_path}"

    try:
        doc = fitz.open(str(full_path))
        total_pages = len(doc)
        if page < 1 or page > total_pages:
            return f"Error: page {page} out of range (PDF has {total_pages} pages, 1-indexed)"

        pg = doc[page - 1]
        blocks = pg.get_text("blocks")
        # Each block: (x0, y0, x1, y1, text, block_no, block_type)
        # type 0 = text, type 1 = image
        text_blocks = [
            (b[0], b[1], b[2], b[3], b[4].strip())
            for b in blocks if b[6] == 0 and b[4].strip()
        ]

        if not text_blocks:
            return json.dumps([])

        # Cluster blocks into rows by y0 proximity (within 5px = same row)
        Y_TOLERANCE = 5.0
        rows: list[list] = []
        for blk in sorted(text_blocks, key=lambda b: (round(b[1] / Y_TOLERANCE), b[0])):
            placed = False
            for row in rows:
                if abs(row[0][1] - blk[1]) <= Y_TOLERANCE:
                    row.append(blk)
                    placed = True
                    break
            if not placed:
                rows.append([blk])

        # Only keep rows with 2+ columns (table-like)
        table_rows = [
            sorted(r, key=lambda b: b[0])  # sort by x position
            for r in rows if len(r) >= 2
        ]

        if len(table_rows) < 2:
            return json.dumps([])  # not enough rows to form a table

        # Group into contiguous table segments (gap > 30px y-distance = new table)
        tables: list[list] = []
        current_table: list = []
        prev_y = None
        for row in sorted(table_rows, key=lambda r: r[0][1]):
            y0 = row[0][1]
            if prev_y is not None and (y0 - prev_y) > 30:
                if len(current_table) >= 2:
                    tables.append(current_table)
                current_table = []
            current_table.append(row)
            prev_y = y0
        if len(current_table) >= 2:
            tables.append(current_table)

        result = []
        for tbl in tables:
            headers = [b[4] for b in tbl[0]]
            body_rows = [[b[4] for b in row] for row in tbl[1:]]
            result.append({"headers": headers, "rows": body_rows})

        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"extract_tables error: {e}"


def tool_list_pdf_pages(output_dir: str, pdf_path: str = "paper.pdf") -> str:
    """Return page count and a brief text snippet per page so the model knows where to look."""
    try:
        import fitz  # PyMuPDF
    except ImportError:
        return "Error: PyMuPDF not installed. Run: pip install pymupdf"

    full_path = _safe_path(output_dir, pdf_path)
    if not full_path.exists():
        return f"Error: PDF not found: {pdf_path}"

    try:
        doc = fitz.open(str(full_path))
        total = len(doc)
        lines = [f"Total pages: {total}"]
        for i, pg in enumerate(doc, start=1):
            text = pg.get_text("text").strip()
            # Keep first 150 chars, collapse whitespace
            snippet = " ".join(text.split())[:150]
            lines.append(f"  Page {i:3d}: {snippet}")
        return "\n".join(lines)
    except Exception as e:
        return f"list_pdf_pages error: {e}"


def tool_render_svg(expr: str) -> str:
    """Evaluate a graphics primitives expression and return the SVG string."""
    try:
        import paper_demo_agent.graphics as _g
        ns = {name: getattr(_g, name) for name in _g.__all__}
        result = eval(expr, {"__builtins__": {}}, ns)  # noqa: S307
        if not isinstance(result, str):
            return f"Error: expression returned {type(result).__name__}, expected str"
        return result
    except Exception as e:
        return f"Error rendering SVG: {e}"


def tool_download_file(output_dir: str, url: str, filename: str) -> str:
    """Download a URL and save it inside output_dir."""
    try:
        import httpx
        target = _safe_path(output_dir, filename)
        target.parent.mkdir(parents=True, exist_ok=True)
        response = httpx.get(url, follow_redirects=True, timeout=15)
        response.raise_for_status()
        target.write_bytes(response.content)
        size = len(response.content)
        size_str = f"{size / 1024:.1f} KB" if size >= 1024 else f"{size} B"
        return f"Downloaded {filename} ({size_str})"
    except Exception as e:
        return f"Download failed: {e}"


def tool_web_search(query: str) -> str:
    """Web search using ddgs (DuckDuckGo), falling back to the Instant Answers API."""
    # Primary: ddgs package (returns real search results)
    try:
        from ddgs import DDGS
        with DDGS() as ddgs:
            hits = list(ddgs.text(query, max_results=6))
        if hits:
            lines = []
            for h in hits:
                title = h.get("title", "")
                url = h.get("href", "")
                body = h.get("body", "")[:300]
                lines.append(f"**{title}**\n{url}\n{body}")
            return "\n\n".join(lines)
    except Exception:
        pass

    # Fallback: DuckDuckGo Instant Answers API (works for well-known topics)
    try:
        import httpx
        params = {"q": query, "format": "json", "no_redirect": "1", "no_html": "1"}
        data = httpx.get("https://api.duckduckgo.com/", params=params, timeout=10).json()
        results = []
        if data.get("AbstractText"):
            results.append(f"Summary: {data['AbstractText'][:500]}")
        for topic in data.get("RelatedTopics", [])[:5]:
            if isinstance(topic, dict) and topic.get("Text"):
                results.append(f"- {topic['Text'][:200]}")
        if results:
            return "\n".join(results)
    except Exception:
        pass

    return f"No results for: {query!r}"


# ─────────────────────────────────────────────────────────────────────────────
# Output validation helpers
# ─────────────────────────────────────────────────────────────────────────────

class _HTMLValidator(HTMLParser):
    """Lightweight HTML validator that tracks unclosed tags and bad attributes."""

    VOID_ELEMENTS = frozenset([
        "area", "base", "br", "col", "embed", "hr", "img", "input",
        "link", "meta", "param", "source", "track", "wbr",
    ])

    def __init__(self):
        super().__init__()
        self.issues: List[str] = []
        self.tag_stack: List[str] = []

    def handle_starttag(self, tag: str, attrs):
        tag = tag.lower()
        if tag not in self.VOID_ELEMENTS:
            self.tag_stack.append(tag)
        attrs_dict = dict(attrs)
        # Check empty src/href
        for attr in ("src", "href"):
            if attr in attrs_dict and not attrs_dict[attr].strip():
                self.issues.append(f"Empty {attr} attribute on <{tag}> (line ~{self.getpos()[0]})")
        # Script tag with no src (content checked in handle_endtag via _last_script_has_src)
        if tag == "script" and "src" not in attrs_dict:
            self._script_no_src = True
        else:
            self._script_no_src = False

    def handle_endtag(self, tag: str):
        tag = tag.lower()
        if tag in self.VOID_ELEMENTS:
            return
        if self.tag_stack and self.tag_stack[-1] == tag:
            self.tag_stack.pop()
        elif tag in self.tag_stack:
            # Mismatched nesting — pop up to the matching tag
            unclosed = []
            while self.tag_stack and self.tag_stack[-1] != tag:
                unclosed.append(self.tag_stack.pop())
            if self.tag_stack:
                self.tag_stack.pop()
            for t in unclosed:
                self.issues.append(f"Unclosed <{t}> tag before </{tag}>")

    def close(self):
        super().close()
        for tag in reversed(self.tag_stack):
            self.issues.append(f"Unclosed <{tag}> tag at end of file")


def _validate_html(content: str, output_dir: str, file_path: str) -> List[str]:
    """Validate HTML file for common issues."""
    issues: List[str] = []

    # Check for doctype
    if not re.match(r'\s*<!DOCTYPE\s', content, re.IGNORECASE):
        issues.append("Missing <!DOCTYPE html> declaration")

    # Parse for unclosed tags and empty attributes
    validator = _HTMLValidator()
    try:
        validator.feed(content)
        validator.close()
        issues.extend(validator.issues)
    except Exception:
        issues.append("HTML parsing error — file may be malformed")

    # Check for broken relative paths (src/href that reference local files)
    base = Path(output_dir)
    file_dir = (base / file_path).parent
    for match in re.finditer(r'(?:src|href)\s*=\s*["\']([^"\']+)["\']', content):
        ref = match.group(1)
        # Skip external URLs, data URIs, anchors, template vars
        if ref.startswith(("http://", "https://", "//", "data:", "#", "{", "mailto:")):
            continue
        ref_path = (file_dir / ref).resolve()
        if not ref_path.exists():
            issues.append(f"Broken reference: {ref} (file not found)")

    return issues


def _validate_python(content: str) -> List[str]:
    """Validate Python file syntax using ast.parse."""
    import ast
    try:
        ast.parse(content)
        return []
    except SyntaxError as e:
        return [f"Python syntax error at line {e.lineno}: {e.msg}"]


def _validate_js(content: str) -> List[str]:
    """Basic JS validation — check matching braces/brackets/parens."""
    issues: List[str] = []
    stack: List[str] = []
    pairs = {")": "(", "]": "[", "}": "{"}
    in_string = None  # track string delimiters
    prev_char = ""
    line_num = 1

    for ch in content:
        if ch == "\n":
            line_num += 1
        # Track strings (skip escaped quotes)
        if in_string:
            if ch == in_string and prev_char != "\\":
                in_string = None
            prev_char = ch
            continue
        if ch in ("'", '"', '`'):
            in_string = ch
            prev_char = ch
            continue
        # Skip single-line comments
        if ch == "/" and prev_char == "/":
            # consume until newline (simplified)
            prev_char = ch
            continue

        if ch in ("(", "[", "{"):
            stack.append((ch, line_num))
        elif ch in pairs:
            if stack and stack[-1][0] == pairs[ch]:
                stack.pop()
            elif stack:
                issues.append(f"Mismatched '{ch}' at line {line_num} (expected closing for '{stack[-1][0]}')")
            else:
                issues.append(f"Unexpected closing '{ch}' at line {line_num}")
        prev_char = ch

    for bracket, ln in stack:
        issues.append(f"Unclosed '{bracket}' opened at line {ln}")

    return issues


def tool_validate_output(output_dir: str, path: str) -> str:
    """Validate a generated file and return a list of issues."""
    target = _safe_path(output_dir, path)
    if not target.exists():
        return f"Error: file not found: {path}"

    try:
        content = target.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return f"Error: {path} is a binary file and cannot be validated as text."

    suffix = target.suffix.lower()
    issues: List[str] = []

    if suffix in (".html", ".htm"):
        issues = _validate_html(content, output_dir, path)
    elif suffix == ".py":
        issues = _validate_python(content)
    elif suffix in (".js", ".mjs"):
        issues = _validate_js(content)
    else:
        return f"Validation not supported for {suffix} files. Supported: .html, .py, .js"

    if not issues:
        return "No issues found"
    return "Issues found:\n" + "\n".join(f"  • {issue}" for issue in issues[:20])


def dispatch_tool(tool_name: str, arguments: Dict[str, Any], output_dir: str) -> str:
    """Dispatch a tool call by name and return the result as a string."""
    try:
        if tool_name == "list_files":
            return tool_list_files(output_dir)
        elif tool_name == "write_file":
            return tool_write_file(output_dir, arguments["path"], arguments["content"])
        elif tool_name == "append_file":
            return tool_append_file(output_dir, arguments["path"], arguments["content"])
        elif tool_name == "read_file":
            return tool_read_file(output_dir, arguments["path"])
        elif tool_name == "search_huggingface":
            return tool_search_huggingface(
                arguments["query"],
                arguments.get("type", "model"),
                arguments.get("limit", 5),
            )
        elif tool_name == "install_package":
            return tool_install_package(arguments["package"])
        elif tool_name == "execute_python":
            return tool_execute_python(arguments["code"], output_dir=output_dir)
        elif tool_name == "extract_pdf_page":
            return tool_extract_pdf_page(
                output_dir,
                page=int(arguments["page"]),
                dpi=int(arguments.get("dpi", 150)),
                crop=arguments.get("crop"),
                filename=arguments.get("filename"),
            )
        elif tool_name == "extract_tables":
            return tool_extract_tables(
                output_dir,
                arguments["pdf_path"],
                page=int(arguments["page"]),
            )
        elif tool_name == "extract_figure":
            return tool_extract_figure(
                output_dir,
                arguments["pdf_path"],
                page=int(arguments["page"]),
                x1=float(arguments["x1"]),
                y1=float(arguments["y1"]),
                x2=float(arguments["x2"]),
                y2=float(arguments["y2"]),
                dpi=int(arguments.get("dpi", 200)),
                filename=arguments.get("filename"),
            )
        elif tool_name == "list_pdf_pages":
            return tool_list_pdf_pages(
                output_dir,
                arguments.get("pdf_path", "paper.pdf"),
            )
        elif tool_name == "render_svg":
            return tool_render_svg(arguments["expr"])
        elif tool_name == "download_file":
            return tool_download_file(output_dir, arguments["url"], arguments["filename"])
        elif tool_name == "web_search":
            return tool_web_search(arguments["query"])
        elif tool_name == "validate_output":
            return tool_validate_output(output_dir, arguments["path"])
        else:
            return f"Unknown tool: {tool_name!r}"
    except KeyError as e:
        return f"Missing required argument: {e}"
    except Exception as e:
        return f"Tool error ({tool_name}): {e}"
