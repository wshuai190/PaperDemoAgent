"""Tests for the graphics primitives module."""

import pytest


# ═══════════════════════════════════════════════════════════════════════
# SVG Primitives
# ═══════════════════════════════════════════════════════════════════════

class TestSvgPrimitives:
    def test_rounded_box_structure(self):
        from paper_demo_agent.graphics.svg_primitives import rounded_box
        svg = rounded_box(10, 20, 100, 40, "Test")
        assert "<rect" in svg
        assert "<text" in svg
        assert "Test" in svg
        assert 'rx="8"' in svg

    def test_rounded_box_custom_color(self):
        from paper_demo_agent.graphics.svg_primitives import rounded_box
        svg = rounded_box(0, 0, 80, 30, "X", color="#ff0000", text_color="#000")
        assert '#ff0000' in svg
        assert '#000' in svg

    def test_arrow_with_marker(self):
        from paper_demo_agent.graphics.svg_primitives import arrow
        svg = arrow(0, 0, 100, 100)
        assert "<line" in svg
        assert 'marker-end="url(#arrowhead)"' in svg

    def test_arrow_without_marker(self):
        from paper_demo_agent.graphics.svg_primitives import arrow
        svg = arrow(0, 0, 100, 100, marker=False)
        assert "marker-end" not in svg

    def test_flow_arrow_with_label(self):
        from paper_demo_agent.graphics.svg_primitives import flow_arrow
        svg = flow_arrow(0, 0, 200, 0, label="data")
        assert "<line" in svg
        assert "data" in svg

    def test_flow_arrow_without_label(self):
        from paper_demo_agent.graphics.svg_primitives import flow_arrow
        svg = flow_arrow(0, 0, 200, 0)
        assert "<line" in svg
        # Only the arrow, no extra text
        assert svg.count("<text") == 0

    def test_layer_stack(self):
        from paper_demo_agent.graphics.svg_primitives import layer_stack
        svg = layer_stack(10, 10, ["A", "B", "C"])
        assert svg.count("<rect") == 3
        assert "A" in svg and "B" in svg and "C" in svg

    def test_parallel_blocks(self):
        from paper_demo_agent.graphics.svg_primitives import parallel_blocks
        svg = parallel_blocks(0, 0, ["H1", "H2", "H3"])
        assert svg.count("<rect") == 3
        assert "H1" in svg

    def test_connection_lines(self):
        from paper_demo_agent.graphics.svg_primitives import connection_lines
        svg = connection_lines([(0, 0), (100, 0)], [(50, 100)])
        # 2 sources × 1 target = 2 lines
        assert svg.count("<line") == 2

    def test_dashed_box(self):
        from paper_demo_agent.graphics.svg_primitives import dashed_box
        svg = dashed_box(0, 0, 200, 100, "Group")
        assert "stroke-dasharray" in svg
        assert "Group" in svg

    def test_svg_wrapper_valid(self):
        from paper_demo_agent.graphics.svg_primitives import svg_wrapper
        svg = svg_wrapper("<circle cx='50' cy='50' r='10' />", width=200, height=200)
        assert svg.startswith("<svg")
        assert svg.endswith("</svg>")
        assert "xmlns" in svg
        assert "arrowhead" in svg  # defs included
        assert "<circle" in svg

    def test_svg_wrapper_custom_viewbox(self):
        from paper_demo_agent.graphics.svg_primitives import svg_wrapper
        svg = svg_wrapper("", viewBox="0 0 1000 500")
        assert 'viewBox="0 0 1000 500"' in svg


# ═══════════════════════════════════════════════════════════════════════
# Architecture Templates
# ═══════════════════════════════════════════════════════════════════════

class TestArchitectureTemplates:
    def test_encoder_decoder_is_complete_svg(self):
        from paper_demo_agent.graphics.architecture_templates import encoder_decoder
        svg = encoder_decoder(["Self-Attn", "FFN"], ["Cross-Attn", "FFN"])
        assert svg.startswith("<svg")
        assert svg.endswith("</svg>")
        assert "Encoder" in svg
        assert "Decoder" in svg

    def test_transformer_block(self):
        from paper_demo_agent.graphics.architecture_templates import transformer_block
        svg = transformer_block(num_heads=4, d_model=256, d_ff=1024)
        assert "<svg" in svg
        assert "Multi-Head Attention" in svg
        assert "FFN" in svg
        assert "Layer Norm" in svg

    def test_pipeline_flow(self):
        from paper_demo_agent.graphics.architecture_templates import pipeline_flow
        svg = pipeline_flow(["A", "B", "C"], title="Test")
        assert "<svg" in svg
        assert "Test" in svg
        assert "A" in svg and "C" in svg

    def test_comparison_diagram(self):
        from paper_demo_agent.graphics.architecture_templates import comparison_diagram
        svg = comparison_diagram(["CNN", "Pool"], ["ViT", "MLP"],
                                 labels=("Old", "New"))
        assert "<svg" in svg
        assert "Old" in svg and "New" in svg

    def test_attention_visualization_default_weights(self):
        from paper_demo_agent.graphics.architecture_templates import attention_visualization
        svg = attention_visualization(["q1", "q2"], ["k1", "k2"])
        assert "<svg" in svg
        assert "Attention Weights" in svg

    def test_attention_visualization_custom_weights(self):
        from paper_demo_agent.graphics.architecture_templates import attention_visualization
        svg = attention_visualization(
            ["a", "b"], ["x", "y"],
            weights_matrix=[[0.9, 0.1], [0.3, 0.7]],
        )
        assert "0.90" in svg
        assert "0.70" in svg


# ═══════════════════════════════════════════════════════════════════════
# Chart Templates
# ═══════════════════════════════════════════════════════════════════════

class TestChartTemplates:
    def test_bar_chart_js(self):
        from paper_demo_agent.graphics.chart_templates import bar_chart_js, CHART_JS_CDN
        html = bar_chart_js([85, 91], ["BERT", "Ours"], "Accuracy")
        assert CHART_JS_CDN in html
        assert "barChart" in html
        assert "<canvas" in html

    def test_comparison_table_html(self):
        from paper_demo_agent.graphics.chart_templates import comparison_table_html
        html = comparison_table_html(
            ["Method", "Acc"],
            [["BERT", "85"], ["Ours", "91"]],
            highlight_row=1,
        )
        assert "<table" in html
        assert "highlight" in html
        assert "BERT" in html

    def test_radar_chart_js(self):
        from paper_demo_agent.graphics.chart_templates import radar_chart_js, CHART_JS_CDN
        html = radar_chart_js(
            ["Acc", "F1"],
            {"A": [80, 75], "B": [90, 88]},
            "Compare",
        )
        assert CHART_JS_CDN in html
        assert "radarChart" in html
        assert "radar" in html

    def test_d3_grouped_bar(self):
        from paper_demo_agent.graphics.chart_templates import d3_grouped_bar, D3_CDN
        html = d3_grouped_bar(
            [{"A": 80, "B": 90}],
            ["Acc"],
            ["A", "B"],
            "Results",
        )
        assert D3_CDN in html
        assert "grouped-bar" in html

    def test_results_card_html_positive(self):
        from paper_demo_agent.graphics.chart_templates import results_card_html
        html = results_card_html("Accuracy", "91.3%", "+2.1%")
        assert "91.3%" in html
        assert "+2.1%" in html
        assert "#22c55e" in html  # green for positive

    def test_results_card_html_negative(self):
        from paper_demo_agent.graphics.chart_templates import results_card_html
        html = results_card_html("Latency", "45ms", "-10ms")
        assert "#ef4444" in html  # red for negative

    def test_cdn_constants(self):
        from paper_demo_agent.graphics.chart_templates import CHART_JS_CDN, D3_CDN
        assert "chart.js@4" in CHART_JS_CDN
        assert "d3.v7" in D3_CDN


# ═══════════════════════════════════════════════════════════════════════
# TikZ Templates
# ═══════════════════════════════════════════════════════════════════════

class TestTikzTemplates:
    def test_tikz_flow_diagram(self):
        from paper_demo_agent.graphics.tikz_templates import tikz_flow_diagram
        tex = tikz_flow_diagram(["Input", "Process", "Output"], title="Flow")
        assert "\\begin{tikzpicture}" in tex
        assert "\\end{tikzpicture}" in tex
        assert "Input" in tex and "Output" in tex
        assert "Flow" in tex

    def test_tikz_block_diagram(self):
        from paper_demo_agent.graphics.tikz_templates import tikz_block_diagram
        tex = tikz_block_diagram(
            [{"id": "a", "label": "A", "color": "inputblue", "pos": "(0,0)"},
             {"id": "b", "label": "B", "color": "transformindigo", "pos": "(4,0)"}],
            [("a", "b", "data")],
        )
        assert "\\begin{tikzpicture}" in tex
        assert "data" in tex

    def test_tikz_encoder_decoder(self):
        from paper_demo_agent.graphics.tikz_templates import tikz_encoder_decoder
        tex = tikz_encoder_decoder(["Attn", "FFN"], ["Cross", "FFN"])
        assert "Encoder" in tex and "Decoder" in tex
        assert "context" in tex

    def test_tikz_comparison_table(self):
        from paper_demo_agent.graphics.tikz_templates import tikz_comparison_table
        tex = tikz_comparison_table(
            ["Method", "Acc"],
            [["BERT", "85"], ["Ours", "91"]],
            highlight_row=1,
        )
        assert "\\toprule" in tex
        assert "\\bottomrule" in tex
        assert "\\rowcolor" in tex
        assert "\\textbf{Ours}" in tex

    def test_tikz_color_defs(self):
        from paper_demo_agent.graphics.tikz_templates import TIKZ_COLOR_DEFS
        assert "\\definecolor{accent}" in TIKZ_COLOR_DEFS
        assert "6366f1" in TIKZ_COLOR_DEFS


# ═══════════════════════════════════════════════════════════════════════
# Mermaid Patterns
# ═══════════════════════════════════════════════════════════════════════

class TestMermaidPatterns:
    def test_mermaid_pipeline(self):
        from paper_demo_agent.graphics.mermaid_patterns import mermaid_pipeline
        md = mermaid_pipeline(["A", "B", "C"])
        assert "%%{init:" in md
        assert "'theme': 'dark'" in md
        assert "flowchart LR" in md
        assert "S0 --> S1" in md

    def test_mermaid_architecture(self):
        from paper_demo_agent.graphics.mermaid_patterns import mermaid_architecture
        md = mermaid_architecture(
            {"Enc": ["Attn", "FFN"]},
            [("0_0", "0_1", "forward")],
        )
        assert "flowchart TD" in md
        assert "subgraph Enc" in md
        assert "forward" in md

    def test_mermaid_class_diagram(self):
        from paper_demo_agent.graphics.mermaid_patterns import mermaid_class_diagram
        md = mermaid_class_diagram([
            {"name": "Model", "attrs": ["dim: int"], "methods": ["forward(x)"]},
        ])
        assert "classDiagram" in md
        assert "class Model" in md
        assert "+dim: int" in md

    def test_mermaid_sequence(self):
        from paper_demo_agent.graphics.mermaid_patterns import mermaid_sequence
        md = mermaid_sequence(
            ["A", "B"],
            [("A", "B", "hello")],
        )
        assert "sequenceDiagram" in md
        assert "participant A" in md
        assert "A->>+B: hello" in md


# ═══════════════════════════════════════════════════════════════════════
# __init__ exports and GRAPHICS_REFERENCE
# ═══════════════════════════════════════════════════════════════════════

class TestGraphicsInit:
    def test_graphics_reference_is_string(self):
        from paper_demo_agent.graphics import GRAPHICS_REFERENCE
        assert isinstance(GRAPHICS_REFERENCE, str)
        assert len(GRAPHICS_REFERENCE) > 500
        assert "rounded_box" in GRAPHICS_REFERENCE
        assert "pipeline_flow" in GRAPHICS_REFERENCE
        assert "bar_chart_js" in GRAPHICS_REFERENCE
        assert "tikz_flow_diagram" in GRAPHICS_REFERENCE
        assert "mermaid_pipeline" in GRAPHICS_REFERENCE

    def test_all_exports_importable(self):
        from paper_demo_agent.graphics import __all__
        import paper_demo_agent.graphics as g
        for name in __all__:
            assert hasattr(g, name), f"Missing export: {name}"


# ═══════════════════════════════════════════════════════════════════════
# Integration: render_svg tool & BaseSkill._graphics_reference
# ═══════════════════════════════════════════════════════════════════════

class TestIntegration:
    def test_render_svg_tool_exists(self):
        from paper_demo_agent.generation.tools import TOOLS
        names = [t["name"] for t in TOOLS]
        assert "render_svg" in names

    def test_render_svg_dispatch(self):
        from paper_demo_agent.generation.tools import dispatch_tool
        result = dispatch_tool(
            "render_svg",
            {"expr": "pipeline_flow(['A','B'], title='T')"},
            "/tmp",
        )
        assert "<svg" in result

    def test_render_svg_error_handling(self):
        from paper_demo_agent.generation.tools import dispatch_tool
        result = dispatch_tool("render_svg", {"expr": "1/0"}, "/tmp")
        assert "Error" in result or "error" in result

    def test_base_skill_graphics_reference(self):
        from paper_demo_agent.skills.base import BaseSkill
        assert hasattr(BaseSkill, "_graphics_reference")
        # Can't instantiate ABC, so test via a concrete subclass
        from paper_demo_agent.graphics import GRAPHICS_REFERENCE

        class DummySkill(BaseSkill):
            def get_system_prompt(self, *a, **kw):
                return ""
            def get_initial_message(self, *a, **kw):
                return ""

        skill = DummySkill()
        ref = skill._graphics_reference()
        assert ref == GRAPHICS_REFERENCE
