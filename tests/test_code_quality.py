"""Tests for the CodeQuality skill utility module and _cdn_reference() in BaseSkill."""

import pytest

from paper_demo_agent.skills.code_quality import (
    CodeQuality,
    VERIFIED_CDNS,
    DARK_THEME_CSS,
    html_boilerplate,
    REVEALJS_VERSION,
    CHARTJS_VERSION,
    D3_VERSION,
    MERMAID_VERSION,
    KATEX_VERSION,
)


# ─── VERIFIED_CDNS dict ───────────────────────────────────────────────────────

class TestVerifiedCdns:
    def test_all_required_keys_present(self):
        required = [
            "revealjs_js", "revealjs_css", "revealjs_theme_black",
            "chartjs", "d3_v7", "mermaid_esm",
            "katex_css", "katex_js", "katex_auto_render",
            "prism_css", "prism_js",
            "distill_template",
            "inter_font", "jetbrains_mono",
        ]
        for key in required:
            assert key in VERIFIED_CDNS, f"Missing CDN key: {key}"

    def test_revealjs_version_pinned(self):
        assert REVEALJS_VERSION in VERIFIED_CDNS["revealjs_js"]
        assert REVEALJS_VERSION in VERIFIED_CDNS["revealjs_css"]

    def test_chartjs_version_pinned(self):
        assert CHARTJS_VERSION in VERIFIED_CDNS["chartjs"]

    def test_d3_version_pinned(self):
        assert D3_VERSION in VERIFIED_CDNS["d3_v7"]

    def test_mermaid_version_pinned(self):
        assert f"@{MERMAID_VERSION}" in VERIFIED_CDNS["mermaid_esm"]

    def test_katex_version_pinned(self):
        assert KATEX_VERSION in VERIFIED_CDNS["katex_css"]
        assert KATEX_VERSION in VERIFIED_CDNS["katex_js"]

    def test_all_urls_are_https(self):
        for key, url in VERIFIED_CDNS.items():
            assert url.startswith("https://"), f"Non-HTTPS URL for {key}: {url}"

    def test_no_empty_urls(self):
        for key, url in VERIFIED_CDNS.items():
            assert url.strip(), f"Empty URL for CDN key: {key}"


# ─── DARK_THEME_CSS ──────────────────────────────────────────────────────────

class TestDarkThemeCss:
    def test_contains_css_variables(self):
        assert "--bg:" in DARK_THEME_CSS
        assert "--accent:" in DARK_THEME_CSS
        assert "--text:" in DARK_THEME_CSS

    def test_has_dark_background(self):
        # The default background should be dark (#0d1117 is GitHub dark)
        assert "#0d1117" in DARK_THEME_CSS

    def test_has_font_family(self):
        assert "font-family" in DARK_THEME_CSS
        assert "Inter" in DARK_THEME_CSS

    def test_has_box_sizing_reset(self):
        assert "box-sizing" in DARK_THEME_CSS

    def test_has_container_class(self):
        assert ".container" in DARK_THEME_CSS


# ─── html_boilerplate() ──────────────────────────────────────────────────────

class TestHtmlBoilerplate:
    def test_presentation_includes_revealjs(self):
        html = html_boilerplate("presentation", title="Test Deck")
        assert "reveal.js" in html.lower()
        assert "Reveal.initialize" in html
        assert REVEALJS_VERSION in html

    def test_presentation_includes_katex(self):
        html = html_boilerplate("presentation", title="Test")
        assert "katex" in html.lower()

    def test_presentation_title_in_html(self):
        html = html_boilerplate("presentation", title="My Paper Talk")
        assert "My Paper Talk" in html

    def test_website_includes_chartjs(self):
        html = html_boilerplate("website", title="Project Page")
        assert "chart.js" in html.lower() or CHARTJS_VERSION in html

    def test_website_includes_d3(self):
        html = html_boilerplate("website", title="Project Page")
        assert "d3" in html.lower()

    def test_website_has_styles_css_link(self):
        html = html_boilerplate("website", title="Test")
        assert "styles.css" in html

    def test_website_has_script_js_link(self):
        html = html_boilerplate("website", title="Test")
        assert "script.js" in html

    def test_flowchart_includes_mermaid(self):
        html = html_boilerplate("flowchart", title="Pipeline")
        assert "mermaid" in html.lower()
        assert f"@{MERMAID_VERSION}" in html

    def test_generic_form_returns_valid_html(self):
        html = html_boilerplate("app", title="Generic")
        assert "<!DOCTYPE html>" in html
        assert "<html" in html
        assert "</html>" in html

    def test_all_forms_have_doctype(self):
        for form in ["presentation", "website", "page_blog", "flowchart", "app"]:
            html = html_boilerplate(form, title="Test")
            assert "<!DOCTYPE html>" in html, f"Missing DOCTYPE for form: {form}"

    def test_all_forms_have_viewport_meta(self):
        for form in ["presentation", "website", "page_blog", "flowchart", "app"]:
            html = html_boilerplate(form, title="Test")
            assert 'name="viewport"' in html, f"Missing viewport meta for form: {form}"


# ─── CodeQuality object ───────────────────────────────────────────────────────

class TestCodeQualityObject:
    def setup_method(self):
        self.cq = CodeQuality()

    def test_cdn_returns_correct_url(self):
        url = self.cq.cdn("chartjs")
        assert "chart.js" in url.lower()
        assert CHARTJS_VERSION in url

    def test_cdn_raises_for_unknown_key(self):
        with pytest.raises(KeyError, match="Unknown CDN key"):
            self.cq.cdn("nonexistent_library_xyz")

    def test_all_cdns_returns_dict(self):
        d = self.cq.all_cdns()
        assert isinstance(d, dict)
        assert len(d) >= 10

    def test_all_cdns_is_copy(self):
        d1 = self.cq.all_cdns()
        d2 = self.cq.all_cdns()
        d1["test_key"] = "test_value"
        assert "test_key" not in d2

    def test_dark_theme_css(self):
        css = self.cq.dark_theme_css()
        assert "--bg:" in css
        assert len(css) > 100

    def test_html_boilerplate_presentation(self):
        html = self.cq.html_boilerplate("presentation", title="Test")
        assert "Reveal" in html

    def test_html_boilerplate_website(self):
        html = self.cq.html_boilerplate("website", title="GPT-4 Page")
        assert "GPT-4 Page" in html

    def test_revealjs_init_script_default(self):
        script = self.cq.revealjs_init_script()
        assert "Reveal.initialize" in script
        assert "RevealHighlight" in script
        assert "RevealMath.KaTeX" in script
        assert "hash" in script

    def test_revealjs_init_script_custom_plugins(self):
        script = self.cq.revealjs_init_script(plugins=["RevealHighlight"])
        assert "RevealHighlight" in script
        assert "RevealNotes" not in script

    def test_chartjs_snippet_basic(self):
        snippet = self.cq.chartjs_snippet(canvas_id="chart1", chart_type="bar")
        assert "chart1" in snippet
        assert "new Chart" in snippet
        assert "'bar'" in snippet

    def test_chartjs_snippet_custom_data(self):
        snippet = self.cq.chartjs_snippet(
            canvas_id="myChart",
            labels=["BERT", "GPT-2", "T5"],
            data=[88.5, 85.1, 91.2],
            label="F1 Score",
        )
        assert "BERT" in snippet
        assert "F1 Score" in snippet
        assert "88.5" in snippet

    def test_repr(self):
        assert "CodeQuality" in repr(self.cq)
        assert "cdns=" in repr(self.cq)


# ─── BaseSkill._cdn_reference() integration ──────────────────────────────────

class TestBaseSkillCdnReference:
    def test_cdn_reference_returns_code_quality(self):
        from paper_demo_agent.skills.base import BaseSkill
        from paper_demo_agent.skills.general_qa import GeneralQASkill
        skill = GeneralQASkill()
        cq = skill._cdn_reference()
        assert isinstance(cq, CodeQuality)

    def test_cdn_reference_has_revealjs(self):
        from paper_demo_agent.skills.general_qa import GeneralQASkill
        skill = GeneralQASkill()
        cq = skill._cdn_reference()
        url = cq.cdn("revealjs_js")
        assert REVEALJS_VERSION in url

    def test_cdn_reference_has_chartjs(self):
        from paper_demo_agent.skills.general_qa import GeneralQASkill
        skill = GeneralQASkill()
        cq = skill._cdn_reference()
        url = cq.cdn("chartjs")
        assert CHARTJS_VERSION in url

    def test_cdn_reference_fresh_instance_each_call(self):
        from paper_demo_agent.skills.general_qa import GeneralQASkill
        skill = GeneralQASkill()
        cq1 = skill._cdn_reference()
        cq2 = skill._cdn_reference()
        # Should return independent instances
        assert cq1 is not cq2
