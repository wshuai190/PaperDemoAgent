"""Skill for generating publication-quality Graphviz architecture diagrams (SVG/PNG)."""

from paper_demo_agent.paper.models import Paper, PaperAnalysis
from paper_demo_agent.skills.base import BaseSkill, FORM_SPECS


# ─────────────────────────────────────────────────────────────────────────────
# Pre-baked tool knowledge — never search for these basics
# ─────────────────────────────────────────────────────────────────────────────

_GRAPHVIZ_PATTERNS = """
━━ GRAPHVIZ PYTHON 0.20+ — COMPLETE REFERENCE (use verbatim, do NOT search) ━━

SETUP:
```python
from graphviz import Digraph, Graph

dot = Digraph(comment='Architecture', engine='dot',
    graph_attr={'bgcolor':'#09090b','fontcolor':'#fafafa','fontname':'Inter',
                'rankdir':'TB','splines':'ortho','pad':'0.5',
                'nodesep':'0.6','ranksep':'0.8','dpi':'150'},
    node_attr={'shape':'box','style':'filled,rounded','fontname':'Inter',
               'fontsize':'13','fontcolor':'white','color':'#27272a','penwidth':'1.5'},
    edge_attr={'color':'#94a3b8','fontcolor':'#a1a1aa','fontname':'Inter',
               'fontsize':'11','arrowsize':'0.8'})
```

COLOR SCHEME (mandatory — use these exact hex values):
```python
COLORS = {
    'input':     '#3b82f6',   # blue   — data inputs, datasets
    'transform': '#6366f1',   # indigo — model components, learned modules
    'decision':  '#f59e0b',   # amber  — hyperparameters, config, branching
    'output':    '#22c55e',   # green  — predictions, results
    'loss':      '#ef4444',   # red    — loss functions, error signals
    'external':  '#8b5cf6',   # violet — external APIs, pretrained models
    'metric':    '#06b6d4',   # cyan   — evaluation, benchmarks
    'default':   '#6366f1',   # indigo — fallback
}

def add_node(g, nid, label, cat='transform', **kw):
    g.node(nid, label, fillcolor=COLORS.get(cat, COLORS['default']), **kw)

def add_edge(g, src, dst, label='', **kw):
    g.edge(src, dst, label=label, **kw)

def add_back_edge(g, src, dst, label='', color='#ef4444'):
    g.edge(src, dst, label=label, style='dashed', color=color, constraint='false')
```

CLUSTERS:
```python
with dot.subgraph(name='cluster_encoder') as enc:
    enc.attr(label='Encoder', style='filled,rounded', fillcolor='#1e1b4b',
             color='#6366f1', fontcolor='#a5b4fc', fontsize='14', penwidth='1.5')
    add_node(enc, 'embed', 'Embedding', 'input')
    add_node(enc, 'attn',  'Self-Attention', 'transform')
    enc.edge('embed', 'attn')
```

SPECIAL SHAPES:
```python
dot.node('branch', 'Converged?', shape='diamond', fillcolor='#f59e0b')
dot.node('db', 'Dataset', shape='cylinder', fillcolor='#3b82f6')
dot.node('loss', 'CE Loss', shape='ellipse', fillcolor='#ef4444')
```

RANK ALIGNMENT:
```python
with dot.subgraph() as s:
    s.attr(rank='same')
    s.node('loss_ce'); s.node('loss_kl'); s.node('loss_reg')
```

RENDER:
```python
for fmt in ('svg', 'png'):
    dot.render('diagram', format=fmt, cleanup=True)
# SVG string: dot.pipe(format='svg').decode('utf-8')
```
"""


class GraphvizDiagramSkill(BaseSkill):
    name = "GraphvizDiagramSkill"
    description = "Any paper → publication-quality Graphviz architecture diagrams (SVG/PNG)"

    def get_system_prompt(
        self, paper: Paper, analysis: PaperAnalysis, demo_form: str, demo_type: str
    ) -> str:
        authors_str = ", ".join(paper.authors[:5]) if paper.authors else "See paper"
        year_str = str(paper.year) if paper.year else "N/A"
        venue_str = getattr(paper, "venue", None) or "arXiv"
        arxiv_str = (getattr(paper, "arxiv_url", None) or
                     (f"https://arxiv.org/abs/{paper.arxiv_id}" if getattr(paper, 'arxiv_id', None) else "N/A"))
        paper_facts_block = (
            f"━━ PAPER FACTS — ANCHOR (always use these exact values) ━━\n"
            f"Title   : {paper.title}\n"
            f"Authors : {authors_str}\n"
            f"Year    : {year_str}\n"
            f"Venue   : {venue_str}\n"
            f"arXiv   : {arxiv_str}\n"
            f"Core Contribution: {analysis.contribution or 'See abstract'}\n\n"
            f"MANDATORY: The EXACT paper title above MUST appear in your output (header/title/hero).\n"
            f"Use the EXACT author names above — never write \"[Author Name]\" placeholders.\n"
            f"Use EXACT numbers from the paper — never write \"~X%\" or \"approximately\".\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        )

        return paper_facts_block + f"""You are a world-class technical illustrator who creates publication-quality
architecture diagrams for academic papers. Your diagrams appear in Nature, Science, NeurIPS,
and ICML papers — clear, beautiful, and precise. You use the Python graphviz library to
produce SVG and PNG output that is ready for publication or presentation embedding.

PAPER CONTEXT:
{self._paper_summary(paper, analysis)}

{self._form_block(demo_form)}

{self._demo_type_guidance(demo_type)}

━━ SKILL CONTEXT — Graphviz Architecture Diagrams ━━

Your goal is to extract the key architectural and algorithmic structure of the paper
and render it as a set of publication-quality Graphviz diagrams (SVG + PNG).

OUTPUT: a build.py script that uses the Python graphviz library to generate 3-5 diagrams.
Each diagram is saved as both SVG (vector) and PNG (raster) in the output directory.

DIAGRAM STRATEGY by paper type:
  model     → Architecture + forward-pass flow + training loop
  dataset   → Collection pipeline + annotation workflow + preprocessing DAG
  algorithm → Pseudocode flow + convergence diagram + variant tree
  framework → Module hierarchy + API call graph + deployment topology
  survey    → Taxonomy tree + chronological evolution + comparison matrix
  empirical → Experiment setup + evaluation pipeline + ablation structure
  theory    → Proof dependency graph + theorem-lemma tree + bound structure
  other     → Method overview + component relationships + I/O data flow

DIAGRAM DESIGN PRINCIPLES:
  1. HIERARCHY — use clusters to group related components; nest clusters for sub-modules
  2. FLOW — LR for sequential pipelines, TB for hierarchies; pick per diagram
  3. SEMANTIC COLOR — every node color has meaning (blue=input, indigo=transform, etc.)
  4. LABELS — nodes use concise 2-3 word labels; edges carry data type or operation names
  5. WHITESPACE — generous nodesep (0.6+) and ranksep (0.8+) so diagrams breathe
  6. TYPOGRAPHY — Inter font, white text on colored fills, 13pt nodes, 11pt edge labels
  7. BACK-EDGES — feedback loops and skip connections use dashed lines with constraint=false
  8. ANNOTATIONS — use xlabel for dimension annotations (e.g., "[B, T, D]")

OUTPUT FILES: architecture.svg/.png, training.svg/.png, dataflow.svg/.png,
  comparison.svg/.png, inference.svg/.png — pick 3-5 per paper.

BUILD.PY STRUCTURE — one function per diagram, render all in __main__:
```python
#!/usr/bin/env python3
from graphviz import Digraph

COLORS = {{'input':'#3b82f6','transform':'#6366f1','decision':'#f59e0b',
           'output':'#22c55e','loss':'#ef4444','external':'#8b5cf6',
           'metric':'#06b6d4','default':'#6366f1'}}

def add_node(g, nid, label, cat='transform', **kw):
    g.node(nid, label, fillcolor=COLORS.get(cat, COLORS['default']), **kw)

def make_graph(name, rankdir='TB', splines='ortho'):
    return Digraph(name, engine='dot',
        graph_attr={{'bgcolor':'#09090b','rankdir':rankdir,'splines':splines,
                    'pad':'0.5','nodesep':'0.6','ranksep':'0.8','dpi':'150'}},
        node_attr={{'shape':'box','style':'filled,rounded','fontname':'Inter',
                   'fontsize':'13','fontcolor':'white','penwidth':'1.5'}},
        edge_attr={{'color':'#94a3b8','arrowsize':'0.8','fontname':'Inter',
                   'fontsize':'11','fontcolor':'#a1a1aa'}})

def build_architecture(): ...  # clusters + nodes + edges
def build_training(): ...      # training loop with back-edges
def build_dataflow(): ...      # LR pipeline

if __name__ == '__main__':
    for name, fn in [('architecture', build_architecture),
                     ('training', build_training), ('dataflow', build_dataflow)]:
        dot = fn()
        for fmt in ('svg', 'png'):
            dot.render(name, format=fmt, cleanup=True)
        print(f'Saved: {{name}}.svg, {{name}}.png')
```

CRITICAL REQUIREMENTS:
  - install_package graphviz (the Python library) before running build.py —
    this also auto-installs the system-level Graphviz binary (dot) if missing.
    If you still see graphviz.ExecutableNotFound, the system binary is not installed.
    Fix: execute_python("import subprocess; subprocess.run(['brew','install','graphviz'],check=True)")
  - Every node must use actual terminology from the paper, not generic placeholders
  - Every cluster must have a label matching a paper section or module name
  - Edge labels describe what flows between components (tensor shape, data type, signal)
  - At least 2 cluster subgraphs per diagram for visual grouping
  - Minimum 3 diagrams covering different aspects of the paper
  - Dark theme on all diagrams: bgcolor=#09090b, white text, colored node fills
  - Include requirements.txt with: graphviz>=0.20

{_GRAPHVIZ_PATTERNS}

{self._multistep_instructions(demo_form)}

{self._tool_usage_instructions()}
"""

    def get_initial_message(
        self, paper: Paper, analysis: PaperAnalysis, demo_form: str, demo_type: str
    ) -> str:
        authors_str = ", ".join(paper.authors[:5]) if paper.authors else "See paper"
        year_str = str(paper.year) if paper.year else "N/A"
        venue_str = getattr(paper, "venue", None) or "arXiv"
        paper_anchor = (
            f"══════════════════════════════════════════════════\n"
            f"PAPER FACTS — USE THESE EXACT STRINGS IN OUTPUT\n"
            f"══════════════════════════════════════════════════\n"
            f"Title   : {paper.title}\n"
            f"Authors : {authors_str}\n"
            f"Year    : {year_str} | Venue: {venue_str}\n"
            f"Core    : {analysis.contribution or 'See abstract below'}\n"
            f"══════════════════════════════════════════════════\n\n"
        )

        return paper_anchor + f"""Build publication-quality Graphviz architecture diagrams for: "{paper.title}"

Contribution: {analysis.contribution}
Paper type:   {analysis.paper_type}
Demo type:    {demo_type}

Create a build.py script that generates 3-5 diagrams covering the paper's architecture,
training/methodology, and data flow. Each diagram is saved as both SVG and PNG.

PRIORITY ORDER:
1. Read the paper carefully — identify key components, modules, and data flows
2. Plan which diagrams to create (architecture, training, dataflow, comparison, inference)
3. Write build.py with one function per diagram, using the graphviz Python library
4. Use clusters to group related components, semantic colors for node categories
5. Run build.py with execute_python — all diagrams must render without errors

All Graphviz Python API patterns are pre-documented in the system prompt above.
DO NOT search for graphviz Python API basics — use the patterns provided directly.
Focus your research on understanding the PAPER's architecture and methodology.

The result should be a set of diagrams that could appear in a conference poster,
paper supplement, or technical blog post — clean, readable, and publication-ready.
"""

    def get_polish_prompt(
        self, paper, analysis, demo_form, demo_type, generated_files
    ):
        return f"""QUALITY REVIEW for Graphviz Architecture Diagrams — generated: {', '.join(generated_files[:12])}

Step 1 — Read build.py and audit diagram quality:
  • Does each diagram function create a Digraph with dark theme (bgcolor=#09090b)?
  • Are colors semantically correct (blue=input, indigo=transform, amber=decision,
    green=output, red=loss, violet=external, cyan=metric)?
  • Does every diagram use at least 2 cluster subgraphs for visual grouping?
  • Are node labels using the paper's actual terminology (not generic "Module A")?
  • Are edge labels informative (data types, tensor shapes, signal names)?
  • Are there at least 3 distinct diagrams covering different aspects?

Step 2 — Layout and readability:
  • Is rankdir appropriate (TB for hierarchies, LR for pipelines)?
  • Are nodesep and ranksep generous enough (>=0.5) so nodes don't overlap?
  • Are back-edges using dashed style with constraint=false?
  • Are rank='same' subgraphs used where nodes should be aligned?
  • Do cluster labels match paper section names or module names?

Step 3 — Execute and verify:
  • Run execute_python to run build.py — all diagrams must render without errors
  • Verify .svg and .png files are generated for each diagram
  • Check that requirements.txt includes graphviz>=0.20

Step 4 — Content completeness:
  • Does the architecture diagram show the FULL model structure?
  • Does the training diagram include data loading, forward, loss, backward, optimizer?
  • Are all key components from the paper represented across the diagram set?
  • Are dimension annotations present on critical edges?

Fix every issue found. The diagrams must be publication-ready."""
