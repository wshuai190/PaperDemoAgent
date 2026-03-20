"""Higher-level SVG templates for common ML architecture diagrams.

Each function composes primitives from ``svg_primitives`` and returns a
complete, self-contained SVG string that can be written to a ``.svg`` file
or embedded in HTML.
"""

from __future__ import annotations
from typing import Optional

from paper_demo_agent.graphics.svg_primitives import (
    BG, BLUE, INDIGO, AMBER, GREEN, RED, TEXT, MUTED, SLATE, SLATE_LT,
    rounded_box, arrow, flow_arrow, layer_stack, parallel_blocks,
    dashed_box, svg_wrapper,
)


def encoder_decoder(encoder_layers: list[str], decoder_layers: list[str],
                    labels: Optional[dict[str, str]] = None) -> str:
    """Standard encoder-decoder architecture (e.g. Transformer).

    Example::

        encoder_decoder(
            ["Self-Attn", "FFN"] * 3,
            ["Cross-Attn", "Self-Attn", "FFN"] * 3,
        )
    """
    labels = labels or {}
    enc_label = labels.get("encoder", "Encoder")
    dec_label = labels.get("decoder", "Decoder")

    parts: list[str] = []

    # encoder stack
    enc_x, enc_y = 80, 80
    parts.append(dashed_box(enc_x - 20, enc_y - 30, 200,
                            len(encoder_layers) * 44 + 40, enc_label))
    parts.append(layer_stack(enc_x, enc_y, encoder_layers))

    # decoder stack
    dec_x = 380
    dec_y = 80
    parts.append(dashed_box(dec_x - 20, dec_y - 30, 200,
                            len(decoder_layers) * 44 + 40, dec_label))
    parts.append(layer_stack(dec_x, dec_y, decoder_layers))

    # connecting arrow
    enc_bottom = enc_y + len(encoder_layers) * 44 // 2
    dec_mid = dec_y + len(decoder_layers) * 44 // 2
    parts.append(flow_arrow(enc_x + 160, enc_bottom,
                            dec_x, dec_mid, label="context"))

    # input / output labels
    parts.append(rounded_box(enc_x, enc_y + len(encoder_layers) * 44 + 20,
                             160, 32, "Input", color=BLUE))
    parts.append(rounded_box(dec_x, dec_y + len(decoder_layers) * 44 + 20,
                             160, 32, "Output", color=GREEN))

    h = max(len(encoder_layers), len(decoder_layers)) * 44 + 140
    return svg_wrapper("\n".join(parts), width=620, height=h)


def transformer_block(num_heads: int = 8, d_model: int = 512,
                      d_ff: int = 2048) -> str:
    """Single transformer block: multi-head attention + FFN + layer-norm + residual.

    Example::

        transformer_block(num_heads=8, d_model=512, d_ff=2048)
    """
    parts: list[str] = []

    # input
    parts.append(rounded_box(220, 380, 160, 36, "Input", color=BLUE))
    parts.append(arrow(300, 380, 300, 350))

    # layer norm 1
    parts.append(rounded_box(220, 314, 160, 36, "Layer Norm", color=SLATE))
    parts.append(arrow(300, 314, 300, 284))

    # multi-head attention
    mha_label = f"Multi-Head Attention ({num_heads}h)"
    parts.append(rounded_box(180, 248, 240, 36, mha_label, color=INDIGO))
    parts.append(arrow(300, 248, 300, 218))

    # residual arrow (left side)
    parts.append(
        f'<path d="M 180 332 L 140 332 L 140 200 L 180 200" '
        f'fill="none" stroke="{SLATE_LT}" stroke-width="1.5" '
        f'stroke-dasharray="4 3" />'
    )
    parts.append(
        f'<text x="125" y="270" fill="{MUTED}" font-size="10" '
        f'text-anchor="middle" font-family="Inter,system-ui,sans-serif">+</text>'
    )

    # add & norm
    parts.append(rounded_box(220, 182, 160, 36, "Add & Norm", color=SLATE))
    parts.append(arrow(300, 182, 300, 152))

    # FFN
    ffn_label = f"FFN ({d_model}→{d_ff}→{d_model})"
    parts.append(rounded_box(180, 116, 240, 36, ffn_label, color=AMBER))
    parts.append(arrow(300, 116, 300, 86))

    # residual arrow (left side)
    parts.append(
        f'<path d="M 180 200 L 120 200 L 120 68 L 180 68" '
        f'fill="none" stroke="{SLATE_LT}" stroke-width="1.5" '
        f'stroke-dasharray="4 3" />'
    )
    parts.append(
        f'<text x="105" y="138" fill="{MUTED}" font-size="10" '
        f'text-anchor="middle" font-family="Inter,system-ui,sans-serif">+</text>'
    )

    # add & norm 2
    parts.append(rounded_box(220, 50, 160, 36, "Add & Norm", color=SLATE))
    parts.append(arrow(300, 50, 300, 24))

    # output
    parts.append(rounded_box(220, 0, 160, 24, "Output", color=GREEN))

    # title
    parts.append(
        f'<text x="300" y="440" text-anchor="middle" fill="{TEXT}" '
        f'font-family="Inter,system-ui,sans-serif" font-size="15" '
        f'font-weight="700">Transformer Block</text>'
    )

    return svg_wrapper("\n".join(parts), width=600, height=460)


def pipeline_flow(steps: list[str], title: str = "") -> str:
    """Left-to-right pipeline diagram.

    Example::

        pipeline_flow(["Tokenize", "Embed", "Encode", "Decode", "Output"],
                       title="Inference Pipeline")
    """
    box_w = 130
    box_h = 40
    gap = 60
    margin = 40
    title_h = 40 if title else 0
    total_w = len(steps) * box_w + (len(steps) - 1) * gap + margin * 2
    total_h = box_h + margin * 2 + title_h

    parts: list[str] = []
    if title:
        parts.append(
            f'<text x="{total_w / 2}" y="28" text-anchor="middle" '
            f'fill="{TEXT}" font-family="Inter,system-ui,sans-serif" '
            f'font-size="16" font-weight="700">{title}</text>'
        )

    colors = [BLUE, INDIGO, INDIGO, AMBER, GREEN]
    y = margin + title_h
    for i, step in enumerate(steps):
        x = margin + i * (box_w + gap)
        c = colors[i % len(colors)]
        parts.append(rounded_box(x, y, box_w, box_h, step, color=c))
        if i < len(steps) - 1:
            parts.append(arrow(x + box_w, y + box_h / 2,
                               x + box_w + gap, y + box_h / 2))

    return svg_wrapper("\n".join(parts), width=total_w, height=total_h)


def comparison_diagram(method_a: list[str], method_b: list[str],
                       labels: tuple[str, str] = ("Previous", "Proposed")) -> str:
    """Side-by-side architecture comparison.

    Example::

        comparison_diagram(
            ["CNN", "Pool", "FC"],
            ["Patch Embed", "Transformer", "MLP Head"],
            labels=("ResNet", "ViT"),
        )
    """
    col_w = 200
    gap = 80
    margin = 40
    title_h = 50
    total_w = col_w * 2 + gap + margin * 2

    parts: list[str] = []

    # labels
    lx = margin + col_w / 2
    rx = margin + col_w + gap + col_w / 2
    parts.append(
        f'<text x="{lx}" y="30" text-anchor="middle" fill="{MUTED}" '
        f'font-family="Inter,system-ui,sans-serif" font-size="14" '
        f'font-weight="600">{labels[0]}</text>'
    )
    parts.append(
        f'<text x="{rx}" y="30" text-anchor="middle" fill="{TEXT}" '
        f'font-family="Inter,system-ui,sans-serif" font-size="14" '
        f'font-weight="600">{labels[1]}</text>'
    )

    # left column (previous)
    parts.append(dashed_box(margin - 10, title_h - 10,
                            col_w + 20, len(method_a) * 48 + 20, ""))
    for i, step in enumerate(method_a):
        y = title_h + i * 48
        parts.append(rounded_box(margin, y, col_w, 36, step, color=SLATE))
        if i < len(method_a) - 1:
            parts.append(arrow(margin + col_w / 2, y + 36,
                               margin + col_w / 2, y + 48))

    # right column (proposed)
    rx_start = margin + col_w + gap
    parts.append(dashed_box(rx_start - 10, title_h - 10,
                            col_w + 20, len(method_b) * 48 + 20, ""))
    for i, step in enumerate(method_b):
        y = title_h + i * 48
        parts.append(rounded_box(rx_start, y, col_w, 36, step, color=INDIGO))
        if i < len(method_b) - 1:
            parts.append(arrow(rx_start + col_w / 2, y + 36,
                               rx_start + col_w / 2, y + 48))

    h = max(len(method_a), len(method_b)) * 48 + title_h + 40
    return svg_wrapper("\n".join(parts), width=total_w, height=h)


def cnn_architecture(layers_config: list[dict]) -> str:
    """CNN architecture with conv, pool, and fc layers.

    *layers_config* is a list of dicts with keys:
      - ``type``: "conv" | "pool" | "fc" | "input" | "output"
      - ``label``: display string (e.g. "Conv 3×3, 64")
      - ``size`` (optional): relative visual height (default 60)

    Example::

        cnn_architecture([
            {"type": "input",  "label": "Input\\n224×224×3"},
            {"type": "conv",   "label": "Conv 3×3\\n64 filters"},
            {"type": "pool",   "label": "MaxPool\\n2×2"},
            {"type": "conv",   "label": "Conv 3×3\\n128 filters"},
            {"type": "pool",   "label": "MaxPool\\n2×2"},
            {"type": "fc",     "label": "FC 1024"},
            {"type": "output", "label": "Softmax"},
        ])
    """
    _type_color = {
        "input":  BLUE,
        "conv":   INDIGO,
        "pool":   SLATE,
        "fc":     AMBER,
        "output": GREEN,
    }

    box_w, box_gap = 110, 50
    margin = 40
    title_h = 40
    max_h = 80

    parts: list[str] = []
    parts.append(
        f'<text x="{(len(layers_config) * (box_w + box_gap) + margin) / 2}" '
        f'y="26" text-anchor="middle" fill="{TEXT}" '
        f'font-family="Inter,system-ui,sans-serif" font-size="15" '
        f'font-weight="700">CNN Architecture</text>'
    )

    for i, layer in enumerate(layers_config):
        ltype = layer.get("type", "fc")
        label = layer.get("label", ltype)
        h = min(max_h, max(36, layer.get("size", 60)))
        color = _type_color.get(ltype, INDIGO)
        x = margin + i * (box_w + box_gap)
        y = title_h + (max_h - h) // 2

        # featuremap-style boxes for conv/pool
        if ltype in ("conv", "pool"):
            offset = 6
            for d in range(2, -1, -1):
                parts.append(
                    f'<rect x="{x + d * offset}" y="{y + d * offset}" '
                    f'width="{box_w}" height="{h}" rx="4" '
                    f'fill="{color}" opacity="{0.4 + d * 0.2:.1f}" />'
                )
            parts.append(
                f'<text x="{x + box_w / 2 + 6}" y="{y + h / 2 + 6}" '
                f'text-anchor="middle" dominant-baseline="central" '
                f'fill="#fafafa" font-family="Inter,system-ui,sans-serif" '
                f'font-size="11" font-weight="600">{label}</text>'
            )
        else:
            parts.append(rounded_box(x, y, box_w, h, label, color=color))

        if i < len(layers_config) - 1:
            mid_y = title_h + max_h / 2
            parts.append(arrow(x + box_w + (offset * 2 if ltype in ("conv", "pool") else 0),
                               mid_y, x + box_w + box_gap, mid_y))

    total_w = margin * 2 + len(layers_config) * (box_w + box_gap)
    total_h = title_h + max_h + margin
    return svg_wrapper("\n".join(parts), width=total_w, height=total_h)


def rnn_cell(cell_type: str = "lstm") -> str:
    """LSTM or GRU cell diagram with gate annotations.

    *cell_type* is either ``"lstm"`` (default) or ``"gru"``.

    Example::

        rnn_cell(cell_type="lstm")
        rnn_cell(cell_type="gru")
    """
    parts: list[str] = []
    title = cell_type.upper() + " Cell"

    if cell_type.lower() == "lstm":
        gates = [
            ("Forget\\nGate", RED,    "σ", 80,  100),
            ("Input\\nGate",  BLUE,   "σ", 220, 100),
            ("Cell\\nGate",   INDIGO, "tanh", 360, 100),
            ("Output\\nGate", GREEN,  "σ", 500, 100),
        ]
        # cell state line
        parts.append(
            f'<line x1="40" y1="70" x2="640" y2="70" '
            f'stroke="{AMBER}" stroke-width="2.5" '
            f'stroke-dasharray="6 3" />'
        )
        parts.append(
            f'<text x="50" y="58" fill="{AMBER}" '
            f'font-family="Inter,system-ui,sans-serif" font-size="11">c_{{t-1}}</text>'
        )
        parts.append(
            f'<text x="608" y="58" fill="{AMBER}" '
            f'font-family="Inter,system-ui,sans-serif" font-size="11">c_t</text>'
        )
        total_w, total_h = 700, 240
    else:  # gru
        gates = [
            ("Update\\nGate", BLUE,   "σ",    100, 100),
            ("Reset\\nGate",  RED,    "σ",    300, 100),
            ("New Gate",      INDIGO, "tanh", 500, 100),
        ]
        total_w, total_h = 660, 220

    # hidden state input/output
    parts.append(
        f'<text x="40" y="{total_h - 60}" fill="{MUTED}" '
        f'font-family="Inter,system-ui,sans-serif" font-size="12">h_{{t-1}}</text>'
    )
    parts.append(
        f'<text x="{total_w - 80}" y="{total_h - 60}" fill="{TEXT}" '
        f'font-family="Inter,system-ui,sans-serif" font-size="12">h_t</text>'
    )

    for label, color, act, gx, gy in gates:
        parts.append(rounded_box(gx, gy, 100, 70, f"{label}\\n({act})", color=color))
        parts.append(arrow(gx + 50, 80, gx + 50, gy))  # from cell state
        parts.append(arrow(gx + 50, gy + 70, gx + 50, gy + 100))  # down to combine

    # title
    parts.append(
        f'<text x="{total_w / 2}" y="30" text-anchor="middle" fill="{TEXT}" '
        f'font-family="Inter,system-ui,sans-serif" font-size="15" font-weight="700">'
        f'{title}</text>'
    )

    return svg_wrapper("\n".join(parts), width=total_w, height=total_h)


def residual_block(num_layers: int = 2) -> str:
    """Residual (skip-connection) block diagram.

    *num_layers* controls how many weight layers are shown inside the block
    (typically 2 or 3 for BasicBlock / Bottleneck).

    Example::

        residual_block(num_layers=2)   # BasicBlock
        residual_block(num_layers=3)   # Bottleneck
    """
    parts: list[str] = []

    box_w, box_h = 200, 40
    gap = 20
    margin_x = 120
    total_h_inner = num_layers * (box_h + gap) + gap

    x = margin_x
    y_start = 80

    # Input
    parts.append(rounded_box(x, y_start - 50, box_w, 36, "Input", color=BLUE))
    parts.append(arrow(x + box_w / 2, y_start - 14, x + box_w / 2, y_start))

    layer_labels = []
    if num_layers == 2:
        layer_labels = ["Conv 3×3 + BN + ReLU", "Conv 3×3 + BN"]
    elif num_layers == 3:
        layer_labels = ["Conv 1×1 + BN + ReLU", "Conv 3×3 + BN + ReLU", "Conv 1×1 + BN"]
    else:
        layer_labels = [f"Conv Layer {i+1}" for i in range(num_layers)]

    # dashed block container
    parts.append(dashed_box(
        x - 20, y_start - 10,
        box_w + 40, total_h_inner + 20,
        "Residual Block"
    ))

    # layer boxes
    ys = []
    for i, label in enumerate(layer_labels):
        ly = y_start + i * (box_h + gap)
        ys.append(ly)
        parts.append(rounded_box(x, ly, box_w, box_h, label, color=INDIGO))
        if i < num_layers - 1:
            parts.append(arrow(x + box_w / 2, ly + box_h,
                               x + box_w / 2, ly + box_h + gap))

    # skip connection (curved path on the right)
    skip_x = x + box_w + 35
    y_top = y_start - 14
    y_bot = ys[-1] + box_h + 20
    parts.append(
        f'<path d="M {x + box_w} {y_start + box_h // 2} '
        f'L {skip_x} {y_start + box_h // 2} '
        f'L {skip_x} {y_bot - 10} '
        f'L {x + box_w} {y_bot - 10}" '
        f'fill="none" stroke="{AMBER}" stroke-width="2" stroke-dasharray="5 3" />'
    )
    parts.append(
        f'<text x="{skip_x + 10}" y="{(y_start + y_bot) // 2}" '
        f'fill="{AMBER}" font-family="Inter,system-ui,sans-serif" '
        f'font-size="11" dominant-baseline="central">skip</text>'
    )

    # Add & ReLU
    y_add = ys[-1] + box_h + gap
    parts.append(arrow(x + box_w / 2, ys[-1] + box_h, x + box_w / 2, y_add))
    parts.append(rounded_box(x, y_add, box_w, 36, "Add & ReLU", color=GREEN))
    parts.append(arrow(x + box_w / 2, y_add + 36, x + box_w / 2, y_add + 56))
    parts.append(rounded_box(x, y_add + 56, box_w, 36, "Output", color=GREEN))

    total_w = x * 2 + box_w + 80
    total_h = y_add + 56 + 36 + 30
    return svg_wrapper("\n".join(parts), width=total_w, height=total_h)


def multi_head_attention_detail(num_heads: int = 4, d_k: int = 64,
                                d_v: int = 64) -> str:
    """Detailed multi-head attention showing Q/K/V projections per head.

    Example::

        multi_head_attention_detail(num_heads=4, d_k=64, d_v=64)
    """
    parts: list[str] = []

    head_w = 90
    head_gap = 12
    heads_total = num_heads * (head_w + head_gap) - head_gap
    margin_x = max(40, (600 - heads_total) // 2)
    total_w = heads_total + margin_x * 2

    # title
    parts.append(
        f'<text x="{total_w / 2}" y="28" text-anchor="middle" fill="{TEXT}" '
        f'font-family="Inter,system-ui,sans-serif" font-size="15" font-weight="700">'
        f'Multi-Head Attention ({num_heads} heads, d_k={d_k})</text>'
    )

    # Q, K, V inputs
    input_y = 50
    inp_w = 80
    inp_gap = 30
    inp_x_base = total_w / 2 - (inp_w * 3 + inp_gap * 2) / 2
    for j, (label, color) in enumerate([("Q", BLUE), ("K", GREEN), ("V", AMBER)]):
        ix = inp_x_base + j * (inp_w + inp_gap)
        parts.append(rounded_box(int(ix), input_y, inp_w, 32, label, color=color))

    # Q/K/V to heads
    head_y = 120
    for i in range(num_heads):
        hx = margin_x + i * (head_w + head_gap)
        # Head box
        parts.append(rounded_box(hx, head_y, head_w, 70,
                                 f"Head {i+1}\\nQ·K/√{d_k}\\n→V", color=INDIGO))
        # Arrow from input area
        parts.append(arrow(int(total_w / 2), input_y + 32,
                           hx + head_w // 2, head_y))

    # Concat + linear
    concat_y = head_y + 70 + 30
    parts.append(arrow(total_w // 2, head_y + 70, total_w // 2, concat_y))
    parts.append(rounded_box(int(total_w / 2 - 120), concat_y, 240, 36,
                             f"Concat + Linear (→{num_heads * d_v})", color=SLATE))
    parts.append(arrow(total_w // 2, concat_y + 36, total_w // 2, concat_y + 66))
    parts.append(rounded_box(int(total_w / 2 - 80), concat_y + 66, 160, 36,
                             "Output", color=GREEN))

    total_h = concat_y + 66 + 36 + 30
    return svg_wrapper("\n".join(parts), width=total_w, height=total_h)


def gan_architecture(gen_layers: list[str], disc_layers: list[str]) -> str:
    """GAN architecture showing Generator vs Discriminator.

    Example::

        gan_architecture(
            ["Noise z", "Dense 256", "Reshape", "Conv 4×4", "Output Image"],
            ["Input Image", "Conv 4×4", "Flatten", "Dense 1", "Real/Fake"],
        )
    """
    col_w = 200
    gap = 100
    margin = 40
    title_h = 50
    total_w = col_w * 2 + gap + margin * 2

    parts: list[str] = []

    # section labels
    lx = margin + col_w / 2
    rx = margin + col_w + gap + col_w / 2
    for label, color, cx in [("Generator", INDIGO, lx), ("Discriminator", RED, rx)]:
        parts.append(
            f'<text x="{cx}" y="30" text-anchor="middle" fill="{color}" '
            f'font-family="Inter,system-ui,sans-serif" font-size="14" '
            f'font-weight="700">{label}</text>'
        )

    # generator column
    parts.append(dashed_box(margin - 10, title_h - 10,
                            col_w + 20, len(gen_layers) * 48 + 20, ""))
    for i, step in enumerate(gen_layers):
        y = title_h + i * 48
        parts.append(rounded_box(margin, y, col_w, 36, step, color=INDIGO))
        if i < len(gen_layers) - 1:
            parts.append(arrow(margin + col_w / 2, y + 36,
                               margin + col_w / 2, y + 48))

    # discriminator column
    rx_start = margin + col_w + gap
    parts.append(dashed_box(rx_start - 10, title_h - 10,
                            col_w + 20, len(disc_layers) * 48 + 20, ""))
    for i, step in enumerate(disc_layers):
        y = title_h + i * 48
        parts.append(rounded_box(rx_start, y, col_w, 36, step, color=RED))
        if i < len(disc_layers) - 1:
            parts.append(arrow(rx_start + col_w / 2, y + 36,
                               rx_start + col_w / 2, y + 48))

    # fake image arrow between gen output and disc input
    gen_out_y = title_h + (len(gen_layers) - 1) * 48 + 18
    disc_in_y = title_h + 18
    arrow_x_mid = margin + col_w + gap / 2
    parts.append(
        f'<path d="M {margin + col_w} {gen_out_y} '
        f'L {arrow_x_mid} {gen_out_y} '
        f'L {arrow_x_mid} {disc_in_y} '
        f'L {rx_start} {disc_in_y}" '
        f'fill="none" stroke="{AMBER}" stroke-width="1.5" '
        f'marker-end="url(#arrowhead)" />'
    )
    parts.append(
        f'<text x="{arrow_x_mid + 6}" y="{(gen_out_y + disc_in_y) // 2}" '
        f'fill="{AMBER}" font-family="Inter,system-ui,sans-serif" '
        f'font-size="11" dominant-baseline="central">fake\\nimage</text>'
    )

    h = max(len(gen_layers), len(disc_layers)) * 48 + title_h + 40
    return svg_wrapper("\n".join(parts), width=total_w, height=h)


def attention_visualization(query_labels: list[str], key_labels: list[str],
                            weights_matrix: Optional[list[list[float]]] = None) -> str:
    """Attention weight heatmap rendered as SVG rects.

    Example::

        attention_visualization(
            ["the", "cat", "sat"],
            ["the", "cat", "sat"],
            weights_matrix=[[0.8, 0.1, 0.1], [0.2, 0.7, 0.1], [0.1, 0.2, 0.7]],
        )
    """
    n_q = len(query_labels)
    n_k = len(key_labels)
    cell = 44
    label_w = 70
    label_h = 50
    margin = 40

    if weights_matrix is None:
        # diagonal-dominant default
        weights_matrix = []
        for i in range(n_q):
            row = [0.1] * n_k
            row[i % n_k] = 0.8
            weights_matrix.append(row)

    parts: list[str] = []

    # title
    parts.append(
        f'<text x="{margin + label_w + n_k * cell / 2}" y="24" '
        f'text-anchor="middle" fill="{TEXT}" '
        f'font-family="Inter,system-ui,sans-serif" font-size="15" '
        f'font-weight="700">Attention Weights</text>'
    )

    ox = margin + label_w
    oy = margin + label_h

    # key labels (top)
    for j, kl in enumerate(key_labels):
        parts.append(
            f'<text x="{ox + j * cell + cell / 2}" y="{oy - 8}" '
            f'text-anchor="middle" fill="{MUTED}" '
            f'font-family="Inter,system-ui,sans-serif" font-size="12">'
            f'{kl}</text>'
        )

    # heatmap cells
    for i in range(n_q):
        # query label
        parts.append(
            f'<text x="{ox - 8}" y="{oy + i * cell + cell / 2}" '
            f'text-anchor="end" dominant-baseline="central" fill="{MUTED}" '
            f'font-family="Inter,system-ui,sans-serif" font-size="12">'
            f'{query_labels[i]}</text>'
        )
        for j in range(n_k):
            w = weights_matrix[i][j]
            # interpolate indigo opacity
            opacity = max(0.1, min(1.0, w))
            parts.append(
                f'<rect x="{ox + j * cell}" y="{oy + i * cell}" '
                f'width="{cell - 2}" height="{cell - 2}" rx="4" '
                f'fill="{INDIGO}" opacity="{opacity:.2f}" />'
            )
            parts.append(
                f'<text x="{ox + j * cell + cell / 2 - 1}" '
                f'y="{oy + i * cell + cell / 2 - 1}" '
                f'text-anchor="middle" dominant-baseline="central" '
                f'fill="{TEXT}" font-family="Inter,system-ui,sans-serif" '
                f'font-size="11">{w:.2f}</text>'
            )

    total_w = margin * 2 + label_w + n_k * cell
    total_h = margin * 2 + label_h + n_q * cell
    return svg_wrapper("\n".join(parts), width=total_w, height=total_h)
