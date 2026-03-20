"""Tested Mermaid.js diagram strings that render correctly in Mermaid v11.

Every function returns a complete Mermaid definition string (including the
``%%{init: ...}%%`` directive) ready to be placed inside a ``<pre class="mermaid">``
block or a markdown ```mermaid fence.

All diagrams use the dark theme with the project accent colour.
"""

_INIT = (
    "%%{init: {'theme': 'dark', 'themeVariables': {"
    "'primaryColor': '#6366f1', 'primaryTextColor': '#fafafa', "
    "'primaryBorderColor': '#818cf8', 'lineColor': '#64748b', "
    "'secondaryColor': '#3b82f6', 'tertiaryColor': '#09090b'"
    "}}}%%"
)


def mermaid_pipeline(steps: list[str]) -> str:
    """Left-to-right flowchart pipeline.

    Example::

        mermaid_pipeline(["Tokenize", "Embed", "Encode", "Decode", "Output"])
    """
    nodes: list[str] = []
    for i, step in enumerate(steps):
        safe = step.replace('"', "'")
        nodes.append(f'    S{i}["{safe}"]')

    arrows: list[str] = []
    for i in range(len(steps) - 1):
        arrows.append(f"    S{i} --> S{i + 1}")

    styles: list[str] = []
    color_cycle = ["#3b82f6", "#6366f1", "#6366f1", "#f59e0b", "#22c55e"]
    for i in range(len(steps)):
        c = color_cycle[i % len(color_cycle)]
        styles.append(f"    style S{i} fill:{c},stroke:{c},color:#fafafa")

    return (
        f"{_INIT}\n"
        "flowchart LR\n"
        + "\n".join(nodes) + "\n"
        + "\n".join(arrows) + "\n"
        + "\n".join(styles)
    )


def mermaid_architecture(components: dict[str, list[str]],
                         connections: list[tuple[str, str, str]]) -> str:
    """Top-down architecture diagram with subgraphs.

    *components* maps subgraph names to lists of node labels.
    *connections* is ``[(src_node_id, dst_node_id, label), ...]``
    where node IDs are auto-generated as ``<subgraph_index>_<node_index>``.

    Example::

        mermaid_architecture(
            {"Encoder": ["Self-Attention", "FFN"],
             "Decoder": ["Cross-Attention", "Self-Attention", "FFN"]},
            [("0_1", "1_0", "context")],
        )
    """
    lines = [f"{_INIT}", "flowchart TD"]

    for sg_i, (sg_name, nodes) in enumerate(components.items()):
        safe_sg = sg_name.replace('"', "'")
        lines.append(f'    subgraph {safe_sg}')
        for n_i, node in enumerate(nodes):
            nid = f"N{sg_i}_{n_i}"
            safe = node.replace('"', "'")
            lines.append(f'        {nid}["{safe}"]')
        lines.append("    end")

    for src, dst, label in connections:
        # Normalise IDs: accept "0_1" → "N0_1"
        s = src if src.startswith("N") else f"N{src}"
        d = dst if dst.startswith("N") else f"N{dst}"
        safe_label = label.replace('"', "'")
        lines.append(f'    {s} -->|"{safe_label}"| {d}')

    return "\n".join(lines)


def mermaid_class_diagram(classes: list[dict]) -> str:
    """Class diagram for ML frameworks / modules.

    *classes* — list of ``{"name": "Encoder", "attrs": ["d_model: int"],
    "methods": ["forward(x)"]}`` dicts.

    Example::

        mermaid_class_diagram([
            {"name": "Encoder", "attrs": ["d_model: int"], "methods": ["forward(x)"]},
            {"name": "Decoder", "attrs": ["d_model: int"], "methods": ["forward(x, ctx)"]},
        ])
    """
    lines = [f"{_INIT}", "classDiagram"]

    for cls in classes:
        name = cls["name"]
        lines.append(f"    class {name} {{")
        for attr in cls.get("attrs", []):
            lines.append(f"        +{attr}")
        for method in cls.get("methods", []):
            lines.append(f"        +{method}")
        lines.append("    }")

    return "\n".join(lines)


def mermaid_sequence(actors: list[str],
                     messages: list[tuple[str, str, str]]) -> str:
    """Sequence diagram for algorithms / protocols.

    *messages* — ``[(from_actor, to_actor, label), ...]``

    Example::

        mermaid_sequence(
            ["Client", "Server", "Database"],
            [("Client", "Server", "POST /predict"),
             ("Server", "Database", "load model"),
             ("Database", "Server", "weights"),
             ("Server", "Client", "prediction")],
        )
    """
    lines = [f"{_INIT}", "sequenceDiagram"]

    for actor in actors:
        lines.append(f"    participant {actor}")

    for src, dst, label in messages:
        safe = label.replace('"', "'")
        lines.append(f"    {src}->>+{dst}: {safe}")

    return "\n".join(lines)
