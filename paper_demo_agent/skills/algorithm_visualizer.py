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
        return f"""QUALITY REVIEW for Algorithm Visualizer — generated: {', '.join(generated_files[:12])}

Step 1 — Read {main_file} and verify:
  • Is the algorithm implemented correctly (not a stub)?
  • Does the step slider show the correct state at each step (not just the final)?
  • Are plots dark-themed (template="plotly_dark")?
  • Do parameter sliders actually affect the algorithm's behavior?

Step 2 — Content:
  • Is there a pseudocode block?
  • Are benchmark numbers from the paper hardcoded in the comparison tab?
  • Is time/space complexity stated clearly?

Step 3 — UX:
  • Can users click "Run" and immediately see something happen?
  • Are the step descriptions clear and informative (not just "Step 3")?
  • Does the "Compare" tab show at least 3 methods with real metrics?

Rewrite anything that falls short. The visualization should make the algorithm
impossible NOT to understand."""
