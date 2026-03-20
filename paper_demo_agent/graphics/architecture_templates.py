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
