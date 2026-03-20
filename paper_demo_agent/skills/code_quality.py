"""CodeQuality — utility module providing verified CDN URLs, HTML boilerplate, and CSS snippets.

This module is NOT a routable skill. It provides shared code-quality helpers that all
skills can import and use. Access the main entry point via BaseSkill._cdn_reference().

Usage (from any skill):
    cdns = self._cdn_reference()
    dark_css = cdns.dark_theme_css()
    boilerplate = cdns.html_boilerplate("presentation", title="My Paper")
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional


# ─────────────────────────────────────────────────────────────────────────────
# Verified CDN URLs — pinned, tested, known-good
# ─────────────────────────────────────────────────────────────────────────────

#: Reveal.js 5.2.1 (unpkg — stable, CDN-backed)
REVEALJS_VERSION = "5.2.1"
CHARTJS_VERSION = "4.4.7"
D3_VERSION = "7"
MERMAID_VERSION = "11"
KATEX_VERSION = "0.16.11"

VERIFIED_CDNS: Dict[str, str] = {
    # ── Fonts ────────────────────────────────────────────────────────────────
    "inter_font": (
        "https://fonts.googleapis.com/css2?family=Inter:"
        "ital,opsz,wght@0,14..32,300..700;1,14..32,300..700&display=swap"
    ),
    "jetbrains_mono": (
        "https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500&display=swap"
    ),

    # ── Math (KaTeX) ─────────────────────────────────────────────────────────
    "katex_css": f"https://cdn.jsdelivr.net/npm/katex@{KATEX_VERSION}/dist/katex.min.css",
    "katex_js": f"https://cdn.jsdelivr.net/npm/katex@{KATEX_VERSION}/dist/katex.min.js",
    "katex_auto_render": (
        f"https://cdn.jsdelivr.net/npm/katex@{KATEX_VERSION}/dist/contrib/auto-render.min.js"
    ),

    # ── Reveal.js 5.2.1 ──────────────────────────────────────────────────────
    "revealjs_css": f"https://unpkg.com/reveal.js@{REVEALJS_VERSION}/dist/reveal.css",
    "revealjs_theme_black": (
        f"https://unpkg.com/reveal.js@{REVEALJS_VERSION}/dist/theme/black.css"
    ),
    "revealjs_highlight_css": (
        f"https://unpkg.com/reveal.js@{REVEALJS_VERSION}/plugin/highlight/monokai.css"
    ),
    "revealjs_js": f"https://unpkg.com/reveal.js@{REVEALJS_VERSION}/dist/reveal.js",
    "revealjs_highlight_js": (
        f"https://unpkg.com/reveal.js@{REVEALJS_VERSION}/plugin/highlight/highlight.js"
    ),
    "revealjs_math_js": (
        f"https://unpkg.com/reveal.js@{REVEALJS_VERSION}/plugin/math/math.js"
    ),
    "revealjs_notes_js": (
        f"https://unpkg.com/reveal.js@{REVEALJS_VERSION}/plugin/notes/notes.js"
    ),

    # ── Chart.js 4.4.7 ───────────────────────────────────────────────────────
    "chartjs": (
        f"https://cdn.jsdelivr.net/npm/chart.js@{CHARTJS_VERSION}/dist/chart.umd.min.js"
    ),

    # ── D3.js v7 ─────────────────────────────────────────────────────────────
    "d3_v7": f"https://d3js.org/d3.v{D3_VERSION}.min.js",

    # ── Mermaid v11 (ESM) ─────────────────────────────────────────────────────
    "mermaid_esm": (
        f"https://cdn.jsdelivr.net/npm/mermaid@{MERMAID_VERSION}/dist/mermaid.esm.min.mjs"
    ),

    # ── Prism.js (syntax highlighting) ───────────────────────────────────────
    "prism_css": "https://cdn.jsdelivr.net/npm/prismjs@1.29.0/themes/prism-tomorrow.min.css",
    "prism_js": "https://cdn.jsdelivr.net/npm/prismjs@1.29.0/prism.min.js",
    "prism_autoloader": (
        "https://cdn.jsdelivr.net/npm/prismjs@1.29.0/plugins/autoloader/prism-autoloader.min.js"
    ),

    # ── Publishing ────────────────────────────────────────────────────────────
    "distill_template": "https://distill.pub/template.v2.js",
}


# ─────────────────────────────────────────────────────────────────────────────
# Dark theme CSS snippet
# ─────────────────────────────────────────────────────────────────────────────

DARK_THEME_CSS = """\
/* ── Dark theme reset (include in ALL demos) ── */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
:root {
  --bg:       #0d1117;
  --surface:  #161b22;
  --border:   #30363d;
  --text:     #e6edf3;
  --muted:    #8b949e;
  --accent:   #58a6ff;
  --accent2:  #79c0ff;
  --success:  #56d364;
  --warning:  #e3b341;
  --danger:   #f85149;
  --code-bg:  #1f2428;
  --radius:   8px;
  --shadow:   0 4px 16px rgba(0,0,0,0.4);
  --font:     'Inter', system-ui, -apple-system, sans-serif;
  --mono:     'JetBrains Mono', 'Fira Code', monospace;
}
html { font-size: 16px; scroll-behavior: smooth; }
body {
  background: var(--bg);
  color: var(--text);
  font-family: var(--font);
  line-height: 1.6;
  min-height: 100vh;
}
a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }
code, pre { font-family: var(--mono); background: var(--code-bg); }
pre { padding: 1rem; border-radius: var(--radius); overflow-x: auto; }
img { max-width: 100%; height: auto; border-radius: var(--radius); }
/* Responsive container */
.container { max-width: 1200px; margin: 0 auto; padding: 0 1.5rem; }
"""


# ─────────────────────────────────────────────────────────────────────────────
# HTML boilerplate templates per form
# ─────────────────────────────────────────────────────────────────────────────

def html_boilerplate(form: str, title: str = "Paper Demo", dark: bool = True) -> str:
    """Return an HTML boilerplate skeleton for the given form.

    Args:
        form: One of 'presentation', 'website', 'page_blog', 'flowchart', 'page_readme'
        title: <title> tag content
        dark: Whether to include inline dark-theme CSS reset

    Returns:
        A complete HTML skeleton string (open tags — body/main content goes in the middle)
    """
    css_inline = f"  <style>\n{DARK_THEME_CSS}\n  </style>" if dark else ""
    cdns = VERIFIED_CDNS

    if form == "presentation":
        return f"""\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <link rel="stylesheet" href="{cdns['revealjs_css']}">
  <link rel="stylesheet" href="{cdns['revealjs_theme_black']}">
  <link rel="stylesheet" href="{cdns['revealjs_highlight_css']}">
  <link rel="stylesheet" href="{cdns['katex_css']}">
  <link href="{cdns['inter_font']}" rel="stylesheet">
  <style>
    .reveal {{ font-family: 'Inter', sans-serif; }}
    .reveal .slides section {{ text-align: left; }}
    .reveal h1, .reveal h2 {{ color: #58a6ff; }}
    .reveal pre code {{ font-size: 0.7em; max-height: 400px; }}
    .reveal .progress {{ color: #58a6ff; }}
    .metric-card {{ background: #1e2a3a; border: 1px solid #30363d; border-radius: 8px;
                   padding: 1rem; display: inline-block; margin: 0.5rem; text-align: center; }}
    .metric-value {{ font-size: 2em; font-weight: 700; color: #58a6ff; }}
    .metric-label {{ color: #8b949e; font-size: 0.85em; }}
  </style>
</head>
<body>
<div class="reveal">
<div class="slides">
<!-- slides go here as <section> elements -->
</div>
</div>
<script src="{cdns['revealjs_js']}"></script>
<script src="{cdns['revealjs_highlight_js']}"></script>
<script src="{cdns['revealjs_math_js']}"></script>
<script src="{cdns['revealjs_notes_js']}"></script>
<script>
Reveal.initialize({{
  hash: true,
  slideNumber: 'c/t',
  transition: 'slide',
  plugins: [RevealHighlight, RevealMath.KaTeX, RevealNotes],
  math: {{ mathjax: '', katex: {{ delimiters: [{{ left:'$$', right:'$$', display:true }}, {{ left:'$', right:'$', display:false }}] }} }},
}});
</script>
</body>
</html>"""

    elif form in ("website", "page_blog"):
        chartjs_tag = f'  <script src="{cdns["chartjs"]}"></script>'
        d3_tag = f'  <script src="{cdns["d3_v7"]}"></script>'
        katex_tags = (
            f'  <link rel="stylesheet" href="{cdns["katex_css"]}">\n'
            f'  <script src="{cdns["katex_js"]}"></script>\n'
            f'  <script src="{cdns["katex_auto_render"]}"></script>'
        )
        return f"""\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="description" content="{title}">
  <title>{title}</title>
  <link href="{cdns['inter_font']}" rel="stylesheet">
  <link href="{cdns['jetbrains_mono']}" rel="stylesheet">
{katex_tags}
  <link rel="stylesheet" href="styles.css">
</head>
<body>
<div class="container">
  <!-- page content goes here -->
</div>
<script>
  // KaTeX auto-render
  document.addEventListener('DOMContentLoaded', () => renderMathInElement(document.body, {{
    delimiters: [
      {{left: '\\\\[', right: '\\\\]', display: true}},
      {{left: '\\\\(', right: '\\\\)', display: false}},
    ],
  }}));
</script>
{chartjs_tag}
{d3_tag}
  <script src="script.js"></script>
</body>
</html>"""

    elif form == "flowchart":
        return f"""\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <link href="{cdns['inter_font']}" rel="stylesheet">
{css_inline}
</head>
<body>
<div class="container">
  <h1>{title}</h1>
  <div class="mermaid">
    <!-- mermaid diagram goes here -->
  </div>
</div>
<script type="module">
  import mermaid from '{cdns["mermaid_esm"]}';
  mermaid.initialize({{ startOnLoad: true, theme: 'dark' }});
</script>
</body>
</html>"""

    else:
        # Generic dark page
        return f"""\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <link href="{cdns['inter_font']}" rel="stylesheet">
{css_inline}
</head>
<body>
<div class="container">
  <!-- content goes here -->
</div>
</body>
</html>"""


# ─────────────────────────────────────────────────────────────────────────────
# Public interface object — returned by BaseSkill._cdn_reference()
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class CodeQuality:
    """Provides verified CDN URLs, HTML boilerplate, and CSS snippets.

    Returned by ``BaseSkill._cdn_reference()``.

    Example::

        cq = self._cdn_reference()
        chartjs_url = cq.cdn("chartjs")
        skeleton = cq.html_boilerplate("website", title="My Demo")
        css = cq.dark_theme_css()
    """

    _cdns: Dict[str, str] = field(default_factory=lambda: dict(VERIFIED_CDNS))

    def cdn(self, key: str) -> str:
        """Return the URL for a specific CDN key.

        Raises KeyError if the key is unknown — this is intentional so callers
        don't silently get an empty string and embed a broken URL.
        """
        if key not in self._cdns:
            raise KeyError(
                f"Unknown CDN key: {key!r}. Available: {sorted(self._cdns)}"
            )
        return self._cdns[key]

    def all_cdns(self) -> Dict[str, str]:
        """Return a copy of all verified CDN URLs."""
        return dict(self._cdns)

    def dark_theme_css(self) -> str:
        """Return the standard dark-theme CSS reset string."""
        return DARK_THEME_CSS

    def html_boilerplate(
        self,
        form: str,
        title: str = "Paper Demo",
        dark: bool = True,
    ) -> str:
        """Return an HTML boilerplate skeleton for the given form.

        Args:
            form: 'presentation', 'website', 'page_blog', 'flowchart', or generic
            title: HTML <title> content
            dark: Include dark theme reset CSS

        Returns:
            HTML skeleton string
        """
        return html_boilerplate(form, title=title, dark=dark)

    def revealjs_init_script(
        self,
        plugins: Optional[list] = None,
        options: Optional[Dict] = None,
    ) -> str:
        """Return the Reveal.initialize() script block.

        Args:
            plugins: List of plugin names to enable (default: [RevealHighlight, RevealMath.KaTeX, RevealNotes])
            options: Additional Reveal.js options dict
        """
        _plugins = plugins or ["RevealHighlight", "RevealMath.KaTeX", "RevealNotes"]
        _opts = {
            "hash": True,
            "slideNumber": "'c/t'",
            "transition": "'slide'",
        }
        if options:
            _opts.update(options)
        plugin_str = ", ".join(_plugins)
        opts_str = ",\n  ".join(f"{k}: {v}" for k, v in _opts.items())
        return (
            f"Reveal.initialize({{\n"
            f"  {opts_str},\n"
            f"  plugins: [{plugin_str}],\n"
            f"}});"
        )

    def chartjs_snippet(
        self,
        canvas_id: str = "myChart",
        chart_type: str = "bar",
        labels: Optional[list] = None,
        data: Optional[list] = None,
        label: str = "Results",
    ) -> str:
        """Return a Chart.js initialization snippet for a simple chart.

        Args:
            canvas_id: HTML canvas element id
            chart_type: 'bar', 'line', 'radar', 'doughnut'
            labels: X-axis or category labels
            data: Data values
            label: Dataset label
        """
        _labels = labels or ["A", "B", "C"]
        _data = data or [1, 2, 3]
        return f"""\
const ctx_{canvas_id} = document.getElementById('{canvas_id}');
new Chart(ctx_{canvas_id}, {{
  type: '{chart_type}',
  data: {{
    labels: {_labels!r},
    datasets: [{{
      label: '{label}',
      data: {_data!r},
      backgroundColor: ['#58a6ff', '#79c0ff', '#56d364', '#e3b341', '#f85149'],
      borderRadius: 6,
    }}],
  }},
  options: {{
    responsive: true,
    plugins: {{ legend: {{ labels: {{ color: '#e6edf3' }} }} }},
    scales: {{
      x: {{ ticks: {{ color: '#8b949e' }}, grid: {{ color: '#30363d' }} }},
      y: {{ ticks: {{ color: '#8b949e' }}, grid: {{ color: '#30363d' }} }},
    }},
  }},
}});"""

    def __repr__(self) -> str:
        return f"CodeQuality(cdns={len(self._cdns)} entries)"
