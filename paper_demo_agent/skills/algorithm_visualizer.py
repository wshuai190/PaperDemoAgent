"""Skill for algorithm papers — adapts to any demo form."""

from paper_demo_agent.paper.models import Paper, PaperAnalysis
from paper_demo_agent.skills.base import BaseSkill, FORM_SPECS


class AlgorithmVisualizerSkill(BaseSkill):
    name = "AlgorithmVisualizerSkill"
    description = "Algorithm paper → interactive step-by-step visualizer"

    def get_system_prompt(self, paper: Paper, analysis: PaperAnalysis, demo_form: str, demo_type: str) -> str:
        return f"""You are an expert algorithm educator who creates the kind of interactive
visualizations that make concepts click instantly — think VisuAlgo, Algorithm Visualizer,
and 3Blue1Brown-style animations in the browser.

PAPER CONTEXT:
{self._paper_summary(paper, analysis)}

{self._form_block(demo_form)}

{self._demo_type_guidance(demo_type)}

━━ SKILL CONTEXT — Algorithm Paper ━━

RESEARCH PHASE — search for these BEFORE writing any code:
  1. web_search("{paper.title} arxiv") → get arXiv URL for citation links
  2. web_search("{paper.title} github implementation") → find reference implementations
  3. web_search("{paper.title} benchmark comparison") → verify reported numbers vs baselines
  4. web_search("{analysis.hf_model_query} algorithm visualization") → find existing visualizations for inspiration
  If the algorithm is a variant of a well-known method (e.g., sorting, graph, optimization):
  5. web_search("VisuAlgo {{algorithm_type}}") → see how similar algorithms are visualized

STEP 0 — DECODE THE ALGORITHM
From the paper, identify:
  • Input/output types: graph, array, text, matrix, set, numbers?
  • Core operation: sort, search, optimize, cluster, route, sample, compress?
  • Iterative or recursive? Single-pass or multi-pass?
  • What state changes at each step?

ALGORITHM IMPLEMENTATION STRATEGY:
  1. Implement the algorithm as a GENERATOR in Python that yields state at each step:
     ```python
     def algorithm_step_by_step(input_data, **params):
         state = initialize(input_data)
         yield ("init", state)  # (label, state_snapshot)
         for step in range(max_steps):
             state = update(state, **params)
             yield (f"Step {{step+1}}: {{describe_what_happened(state)}}", state)
         yield ("done", state)
     ```
  2. Store all yielded states in a list → slider over them for "rewind/forward" UX

VISUALIZATION PATTERNS (pick based on algorithm type):

  # ARRAY/SEQUENCE ALGORITHM → Plotly bar chart that animates:
  ```python
  import plotly.graph_objects as go

  def visualize_array_state(arr, highlight_indices=None, title=""):
      colors = ["#6366f1"] * len(arr)
      if highlight_indices:
          for i in highlight_indices: colors[i] = "#ef4444"
      fig = go.Figure(go.Bar(y=arr, marker_color=colors))
      fig.update_layout(title=title, template="plotly_dark",
                        showlegend=False, margin=dict(t=40, b=20))
      return fig
  ```

  # GRAPH ALGORITHM → NetworkX + Plotly:
  ```python
  import networkx as nx, plotly.graph_objects as go

  def draw_graph(G, highlighted_nodes=None, highlighted_edges=None):
      pos = nx.spring_layout(G, seed=42)
      edge_x, edge_y = [], []
      for u, v in G.edges():
          edge_x += [pos[u][0], pos[v][0], None]
          edge_y += [pos[u][1], pos[v][1], None]
      node_x = [pos[n][0] for n in G.nodes()]
      node_y = [pos[n][1] for n in G.nodes()]
      colors = ["#ef4444" if n in (highlighted_nodes or []) else "#6366f1"
                for n in G.nodes()]
      fig = go.Figure()
      fig.add_trace(go.Scatter(x=edge_x, y=edge_y, mode="lines",
                               line=dict(color="#334155", width=1)))
      fig.add_trace(go.Scatter(x=node_x, y=node_y, mode="markers+text",
                               marker=dict(size=20, color=colors),
                               text=list(G.nodes()), textposition="top center"))
      fig.update_layout(template="plotly_dark", showlegend=False,
                        xaxis=dict(showgrid=False, zeroline=False),
                        yaxis=dict(showgrid=False, zeroline=False))
      return fig
  ```

  # OPTIMIZATION ALGORITHM → Loss/objective convergence curve:
  ```python
  def plot_convergence(history):
      fig = go.Figure()
      fig.add_trace(go.Scatter(y=history, mode="lines+markers",
                               line=dict(color="#22c55e", width=2)))
      fig.update_layout(title="Convergence", xaxis_title="Iteration",
                        yaxis_title="Objective", template="plotly_dark")
      return fig
  ```

GRADIO LAYOUT BLUEPRINT (for app form):
  ```python
  with gr.Blocks(theme=gr.themes.Soft(), css=CSS) as demo:
      gr.HTML(HEADER)
      with gr.Tabs():
          with gr.TabItem("▶ Step-by-step"):
              with gr.Row():
                  with gr.Column(scale=1):
                      # Input configuration
                      size_slider = gr.Slider(4, 20, value=10, label="Input size")
                      seed_input  = gr.Number(value=42, label="Random seed")
                      param_sliders = [...]  # algorithm-specific params
                      run_btn = gr.Button("Run Algorithm", variant="primary")
                  with gr.Column(scale=2):
                      viz_plot = gr.Plot(label="Visualization")
                      step_slider = gr.Slider(0, 100, step=1, label="Step",
                                              interactive=True)
                      step_label = gr.Textbox(label="What happened", interactive=False)
          with gr.TabItem("📈 Analysis"):
              convergence_plot = gr.Plot(label="Convergence / Complexity")
              complexity_md = gr.Markdown(COMPLEXITY_MD)
          with gr.TabItem("⚡ Compare"):
              compare_plot = gr.Plot(label="vs. Baseline methods")
              comparison_table = gr.Dataframe(label="Benchmark results")
          with gr.TabItem("📖 About"):
              gr.Markdown(ABOUT_MD)
  ```

COMPARISON SECTION (use real numbers from paper):
  • Hardcode the paper's benchmark table: algorithm vs. baselines
  • Metrics: runtime complexity, accuracy/quality, memory usage
  • Create a bar chart comparing all methods side by side

PSEUDOCODE DISPLAY (always include):
  • Show the pseudocode as a code block in markdown with line numbers
  • Link each step in the visualization to a line in the pseudocode
  • Highlight the "current line" as the algorithm progresses

FORM ADAPTATION — when the demo form is NOT 'app':

  PRESENTATION (reveal.js):
    • Slide 1: Title + algorithm name + key complexity result
    • Slide 2: Problem — what does this algorithm solve? (with concrete example)
    • Slide 3: Pseudocode slide (syntax-highlighted code block)
    • Slide 4-7: Step-by-step walkthrough — each slide shows one algorithm step
      using data-auto-animate to smoothly transition between states.
      Use inline SVG to draw array states, graph states, or tree structures.
    • Slide 8: Complexity analysis (time + space, with comparison table)
    • Slide 9: Benchmark results vs baselines (grouped bar chart as SVG)
    • Slide 10-11: Real-world applications and examples
    • Slide 12: Limitations and edge cases
    • Slide 13: Conclusion + BibTeX → Slide 14: Q&A

  WEBSITE (static HTML):
    • Hero: algorithm name, one-line description, complexity badges
    • Interactive section: step slider that updates an SVG visualization
      (use vanilla JS to animate array bars, graph nodes, or matrix cells)
    • Pseudocode panel with line highlighting synchronized to step slider
    • Performance comparison: Chart.js bar chart with real numbers
    • Complexity analysis section with formal proofs (KaTeX)
    • BibTeX + copy button

  SLIDES / LATEX:
    • Extract algorithm pseudocode figures from the PDF using extract_pdf_page
    • Use TikZ or matplotlib to create step-by-step diagrams
    • Hard-code ALL benchmark comparison numbers as tables
    • Show complexity analysis with formal notation

FIGURE INTEGRATION (for slides/latex/presentation forms):
  • Use extract_pdf_page to get the paper's own algorithm diagrams and result figures
  • Embed extracted figures in the relevant slides
  • Reproduce comparison tables as structured data (not image embeds)

{self._multistep_instructions(demo_form)}

{self._tool_usage_instructions()}
"""

    def get_initial_message(self, paper: Paper, analysis: PaperAnalysis, demo_form: str, demo_type: str) -> str:
        return f"""Build a {demo_form} interactive algorithm visualizer for: "{paper.title}"

Contribution: {analysis.contribution}
Demo type: {demo_type}
Interaction: {analysis.interaction_pattern}

PRIORITY ORDER:
1. Implement the algorithm as a Python generator that yields state at each step
2. Build the step-by-step visualizer with a slider to navigate steps
3. Add parameter controls (sliders/inputs) to explore algorithm behavior
4. Compare against the baseline methods using real numbers from the paper

Make the algorithm feel TANGIBLE — users should be able to watch it work,
slow it down, and understand why each step happens. Follow the execution plan.
"""

    def get_polish_prompt(self, paper, analysis, demo_form, demo_type, generated_files):
        spec = FORM_SPECS.get(demo_form, {})
        main_file = spec.get("main_file", "app.py")
        figures_available = [f for f in generated_files if f.startswith("figures/")]

        base_checks = f"""QUALITY REVIEW for Algorithm Visualizer — generated: {', '.join(generated_files[:12])}

Step 1 — Read {main_file} and verify:
  • Is the algorithm implemented correctly (not a stub)?
  • Are benchmark numbers from the paper hardcoded in the comparison section?
  • Is time/space complexity stated clearly?
  • Is there a pseudocode block or algorithm description?"""

        if demo_form == "app":
            return base_checks + f"""
Step 2 — Interactivity:
  • Does the step slider show the correct state at each step (not just the final)?
  • Are plots dark-themed (template="plotly_dark")?
  • Do parameter sliders actually affect the algorithm's behavior?
  • Can users click "Run" and immediately see something happen?
  • Are the step descriptions clear and informative (not just "Step 3")?
  • Does the "Compare" tab show at least 3 methods with real metrics?

Step 3 — UX polish:
  • Does the header show paper title and authors?
  • Does the About tab have abstract and BibTeX?

Rewrite anything that falls short. The visualization should make the algorithm
impossible NOT to understand."""
        elif demo_form == "presentation":
            return base_checks + f"""
Step 2 — Slide-specific checks:
  • Are there >=14 slides covering the full algorithm story?
  • Do step-by-step slides use data-auto-animate for smooth transitions?
  • Are there inline SVG diagrams showing algorithm state at key steps?
  • Does the results slide have a real comparison table with paper numbers?
  • Do all list slides use class="fragment"?

Step 3 — Content completeness:
  • Is the pseudocode shown on a dedicated slide?
  • Are complexity results (time/space) shown with formal notation?

Fix everything. Target: algorithm tutorial talk quality."""
        elif demo_form == "website":
            return base_checks + f"""
Step 2 — Interactive visualization:
  • Is there a step slider that updates an SVG/canvas visualization?
  • Does the pseudocode panel highlight the current line?
  • Is there a Chart.js comparison chart with real paper numbers?
  • Does the dark mode toggle work?

Step 3 — Content:
  • Are all benchmark baselines included in the comparison?
  • Is the complexity analysis section present with KaTeX math?

Fix everything. Target: VisuAlgo-quality interactive explainer."""
        elif demo_form in ("slides", "latex"):
            figs_line = f"  • Pre-extracted figures: {', '.join(figures_available)}\n" if figures_available else ""
            return base_checks + f"""
Step 2 — Slide content:
{figs_line}  • Are extracted figures embedded in relevant slides?
  • Are ALL benchmark numbers hard-coded as structured tables?
  • Is there a diagram showing the algorithm flow (TikZ or matplotlib)?

Fix everything. Target: conference oral presentation quality."""
        else:
            return base_checks + """

Fix anything that falls short. The visualization should make the algorithm
impossible NOT to understand."""
