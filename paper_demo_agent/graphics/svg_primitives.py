"""Low-level SVG building blocks for composing diagrams programmatically.

All functions return SVG markup strings.  The LLM calls these inside
``execute_python`` to generate ``.svg`` files, or the raw patterns are
included in HTML output directly.

Color palette (dark theme):
    Background : #09090b
    Blue/input : #3b82f6    Indigo/transform : #6366f1
    Amber/decision : #f59e0b   Green/output : #22c55e   Red/loss : #ef4444
    Text white : #fafafa    Text muted : #94a3b8
    Lines      : #475569    Lines light : #64748b
"""

from __future__ import annotations
from typing import Optional

# ── colour constants ──────────────────────────────────────────────────
BG       = "#09090b"
BLUE     = "#3b82f6"
INDIGO   = "#6366f1"
AMBER    = "#f59e0b"
GREEN    = "#22c55e"
RED      = "#ef4444"
TEXT     = "#fafafa"
MUTED    = "#94a3b8"
SLATE    = "#475569"
SLATE_LT = "#64748b"


def rounded_box(x: float, y: float, w: float, h: float, label: str,
                color: str = BLUE, text_color: str = "#fff", rx: int = 8) -> str:
    """Rounded rectangle with centred text.

    Example::

        rounded_box(50, 50, 160, 40, "Encoder", color="#6366f1")
    """
    return (
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" '
        f'fill="{color}" />\n'
        f'<text x="{x + w / 2}" y="{y + h / 2}" '
        f'text-anchor="middle" dominant-baseline="central" '
        f'fill="{text_color}" font-family="Inter,system-ui,sans-serif" '
        f'font-size="14" font-weight="600">{label}</text>'
    )


def arrow(x1: float, y1: float, x2: float, y2: float,
          color: str = SLATE_LT, stroke: int = 2, marker: bool = True) -> str:
    """Straight line with optional arrowhead.

    Example::

        arrow(100, 70, 250, 70)
    """
    marker_attr = ' marker-end="url(#arrowhead)"' if marker else ""
    return (
        f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
        f'stroke="{color}" stroke-width="{stroke}"{marker_attr} />'
    )


def flow_arrow(x1: float, y1: float, x2: float, y2: float,
               label: str = "", color: str = SLATE_LT) -> str:
    """Arrow with a text label placed at the midpoint.

    Example::

        flow_arrow(100, 50, 300, 50, label="embeddings")
    """
    mid_x = (x1 + x2) / 2
    mid_y = (y1 + y2) / 2
    parts = [arrow(x1, y1, x2, y2, color=color)]
    if label:
        parts.append(
            f'<text x="{mid_x}" y="{mid_y - 8}" text-anchor="middle" '
            f'fill="{MUTED}" font-family="Inter,system-ui,sans-serif" '
            f'font-size="11">{label}</text>'
        )
    return "\n".join(parts)


def layer_stack(x: float, y: float, layers: list[str],
                spacing: int = 8, width: int = 160) -> str:
    """Vertical stack of rounded boxes (e.g. encoder/decoder layers).

    Example::

        layer_stack(50, 50, ["Layer 1", "Layer 2", "Layer 3"])
    """
    box_h = 36
    parts: list[str] = []
    colors = [INDIGO, BLUE, INDIGO, BLUE, INDIGO, BLUE]
    for i, label in enumerate(layers):
        cy = y + i * (box_h + spacing)
        c = colors[i % len(colors)]
        parts.append(rounded_box(x, cy, width, box_h, label, color=c))
        if i < len(layers) - 1:
            parts.append(arrow(x + width / 2, cy + box_h,
                               x + width / 2, cy + box_h + spacing,
                               color=SLATE))
    return "\n".join(parts)


def parallel_blocks(x: float, y: float, blocks: list[str],
                    spacing: int = 20, width: int = 120) -> str:
    """Horizontal row of boxes (e.g. multi-head attention heads).

    Example::

        parallel_blocks(50, 50, ["Head 1", "Head 2", "Head 3"])
    """
    box_h = 36
    parts: list[str] = []
    colors = [INDIGO, BLUE, AMBER, GREEN, RED]
    for i, label in enumerate(blocks):
        cx = x + i * (width + spacing)
        c = colors[i % len(colors)]
        parts.append(rounded_box(cx, y, width, box_h, label, color=c))
    return "\n".join(parts)


def connection_lines(sources: list[tuple[float, float]],
                     targets: list[tuple[float, float]],
                     color: str = SLATE) -> str:
    """Draw lines from every source to every target.

    Example::

        connection_lines([(100, 80), (200, 80)], [(150, 160)])
    """
    parts: list[str] = []
    for sx, sy in sources:
        for tx, ty in targets:
            parts.append(arrow(sx, sy, tx, ty, color=color, marker=False))
    return "\n".join(parts)


def dashed_box(x: float, y: float, w: float, h: float, label: str,
               color: str = SLATE) -> str:
    """Dashed-border container for grouping related elements.

    Example::

        dashed_box(30, 30, 300, 200, "Encoder Block")
    """
    return (
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" '
        f'fill="none" stroke="{color}" stroke-width="1.5" '
        f'stroke-dasharray="6 4" />\n'
        f'<text x="{x + 8}" y="{y + 16}" '
        f'fill="{MUTED}" font-family="Inter,system-ui,sans-serif" '
        f'font-size="11" font-weight="500">{label}</text>'
    )


_ARROWHEAD_DEF = (
    '<defs>\n'
    '  <marker id="arrowhead" markerWidth="10" markerHeight="7" '
    'refX="10" refY="3.5" orient="auto" markerUnits="strokeWidth">\n'
    '    <polygon points="0 0, 10 3.5, 0 7" fill="#64748b" />\n'
    '  </marker>\n'
    '</defs>'
)


def svg_wrapper(content: str, width: int = 800, height: int = 600,
                bg: str = BG, viewBox: Optional[str] = None) -> str:
    """Wrap SVG content in a complete ``<svg>`` element with arrowhead defs.

    Example::

        svg_wrapper(rounded_box(50, 50, 160, 40, "Hello"), width=300, height=140)
    """
    vb = viewBox or f"0 0 {width} {height}"
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{width}" height="{height}" viewBox="{vb}">\n'
        f'<rect width="100%" height="100%" fill="{bg}" />\n'
        f'{_ARROWHEAD_DEF}\n'
        f'{content}\n'
        '</svg>'
    )
