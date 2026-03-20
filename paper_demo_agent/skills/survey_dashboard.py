"""Skill for survey/review papers — adapts to any demo form."""

from paper_demo_agent.paper.models import Paper, PaperAnalysis
from paper_demo_agent.skills.base import BaseSkill, FORM_SPECS


class SurveyDashboardSkill(BaseSkill):
    name = "SurveyDashboardSkill"
    description = "Survey/review paper → comparison dashboard or landscape map"

    def get_system_prompt(self, paper: Paper, analysis: PaperAnalysis, demo_form: str, demo_type: str) -> str:
        return f"""You are an expert research landscape analyst who builds the kinds of
interactive survey tools that become the definitive reference for a field —
like Papers with Code method comparison pages, awesome-* GitHub lists, and
the NLP-Progress leaderboard, but richer and more visual.

PAPER CONTEXT:
{self._paper_summary(paper, analysis)}

{self._form_block(demo_form)}

{self._demo_type_guidance(demo_type)}

━━ SKILL CONTEXT — Survey / Review Paper ━━

RESEARCH PHASE — search for these BEFORE writing any code:
  1. web_search("{paper.title} arxiv") → get arXiv URL for citation links
  2. web_search("{paper.title} github awesome list") → find companion repositories
  3. web_search("{paper.title} survey comparison table") → find extended comparison data
  4. For 3-5 key methods mentioned in the survey:
     web_search("method_name arxiv year") → verify year, venue, and key metrics
  5. web_search("{analysis.hf_model_query} papers with code") → find leaderboard data

STEP 0 — DECODE THE SURVEY'S STRUCTURE
From the paper, identify:
  • What taxonomy/categorization does the paper use? (e.g., supervised/unsupervised/RL)
  • How many methods/papers are covered? (typically 20-100+)
  • What properties does the paper compare? (accuracy, speed, year, venue, task)
  • What is the key narrative? (evolution over time / accuracy-efficiency trade-off / etc.)

DATA STRUCTURE (build this first, then build UI around it):
  ```python
  METHODS = [
      {{
          "name": "BERT",
          "year": 2019,
          "category": "encoder-only",
          "subcategory": "pre-training",
          "task": "language understanding",
          "params_M": 340,
          "accuracy": 86.7,
          "venue": "NAACL",
          "advantage": "Strong contextual representations",
          "limitation": "Slow inference, large memory",
          "arxiv": "1810.04805",
      }},
      # ... extract ALL methods from the paper (20-80 entries)
  ]

  TAXONOMY = {{
      "Category A": {{
          "Subcategory A1": ["Method1", "Method2"],
          "Subcategory A2": ["Method3"],
      }},
      "Category B": {{
          "Subcategory B1": ["Method4", "Method5", "Method6"],
      }}
  }}

  TIMELINE = [
      {{"year": 2017, "method": "Transformer", "milestone": "Self-attention introduced"}},
      {{"year": 2018, "method": "GPT",         "milestone": "Autoregressive pre-training"}},
      # ...
  ]
  ```

INTERACTIVE COMPARISON TABLE (core feature — must be excellent):
  Website (vanilla JS):
  ```javascript
  // Render table from METHODS array
  function renderTable(methods) {{
    const tbody = document.querySelector('#methods-table tbody');
    tbody.innerHTML = methods.map(m => `
      <tr data-category="${{m.category}}">
        <td><strong>${{m.name}}</strong></td>
        <td><span class="badge badge-${{m.category.replace(' ','-')}}">${{m.category}}</span></td>
        <td>${{m.year}}</td>
        <td>${{m.accuracy != null ? m.accuracy.toFixed(1)+'%' : '—'}}</td>
        <td>${{m.params_M != null ? m.params_M+'M' : '—'}}</td>
        <td class="advantage">${{m.advantage}}</td>
        <td><a href="https://arxiv.org/abs/${{m.arxiv}}" target="_blank">📄</a></td>
      </tr>`).join('');
  }}

  // Filter by category:
  function filterByCategory(cat) {{
    const rows = document.querySelectorAll('#methods-table tbody tr');
    rows.forEach(r => r.style.display = (cat === 'all' || r.dataset.category === cat) ? '' : 'none');
  }}

  // Sort by column:
  let sortDir = 1;
  function sortTable(col) {{
    const sorted = [...METHODS].sort((a, b) => sortDir * ((a[col] || 0) - (b[col] || 0)));
    sortDir = -sortDir;
    renderTable(sorted);
  }}

  // Search:
  document.querySelector('#search').addEventListener('input', e => {{
    const q = e.target.value.toLowerCase();
    renderTable(METHODS.filter(m => JSON.stringify(m).toLowerCase().includes(q)));
  }});
  ```

  Gradio: use gr.Dataframe with value=pd.DataFrame(METHODS), interactive=False

TIMELINE VISUALIZATION (Chart.js for website):
  ```javascript
  new Chart(document.querySelector('#timeline'), {{
    type: 'scatter',
    data: {{
      datasets: Object.entries(CATEGORY_COLORS).map(([cat, color]) => ({{
        label: cat,
        data: TIMELINE.filter(m => m.category === cat).map(m => ({{
          x: m.year, y: Object.keys(TAXONOMY).indexOf(cat),
          r: 8, label: m.name
        }})),
        backgroundColor: color,
      }}))
    }},
    options: {{
      plugins: {{ tooltip: {{ callbacks: {{ label: ctx => ctx.raw.label }} }} }},
      scales: {{
        x: {{ title: {{ display: true, text: 'Year' }}, min: START_YEAR, max: END_YEAR }},
        y: {{ display: false }}
      }},
      responsive: true
    }}
  }});
  ```

"FIND THE RIGHT METHOD" FEATURE (killer UX):
  • A questionnaire: "I need a method that is: [fast / accurate / easy to train]"
  • User selects constraints → system recommends top 3 matching methods
  • Show comparison card for each recommendation
  ```javascript
  function recommend(constraints) {{
    return METHODS
      .filter(m => constraints.every(c => matches(m, c)))
      .sort((a, b) => b.score - a.score)
      .slice(0, 3);
  }}
  ```

WEBSITE LAYOUT BLUEPRINT:
  <!-- sticky nav: Overview | Methods | Timeline | Compare | Find a Method | Citation -->
  <!-- Hero: survey title, field overview stat (N methods, N years, N venues) -->
  <!-- Overview: taxonomy tree diagram (use nested divs with CSS) -->
  <!-- Methods: filter bar (by category + search) + sortable table -->
  <!-- Timeline: Chart.js scatter/bubble chart of methods by year -->
  <!-- Compare: select 2-3 methods → side-by-side detail panel -->
  <!-- Find: constraint questionnaire → recommendations -->
  <!-- Citation: BibTeX + copy button -->

DESIGN RULES:
  • Use CSS custom properties — NO Tailwind, NO Bootstrap, NO external CSS frameworks
  • Category badges with distinct colors (one color per top-level category)
  • Sort arrows on column headers, highlighted when sorted
  • Sticky header on the methods table
  • Mobile: table scrolls horizontally, filters collapse into a drawer

FORM ADAPTATION — when the demo form is NOT 'app' or 'website':

  PRESENTATION (reveal.js):
    • Slide 1: Survey title + "N methods across M years" stat
    • Slide 2: Field overview — what area does this survey cover and why?
    • Slide 3: Taxonomy tree as inline SVG diagram (categories + subcategories)
    • Slide 4-5: Timeline — show the evolution with key milestones
    • Slide 6-8: Category deep-dives (one slide per major category, 3-5 methods each)
    • Slide 9: Comparison table — methods side-by-side on key metrics
    • Slide 10: Trends and insights — what patterns emerge?
    • Slide 11: Open challenges and future directions
    • Slide 12: "How to choose" — decision tree for picking a method
    • Slide 13: Conclusion → Slide 14: Q&A

  SLIDES / LATEX:
    • Extract taxonomy/overview figures from PDF using extract_pdf_page
    • Build comparison tables covering ALL methods as structured data
    • Use TikZ for taxonomy tree diagram
    • Include timeline figure from the paper

FIGURE INTEGRATION (for slides/latex/presentation forms):
  • Use extract_pdf_page to embed the paper's taxonomy figures, timeline charts
  • Reproduce method comparison tables as structured data (not screenshots)

{self._multistep_instructions(demo_form)}

{self._tool_usage_instructions()}
"""

    def get_initial_message(self, paper: Paper, analysis: PaperAnalysis, demo_form: str, demo_type: str) -> str:
        return f"""Build a {demo_form} survey dashboard for: "{paper.title}"

Contribution: {analysis.contribution}
Demo type: {demo_type}

PRIORITY ORDER:
1. Build the METHODS data array — extract ALL methods/papers from the survey with their properties
2. Build the TAXONOMY structure — the categorization scheme the paper uses
3. Build the interactive comparison table with filter, sort, and search
4. Add the timeline visualization showing evolution of the field
5. Add the "Find the right method" recommendation feature

The result must be the definitive reference for this research area.
Extract real method names, real years, real metrics from the paper.
Follow the execution plan step by step.
"""

    def get_polish_prompt(self, paper, analysis, demo_form, demo_type, generated_files):
        spec = FORM_SPECS.get(demo_form, {})
        main_file = spec.get("main_file", "app.py")
        figures_available = [f for f in generated_files if f.startswith("figures/")]

        base_checks = f"""QUALITY REVIEW for Survey Dashboard — generated: {', '.join(generated_files[:12])}

Step 1 — Read {main_file} and verify data completeness:
  • Does the METHODS data contain at least 10+ real methods from the paper?
  • Are method names, years, and categories accurate to the paper?
  • Is there a BibTeX citation block?"""

        if demo_form in ("app", "website"):
            return base_checks + """
Step 2 — Interactivity:
  • Does table filtering work (filter by category, search by name)?
  • Does column sorting work (click header → sort ascending/descending)?
  • Is there a timeline visualization?
  • Is the "Find a method" or recommendation feature implemented?
  • Are there "Compare two methods" side-by-side cards?

Step 3 — UX:
  • Can a user find "all methods from 2021-2023 in category X" in < 3 clicks?
  • Is the taxonomy tree or category overview visible on load?

Fix anything missing. The dashboard should become the go-to reference
for anyone entering this research area."""
        elif demo_form == "presentation":
            return base_checks + """
Step 2 — Slide-specific:
  • Is there a taxonomy diagram as inline SVG?
  • Are there >=14 slides covering overview, categories, comparison, trends?
  • Is there a timeline visualization (even simplified as SVG)?
  • Does the comparison slide have a styled table with all key methods?
  • Do all bullet lists use class="fragment"?

Step 3 — Content:
  • Are category deep-dive slides present for the main taxonomy branches?
  • Is there a "trends and insights" slide with concrete observations?

Fix everything. Target: keynote survey talk quality."""
        elif demo_form in ("slides", "latex"):
            figs_line = f"  • Pre-extracted figures: {', '.join(figures_available)}\n" if figures_available else ""
            return base_checks + f"""
Step 2 — Slide content:
{figs_line}  • Are extracted figures (taxonomy, timeline) embedded in relevant slides?
  • Is the comparison table structured (add_table/tabular) with ALL methods?
  • Is there a taxonomy/overview diagram (TikZ or extracted figure)?

Fix everything. Target: conference tutorial survey talk quality."""
        else:
            return base_checks + """

Fix anything missing. The dashboard should become the go-to reference
for anyone entering this research area."""
