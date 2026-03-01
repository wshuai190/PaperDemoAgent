"""Tests for paper parser."""

import pytest
from unittest.mock import patch, MagicMock

from paper_demo_agent.paper.parser import detect_source_type, PaperParser
from paper_demo_agent.paper.models import Paper


class TestDetectSourceType:
    def test_arxiv_id_short(self):
        assert detect_source_type("1706.03762") == "arxiv"

    def test_arxiv_id_with_version(self):
        assert detect_source_type("1706.03762v5") == "arxiv"

    def test_arxiv_url(self):
        assert detect_source_type("https://arxiv.org/abs/1706.03762") == "arxiv"

    def test_arxiv_url_no_scheme(self):
        assert detect_source_type("arxiv.org/abs/1706.03762") == "arxiv"

    def test_pdf_extension(self):
        assert detect_source_type("/tmp/paper.pdf") == "pdf"

    def test_pdf_extension_uppercase(self):
        assert detect_source_type("/tmp/paper.PDF") == "pdf"

    def test_http_url(self):
        assert detect_source_type("https://example.com/paper") == "url"

    def test_raw_text(self):
        assert detect_source_type("This is the title of a paper") == "text"


class TestPaperParser:
    def test_parse_text(self):
        parser = PaperParser()
        text = "Abstract\nThis paper presents a new method for doing things."
        paper = parser._parse_text(text)
        assert isinstance(paper, Paper)
        assert paper.source_type == "text"
        assert paper.full_text == text

    def test_extract_sections(self):
        from paper_demo_agent.paper.parser import _extract_sections
        text = "INTRODUCTION\nThis is the intro.\n\nMETHOD\nThis is the method."
        sections = _extract_sections(text)
        assert isinstance(sections, dict)

    def test_extract_title_abstract(self):
        from paper_demo_agent.paper.parser import _extract_title_abstract
        text = "Attention Is All You Need\n\nAbstract\nWe propose a new model architecture."
        title, abstract = _extract_title_abstract(text)
        assert isinstance(title, str)
        assert isinstance(abstract, str)

    def test_extract_arxiv_id(self):
        from paper_demo_agent.paper.parser import _extract_arxiv_id
        assert _extract_arxiv_id("1706.03762") == "1706.03762"
        assert _extract_arxiv_id("https://arxiv.org/abs/1706.03762") == "1706.03762"
        assert _extract_arxiv_id("arxiv.org/abs/2301.00001v3") == "2301.00001v3"
