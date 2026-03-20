"""HTML / JavaScript chart code generators for embedding in demos.

Returns *code strings* (not rendered images).  The LLM writes these into
HTML files so charts run client-side via Chart.js or D3.js.

All templates use the shared dark colour palette.
"""
from __future__ import annotations
from typing import Optional

CHART_JS_CDN = "https://cdn.jsdelivr.net/npm/chart.js@4/dist/chart.umd.min.js"
"""Chart.js v4 UMD CDN link (dark-theme compatible)."""

D3_CDN = "https://d3js.org/d3.v7.min.js"
"""D3.js v7 CDN link."""

# ── colour constants (match svg_primitives) ───────────────────────────
_COLORS = ["#3b82f6", "#6366f1", "#f59e0b", "#22c55e", "#ef4444",
           "#8b5cf6", "#06b6d4", "#ec4899"]


def bar_chart_js(data: list[float], labels: list[str], title: str,
                 colors: Optional[list[str]] = None,
                 highlight_idx: int = 0) -> str:
    """Chart.js bar chart with one highlighted bar (the proposed method).

    Example::

        bar_chart_js([85.2, 87.1, 91.3], ["BERT", "RoBERTa", "Ours"],
                     "Accuracy (%)", highlight_idx=2)
    """
    if colors is None:
        colors = [_COLORS[i % len(_COLORS)] for i in range(len(data))]
    # brighten the highlighted bar
    bg = list(colors)
    border = list(colors)
    for i in range(len(bg)):
        if i != highlight_idx:
            bg[i] = bg[i] + "99"  # 60 % opacity hex suffix

    return f"""<canvas id="barChart" width="600" height="350"></canvas>
<script src="{CHART_JS_CDN}"></script>
<script>
new Chart(document.getElementById('barChart'), {{
  type: 'bar',
  data: {{
    labels: {labels},
    datasets: [{{
      label: '{title}',
      data: {data},
      backgroundColor: {bg},
      borderColor: {border},
      borderWidth: 1
    }}]
  }},
  options: {{
    responsive: true,
    plugins: {{
      title: {{ display: true, text: '{title}', color: '#fafafa', font: {{ size: 16 }} }},
      legend: {{ display: false }}
    }},
    scales: {{
      x: {{ ticks: {{ color: '#94a3b8' }}, grid: {{ color: '#27272a' }} }},
      y: {{ ticks: {{ color: '#94a3b8' }}, grid: {{ color: '#27272a' }},
            beginAtZero: false }}
    }}
  }}
}});
</script>"""


def comparison_table_html(headers: list[str], rows: list[list[str]],
                          highlight_row: int = 0) -> str:
    """Styled HTML table with one highlighted row for the proposed method.

    Example::

        comparison_table_html(
            ["Method", "Acc", "F1"],
            [["BERT", "85.2", "84.1"], ["Ours", "91.3", "90.8"]],
            highlight_row=1,
        )
    """
    head_cells = "".join(f"<th>{h}</th>" for h in headers)
    body_rows: list[str] = []
    for i, row in enumerate(rows):
        cls = ' class="highlight"' if i == highlight_row else ""
        cells = "".join(f"<td>{c}</td>" for c in row)
        body_rows.append(f"  <tr{cls}>{cells}</tr>")

    return f"""<style>
.results-table {{ border-collapse: collapse; width: 100%; font-family: Inter, system-ui, sans-serif; }}
.results-table th {{ background: #18181b; color: #94a3b8; padding: 10px 16px;
  text-align: left; font-size: 13px; text-transform: uppercase; letter-spacing: 0.05em; }}
.results-table td {{ padding: 10px 16px; color: #fafafa; border-bottom: 1px solid #27272a; }}
.results-table tr.highlight td {{ background: #6366f120; font-weight: 600; }}
</style>
<table class="results-table">
<thead><tr>{head_cells}</tr></thead>
<tbody>
{chr(10).join(body_rows)}
</tbody>
</table>"""


def radar_chart_js(metrics: list[str], scores_dict: dict[str, list[float]],
                   title: str) -> str:
    """Chart.js radar chart comparing methods on multiple metrics.

    Example::

        radar_chart_js(
            ["Acc", "F1", "Latency", "Memory", "Params"],
            {"BERT": [85, 84, 60, 70, 50], "Ours": [91, 90, 80, 85, 65]},
            "Method Comparison",
        )
    """
    datasets: list[str] = []
    for i, (method, scores) in enumerate(scores_dict.items()):
        c = _COLORS[i % len(_COLORS)]
        datasets.append(
            f"    {{ label: '{method}', data: {scores}, "
            f"borderColor: '{c}', backgroundColor: '{c}33', "
            f"pointBackgroundColor: '{c}', pointRadius: 4 }}"
        )
    ds_str = ",\n".join(datasets)

    return f"""<canvas id="radarChart" width="500" height="500"></canvas>
<script src="{CHART_JS_CDN}"></script>
<script>
new Chart(document.getElementById('radarChart'), {{
  type: 'radar',
  data: {{
    labels: {metrics},
    datasets: [
{ds_str}
    ]
  }},
  options: {{
    responsive: true,
    plugins: {{
      title: {{ display: true, text: '{title}', color: '#fafafa', font: {{ size: 16 }} }},
      legend: {{ labels: {{ color: '#94a3b8' }} }}
    }},
    scales: {{
      r: {{
        angleLines: {{ color: '#27272a' }},
        grid: {{ color: '#27272a' }},
        pointLabels: {{ color: '#94a3b8', font: {{ size: 12 }} }},
        ticks: {{ display: false }}
      }}
    }}
  }}
}});
</script>"""


def d3_grouped_bar(data: list[dict], group_labels: list[str],
                   series_labels: list[str], title: str) -> str:
    """D3.js grouped bar chart snippet.

    *data* is a list of dicts, one per group, with keys matching
    *series_labels*.

    Example::

        d3_grouped_bar(
            [{"BERT": 85, "Ours": 91}, {"BERT": 84, "Ours": 90}],
            ["Accuracy", "F1"],
            ["BERT", "Ours"],
            "Benchmark Results",
        )
    """
    import json
    data_json = json.dumps(data)
    colors_json = json.dumps(_COLORS[:len(series_labels)])

    return f"""<div id="grouped-bar" style="width:600px;height:400px"></div>
<script src="{D3_CDN}"></script>
<script>
(function() {{
  const data = {data_json};
  const groups = {json.dumps(group_labels)};
  const series = {json.dumps(series_labels)};
  const colors = d3.scaleOrdinal().domain(series).range({colors_json});

  const margin = {{top: 40, right: 20, bottom: 40, left: 50}};
  const width = 600 - margin.left - margin.right;
  const height = 400 - margin.top - margin.bottom;

  const svg = d3.select('#grouped-bar').append('svg')
    .attr('width', 600).attr('height', 400)
    .append('g').attr('transform', `translate(${{margin.left}},${{margin.top}})`);

  svg.append('rect').attr('width', width).attr('height', height).attr('fill', '#09090b');

  const x0 = d3.scaleBand().domain(groups).range([0, width]).padding(0.2);
  const x1 = d3.scaleBand().domain(series).range([0, x0.bandwidth()]).padding(0.05);
  const allVals = data.flatMap(d => series.map(s => d[s] || 0));
  const y = d3.scaleLinear().domain([0, d3.max(allVals) * 1.1]).range([height, 0]);

  svg.append('g').attr('transform', `translate(0,${{height}})`)
    .call(d3.axisBottom(x0)).selectAll('text').attr('fill', '#94a3b8');
  svg.append('g').call(d3.axisLeft(y).ticks(5))
    .selectAll('text').attr('fill', '#94a3b8');

  svg.append('text').attr('x', width / 2).attr('y', -12)
    .attr('text-anchor', 'middle').attr('fill', '#fafafa')
    .attr('font-size', '15px').attr('font-weight', '700').text('{title}');

  const groupG = svg.selectAll('.group')
    .data(data).enter().append('g')
    .attr('transform', (d, i) => `translate(${{x0(groups[i])}},0)`);

  groupG.selectAll('rect')
    .data((d) => series.map(s => ({{key: s, value: d[s] || 0}})))
    .enter().append('rect')
    .attr('x', d => x1(d.key)).attr('y', d => y(d.value))
    .attr('width', x1.bandwidth())
    .attr('height', d => height - y(d.value))
    .attr('fill', d => colors(d.key)).attr('rx', 3);
}})();
</script>"""


def line_chart_js(data_series: dict[str, list[float]], labels: list[str],
                  title: str, y_label: str = "Value") -> str:
    """Chart.js multi-line chart for training curves, metrics over epochs, etc.

    *data_series* maps series name → list of y-values (same length as *labels*).
    *labels* are the x-axis tick labels (e.g. epoch numbers or step names).

    Example::

        line_chart_js(
            {"Train Loss": [2.3, 1.8, 1.4, 1.1, 0.9],
             "Val Loss":   [2.5, 2.0, 1.6, 1.3, 1.1]},
            labels=["1", "2", "3", "4", "5"],
            title="Training Curves",
            y_label="Loss",
        )
    """
    import json
    datasets: list[str] = []
    for i, (name, values) in enumerate(data_series.items()):
        c = _COLORS[i % len(_COLORS)]
        datasets.append(
            f"    {{ label: {json.dumps(name)}, data: {json.dumps(values)}, "
            f"borderColor: '{c}', backgroundColor: '{c}22', "
            f"pointBackgroundColor: '{c}', pointRadius: 4, "
            f"tension: 0.3, fill: false }}"
        )
    ds_str = ",\n".join(datasets)

    return f"""<canvas id="lineChart_{title.replace(' ','_')}" width="640" height="380"></canvas>
<script src="{CHART_JS_CDN}"></script>
<script>
new Chart(document.getElementById('lineChart_{title.replace(' ','_')}'), {{
  type: 'line',
  data: {{
    labels: {json.dumps(labels)},
    datasets: [
{ds_str}
    ]
  }},
  options: {{
    responsive: true,
    interaction: {{ mode: 'index', intersect: false }},
    plugins: {{
      title: {{ display: true, text: {json.dumps(title)}, color: '#fafafa', font: {{ size: 16 }} }},
      legend: {{ labels: {{ color: '#94a3b8' }} }}
    }},
    scales: {{
      x: {{ ticks: {{ color: '#94a3b8' }}, grid: {{ color: '#27272a' }} }},
      y: {{
        ticks: {{ color: '#94a3b8' }},
        grid: {{ color: '#27272a' }},
        title: {{ display: true, text: {json.dumps(y_label)}, color: '#94a3b8' }}
      }}
    }}
  }}
}});
</script>"""


def heatmap_d3(matrix: list[list[float]], row_labels: list[str],
               col_labels: list[str], title: str,
               color_scheme: str = "Blues") -> str:
    """D3.js heatmap for attention matrices, confusion matrices, similarity grids, etc.

    *matrix* is a 2D list [rows][cols] of float values (0–1 or raw, auto-normalised).
    *color_scheme* is a D3 sequential scheme name: "Blues", "Purples", "YlOrRd", etc.

    Example::

        heatmap_d3(
            [[0.9, 0.1, 0.0], [0.2, 0.7, 0.1], [0.05, 0.15, 0.8]],
            row_labels=["cat", "dog", "bird"],
            col_labels=["cat", "dog", "bird"],
            title="Confusion Matrix",
        )
    """
    import json
    flat_vals = [v for row in matrix for v in row]
    max_val = max(flat_vals) if flat_vals else 1.0
    norm_matrix = [[v / max_val for v in row] for row in matrix]

    data_json = json.dumps(norm_matrix)
    rows_json = json.dumps(row_labels)
    cols_json = json.dumps(col_labels)
    orig_json = json.dumps(matrix)

    return f"""<div id="heatmap_{title.replace(' ','_')}" style="max-width:600px"></div>
<script src="{D3_CDN}"></script>
<script>
(function() {{
  const matrix = {data_json};
  const orig = {orig_json};
  const rows = {rows_json};
  const cols = {cols_json};
  const cell = Math.min(44, Math.floor(480 / Math.max(rows.length, cols.length)));

  const margin = {{top: 50, right: 20, bottom: 20, left: 80}};
  const width  = cols.length * cell + margin.left + margin.right;
  const height = rows.length * cell + margin.top  + margin.bottom;

  const svg = d3.select('#heatmap_{title.replace(' ','_')}').append('svg')
    .attr('width', width).attr('height', height);

  const g = svg.append('g').attr('transform', `translate(${{margin.left}},${{margin.top}})`);

  svg.append('text').attr('x', width / 2).attr('y', 26)
    .attr('text-anchor', 'middle').attr('fill', '#fafafa')
    .attr('font-size', '15px').attr('font-weight', '700').text({json.dumps(title)});

  const color = d3.scaleSequential(d3.interpolate{color_scheme}).domain([0, 1]);

  // cells
  for (let r = 0; r < rows.length; r++) {{
    for (let c = 0; c < cols.length; c++) {{
      g.append('rect')
        .attr('x', c * cell).attr('y', r * cell)
        .attr('width', cell - 2).attr('height', cell - 2)
        .attr('rx', 3).attr('fill', color(matrix[r][c]));
      const val = orig[r][c];
      const fmt = Number.isInteger(val) ? val : val.toFixed(2);
      g.append('text')
        .attr('x', c * cell + cell / 2 - 1).attr('y', r * cell + cell / 2 - 1)
        .attr('text-anchor', 'middle').attr('dominant-baseline', 'central')
        .attr('fill', matrix[r][c] > 0.5 ? '#09090b' : '#fafafa')
        .attr('font-size', Math.max(9, cell * 0.25) + 'px').text(fmt);
    }}
  }}

  // row labels
  rows.forEach((label, r) => {{
    g.append('text').attr('x', -6).attr('y', r * cell + cell / 2)
      .attr('text-anchor', 'end').attr('dominant-baseline', 'central')
      .attr('fill', '#94a3b8').attr('font-size', '12px').text(label);
  }});

  // col labels
  cols.forEach((label, c) => {{
    g.append('text').attr('x', c * cell + cell / 2).attr('y', -8)
      .attr('text-anchor', 'middle').attr('fill', '#94a3b8')
      .attr('font-size', '12px').text(label);
  }});
}})();
</script>"""


def metric_dashboard_html(metrics_dict: dict[str, dict]) -> str:
    """Grid of metric result cards.

    *metrics_dict* maps metric name → dict with keys:
      - ``value``: display string (e.g. "91.3%")
      - ``delta``: change string (e.g. "+2.1%") — optional
      - ``delta_label``: comparison label (default "vs SOTA") — optional
      - ``subtitle``: small grey description — optional

    Example::

        metric_dashboard_html({
            "NDCG@10":   {"value": "0.421", "delta": "+3.2%", "subtitle": "TREC DL 2020"},
            "MAP":       {"value": "0.318", "delta": "+1.8%"},
            "Recall@100":{"value": "0.892", "delta": "+0.5%"},
        })
    """
    cards: list[str] = []
    for metric, info in metrics_dict.items():
        value = info.get("value", "—")
        delta = info.get("delta", "")
        delta_label = info.get("delta_label", "vs SOTA")
        subtitle = info.get("subtitle", "")

        badge_html = ""
        if delta:
            positive = delta.startswith("+")
            badge_bg = "#22c55e20" if positive else "#ef444420"
            badge_color = "#22c55e" if positive else "#ef4444"
            arrow_char = "&#9650;" if positive else "&#9660;"
            badge_html = (
                f'<div style="display:inline-flex;align-items:center;gap:4px;'
                f'background:{badge_bg};color:{badge_color};padding:3px 8px;'
                f'border-radius:5px;font-size:12px;font-weight:600;margin-top:6px;">'
                f'{arrow_char} {delta} '
                f'<span style="color:#94a3b8;font-weight:400">{delta_label}</span></div>'
            )

        subtitle_html = (
            f'<div style="color:#64748b;font-size:11px;margin-top:4px">{subtitle}</div>'
            if subtitle else ""
        )

        cards.append(
            f'<div style="background:#18181b;border:1px solid #27272a;border-radius:12px;'
            f'padding:20px 24px;font-family:Inter,system-ui,sans-serif;">'
            f'<div style="color:#94a3b8;font-size:12px;text-transform:uppercase;'
            f'letter-spacing:0.05em;">{metric}</div>'
            f'<div style="color:#fafafa;font-size:32px;font-weight:700;margin:6px 0">'
            f'{value}</div>'
            f'{badge_html}{subtitle_html}'
            f'</div>'
        )

    grid_html = "\n".join(
        f'  <div style="grid-column:span 1">{card}</div>' for card in cards
    )
    cols = min(len(metrics_dict), 4)
    return (
        f'<div style="display:grid;grid-template-columns:repeat({cols},1fr);'
        f'gap:16px;margin:24px 0">\n{grid_html}\n</div>'
    )


def results_card_html(metric: str, value: str, delta: str,
                      delta_label: str = "vs SOTA") -> str:
    """Single metric display card with a delta badge.

    Example::

        results_card_html("Accuracy", "91.3%", "+2.1%", delta_label="vs BERT")
    """
    positive = delta.startswith("+")
    badge_bg = "#22c55e20" if positive else "#ef444420"
    badge_color = "#22c55e" if positive else "#ef4444"
    arrow_char = "&#9650;" if positive else "&#9660;"

    return f"""<div style="background:#18181b; border:1px solid #27272a; border-radius:12px;
  padding:24px 28px; font-family:Inter,system-ui,sans-serif; display:inline-block; min-width:180px;">
  <div style="color:#94a3b8; font-size:13px; text-transform:uppercase; letter-spacing:0.05em;">{metric}</div>
  <div style="color:#fafafa; font-size:36px; font-weight:700; margin:8px 0;">{value}</div>
  <div style="display:inline-flex; align-items:center; gap:6px;
    background:{badge_bg}; color:{badge_color}; padding:4px 10px;
    border-radius:6px; font-size:13px; font-weight:600;">
    <span>{arrow_char}</span> {delta} <span style="color:#94a3b8; font-weight:400;">{delta_label}</span>
  </div>
</div>"""
