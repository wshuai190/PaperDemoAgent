"""Skill for empirical study papers — adapts to any demo form."""

from paper_demo_agent.paper.models import Paper, PaperAnalysis
from paper_demo_agent.skills.base import BaseSkill, FORM_SPECS


class FindingsDashboardSkill(BaseSkill):
    name = "FindingsDashboardSkill"
    description = "Empirical paper → interactive findings dashboard"

    def get_system_prompt(self, paper: Paper, analysis: PaperAnalysis, demo_form: str, demo_type: str) -> str:
        return f"""You are an expert research communicator who turns dense empirical papers
into clear, beautiful dashboards — like Papers with Code leaderboards, but richer.
You never omit a number, never misstate a baseline, and always make the main finding
impossible to miss.

PAPER CONTEXT:
{self._paper_summary(paper, analysis)}

{self._form_block(demo_form)}

{self._demo_type_guidance(demo_type)}

━━ SKILL CONTEXT — Empirical Study Paper ━━

RESEARCH PHASE — search for these BEFORE writing any code:
  1. web_search("{paper.title} arxiv") → get arXiv URL for citation links
  2. web_search("{paper.title} results benchmark") → cross-verify reported numbers
  3. web_search("{paper.title} github code") → find official code + pretrained models
  4. web_search("{paper.title} leaderboard papers with code") → find where this ranks
  5. For each major baseline mentioned in the paper:
     web_search("baseline_name {{task_name}} results") → verify baseline numbers

STEP 0 — EXTRACT ALL NUMBERS FROM THE PAPER
Before writing code, list every quantitative result:
  • Main benchmarks: task, metric, dataset, proposed method score, baseline scores
  • Ablation study: which components contribute how much (Δ accuracy/F1/etc.)
  • Efficiency: FLOPs, parameters, latency, GPU memory
  • Human evaluation: MOS scores, preference rates, inter-annotator agreement
  • Statistical significance: p-values, confidence intervals if stated

CRITICAL: Hard-code ALL these numbers. The demo is worthless without real data.

DATA STRUCTURE BLUEPRINT:
  ```python
  # Always structure data like this (edit with real paper values):
  MAIN_RESULTS = [
      {{"Method": "Our Method (Paper)", "BLEU-4": 41.2, "ROUGE-L": 62.8,
        "CIDEr": 134.5, "Params (M)": 123, "Highlighted": True}},
      {{"Method": "Baseline A",          "BLEU-4": 38.7, "ROUGE-L": 60.1,
        "CIDEr": 128.3, "Params (M)": 110, "Highlighted": False}},
      {{"Method": "SOTA (Prior Work)",   "BLEU-4": 40.1, "ROUGE-L": 61.9,
        "CIDEr": 132.0, "Params (M)": 245, "Highlighted": False}},
  ]

  ABLATION_RESULTS = [
      {{"Config": "Full model",         "Metric": 41.2, "Delta": "+0.0"}},
      {{"Config": "w/o Component A",    "Metric": 38.4, "Delta": "-2.8"}},
      {{"Config": "w/o Component B",    "Metric": 39.1, "Delta": "-2.1"}},
      {{"Config": "Baseline (no mods)", "Metric": 36.2, "Delta": "-5.0"}},
  ]
  ```

CHART PATTERNS (for website/Gradio):

  WEBSITE → Use Chart.js v4 from CDN (https://cdn.jsdelivr.net/npm/chart.js@4.4.3/dist/chart.umd.min.js):
  ```javascript
  // Grouped bar chart — main results:
  new Chart(ctx, {{
    type: 'bar',
    data: {{
      labels: ['BLEU-4', 'ROUGE-L', 'CIDEr'],
      datasets: [
        {{ label: 'Our Method', data: [41.2, 62.8, 134.5], backgroundColor: '#6366f1' }},
        {{ label: 'Baseline A', data: [38.7, 60.1, 128.3], backgroundColor: '#3b82f6' }},
        {{ label: 'SOTA Prior', data: [40.1, 61.9, 132.0], backgroundColor: '#94a3b8' }},
      ]
    }},
    options: {{
      responsive: true,
      plugins: {{ legend: {{ position: 'top' }}, title: {{ display: true, text: 'Main Results' }} }},
      scales: {{ y: {{ beginAtZero: false, min: 34 }} }}
    }}
  }});

  // Heatmap for ablation (use canvas + manual drawing or Chart.js matrix plugin)
  ```

  GRADIO → Use Plotly (import plotly.express as px, plotly.graph_objects as go):
  ```python
  import plotly.graph_objects as go
  import pandas as pd

  def make_bar_chart(results):
      df = pd.DataFrame(results)
      methods = df["Method"].tolist()
      colors = ["#6366f1" if r.get("Highlighted") else "#3b82f6" for r in results]
      fig = go.Figure(go.Bar(x=methods, y=df["MainMetric"], marker_color=colors,
                             text=df["MainMetric"].round(1), textposition="auto"))
      fig.update_layout(title="Main Results", template="plotly_dark",
                        yaxis_title="Score", margin=dict(t=50))
      return fig

  def make_ablation_heatmap(ablation):
      df = pd.DataFrame(ablation)
      fig = go.Figure(go.Bar(x=df["Config"], y=df["Delta"].str.replace("+","").astype(float),
                              marker_color=["#22c55e" if float(d.replace("+","")) >= 0 else "#ef4444"
                                            for d in df["Delta"]]))
      fig.update_layout(title="Ablation Study — Component Contributions",
                        template="plotly_dark", yaxis_title="Δ Score")
      return fig
  ```

WEBSITE LAYOUT BLUEPRINT (for website form):
  ```html
  <!-- sticky nav: Overview | Main Results | Ablation | Efficiency | Insights -->
  <!-- Hero: paper title, key headline result ("Achieves 41.2 BLEU — 1.1 points above SOTA") -->
  <!-- Section 1: Main Results — grouped bar chart + full results table -->
  <!-- Section 2: Ablation Study — bar chart showing Δ for each component -->
  <!-- Section 3: Efficiency — scatter plot (accuracy vs. FLOPs/parameters) -->
  <!-- Section 4: Key Insights — 3-5 numbered takeaways from the paper -->
  <!-- Section 5: Citation — BibTeX block + copy button -->
  ```

GRADIO LAYOUT BLUEPRINT (for app form):
  ```python
  with gr.Tabs():
      with gr.TabItem("🏆 Main Results"):
          main_chart = gr.Plot()
          main_table = gr.Dataframe(value=pd.DataFrame(MAIN_RESULTS))
      with gr.TabItem("🔬 Ablation"):
          ablation_chart = gr.Plot()
          ablation_table = gr.Dataframe(value=pd.DataFrame(ABLATION_RESULTS))
      with gr.TabItem("⚡ Efficiency"):
          efficiency_plot = gr.Plot()   # scatter: accuracy vs. params
          efficiency_table = gr.Dataframe(value=pd.DataFrame(EFFICIENCY_DATA))
      with gr.TabItem("💡 Insights"):
          gr.Markdown(INSIGHTS_MD)     # 5 key findings explained
      with gr.TabItem("📖 About"):
          gr.Markdown(ABOUT_MD)
  ```

DESIGN RULES FOR WEBSITE:
  • Use CSS custom properties — NO Tailwind, NO Bootstrap
  • Dark mode by default with light mode toggle
  • Stat summary cards at top: bold number + metric name + comparison arrow (↑ vs prior SOTA)
  • Highlight OUR METHOD row in all tables with a colored left border
  • Charts must use dark background: `backgroundColor: '#09090b'` for Chart.js

FORM ADAPTATION — when the demo form is NOT 'app' or 'website':

  PRESENTATION (reveal.js):
    • Slide 1: Title + headline result ("Achieves X — Y points above SOTA")
    • Slide 2: Problem + motivation (why these experiments matter)
    • Slide 3: Experimental setup (datasets, metrics, baselines)
    • Slide 4-5: Main results — comparison table + grouped bar chart as inline SVG
    • Slide 6: Ablation study — component contribution visualization
    • Slide 7: Efficiency analysis — accuracy vs compute scatter as SVG
    • Slide 8: Key insights — 3-5 numbered takeaways with fragments
    • Slide 9-10: Qualitative examples (if applicable)
    • Slide 11: Statistical significance / confidence analysis
    • Slide 12: Limitations → Slide 13: Conclusion → Slide 14: Q&A

  SLIDES / LATEX:
    • MANDATORY: Extract result tables and charts from PDF using extract_pdf_page
    • Hard-code ALL comparison numbers as structured tables (add_table / tabular)
    • Use add_chart / TikZ for visual comparisons
    • Include ablation results as a separate table
    • Efficiency scatter plot using matplotlib → BytesIO → add_picture

FIGURE INTEGRATION (for slides/latex/presentation forms):
  • Use extract_pdf_page to embed the paper's own result figures and charts
  • ALWAYS reproduce comparison tables as structured data (not image embeds)
  • Embed qualitative example figures from the paper where applicable

{self._multistep_instructions(demo_form)}

{self._tool_usage_instructions()}
"""

    def get_initial_message(self, paper: Paper, analysis: PaperAnalysis, demo_form: str, demo_type: str) -> str:
        return f"""Build a {demo_form} findings dashboard for: "{paper.title}"

Contribution: {analysis.contribution}
Demo type: {demo_type}

PRIORITY ORDER:
1. Extract ALL quantitative results from the paper (benchmarks, ablations, efficiency)
2. Hard-code every number — accuracy is paramount
3. Build main results chart comparing proposed method vs. all baselines
4. Build ablation study visualization showing each component's contribution
5. Highlight the key finding clearly ("Our method achieves X% improvement on Y")

No guessing on numbers. Use real values from the paper.
Follow the execution plan step by step.
"""

    def get_polish_prompt(self, paper, analysis, demo_form, demo_type, generated_files):
        spec = FORM_SPECS.get(demo_form, {})
        main_file = spec.get("main_file", "app.py")
        figures_available = [f for f in generated_files if f.startswith("figures/")]

        base_checks = f"""QUALITY REVIEW for Findings Dashboard — generated: {', '.join(generated_files[:12])}

Step 1 — Read {main_file} and verify data accuracy:
  • Are ALL quantitative results hardcoded (not placeholder numbers like 0.0 or 100)?
  • Is the proposed method highlighted/distinguished from baselines?
  • Are dataset/task names exactly matching those in the paper?
  • Is there a BibTeX citation block?"""

        if demo_form in ("app", "website"):
            figs_line = f"  • Pre-extracted figures available: {', '.join(figures_available)}. Embed them with <img> tags in relevant sections!\n" if figures_available else ""
            return base_checks + f"""
Step 2 — Chart quality:
{figs_line}  • Are bar charts grouped (all metrics side by side for all methods)?
  • Do charts have proper axis labels, titles, and legends?
  • Are dark themes applied to all charts?
  • Is there an efficiency plot (accuracy vs. parameters/FLOPs)?
  • Is there an ablation study visualization?
  • Does the headline stat card show the main finding prominently?

Step 3 — Content completeness:
  • Is there a "Key Insights" section with 5+ numbered takeaways?

Fix anything missing. The dashboard should let a reviewer understand the paper's
contribution in under 2 minutes."""
        elif demo_form == "presentation":
            return base_checks + """
Step 2 — Slide-specific:
  • Is there a headline result on slide 1 or 2 ("Achieves X — Y above SOTA")?
  • Are results shown as both a table AND a chart (SVG bar chart)?
  • Is there an ablation slide showing component contributions?
  • Are there >=14 slides covering setup, results, ablation, insights?
  • Do all bullet lists use class="fragment"?

Step 3 — Visual:
  • Are inline SVG charts used for main results comparison?
  • Is the proposed method visually distinguished (different color)?

Fix everything. Target: NeurIPS spotlight results presentation."""
        elif demo_form in ("slides", "latex"):
            figs_line = f"  • Pre-extracted figures: {', '.join(figures_available)}\n" if figures_available else ""
            return base_checks + f"""
Step 2 — Slide content:
{figs_line}  • Are extracted figures embedded in relevant slides?
  • Are ALL comparison tables structured (add_table/tabular, NOT images)?
  • Is there a chart (add_chart/TikZ) for the main results comparison?
  • Is there an ablation table or chart?

Fix everything. Target: conference oral presentation quality."""
        else:
            return base_checks + """

Fix anything missing. The dashboard should let a reviewer understand the paper's
contribution in under 2 minutes."""
