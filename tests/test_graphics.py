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

    def test_cnn_architecture_basic(self):
        from paper_demo_agent.graphics.architecture_templates import cnn_architecture
        svg = cnn_architecture([
            {"type": "input",  "label": "Input 224x224"},
            {"type": "conv",   "label": "Conv 3x3"},
            {"type": "pool",   "label": "MaxPool 2x2"},
            {"type": "fc",     "label": "FC 1024"},
            {"type": "output", "label": "Softmax"},
        ])
        assert "<svg" in svg
        assert "CNN Architecture" in svg
        assert "Conv 3x3" in svg
        assert "MaxPool 2x2" in svg

    def test_cnn_architecture_empty(self):
        from paper_demo_agent.graphics.architecture_templates import cnn_architecture
        svg = cnn_architecture([])
        assert "<svg" in svg

    def test_rnn_cell_lstm(self):
        from paper_demo_agent.graphics.architecture_templates import rnn_cell
        svg = rnn_cell(cell_type="lstm")
        assert "<svg" in svg
        assert "LSTM Cell" in svg
        assert "Forget" in svg
        assert "c_" in svg  # cell state label

    def test_rnn_cell_gru(self):
        from paper_demo_agent.graphics.architecture_templates import rnn_cell
        svg = rnn_cell(cell_type="gru")
        assert "<svg" in svg
        assert "GRU Cell" in svg
        assert "Update" in svg

    def test_residual_block_basic(self):
        from paper_demo_agent.graphics.architecture_templates import residual_block
        svg = residual_block(num_layers=2)
        assert "<svg" in svg
        assert "Residual Block" in svg
        assert "Add & ReLU" in svg
        assert "skip" in svg

    def test_residual_block_bottleneck(self):
        from paper_demo_agent.graphics.architecture_templates import residual_block
        svg = residual_block(num_layers=3)
        assert "<svg" in svg
        assert "Conv 1x1" in svg or "Conv 3x3" in svg or "Conv" in svg

    def test_multi_head_attention_detail(self):
        from paper_demo_agent.graphics.architecture_templates import multi_head_attention_detail
        svg = multi_head_attention_detail(num_heads=4, d_k=64, d_v=64)
        assert "<svg" in svg
        assert "Multi-Head Attention" in svg
        assert "Head 1" in svg
        assert "Head 4" in svg
        assert "Concat" in svg

    def test_gan_architecture(self):
        from paper_demo_agent.graphics.architecture_templates import gan_architecture
        svg = gan_architecture(
            ["Noise z", "Dense 256", "Output Image"],
            ["Input Image", "Conv 4x4", "Real/Fake"],
        )
        assert "<svg" in svg
        assert "Generator" in svg
        assert "Discriminator" in svg
        assert "fake" in svg


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

    def test_line_chart_js(self):
        from paper_demo_agent.graphics.chart_templates import line_chart_js, CHART_JS_CDN
        html = line_chart_js(
            {"Train Loss": [2.3, 1.8, 1.4], "Val Loss": [2.5, 2.0, 1.7]},
            labels=["1", "2", "3"],
            title="Training Curves",
            y_label="Loss",
        )
        assert CHART_JS_CDN in html
        assert "lineChart_" in html
        assert "Train Loss" in html
        assert "Val Loss" in html
        assert "type: 'line'" in html

    def test_line_chart_js_single_series(self):
        from paper_demo_agent.graphics.chart_templates import line_chart_js
        html = line_chart_js({"Acc": [0.6, 0.7, 0.8]}, ["1", "2", "3"], "Accuracy")
        assert "<canvas" in html
        assert "Accuracy" in html

    def test_heatmap_d3(self):
        from paper_demo_agent.graphics.chart_templates import heatmap_d3, D3_CDN
        html = heatmap_d3(
            [[0.9, 0.1], [0.2, 0.8]],
            row_labels=["cat", "dog"],
            col_labels=["cat", "dog"],
            title="Confusion Matrix",
        )
        assert D3_CDN in html
        assert "heatmap_" in html
        assert "Confusion Matrix" in html
        assert "cat" in html
        assert "dog" in html

    def test_heatmap_d3_normalisation(self):
        # Values > 1 should be auto-normalised without errors
        from paper_demo_agent.graphics.chart_templates import heatmap_d3
        html = heatmap_d3(
            [[100, 20], [30, 90]],
            row_labels=["A", "B"],
            col_labels=["X", "Y"],
            title="Big Values",
        )
        assert "heatmap_" in html

    def test_metric_dashboard_html(self):
        from paper_demo_agent.graphics.chart_templates import metric_dashboard_html
        html = metric_dashboard_html({
            "NDCG@10": {"value": "0.421", "delta": "+3.2%"},
            "MAP":     {"value": "0.318", "delta": "-0.5%", "delta_label": "vs BM25"},
            "Recall":  {"value": "0.892", "subtitle": "Recall@100"},
        })
        assert "NDCG@10" in html
        assert "0.421" in html
        assert "+3.2%" in html
        assert "#22c55e" in html   # positive delta green
        assert "#ef4444" in html   # negative delta red
        assert "vs BM25" in html
        assert "Recall@100" in html
        assert "grid-template-columns" in html


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

    def test_mermaid_training_loop_default(self):
        from paper_demo_agent.graphics.mermaid_patterns import mermaid_training_loop
        md = mermaid_training_loop()
        assert "%%{init:" in md
        assert "flowchart LR" in md
        assert "Forward Pass" in md
        assert "Backward Pass" in md
        assert "S0 --> S1" in md

    def test_mermaid_training_loop_custom(self):
        from paper_demo_agent.graphics.mermaid_patterns import mermaid_training_loop
        md = mermaid_training_loop(["Load", "Forward", "Loss", "Step"])
        assert "Load" in md
        assert "Step" in md
        assert "S0 --> S1" in md

    def test_mermaid_training_loop_with_question(self):
        from paper_demo_agent.graphics.mermaid_patterns import mermaid_training_loop
        md = mermaid_training_loop(["Batch", "Forward", "Converged?"])
        assert "Yes" in md
        assert "No" in md
        assert "End Training" in md

    def test_mermaid_comparison(self):
        from paper_demo_agent.graphics.mermaid_patterns import mermaid_comparison
        md = mermaid_comparison(
            ["BM25", "Re-rank"],
            ["Dense", "Cross-Encoder"],
            labels=("Old", "New"),
        )
        assert "%%{init:" in md
        assert "flowchart TD" in md
        assert '"Old"' in md
        assert '"New"' in md
        assert "A0" in md and "B0" in md
        assert "#6366f1" in md   # proposed accent colour

    def test_mermaid_comparison_default_labels(self):
        from paper_demo_agent.graphics.mermaid_patterns import mermaid_comparison
        md = mermaid_comparison(["A"], ["B"])
        assert "Baseline" in md
        assert "Proposed" in md


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
        # new additions
        assert "cnn_architecture" in GRAPHICS_REFERENCE
        assert "rnn_cell" in GRAPHICS_REFERENCE
        assert "residual_block" in GRAPHICS_REFERENCE
        assert "multi_head_attention_detail" in GRAPHICS_REFERENCE
        assert "gan_architecture" in GRAPHICS_REFERENCE
        assert "line_chart_js" in GRAPHICS_REFERENCE
        assert "heatmap_d3" in GRAPHICS_REFERENCE
        assert "metric_dashboard_html" in GRAPHICS_REFERENCE
        assert "mermaid_training_loop" in GRAPHICS_REFERENCE
        assert "mermaid_comparison" in GRAPHICS_REFERENCE

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
