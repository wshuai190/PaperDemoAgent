r"""LaTeX / TikZ code generators for Beamer presentations.

Each function returns a complete TikZ code string that can be pasted into
a ``\begin{frame}`` environment.  All templates use the accent colour
``#6366f1`` and a consistent dark-theme palette.
"""

# ── colour definitions for TikZ preamble ──────────────────────────────
TIKZ_COLOR_DEFS = r"""% Graphics-module colour definitions
\definecolor{accent}{HTML}{6366f1}
\definecolor{inputblue}{HTML}{3b82f6}
\definecolor{transformindigo}{HTML}{6366f1}
\definecolor{decisionamber}{HTML}{f59e0b}
\definecolor{outputgreen}{HTML}{22c55e}
\definecolor{lossred}{HTML}{ef4444}
\definecolor{textwhite}{HTML}{fafafa}
\definecolor{textmuted}{HTML}{94a3b8}
\definecolor{darkbg}{HTML}{09090b}
"""


def tikz_flow_diagram(steps: list[str], title: str = "") -> str:
    r"""Horizontal flow chart with arrows for Beamer slides.

    Example::

        tikz_flow_diagram(["Tokenize", "Embed", "Encode", "Decode"],
                          title="Inference Pipeline")
    """
    colors = ["inputblue", "transformindigo", "transformindigo",
              "decisionamber", "outputgreen"]
    nodes: list[str] = []
    for i, step in enumerate(steps):
        c = colors[i % len(colors)]
        pos = f"at ({i * 3.2},0)" if i > 0 else ""
        anchor = "" if i == 0 else f", right=0.6cm of n{i - 1}"
        if i == 0:
            nodes.append(
                f"  \\node[draw={c}, fill={c}, text=textwhite, "
                f"rounded corners=4pt, minimum height=0.8cm, "
                f"minimum width=2.4cm, font=\\small\\bfseries] "
                f"(n{i}) {{{step}}};"
            )
        else:
            nodes.append(
                f"  \\node[draw={c}, fill={c}, text=textwhite, "
                f"rounded corners=4pt, minimum height=0.8cm, "
                f"minimum width=2.4cm, font=\\small\\bfseries{anchor}] "
                f"(n{i}) {{{step}}};"
            )

    arrows: list[str] = []
    for i in range(len(steps) - 1):
        arrows.append(f"  \\draw[->, thick, textmuted] (n{i}) -- (n{i + 1});")

    title_node = ""
    if title:
        title_node = (
            f"  \\node[above=0.6cm of n{len(steps) // 2}, "
            f"font=\\bfseries, text=textwhite] {{{title}}};"
        )

    return (
        "\\begin{tikzpicture}[node distance=0.6cm]\n"
        + "\n".join(nodes) + "\n"
        + "\n".join(arrows) + "\n"
        + title_node + "\n"
        + "\\end{tikzpicture}"
    )


def tikz_block_diagram(blocks: list[dict], connections: list[tuple[str, str, str]]) -> str:
    r"""Block diagram with labelled connections.

    *blocks* — list of ``{"id": "enc", "label": "Encoder", "color": "inputblue",
    "pos": "(0,0)"}`` dicts.
    *connections* — ``[("enc", "dec", "context"), ...]``

    Example::

        tikz_block_diagram(
            [{"id": "enc", "label": "Encoder", "color": "inputblue", "pos": "(0,0)"},
             {"id": "dec", "label": "Decoder", "color": "transformindigo", "pos": "(4,0)"}],
            [("enc", "dec", "context vectors")],
        )
    """
    nodes: list[str] = []
    for b in blocks:
        nodes.append(
            f"  \\node[draw={b['color']}, fill={b['color']}, text=textwhite, "
            f"rounded corners=4pt, minimum height=1cm, minimum width=2.8cm, "
            f"font=\\small\\bfseries] ({b['id']}) at {b['pos']} {{{b['label']}}};"
        )

    edges: list[str] = []
    for src, dst, lbl in connections:
        edges.append(
            f"  \\draw[->, thick, textmuted] ({src}) -- node[above, "
            f"font=\\scriptsize, text=textmuted] {{{lbl}}} ({dst});"
        )

    return (
        "\\begin{tikzpicture}\n"
        + "\n".join(nodes) + "\n"
        + "\n".join(edges) + "\n"
        + "\\end{tikzpicture}"
    )


def tikz_encoder_decoder(enc_layers: list[str], dec_layers: list[str]) -> str:
    r"""Encoder-decoder architecture for Beamer slides.

    Example::

        tikz_encoder_decoder(
            ["Self-Attn", "FFN", "Self-Attn", "FFN"],
            ["Cross-Attn", "Self-Attn", "FFN"],
        )
    """
    enc_nodes: list[str] = []
    for i, layer in enumerate(enc_layers):
        c = "inputblue" if i % 2 == 0 else "transformindigo"
        y = -i * 1.0
        enc_nodes.append(
            f"  \\node[draw={c}, fill={c}, text=textwhite, "
            f"rounded corners=3pt, minimum width=2.6cm, minimum height=0.6cm, "
            f"font=\\scriptsize\\bfseries] (e{i}) at (0,{y}) {{{layer}}};"
        )

    dec_nodes: list[str] = []
    for i, layer in enumerate(dec_layers):
        c = "decisionamber" if "Cross" in layer else "transformindigo"
        y = -i * 1.0
        dec_nodes.append(
            f"  \\node[draw={c}, fill={c}, text=textwhite, "
            f"rounded corners=3pt, minimum width=2.6cm, minimum height=0.6cm, "
            f"font=\\scriptsize\\bfseries] (d{i}) at (5,{y}) {{{layer}}};"
        )

    # arrows between consecutive layers
    enc_arrows = [f"  \\draw[->, textmuted] (e{i}) -- (e{i + 1});"
                  for i in range(len(enc_layers) - 1)]
    dec_arrows = [f"  \\draw[->, textmuted] (d{i}) -- (d{i + 1});"
                  for i in range(len(dec_layers) - 1)]

    # cross-connection
    enc_mid = len(enc_layers) // 2
    dec_mid = len(dec_layers) // 2
    cross = (
        f"  \\draw[->, thick, decisionamber, dashed] (e{enc_mid}.east) "
        f"-- node[above, font=\\scriptsize, text=textmuted] {{context}} (d{dec_mid}.west);"
    )

    # labels
    enc_label = (
        f"  \\node[above=0.3cm of e0, font=\\small\\bfseries, text=textwhite] "
        f"{{Encoder}};"
    )
    dec_label = (
        f"  \\node[above=0.3cm of d0, font=\\small\\bfseries, text=textwhite] "
        f"{{Decoder}};"
    )

    return (
        "\\begin{tikzpicture}[node distance=0.2cm]\n"
        + "\n".join(enc_nodes) + "\n"
        + "\n".join(dec_nodes) + "\n"
        + "\n".join(enc_arrows) + "\n"
        + "\n".join(dec_arrows) + "\n"
        + cross + "\n"
        + enc_label + "\n" + dec_label + "\n"
        + "\\end{tikzpicture}"
    )


def tikz_comparison_table(headers: list[str], rows: list[list[str]],
                          highlight_row: int = 0) -> str:
    r"""Booktabs table with bold best-result row for Beamer.

    Example::

        tikz_comparison_table(
            ["Method", "Acc", "F1"],
            [["BERT", "85.2", "84.1"], ["Ours", "91.3", "90.8"]],
            highlight_row=1,
        )
    """
    col_spec = "l" + "c" * (len(headers) - 1)
    head_cells = " & ".join(f"\\textbf{{{h}}}" for h in headers)
    body: list[str] = []
    for i, row in enumerate(rows):
        if i == highlight_row:
            cells = " & ".join(f"\\textbf{{{c}}}" for c in row)
            body.append(f"  \\rowcolor{{accent!15}} {cells} \\\\")
        else:
            cells = " & ".join(row)
            body.append(f"  {cells} \\\\")

    return (
        f"\\begin{{tabular}}{{{col_spec}}}\n"
        f"  \\toprule\n"
        f"  {head_cells} \\\\\n"
        f"  \\midrule\n"
        + "\n".join(body) + "\n"
        f"  \\bottomrule\n"
        f"\\end{{tabular}}"
    )
