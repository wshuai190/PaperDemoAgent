"""Graphics primitives — pre-baked SVG / chart / TikZ / Mermaid templates.

The LLM agent uses these to compose high-quality visuals instead of
improvising diagram code from scratch.
"""

# ── SVG primitives ────────────────────────────────────────────────────
from paper_demo_agent.graphics.svg_primitives import (
    rounded_box,
    arrow,
    flow_arrow,
    layer_stack,
    parallel_blocks,
    connection_lines,
    dashed_box,
    svg_wrapper,
    BG, BLUE, INDIGO, AMBER, GREEN, RED, TEXT, MUTED, SLATE, SLATE_LT,
)

# ── Architecture templates ────────────────────────────────────────────
from paper_demo_agent.graphics.architecture_templates import (
    encoder_decoder,
    transformer_block,
    pipeline_flow,
    comparison_diagram,
    attention_visualization,
    cnn_architecture,
    rnn_cell,
    residual_block,
    multi_head_attention_detail,
    gan_architecture,
)

# ── Chart templates ───────────────────────────────────────────────────
from paper_demo_agent.graphics.chart_templates import (
    bar_chart_js,
    comparison_table_html,
    radar_chart_js,
    d3_grouped_bar,
    results_card_html,
    line_chart_js,
    heatmap_d3,
    metric_dashboard_html,
    CHART_JS_CDN,
    D3_CDN,
)

# ── TikZ templates ────────────────────────────────────────────────────
from paper_demo_agent.graphics.tikz_templates import (
    tikz_flow_diagram,
    tikz_block_diagram,
    tikz_encoder_decoder,
    tikz_comparison_table,
    TIKZ_COLOR_DEFS,
)

# ── Mermaid patterns ──────────────────────────────────────────────────
from paper_demo_agent.graphics.mermaid_patterns import (
    mermaid_pipeline,
    mermaid_architecture,
    mermaid_class_diagram,
    mermaid_sequence,
    mermaid_training_loop,
    mermaid_comparison,
)

# ── Dark theme ────────────────────────────────────────────────────────
from paper_demo_agent.graphics.themes import DARK_THEME_CSS

__all__ = [
    # svg primitives
    "rounded_box", "arrow", "flow_arrow", "layer_stack", "parallel_blocks",
    "connection_lines", "dashed_box", "svg_wrapper",
    "BG", "BLUE", "INDIGO", "AMBER", "GREEN", "RED", "TEXT", "MUTED",
    "SLATE", "SLATE_LT",
    # architecture templates
    "encoder_decoder", "transformer_block", "pipeline_flow",
    "comparison_diagram", "attention_visualization",
    "cnn_architecture", "rnn_cell", "residual_block",
    "multi_head_attention_detail", "gan_architecture",
    # chart templates
    "bar_chart_js", "comparison_table_html", "radar_chart_js",
    "d3_grouped_bar", "results_card_html",
    "line_chart_js", "heatmap_d3", "metric_dashboard_html",
    "CHART_JS_CDN", "D3_CDN",
    # tikz templates
    "tikz_flow_diagram", "tikz_block_diagram", "tikz_encoder_decoder",
    "tikz_comparison_table", "TIKZ_COLOR_DEFS",
    # mermaid patterns
    "mermaid_pipeline", "mermaid_architecture", "mermaid_class_diagram",
    "mermaid_sequence", "mermaid_training_loop", "mermaid_comparison",
    # reference constant
    "GRAPHICS_REFERENCE",
    # dark theme
    "DARK_THEME_CSS",
]


# ══════════════════════════════════════════════════════════════════════
# GRAPHICS_REFERENCE — injected into skill prompts so the LLM knows
# which functions are available and how to call them.
# ══════════════════════════════════════════════════════════════════════

GRAPHICS_REFERENCE = r"""
━━ GRAPHICS PRIMITIVES REFERENCE ━━

You have access to pre-built graphics functions via `from paper_demo_agent.graphics import *`.
Use these in `execute_python` to generate SVG files, or reference the patterns for inline use.

DARK THEME CSS:
  `DARK_THEME_CSS` — a complete production-ready CSS string for dark-themed HTML demos.
  Usage: write_file('styles.css', DARK_THEME_CSS) — then <link rel="stylesheet" href="styles.css">
  Includes: CSS variables, reset, typography, cards, buttons, forms, nav, badges, tables,
            progress bars, code blocks with syntax tokens, hero, tabs, tooltips, scrollbar,
            utilities, responsive breakpoints (xs/sm/md/lg/xl).
  All bg/accent colours match the SVG primitives palette.

COLOR SCHEME (dark theme):
  Background : #09090b
  Blue/input : #3b82f6    Indigo/transform : #6366f1
  Amber/decision : #f59e0b   Green/output : #22c55e   Red/loss : #ef4444
  Text white : #fafafa    Text muted : #94a3b8
  Lines      : #475569    Lines light : #64748b

─── SVG Primitives (paper_demo_agent.graphics.svg_primitives) ───

  rounded_box(x, y, w, h, label, color='#3b82f6', text_color='#fff', rx=8)
      → SVG rect + centred text label
      Ex: rounded_box(50, 50, 160, 40, "Encoder", color="#6366f1")

  arrow(x1, y1, x2, y2, color='#64748b', stroke=2, marker=True)
      → line with optional arrowhead
      Ex: arrow(100, 70, 250, 70)

  flow_arrow(x1, y1, x2, y2, label='', color='#64748b')
      → arrow with text label at midpoint
      Ex: flow_arrow(100, 50, 300, 50, label="embeddings")

  layer_stack(x, y, layers, spacing=8, width=160)
      → vertical stack of rounded boxes (encoder/decoder layers)
      Ex: layer_stack(50, 50, ["Layer 1", "Layer 2", "Layer 3"])

  parallel_blocks(x, y, blocks, spacing=20, width=120)
      → horizontal row of boxes (multi-head attention heads)
      Ex: parallel_blocks(50, 50, ["Head 1", "Head 2", "Head 3"])

  connection_lines(sources, targets, color='#475569')
      → lines from every (x,y) in sources to every (x,y) in targets
      Ex: connection_lines([(100,80),(200,80)], [(150,160)])

  dashed_box(x, y, w, h, label, color='#475569')
      → dashed border container for grouping
      Ex: dashed_box(30, 30, 300, 200, "Encoder Block")

  svg_wrapper(content, width=800, height=600, bg='#09090b', viewBox=None)
      → wraps content in complete <svg> with arrowhead defs
      Ex: svg_wrapper(rounded_box(50,50,160,40,"Hi"), width=300, height=140)

─── Architecture Templates (paper_demo_agent.graphics.architecture_templates) ───

  encoder_decoder(encoder_layers, decoder_layers, labels=None)
      → complete encoder-decoder SVG (Transformer style)

  transformer_block(num_heads=8, d_model=512, d_ff=2048)
      → single transformer block SVG (attention + FFN + residual)

  pipeline_flow(steps, title='')
      → left-to-right pipeline diagram
      Ex: pipeline_flow(["Tokenize","Embed","Encode","Decode"], title="Pipeline")

  comparison_diagram(method_a, method_b, labels=('Previous','Proposed'))
      → side-by-side architecture comparison

  attention_visualization(query_labels, key_labels, weights_matrix=None)
      → attention weight heatmap as SVG

  cnn_architecture(layers_config)
      → CNN with conv/pool/fc layers (featuremap stacked boxes for conv/pool)
      layers_config: [{"type":"conv","label":"Conv 3×3","size":60}, ...]
      types: "input", "conv", "pool", "fc", "output"
      Ex: cnn_architecture([{"type":"input","label":"224×224"},{"type":"conv","label":"64ch"},{"type":"pool","label":"MaxPool"},{"type":"fc","label":"FC 1024"},{"type":"output","label":"Softmax"}])

  rnn_cell(cell_type='lstm')
      → LSTM or GRU cell diagram with gate annotations
      cell_type: "lstm" | "gru"
      Ex: rnn_cell("lstm")

  residual_block(num_layers=2)
      → Skip connection diagram (BasicBlock=2, Bottleneck=3)
      Ex: residual_block(num_layers=2)

  multi_head_attention_detail(num_heads=4, d_k=64, d_v=64)
      → Detailed MHA with Q/K/V projections per head + concat + linear
      Ex: multi_head_attention_detail(num_heads=8, d_k=64, d_v=64)

  gan_architecture(gen_layers, disc_layers)
      → Generator vs Discriminator side-by-side with fake image arrow
      Ex: gan_architecture(["Noise z","Dense 256","Conv 4×4","Image"],["Image","Conv 4×4","Dense 1","Real/Fake"])

─── Chart Templates (paper_demo_agent.graphics.chart_templates) ───
    Returns JS/HTML code strings for embedding in HTML demos.

  CHART_JS_CDN  → "https://cdn.jsdelivr.net/npm/chart.js@4/dist/chart.umd.min.js"
  D3_CDN        → "https://d3js.org/d3.v7.min.js"

  bar_chart_js(data, labels, title, colors=None, highlight_idx=0)
      → Chart.js bar chart (dark theme, highlighted bar for proposed method)

  comparison_table_html(headers, rows, highlight_row=0)
      → styled HTML table with highlighted row

  radar_chart_js(metrics, scores_dict, title)
      → Chart.js radar chart comparing methods on multiple metrics

  d3_grouped_bar(data, group_labels, series_labels, title)
      → D3.js grouped bar chart

  results_card_html(metric, value, delta, delta_label='vs SOTA')
      → metric card with big number + delta badge

  line_chart_js(data_series, labels, title, y_label='Value')
      → Chart.js multi-line chart for training curves / metrics over time
      data_series: {"Train Loss": [2.3,1.8,...], "Val Loss": [2.5,2.0,...]}
      Ex: line_chart_js({"Train":[2.3,1.5,0.9],"Val":[2.6,1.8,1.2]}, labels=["1","2","3"], title="Loss")

  heatmap_d3(matrix, row_labels, col_labels, title, color_scheme='Blues')
      → D3.js heatmap for attention/confusion/similarity matrices
      matrix: 2D list of floats (auto-normalised)
      color_scheme: "Blues", "Purples", "YlOrRd", "Greens", etc.
      Ex: heatmap_d3([[0.9,0.1],[0.2,0.8]], ["A","B"], ["X","Y"], "Attention")

  metric_dashboard_html(metrics_dict)
      → Grid of metric cards with values and delta badges
      metrics_dict: {"NDCG@10": {"value":"0.421","delta":"+3.2%","subtitle":"TREC DL"}, ...}
      Ex: metric_dashboard_html({"NDCG@10":{"value":"0.421","delta":"+3.2%"},"MAP":{"value":"0.318","delta":"+1.8%"}})

─── TikZ Templates (paper_demo_agent.graphics.tikz_templates) ───
    Returns LaTeX/TikZ code for Beamer slides.

  TIKZ_COLOR_DEFS → colour definition block for LaTeX preamble

  tikz_flow_diagram(steps, title='')
      → horizontal flow chart with arrows

  tikz_block_diagram(blocks, connections)
      → block diagram with labelled connections
      blocks: [{"id":"enc", "label":"Encoder", "color":"inputblue", "pos":"(0,0)"}, ...]
      connections: [("enc", "dec", "context"), ...]

  tikz_encoder_decoder(enc_layers, dec_layers)
      → encoder-decoder architecture

  tikz_comparison_table(headers, rows, highlight_row=0)
      → booktabs table with bold best result

─── Mermaid Patterns (paper_demo_agent.graphics.mermaid_patterns) ───
    Returns tested Mermaid v11 strings with dark theme init.

  mermaid_pipeline(steps)
      → LR flowchart pipeline

  mermaid_architecture(components, connections)
      → TD architecture with subgraphs
      components: {"Encoder": ["Self-Attn", "FFN"], ...}
      connections: [("0_1", "1_0", "context"), ...]

  mermaid_class_diagram(classes)
      → class diagram
      classes: [{"name":"Encoder", "attrs":["d_model: int"], "methods":["forward(x)"]}, ...]

  mermaid_sequence(actors, messages)
      → sequence diagram
      messages: [("Client", "Server", "POST /predict"), ...]

  mermaid_training_loop(steps=None)
      → Training pipeline flowchart (data→forward→loss→backward→update)
      Defaults to standard 6-stage loop; pass custom steps to override.
      Appends loop-back arrow automatically if last step ends with "?"
      Ex: mermaid_training_loop()
      Ex: mermaid_training_loop(["Load Batch","Forward","Loss","Backward","SGD Step","Converged?"])

  mermaid_comparison(method_a_steps, method_b_steps, labels=('Baseline','Proposed'))
      → Side-by-side method comparison as parallel subgraphs
      Baseline styled muted, proposed styled accent indigo
      Ex: mermaid_comparison(["BM25","Re-rank"],["Dense","Cross-Encoder"],labels=("BM25+CE","Ours"))

─── Usage via render_svg tool ───

  Call `render_svg` with a Python expression that uses these functions.
  The expression is evaluated and the resulting SVG string is returned.
  Example: render_svg(expr="pipeline_flow(['Input','Model','Output'], title='Demo')")
"""
