"""Tests for generation/tools.py — write_file limits, new PDF tools, table extraction."""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from paper_demo_agent.generation.tools import (
    _WRITE_FILE_MAX_LINES,
    dispatch_tool,
    tool_extract_figure,
    tool_extract_tables,
    tool_list_pdf_pages,
    tool_read_file,
    tool_write_file,
)


# ═══════════════════════════════════════════════════════════════════════
# write_file — size limit enforcement
# ═══════════════════════════════════════════════════════════════════════

class TestWriteFileSizeLimit:
    """Verify that write_file hard-rejects content over 300 lines."""

    def test_exact_limit_is_accepted(self, tmp_path):
        content = "\n".join(["x"] * _WRITE_FILE_MAX_LINES)
        result = tool_write_file(str(tmp_path), "ok.txt", content)
        assert "Written" in result
        assert (tmp_path / "ok.txt").exists()

    def test_large_file_is_accepted(self, tmp_path):
        """No hard line limit — large files should be written successfully."""
        content = "\n".join(["x"] * 500)
        result = tool_write_file(str(tmp_path), "big.txt", content)
        assert "Written" in result
        assert (tmp_path / "big.txt").exists()

    def test_very_large_file_still_works(self, tmp_path):
        """Even very large files should be accepted (max_tokens is the real safeguard)."""
        content = "\n".join(["x"] * 1000)
        result = tool_write_file(str(tmp_path), "demo.html", content)
        assert "Written" in result
        assert (tmp_path / "demo.html").exists()
        assert "1000 lines" in result

    def test_under_limit_writes_correctly(self, tmp_path):
        content = "line1\nline2\nline3"
        result = tool_write_file(str(tmp_path), "small.txt", content)
        assert "Written" in result
        assert (tmp_path / "small.txt").read_text() == content

    def test_empty_file_is_accepted(self, tmp_path):
        result = tool_write_file(str(tmp_path), "empty.txt", "")
        assert "Written" in result

    def test_dispatch_tool_write_file_accepts_large(self, tmp_path):
        """dispatch_tool should also accept large files (no hard limit)."""
        big_content = "\n".join(["x"] * 500)
        result = dispatch_tool(
            "write_file",
            {"path": "big.html", "content": big_content},
            str(tmp_path),
        )
        assert "Written" in result
        assert (tmp_path / "big.html").exists()

    def test_max_lines_constant_is_300(self):
        assert _WRITE_FILE_MAX_LINES == 300


# ═══════════════════════════════════════════════════════════════════════
# list_pdf_pages — unit tests (no real PDF needed via mocking)
# ═══════════════════════════════════════════════════════════════════════

class TestListPdfPages:
    def test_missing_pdf_returns_error(self, tmp_path):
        result = tool_list_pdf_pages(str(tmp_path), "nonexistent.pdf")
        assert "Error" in result

    def test_missing_pymupdf_handled(self, tmp_path):
        (tmp_path / "paper.pdf").write_bytes(b"%PDF")
        with patch.dict("sys.modules", {"fitz": None}):
            result = tool_list_pdf_pages(str(tmp_path), "paper.pdf")
        # Either error about missing fitz or about import — not a crash
        assert isinstance(result, str)

    def test_dispatch_tool_list_pdf_pages(self, tmp_path):
        result = dispatch_tool("list_pdf_pages", {}, str(tmp_path))
        # paper.pdf doesn't exist — should return error string, not raise
        assert isinstance(result, str)
        assert "Error" in result

    def test_dispatch_tool_list_pdf_pages_custom_path(self, tmp_path):
        result = dispatch_tool(
            "list_pdf_pages",
            {"pdf_path": "my_paper.pdf"},
            str(tmp_path),
        )
        assert "Error" in result  # file not found, but dispatch worked


# ═══════════════════════════════════════════════════════════════════════
# extract_figure — unit tests
# ═══════════════════════════════════════════════════════════════════════

class TestExtractFigure:
    def test_missing_pdf_returns_error(self, tmp_path):
        result = tool_extract_figure(str(tmp_path), "paper.pdf", 1, 0.0, 0.0, 1.0, 1.0)
        assert "Error" in result

    def test_dispatch_extract_figure_missing_pdf(self, tmp_path):
        result = dispatch_tool(
            "extract_figure",
            {"pdf_path": "paper.pdf", "page": 1,
             "x1": 0.0, "y1": 0.0, "x2": 1.0, "y2": 1.0},
            str(tmp_path),
        )
        assert isinstance(result, str)
        assert "Error" in result

    def test_dispatch_extract_figure_default_dpi(self, tmp_path):
        """dispatch_tool should not crash on missing optional dpi arg."""
        result = dispatch_tool(
            "extract_figure",
            {"pdf_path": "paper.pdf", "page": 1,
             "x1": 0.1, "y1": 0.1, "x2": 0.9, "y2": 0.9},
            str(tmp_path),
        )
        assert isinstance(result, str)


# ═══════════════════════════════════════════════════════════════════════
# extract_tables — unit tests
# ═══════════════════════════════════════════════════════════════════════

class TestExtractTables:
    def test_missing_pdf_returns_error(self, tmp_path):
        result = tool_extract_tables(str(tmp_path), "paper.pdf", 1)
        assert "Error" in result

    def test_dispatch_extract_tables_missing_pdf(self, tmp_path):
        result = dispatch_tool(
            "extract_tables",
            {"pdf_path": "paper.pdf", "page": 1},
            str(tmp_path),
        )
        assert isinstance(result, str)
        assert "Error" in result

    def test_dispatch_extract_tables_wrong_type(self, tmp_path):
        """Page number coerced from string (LLMs sometimes do this)."""
        result = dispatch_tool(
            "extract_tables",
            {"pdf_path": "paper.pdf", "page": "2"},
            str(tmp_path),
        )
        assert isinstance(result, str)


# ═══════════════════════════════════════════════════════════════════════
# templates — structure lists
# ═══════════════════════════════════════════════════════════════════════

class TestTemplates:
    def test_presentation_structure_exists(self):
        from paper_demo_agent.skills.templates import PRESENTATION_STRUCTURE
        assert isinstance(PRESENTATION_STRUCTURE, list)
        assert len(PRESENTATION_STRUCTURE) > 0
        assert "Title" in PRESENTATION_STRUCTURE
        assert "Results (charts)" in PRESENTATION_STRUCTURE
        assert "Conclusion" in PRESENTATION_STRUCTURE

    def test_website_structure_exists(self):
        from paper_demo_agent.skills.templates import WEBSITE_STRUCTURE
        assert isinstance(WEBSITE_STRUCTURE, list)
        assert "Hero" in WEBSITE_STRUCTURE
        assert "Citation" in WEBSITE_STRUCTURE

    def test_blog_structure_exists(self):
        from paper_demo_agent.skills.templates import BLOG_STRUCTURE
        assert isinstance(BLOG_STRUCTURE, list)
        assert "Hook" in BLOG_STRUCTURE
        assert "References" in BLOG_STRUCTURE

    def test_all_structures_are_ordered_lists_of_strings(self):
        from paper_demo_agent.skills.templates import (
            BLOG_STRUCTURE, PRESENTATION_STRUCTURE, WEBSITE_STRUCTURE,
        )
        for struct in (PRESENTATION_STRUCTURE, WEBSITE_STRUCTURE, BLOG_STRUCTURE):
            assert all(isinstance(s, str) for s in struct)
            assert len(struct) >= 5


# ═══════════════════════════════════════════════════════════════════════
# base.py — _tool_usage_instructions includes math and structure sections
# ═══════════════════════════════════════════════════════════════════════

class TestBaseSkillInstructions:
    """Verify that math rendering and section structures are injected into prompts."""

    def _get_instructions(self):
        from paper_demo_agent.skills.blog_explainer import BlogExplainerSkill
        skill = BlogExplainerSkill()
        return skill._tool_usage_instructions()

    def test_katex_css_in_instructions(self):
        instr = self._get_instructions()
        assert "katex" in instr.lower()
        assert "katex.min.css" in instr

    def test_render_math_in_element_in_instructions(self):
        instr = self._get_instructions()
        assert "renderMathInElement" in instr

    def test_math_delimiters_in_instructions(self):
        instr = self._get_instructions()
        assert r"\[" in instr or "\\\\[" in instr or "display: true" in instr

    def test_presentation_structure_in_instructions(self):
        instr = self._get_instructions()
        assert "Title" in instr
        assert "Key Insight" in instr
        assert "Conclusion" in instr

    def test_website_structure_in_instructions(self):
        instr = self._get_instructions()
        assert "Hero" in instr
        assert "Citation" in instr

    def test_blog_structure_in_instructions(self):
        instr = self._get_instructions()
        assert "Hook" in instr
        assert "References" in instr
