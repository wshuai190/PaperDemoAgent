"""Agent tools for the demo generation loop."""

import json
import os
import subprocess
import sys
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
        "description": "Write content to a file in the output directory. Paths are relative to the output directory.",
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


def tool_write_file(output_dir: str, path: str, content: str) -> str:
    target = _safe_path(output_dir, path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return f"Written {len(content)} bytes to {path}"


def tool_read_file(output_dir: str, path: str) -> str:
    target = _safe_path(output_dir, path)
    if not target.exists():
        return f"Error: file not found: {path}"
    try:
        return target.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        size = target.stat().st_size
        return f"Error: {path} is a binary file ({size} bytes) and cannot be read as text."


def tool_search_huggingface(query: str, type: str = "model", limit: int = 5) -> str:
    # LLMs sometimes send floats for integer params — islice() requires int
    limit = max(1, min(int(limit), 20))
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
            results = list(api.list_models(search=query, limit=limit, sort="downloads"))
            items = [
                {"id": r.id, "downloads": getattr(r, "downloads", 0), "likes": getattr(r, "likes", 0)}
                for r in results
            ]

        if not items:
            return f"No {type}s found for query: {query!r}"
        return json.dumps(items, indent=2)
    except Exception as e:
        return f"HuggingFace search error: {e}"


def tool_install_package(package: str) -> str:
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", package, "-q"],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode == 0:
            return f"Installed: {package}"
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


def dispatch_tool(tool_name: str, arguments: Dict[str, Any], output_dir: str) -> str:
    """Dispatch a tool call by name and return the result as a string."""
    try:
        if tool_name == "list_files":
            return tool_list_files(output_dir)
        elif tool_name == "write_file":
            return tool_write_file(output_dir, arguments["path"], arguments["content"])
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
        elif tool_name == "download_file":
            return tool_download_file(output_dir, arguments["url"], arguments["filename"])
        elif tool_name == "web_search":
            return tool_web_search(arguments["query"])
        else:
            return f"Unknown tool: {tool_name!r}"
    except KeyError as e:
        return f"Missing required argument: {e}"
    except Exception as e:
        return f"Tool error ({tool_name}): {e}"
