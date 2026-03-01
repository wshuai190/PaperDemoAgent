"""Skill for generating interactive flowchart/diagram demos — any paper type."""

from paper_demo_agent.paper.models import Paper, PaperAnalysis
from paper_demo_agent.skills.base import BaseSkill


# ─────────────────────────────────────────────────────────────────────────────
# Pre-baked tool knowledge — never search for these basics
# ─────────────────────────────────────────────────────────────────────────────

_GRAPHVIZ_PATTERNS = """
━━ GRAPHVIZ PYTHON 0.20+ — COMPLETE REFERENCE (use verbatim, do NOT search) ━━

BASIC SETUP:
```python
from graphviz import Digraph, Graph

# Dark-themed directed graph
dot = Digraph(
    comment='Architecture',
    engine='dot',       # use 'neato' for undirected, 'circo' for circular
    graph_attr={
        'bgcolor': '#09090b',
        'fontcolor': '#fafafa',
        'fontname': 'Inter',
        'rankdir': 'TB',    # TB=top→bottom, LR=left→right
        'splines': 'ortho', # 'curved', 'polyline', 'ortho', 'spline'
        'pad': '0.5',
        'nodesep': '0.6',
        'ranksep': '0.8',
    },
    node_attr={
        'shape': 'box',
        'style': 'filled,rounded',
        'fontname': 'Inter',
        'fontsize': '13',
        'fontcolor': 'white',
        'color': '#27272a',
        'penwidth': '1.5',
    },
    edge_attr={
        'color': '#94a3b8',
        'fontcolor': '#a1a1aa',
        'fontname': 'Inter',
        'fontsize': '11',
        'arrowsize': '0.8',
    }
)
```

NODE COLORS (use these exact hex values matching Mermaid color scheme):
```python
COLORS = {
    'input':     '#3b82f6',   # blue   — data inputs, datasets
    'transform': '#6366f1',   # indigo — model components, learned modules
    'decision':  '#f59e0b',   # amber  — hyperparameters, config, branching
    'output':    '#22c55e',   # green  — predictions, results
    'loss':      '#ef4444',   # red    — loss functions, error signals
    'external':  '#8b5cf6',   # violet — external APIs, pretrained models
    'metric':    '#06b6d4',   # cyan   — evaluation, benchmarks
    'default':   '#6366f1',   # indigo
}

def add_node(dot, node_id, label, color='transform', tooltip=''):
    dot.node(node_id, label,
             fillcolor=COLORS.get(color, COLORS['default']),
             tooltip=tooltip)

def add_edge(dot, src, dst, label='', color='#94a3b8'):
    dot.edge(src, dst, label=label, color=color)
```

CLUSTER SUBGRAPHS (group related nodes):
```python
with dot.subgraph(name='cluster_encoder') as enc:
    enc.attr(
        label='Encoder',
        style='filled,rounded',
        fillcolor='#1e1b4b',   # dark indigo background
        color='#6366f1',       # accent border
        fontcolor='#a5b4fc',
        fontsize='12',
        penwidth='1.5',
    )
    enc.node('embed', 'Token\nEmbedding', fillcolor='#3b82f6')
    enc.node('attn',  'Multi-Head\nAttention', fillcolor='#6366f1')
    enc.node('ffn',   'Feed-Forward\nNetwork', fillcolor='#6366f1')
    enc.edge('embed', 'attn')
    enc.edge('attn', 'ffn')
```

RENDER TO SVG STRING (for inline HTML embedding):
```python
# Returns SVG bytes — strip XML header for inline HTML
svg_bytes = dot.pipe(format='svg')
svg_str = svg_bytes.decode('utf-8')
# Strip XML declaration and DOCTYPE for safe HTML embedding:
svg_inline = svg_str[svg_str.find('<svg'):]

# Write SVG file:
dot.render('diagram', format='svg', cleanup=True)
# Produces 'diagram.svg'
```

PIPELINE EXAMPLE (encode → decode architecture):
```python
from graphviz import Digraph

def build_architecture_diagram():
    dot = Digraph('arch', engine='dot',
        graph_attr={'bgcolor':'#09090b','rankdir':'LR','splines':'ortho'},
        node_attr={'shape':'box','style':'filled,rounded','fontname':'Inter',
                   'fontsize':'12','fontcolor':'white','penwidth':'1.5'},
        edge_attr={'color':'#94a3b8','arrowsize':'0.8'})

    # Input
    dot.node('inp', 'Input\nTokens', fillcolor='#3b82f6')

    # Encoder cluster
    with dot.subgraph(name='cluster_enc') as c:
        c.attr(label='Encoder', style='filled', fillcolor='#1e1b4b',
               color='#6366f1', fontcolor='#a5b4fc')
        c.node('emb', 'Embedding', fillcolor='#3b82f6')
        c.node('enc_attn', 'Self-Attention', fillcolor='#6366f1')
        c.node('enc_ffn', 'FFN', fillcolor='#6366f1')
        c.edge('emb', 'enc_attn')
        c.edge('enc_attn', 'enc_ffn')

    # Output
    dot.node('out', 'Output\nLogits', fillcolor='#22c55e')

    dot.edge('inp', 'emb')
    dot.edge('enc_ffn', 'out')
    return dot

svg = build_architecture_diagram().pipe(format='svg').decode()
svg_inline = svg[svg.find('<svg'):]
```

SEQUENCE-STYLE DIAGRAM (training loop):
```python
def build_training_loop():
    dot = Digraph('train', engine='dot',
        graph_attr={'bgcolor':'#09090b','rankdir':'TB'},
        node_attr={'shape':'box','style':'filled,rounded','fontname':'Inter',
                   'fontsize':'12','fontcolor':'white'})

    dot.node('data',    'Data Batch',          fillcolor='#3b82f6')
    dot.node('forward', 'Forward Pass',         fillcolor='#6366f1')
    dot.node('loss',    'Compute Loss',         fillcolor='#ef4444')
    dot.node('backward','Backward Pass',        fillcolor='#f59e0b')
    dot.node('update',  'Optimizer Step',       fillcolor='#8b5cf6')
    dot.node('ckpt',    'Checkpoint?',          fillcolor='#f59e0b', shape='diamond')
    dot.node('save',    'Save Model',           fillcolor='#22c55e')

    dot.edge('data', 'forward')
    dot.edge('forward', 'loss')
    dot.edge('loss', 'backward')
    dot.edge('backward', 'update')
    dot.edge('update', 'ckpt')
    dot.edge('ckpt', 'save',  label='Yes')
    dot.edge('ckpt', 'data',  label='No', constraint='false')  # back-edge
    return dot
```

EMBED GRAPHVIZ SVG IN HTML:
```html
<div id="diagram-container" style="background:#09090b; padding:16px; border-radius:8px;">
  <!-- Paste svg_inline here — generated by dot.pipe(format='svg').decode() -->
  <svg ...>...</svg>
</div>
<script>
  // Make SVG nodes clickable
  document.querySelectorAll('#diagram-container svg [id]').forEach(el => {
    el.style.cursor = 'pointer';
    el.addEventListener('click', () => showDetail(el.id));
  });
</script>
```
"""

_ICON_GUIDE = """
━━ ICON STRATEGY — Font Awesome 6 (zero downloads, zero searches) ━━

Add this ONE CDN link in <head> and you get hundreds of icons instantly:
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.6.0/css/all.min.css">

USAGE:
  <i class="fa-solid fa-brain" style="color:#6366f1"></i>          — brain / neural network
  <i class="fa-solid fa-database" style="color:#3b82f6"></i>       — dataset / storage
  <i class="fa-solid fa-diagram-project" style="color:#f59e0b"></i> — pipeline / flow
  <i class="fa-solid fa-gears" style="color:#22c55e"></i>          — training / optimization
  <i class="fa-solid fa-magnifying-glass"></i>                      — search / attention
  <i class="fa-solid fa-layer-group"></i>                           — layers / encoder / decoder
  <i class="fa-solid fa-chart-line"></i>                            — results / metrics
  <i class="fa-solid fa-bolt"></i>                                  — inference / speed
  <i class="fa-solid fa-code"></i>                                  — code / implementation
  <i class="fa-solid fa-arrows-spin"></i>                           — loop / iteration
  <i class="fa-solid fa-cube"></i>                                  — model / module
  <i class="fa-solid fa-arrow-right-arrow-left"></i>               — encoder-decoder / transform
  <i class="fa-solid fa-wave-square"></i>                           — signal / embedding
  <i class="fa-solid fa-fire"></i>                                  — loss / gradient
  <i class="fa-solid fa-shuffle"></i>                               — augmentation / dropout

BRAND ICONS (for tech logos):
  <i class="fa-brands fa-python"></i>   <i class="fa-brands fa-github"></i>
  <i class="fa-brands fa-google"></i>   <i class="fa-brands fa-docker"></i>

SIMPLE ICONS CDN (for ML brand logos not in Font Awesome):
  <img src="https://cdn.simpleicons.org/pytorch/ffffff" height="20">
  <img src="https://cdn.simpleicons.org/tensorflow/ffffff" height="20">
  <img src="https://cdn.simpleicons.org/huggingface/ffffff" height="20">

WHERE TO USE: header, legend, section titles, diagram node annotations, feature cards.
DO NOT web_search for icons. DO NOT download from flaticon.com. Use Font Awesome classes directly.
"""


class FlowchartGeneratorSkill(BaseSkill):
    name = "FlowchartGeneratorSkill"
    description = "Any paper → interactive Mermaid.js diagram explorer (with Graphviz SVG assets)"

    def get_system_prompt(
        self, paper: Paper, analysis: PaperAnalysis, demo_form: str, demo_type: str
    ) -> str:
        return f"""You are a world-class information architect and interactive diagram engineer.
Your specialty: turning dense academic papers into beautiful, explorable diagrams
that let readers navigate the methodology intuitively.

PAPER CONTEXT:
{self._paper_summary(paper, analysis)}

{self._form_block(demo_form)}

{self._demo_type_guidance(demo_type)}

━━ SKILL CONTEXT — Flowchart / Diagram Explorer ━━

Your goal is to extract the FULL computational and conceptual structure of the paper
and render it as a set of interactive, linked diagrams.

DIAGRAM STRATEGY by paper type:
  model       → Architecture diagram + forward-pass flow + training loop + inference pipeline
  dataset     → Collection pipeline + annotation flow + data processing DAG + split statistics
  algorithm   → Pseudocode flow + convergence diagram + complexity comparison + variant tree
  framework   → Module hierarchy + API call graph + deployment flow + extension points
  survey      → Taxonomy tree + chronological timeline + comparison matrix + citation network
  empirical   → Experiment setup flow + data pipeline + evaluation protocol + result hierarchy
  theory      → Proof structure + concept dependency graph + theorem → lemma → corollary chain
  other       → Method overview + key steps + component relationships + I/O data flow

COLOR CODING (mandatory, use these exact hex values across ALL diagrams):
  #3b82f6  blue    → Inputs, data, datasets
  #6366f1  indigo  → Core transforms, model components, learned modules
  #f59e0b  amber   → Decision points, hyperparameters, configuration nodes
  #22c55e  green   → Outputs, predictions, final results
  #ef4444  red     → Loss functions, error signals, failure modes
  #8b5cf6  violet  → External tools, APIs, pre-trained models
  #06b6d4  cyan    → Evaluation metrics, benchmarks, comparisons

MERMAID V11 SYNTAX REQUIREMENTS:
  • Always use `%%{{init: {{'theme':'base','themeVariables':{{'primaryColor':'#6366f1',
    'primaryTextColor':'#fff','primaryBorderColor':'#4f46e5','lineColor':'#94a3b8',
    'secondaryColor':'#1e1b4b','tertiaryColor':'#18181b','background':'#09090b',
    'mainBkg':'#111113','nodeBorder':'#27272a','clusterBkg':'#18181b',
    'titleColor':'#fafafa','edgeLabelBackground':'#18181b','fontSize':'16px'}}}}}}%%`
    at the top of every diagram definition
  • Use `flowchart TD` (not `graph TD`) for main pipeline diagrams
  • Use `sequenceDiagram` for training/inference loops
  • Use `mindmap` for concept hierarchies and taxonomy trees
  • Node IDs must be simple alphanumeric (e.g., `A`, `enc1`, `loss_fn`) — no spaces
  • Node labels can use HTML-like formatting: `A["<b>Encoder</b><br/>d=512"]`
  • Edge labels: `A -->|"attention weights"| B`

CRITICAL — TAB + RENDERING ARCHITECTURE (prevents diagram collision):

  ⚠️  DO NOT use `startOnLoad: true` — it renders ALL diagrams at once and causes collisions.
  ⚠️  DO NOT put all .mermaid divs in the DOM visible at once.

  CORRECT PATTERN — lazy per-tab rendering:
  ```javascript
  // ESM import + initialize with startOnLoad: false
  import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs';
  mermaid.initialize({{
    startOnLoad: false,   // ← MUST be false — we render manually per tab
    theme: 'base',
    themeVariables: {{ primaryColor: '#6366f1', /* ... rest of theme vars */ }}
  }});

  const renderedTabs = new Set();   // track which tabs have been rendered

  async function switchTab(tabId) {{
    // 1. Hide all panels + deactivate all tab buttons
    document.querySelectorAll('.diagram-panel').forEach(p => p.style.display = 'none');
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));

    // 2. Show the selected panel
    const panel = document.getElementById('panel-' + tabId);
    panel.style.display = 'flex';   // use flex so canvas + detail panel sit side by side
    document.querySelector(`.tab-btn[data-tab="${{tabId}}"]`).classList.add('active');

    // 3. Lazy-render Mermaid only if this tab hasn't been rendered yet
    if (!renderedTabs.has(tabId)) {{
      renderedTabs.add(tabId);
      const mermaidEl = panel.querySelector('.mermaid');
      if (mermaidEl) {{
        await mermaid.run({{ nodes: [mermaidEl] }});   // render only this element
        attachHandlers(panel);   // attach click/hover handlers after SVG is in DOM
      }}
    }}
  }}

  // Initialize — only render the first tab on load
  window.addEventListener('load', () => switchTab('pipeline'));
  ```

  CSS FOR PANEL ISOLATION (prevents overflow + collision):
  ```css
  .diagram-panel {{
    display: none;           /* hidden by default */
    gap: 12px;
    overflow: hidden;        /* clip content to panel bounds */
    height: calc(100vh - 200px);
    min-height: 500px;
  }}
  .diagram-panel.shown {{ display: flex; }}

  #diagram-canvas {{
    flex: 1;
    overflow: hidden;        /* CRITICAL — clip the SVG, don't let it bleed */
    position: relative;
    background: var(--bg2);
    border-radius: 8px;
    border: 1px solid var(--border);
  }}

  .mermaid {{
    display: block;
    transform-origin: top left;   /* zoom/pan anchor */
    will-change: transform;
  }}
  ```

  HTML PANEL STRUCTURE (one panel per tab, each with its own .mermaid div):
  ```html
  <!-- Tab buttons -->
  <div class="tab-bar">
    <button class="tab-btn active" data-tab="pipeline"   onclick="switchTab('pipeline')">Pipeline</button>
    <button class="tab-btn"        data-tab="training"   onclick="switchTab('training')">Training</button>
    <button class="tab-btn"        data-tab="inference"  onclick="switchTab('inference')">Inference</button>
    <button class="tab-btn"        data-tab="concepts"   onclick="switchTab('concepts')">Concepts</button>
  </div>

  <!-- One panel per tab — each has its OWN .mermaid div, never shared -->
  <div id="panel-pipeline" class="diagram-panel">
    <div id="diagram-canvas">
      <div class="mermaid">
        %%{{init: ...}}%%
        flowchart TD
          A["Input"] --> B["Encoder"]
          B --> C["Output"]
      </div>
    </div>
    <div id="detail-panel"><!-- detail panel --></div>
  </div>

  <div id="panel-training" class="diagram-panel" style="display:none">
    <div id="diagram-canvas-2">
      <div class="mermaid">
        %%{{init: ...}}%%
        flowchart TD
          D["Data"] --> E["Forward"] --> F["Loss"]
      </div>
    </div>
    <div id="detail-panel-2"><!-- detail panel --></div>
  </div>
  <!-- ... more panels ... -->
  ```

  ⚠️  Each panel MUST have a UNIQUE id for diagram-canvas and detail-panel
      (e.g., diagram-canvas, diagram-canvas-2, diagram-canvas-3, diagram-canvas-4)

  NODE CLICK HANDLER (after mermaid.run() completes):
  ```javascript
  function attachHandlers(panel) {{
    panel.querySelectorAll('svg .node, svg .cluster').forEach(node => {{
      const rawId = node.querySelector('[id]')?.id || node.id || '';
      // Mermaid adds prefix like "flowchart-A-0" — extract the original node ID
      const id = rawId.replace(/^.*?-([A-Za-z0-9_]+)-[0-9]+$/, '$1') || rawId;
      if (!id) return;
      node.style.cursor = 'pointer';
      node.addEventListener('click', (e) => {{
        e.stopPropagation();
        showDetail(panel, id);
      }});
    }});
  }}
  ```

  DETAIL PANEL DATA STRUCTURE:
  ```javascript
  const nodeDetails = {{
    'A': {{ title: 'Input Data', desc: 'Raw text or image fed into the pipeline.',
             section: 'Section 3.1', code: 'x = tokenizer(raw_input, return_tensors="pt")' }},
    'B': {{ title: 'Encoder', desc: 'Transforms input into latent representation.',
             section: 'Section 3.2', code: 'z = encoder(x)  # [B, seq_len, d_model]' }},
    // ... one entry per node
  }};

  function showDetail(nodeId) {{
    const d = nodeDetails[nodeId];
    if (!d) return;
    document.querySelector('#detail-title').textContent = d.title;
    document.querySelector('#detail-desc').textContent = d.desc;
    document.querySelector('#detail-section').textContent = 'Ref: ' + d.section;
    document.querySelector('#detail-code').textContent = d.code || '';
  }}
  ```

  ZOOM + PAN:
  ```javascript
  let zoom = 1, panX = 0, panY = 0, dragging = false, startX, startY;
  const canvas = document.querySelector('#diagram-canvas');

  canvas.addEventListener('wheel', e => {{
    e.preventDefault();
    zoom = Math.max(0.3, Math.min(3, zoom * (e.deltaY > 0 ? 0.9 : 1.1)));
    canvas.style.transform = `scale(${{zoom}}) translate(${{panX}}px, ${{panY}}px)`;
  }}, {{ passive: false }});

  canvas.addEventListener('pointerdown', e => {{ dragging=true; startX=e.clientX-panX; startY=e.clientY-panY; }});
  canvas.addEventListener('pointermove', e => {{
    if (!dragging) return;
    panX = e.clientX - startX; panY = e.clientY - startY;
    canvas.style.transform = `scale(${{zoom}}) translate(${{panX}}px, ${{panY}}px)`;
  }});
  canvas.addEventListener('pointerup', () => dragging = false);
  ```

  SEARCH + HIGHLIGHT:
  ```javascript
  document.querySelector('#search').addEventListener('input', e => {{
    const q = e.target.value.toLowerCase();
    document.querySelectorAll('.mermaid svg .node text').forEach(t => {{
      const matches = t.textContent.toLowerCase().includes(q) && q.length > 0;
      t.closest('.node').style.opacity = (!q || matches) ? '1' : '0.2';
    }});
  }});
  ```

  STEP-BY-STEP WALKTHROUGH:
  ```javascript
  const walkthrough = ['A', 'B', 'C', 'D'];  // node IDs in execution order
  let stepIdx = 0;
  document.querySelector('#next-step').onclick = () => {{
    if (stepIdx < walkthrough.length - 1) {{
      stepIdx++;
      highlightNode(walkthrough[stepIdx]);
      showDetail(walkthrough[stepIdx]);
      document.querySelector('#step-counter').textContent =
        `Step ${{stepIdx + 1}} / ${{walkthrough.length}}`;
    }}
  }};
  ```

LAYOUT SPEC:
  ┌────────────────────────────────────────────────────────────────┐
  │ header: title | authors | arXiv link   [logos]  [dark toggle] │
  ├────────────────────────────────────────────────────────────────┤
  │ tab bar: [Pipeline] [Training] [Inference] [Concepts]         │
  │ search: [___________________] [Step 1/N] [< Prev] [Next >]    │
  ├───────────────────────────────────────┬────────────────────────┤
  │                                       │ DETAIL PANEL           │
  │   DIAGRAM CANVAS                      │ ─────────────────────  │
  │   (Mermaid SVG, zoomable/pannable)    │ [Node Title]           │
  │                                       │ [Description]          │
  │                                       │ [Section: X.Y]         │
  │                                       │ [Pseudocode block]     │
  ├───────────────────────────────────────┴────────────────────────┤
  │ [Copy Mermaid Source]  [Download SVG]  ── LEGEND ──  [logos]   │
  └────────────────────────────────────────────────────────────────┘

{_GRAPHVIZ_PATTERNS}

{_ICON_GUIDE}

ICON INTEGRATION IN FLOWCHART HTML:
  1. Add Font Awesome CDN link in <head> (see ICON STRATEGY above)
  2. Use <i class="fa-solid fa-..."> icons in header, legend, and section titles
  3. Use Simple Icons CDN <img> tags for ML brand logos (pytorch, tensorflow, etc.)
  4. DO NOT search for icons — all icons are available via CDN, zero downloads needed

QUALITY CHECKLIST:
  □ All 4 diagram tabs are fully implemented with real paper content
  □ Every node has a nodeDetails entry (no blank detail panels)
  □ Color coding is consistent across all diagrams
  □ Zoom and pan work smoothly without jitter
  □ Search highlights nodes within 200ms of typing
  □ Step-by-step walkthrough covers the critical path through the algorithm
  □ Dark theme passes WCAG AA contrast (4.5:1 minimum)
  □ Export buttons work: SVG download produces a valid SVG file
  □ Font Awesome icons displayed in header/legend (no downloaded PNGs)
  □ Mobile-responsive: stacks vertically below 768px

{self._multistep_instructions(demo_form)}

{self._tool_usage_instructions()}
"""

    def get_polish_prompt(self, paper, analysis, demo_form, demo_type, generated_files):
        return f"""QUALITY REVIEW for Flowchart Explorer — generated: {', '.join(generated_files[:12])}

Step 1 — Read index.html and check for collision bugs:
  • Is `startOnLoad: false` set in mermaid.initialize()? (CRITICAL — if true, all diagrams render at once → collision)
  • Does each tab have its OWN separate panel div and its OWN .mermaid div?
  • Does `switchTab()` call `mermaid.run({{nodes:[el]}})` for the specific panel element?
  • Is diagram-canvas overflow: hidden so SVGs don't bleed out of their container?
  • Are all 4 diagram tabs implemented with real paper content (not placeholder "TODO")?
  • Is every node in nodeDetails (no node without an explanation)?

Step 2 — Interactivity:
  • Does clicking a node update the detail panel (title, desc, section, code)?
  • Do zoom (scroll wheel) and pan (drag) work?
  • Does the search bar dim non-matching nodes?
  • Do Next/Prev buttons walk through the step-by-step sequence?

Step 3 — Visual quality + logos:
  • Are all colors using the specified hex values (#3b82f6 blue, #6366f1 indigo, etc.)?
  • Is the dark theme applied to all Mermaid diagrams via themeVariables?
  • Are legend and export buttons (Copy Mermaid / Download SVG) implemented?
  • Are technology logos fetched from Simple Icons CDN and shown in header/legend?
    If not: use download_file to fetch relevant logos now.

Step 4 — Content:
  • Do node labels use the actual terminology from the paper?
  • Are edge labels informative (not just arrows)?
  • Does the header show paper title, authors, and arXiv link?

Fix every issue found. The result must be a fully interactive diagram explorer."""

    def get_initial_message(
        self, paper: Paper, analysis: PaperAnalysis, demo_form: str, demo_type: str
    ) -> str:
        return f"""Build an interactive flowchart explorer for: "{paper.title}"

Contribution: {analysis.contribution}
Paper type:   {analysis.paper_type}
Demo type:    {demo_type}

Extract the full algorithmic and conceptual structure of this paper.
Create 4 diagram tabs that give readers different views of the methodology.
Make every node clickable with detailed explanations.

Use download_file to fetch technology logos from Simple Icons CDN and display
them in the header/legend panel (e.g., PyTorch, TensorFlow, HuggingFace logos).

All Mermaid.js and JavaScript patterns are pre-documented in the system prompt above.
DO NOT search for Mermaid.js CDN or syntax — use the patterns provided directly.

Follow the numbered execution plan. The result should feel like a mini
interactive textbook for this paper — not just a static diagram.
"""
