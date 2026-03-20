"""Paper fetching and parsing for Paper Demo Agent."""
from __future__ import annotations

import os
import re
import tempfile
from pathlib import Path
from typing import Dict, Optional
from urllib.parse import urlparse

from paper_demo_agent.paper.models import Paper

_PDF_BYTES_LIMIT = 20 * 1024 * 1024  # 20 MB — stay within API payload limits


def detect_source_type(source: str) -> str:
    """Detect whether the source is an arXiv ID/URL, local PDF, URL, or raw text."""
    s = source.strip()
    if re.match(r"^\d{4}\.\d{4,5}(v\d+)?$", s):
        return "arxiv"
    if "arxiv.org" in s:
        return "arxiv"
    if s.lower().endswith(".pdf") or (os.path.isfile(s) and s.lower().endswith(".pdf")):
        return "pdf"
    if s.startswith("http://") or s.startswith("https://"):
        return "url"
    if os.path.isfile(s):
        return "pdf"
    return "text"


def _extract_arxiv_id(source: str) -> str:
    """Extract the arXiv ID from a URL or raw ID string."""
    source = source.strip()
    # Already a bare ID
    if re.match(r"^\d{4}\.\d{4,5}(v\d+)?$", source):
        return source
    # URL patterns: /abs/XXXX.XXXX, /pdf/XXXX.XXXX
    m = re.search(r"(\d{4}\.\d{4,5}(?:v\d+)?)", source)
    if m:
        return m.group(1)
    raise ValueError(f"Cannot extract arXiv ID from: {source!r}")


def _parse_pdf_bytes(data: bytes) -> tuple[str, Dict[str, str]]:
    """Extract full text and sections from PDF bytes using PyMuPDF."""
    try:
        import fitz  # PyMuPDF
    except ImportError:
        raise ImportError("PyMuPDF is required to parse PDFs: pip install pymupdf")

    doc = fitz.open(stream=data, filetype="pdf")
    pages = []
    for page in doc:
        pages.append(page.get_text())
    full_text = "\n".join(pages)
    sections = _extract_sections(full_text)
    return full_text, sections


def _parse_pdf_path(path: str) -> tuple[str, Dict[str, str]]:
    """Extract full text and sections from a local PDF file."""
    try:
        import fitz
    except ImportError:
        raise ImportError("PyMuPDF is required to parse PDFs: pip install pymupdf")

    doc = fitz.open(path)
    pages = []
    for page in doc:
        pages.append(page.get_text())
    full_text = "\n".join(pages)
    sections = _extract_sections(full_text)
    return full_text, sections


def _extract_sections(text: str) -> Dict[str, str]:
    """Heuristically split paper text into named sections."""
    section_pattern = re.compile(
        r"^(?:\d+\.?\s+)?([A-Z][A-Z\s\-]{2,50})$", re.MULTILINE
    )
    matches = list(section_pattern.finditer(text))
    if len(matches) < 2:
        # fallback: split by double newline, name by first line
        return {"Full Text": text[:20000]}

    sections: Dict[str, str] = {}
    for i, m in enumerate(matches):
        name = m.group(1).strip().title()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        content = text[start:end].strip()
        if content:
            sections[name] = content[:5000]  # cap per section
    return sections


_JUNK_LINE_RE = re.compile(
    r"""
    \[?\d{4}-\d{4}-\d{4}-\d{4}\]?  # ORCID ID
    | @\w+\.\w+                      # email
    | \b(?:university|institute|department|school|laboratory|lab|corp|inc)\b
    | \d{1,3}\s*[,;]\s*\d{1,3}       # affiliation numbers like "1, 2"
    | ^\d+$                          # bare page number
    | ^[*†‡§¶]+$                     # footnote markers
    """,
    re.VERBOSE | re.IGNORECASE,
)


def _is_title_candidate(line: str) -> bool:
    """Return True if a line looks like it could be a paper title."""
    if len(line) < 8 or len(line) > 200:
        return False
    # Titles always start with an uppercase letter or digit
    if not line[0].isupper() and not line[0].isdigit():
        return False
    if line.lower().startswith(("abstract", "introduction", "keywords", "preprint", "arxiv")):
        return False
    if _JUNK_LINE_RE.search(line):
        return False
    # Lines that are ALL CAPS and very short are usually section headers
    if line.isupper() and len(line) < 30:
        return False
    # Sentence fragments (lines ending with a comma or continuing mid-word) are body text
    if line.endswith(",") or line.endswith(";"):
        return False
    return True


def _extract_title_abstract(text: str) -> tuple[str, str]:
    """Best-effort extraction of title and abstract from raw text."""
    lines = [l.strip() for l in text.split("\n") if l.strip()]

    # Title: longest candidate line in the first 20 lines, filtering junk
    title = ""
    for line in lines[:20]:
        if _is_title_candidate(line) and len(line) > len(title):
            title = line

    # Abstract: text between 'Abstract' marker and next section header
    abstract = ""
    abstract_match = re.search(
        r"(?i)\babstract\b[\s\-—]*\n(.*?)(?=\n\s*(?:\d+\.?\s+)?[A-Z][A-Za-z\s]{3,}|\Z)",
        text,
        re.DOTALL,
    )
    if abstract_match:
        abstract = abstract_match.group(1).strip()[:2000]

    return title, abstract


_AUTHOR_JUNK_RE = re.compile(
    r"""
    ^\d+$                              # bare numbers (affiliations, page nums)
    | \[?\d{4}-\d{4}-\d{4}-\d{4}\]?   # ORCID IDs
    | @\w+\.\w+                        # email addresses
    | \b(?:university|institute|department|school|laboratory|lab|corp|inc|australia|usa|china|germany|france|uk|abstract|keywords|introduction|preprint)\b
    | ^\*|^†|^‡|^§                     # footnote markers at start
    | ^\{|^\}                          # braces from LaTeX artifacts
    """,
    re.VERBOSE | re.IGNORECASE,
)

# Strip ORCID IDs, affiliation numbers, and footnote markers from author lines
_ORCID_STRIP_RE = re.compile(r"\[[\d\-]+\]|\([\d\-]+\)")


def _extract_authors_from_text(text: str) -> list[str]:
    """Best-effort extraction of author names from the first page of a PDF.

    Strategy: find lines between the title and abstract that contain ORCID IDs,
    comma-separated names, or 'and' connectors — strong signals of author lines.
    Then clean and split into individual names.
    """
    lines = [l.strip() for l in text.split("\n") if l.strip()]

    # Find abstract start
    abstract_start = len(lines)
    for i, line in enumerate(lines[:40]):
        if re.match(r"(?i)^abstract[\s.:—\-]", line):
            abstract_start = i
            break

    # Collect author-block lines: lines between title and abstract that
    # contain ORCID IDs or look like comma-separated names.
    # First, find the title (first long non-junk line).
    title_end = 0
    for i, line in enumerate(lines[:20]):
        if _is_title_candidate(line):
            title_end = i + 1

    # Author lines are the region right after title, before abstract.
    # Strong signal: ORCID IDs like [0000-0002-...] on the line.
    author_block_lines: list[str] = []
    for i in range(title_end, min(abstract_start, title_end + 15)):
        line = lines[i]
        # Skip institution / email / junk lines
        if _AUTHOR_JUNK_RE.search(line):
            continue
        if len(line) < 4:
            continue
        # Strong signal: has ORCID or affiliation superscripts like "Name1,2"
        has_orcid = bool(re.search(r"\d{4}-\d{4}", line))
        has_and = bool(re.search(r"\band\b", line))
        has_comma_names = bool(re.search(r"[A-Z][a-z]+\s+[A-Z][a-z]+\s*,", line))
        if has_orcid or has_and or has_comma_names:
            author_block_lines.append(line)

    if not author_block_lines:
        return []

    # Join author block and extract names
    block = " ".join(author_block_lines)
    # Strip ORCID IDs and bracketed numbers
    block = _ORCID_STRIP_RE.sub("", block)
    # Strip superscript-style affiliation numbers (e.g., "Zhuang⋆3,1")
    block = re.sub(r"[⋆*†‡§¶]+", "", block)
    # Remove trailing affiliation digit clusters stuck to names (e.g., "Wang1" → "Wang")
    block = re.sub(r"(\b[A-Z][a-z]+)\d[\d,]*", r"\1", block)

    # Split by comma or "and"
    parts = re.split(r"\s*,\s*|\s+and\s+", block)
    candidates: list[str] = []
    for part in parts:
        part = part.strip()
        if not part or len(part) < 4:
            continue
        # A name is 2+ words, each starting uppercase
        words = part.split()
        if len(words) >= 2 and all(w[0].isupper() for w in words if len(w) > 1):
            if not _AUTHOR_JUNK_RE.search(part):
                candidates.append(part)

    return candidates


class PaperParser:
    """Fetch and parse scientific papers from various sources."""

    def parse(self, source: str) -> Paper:
        """Parse a paper from an arXiv ID/URL, local PDF, URL, or raw text."""
        source_type = detect_source_type(source)

        if source_type == "arxiv":
            return self._parse_arxiv(source)
        elif source_type == "pdf":
            return self._parse_local_pdf(source)
        elif source_type == "url":
            return self._parse_url(source)
        else:
            return self._parse_text(source)

    def parse_pdf_bytes(self, data: bytes, filename: str = "upload.pdf") -> Paper:
        """Parse a PDF from raw bytes (used by UI file upload)."""
        full_text, sections = _parse_pdf_bytes(data)
        title, abstract = _extract_title_abstract(full_text)
        authors = _extract_authors_from_text(full_text)
        return Paper(
            title=title or filename,
            abstract=abstract,
            full_text=full_text,
            sections=sections,
            source_type="pdf",
            source=filename,
            authors=authors,
            pdf_bytes=data if len(data) <= _PDF_BYTES_LIMIT else None,
        )

    def _parse_arxiv(self, source: str) -> Paper:
        try:
            import arxiv
        except ImportError:
            raise ImportError("arxiv library is required: pip install arxiv")

        arxiv_id = _extract_arxiv_id(source)
        client = arxiv.Client()
        search = arxiv.Search(id_list=[arxiv_id])
        results = list(client.results(search))

        if not results:
            raise ValueError(f"No paper found for arXiv ID: {arxiv_id}")

        result = results[0]

        # Download PDF for full text
        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = result.download_pdf(dirpath=tmpdir)
            full_text, sections = _parse_pdf_path(str(pdf_path))
            raw_bytes = Path(pdf_path).read_bytes()

        title = result.title
        abstract = result.summary
        authors = [a.name for a in result.authors]
        year = result.published.year if result.published else None

        return Paper(
            title=title,
            abstract=abstract,
            full_text=full_text,
            sections=sections,
            source_type="arxiv",
            source=source,
            authors=authors,
            year=year,
            arxiv_id=arxiv_id,
            pdf_bytes=raw_bytes if len(raw_bytes) <= _PDF_BYTES_LIMIT else None,
        )

    def _parse_local_pdf(self, path: str) -> Paper:
        if not os.path.isfile(path):
            raise FileNotFoundError(f"PDF not found: {path}")
        full_text, sections = _parse_pdf_path(path)
        title, abstract = _extract_title_abstract(full_text)
        authors = _extract_authors_from_text(full_text)
        raw_bytes = Path(path).read_bytes()
        return Paper(
            title=title or Path(path).stem,
            abstract=abstract,
            full_text=full_text,
            sections=sections,
            source_type="pdf",
            source=path,
            authors=authors,
            pdf_bytes=raw_bytes if len(raw_bytes) <= _PDF_BYTES_LIMIT else None,
        )

    def _parse_url(self, url: str) -> Paper:
        """Fetch a web page and extract text (fallback for non-arXiv URLs)."""
        try:
            import httpx
            from bs4 import BeautifulSoup
        except ImportError:
            raise ImportError("httpx and beautifulsoup4 are required")

        response = httpx.get(url, follow_redirects=True, timeout=30)
        response.raise_for_status()

        content_type = response.headers.get("content-type", "")
        if "pdf" in content_type:
            full_text, sections = _parse_pdf_bytes(response.content)
            title, abstract = _extract_title_abstract(full_text)
            return Paper(
                title=title or url,
                abstract=abstract,
                full_text=full_text,
                sections=sections,
                source_type="pdf",
                source=url,
            )

        soup = BeautifulSoup(response.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer"]):
            tag.decompose()
        text = soup.get_text(separator="\n")
        title_tag = soup.find("title")
        title = title_tag.get_text().strip() if title_tag else url
        return Paper(
            title=title,
            abstract="",
            full_text=text[:30000],
            sections={"Content": text[:20000]},
            source_type="url",
            source=url,
        )

    def _parse_text(self, text: str) -> Paper:
        """Parse raw text as a paper."""
        title, abstract = _extract_title_abstract(text)
        return Paper(
            title=title or "Unknown Paper",
            abstract=abstract,
            full_text=text,
            sections=_extract_sections(text),
            source_type="text",
            source=text[:80] + "..." if len(text) > 80 else text,
        )
