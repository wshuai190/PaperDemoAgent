"""Skill for any paper → Streamlit interactive web application."""

from paper_demo_agent.paper.models import Paper, PaperAnalysis
from paper_demo_agent.skills.base import BaseSkill, FORM_SPECS


_STREAMLIT_PATTERNS = """
━━ STREAMLIT API QUICK REFERENCE (v1.38+) ━━

DEPRECATION RULE (MANDATORY):
  • NEVER use `use_column_width` in `st.image` or any API.
  • Always use `use_container_width=True`.

PAGE CONFIG (MUST be first st.* call):
  ```python
  import streamlit as st
  st.set_page_config(page_title="Paper — Demo", page_icon="🔬",
                     layout="wide", initial_sidebar_state="expanded")
  ```

CACHING:
  ```python
  @st.cache_data(ttl=3600, show_spinner="Loading data…")
  def load_data(path: str) -> pd.DataFrame:
      return pd.read_csv(path)

  @st.cache_resource(show_spinner="Loading model…")
  def load_model(model_id: str):
      from transformers import pipeline
      return pipeline("text-classification", model=model_id, device_map="auto")
  ```

LAYOUT — columns, tabs, sidebar, expander:
  ```python
  col1, col2 = st.columns([2, 3])
  tab1, tab2, tab3 = st.tabs(["🚀 Demo", "📊 Results", "📖 About"])
  with st.sidebar:
      lr = st.slider("Learning Rate", 1e-5, 1e-2, 1e-3, format="%.1e")
      model_choice = st.selectbox("Model", ["Base", "Large"])
  with st.expander("Details", expanded=False):
      st.markdown("…")
  ```

WIDGETS — text, numeric, selection, file, button:
  ```python
  user_input = st.text_input("Enter text", placeholder="Type…")
  threshold = st.slider("Threshold", 0.0, 1.0, 0.5, step=0.05)
  dataset = st.selectbox("Dataset", ["CIFAR-10", "ImageNet"])
  metrics = st.multiselect("Metrics", ["Accuracy", "F1"], default=["Accuracy"])
  uploaded = st.file_uploader("Upload image", type=["png", "jpg"])
  if st.button("Run", type="primary", use_container_width=True):
      with st.spinner("Running…"):
          result = model.predict(user_input)
      st.success(f"Result: {{result}}")
  ```

CHARTS (prefer Plotly for interactivity):
  ```python
  import plotly.express as px
  fig = px.bar(df, x="model", y="accuracy", color="dataset",
               barmode="group", color_discrete_sequence=px.colors.qualitative.Set2)
  fig.update_layout(template="plotly_dark", height=400)
  st.plotly_chart(fig, use_container_width=True)

  # matplotlib fallback for specialized plots
  st.pyplot(fig_mpl)
  ```

SESSION STATE:
  ```python
  if "step" not in st.session_state:
      st.session_state.step = 0
  if st.button("Next"):
      st.session_state.step += 1
      st.rerun()
  ```

PROGRESS: st.progress(value, text=…) / st.spinner("…") / st.success/warning/error/info("…")

DATA DISPLAY:
  ```python
  st.dataframe(df, use_container_width=True)
  c1, c2, c3 = st.columns(3)
  c1.metric("Accuracy", "94.2%", "+1.3%")
  st.latex(r"\\mathcal{{L}} = -\\sum_i y_i \\log(\\hat{{y}}_i)")
  st.code("model = AutoModel.from_pretrained('bert-base')", language="python")
  ```

DEPLOYMENT — .streamlit/config.toml:
  ```toml
  [theme]
  primaryColor = "#6366f1"
  backgroundColor = "#0e1117"
  secondaryBackgroundColor = "#1a1b2e"
  textColor = "#fafafa"
  font = "sans serif"
  [server]
  headless = true
  port = 8501
  ```

CUSTOM CSS:
  ```python
  st.markdown('<style>.stApp {{font-family: Inter, sans-serif}} '
              'h1 {{color: #6366f1; font-weight: 700; letter-spacing: -0.02em}} '
              '.main .block-container {{max-width: 1200px; padding-top: 2rem}}</style>',
              unsafe_allow_html=True)
  ```
"""


class StreamlitDemoSkill(BaseSkill):
    name = "StreamlitDemoSkill"
    description = "Any paper → Streamlit interactive web application"

    def get_system_prompt(self, paper: Paper, analysis: PaperAnalysis, demo_form: str, demo_type: str) -> str:
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
        return paper_facts_block + f"""You are a senior Python developer who has shipped dozens of Streamlit apps and data dashboards.
You know every Streamlit API, every Plotly pattern, and how to make research papers come alive
through interactive exploration. Your apps feel fast, polished, and genuinely useful.

PAPER CONTEXT:
{self._paper_summary(paper, analysis)}

{self._form_block(demo_form)}

{self._demo_type_guidance(demo_type)}

━━ SKILL CONTEXT — Streamlit Interactive Web App ━━

STEP 0 — IDENTIFY THE PAPER'S CORE INTERACTIVE ELEMENT
Before writing any code, determine what the user should interact with:
  • Model inference paper → Upload/enter input, run model, show predictions + confidence
  • Dataset/benchmark paper → Explore dataset splits, filter by class/metric, compare models
  • Algorithm paper → Tune hyperparameters via sliders, visualize algorithm steps
  • Empirical/survey paper → Dashboard with charts comparing methods across datasets
  • Theory paper → Interactive equation explorer, parameter sensitivity visualization
  • Framework paper → Step-by-step tutorial walkthrough with live code examples

ARCHITECTURE RULES:
  1. `st.set_page_config()` MUST be the very first Streamlit call — before any other st.* calls
  2. Use `@st.cache_data` for data loading and `@st.cache_resource` for ML models
  3. NEVER load models or data at module level — always inside cached functions
  4. Use `st.sidebar` for all parameter controls; main area for outputs and visualizations
  5. Organize content with `st.tabs()` — minimum 3 tabs: Demo, Results/Analysis, About
  6. Use `st.spinner()` or `st.progress()` for any operation taking >0.5 seconds
  7. Use `st.session_state` for multi-step interactions and persisting user choices across reruns
  8. Handle errors gracefully: wrap model calls in try/except, show `st.error()` messages
  9. All charts should use Plotly for interactivity — fall back to matplotlib for specialized plots
  10. End with: `if __name__ == "__main__":` guard (Streamlit runs the file directly, but this is good practice)

STREAMLIT API PATTERNS:
{_STREAMLIT_PATTERNS}

APP STRUCTURE BLUEPRINT:
  ```python
  import streamlit as st
  import pandas as pd
  import plotly.express as px

  # ── Page config (MUST be first) ──────────────────────────────────
  st.set_page_config(
      page_title="{{paper.title[:50]}} — Demo",
      page_icon="🔬",
      layout="wide",
      initial_sidebar_state="expanded",
  )

  # ── Custom CSS ───────────────────────────────────────────────────
  st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

  # ── Header ───────────────────────────────────────────────────────
  st.markdown("# 🔬 {{paper.title}}")
  st.caption("Authors · Venue · Year · [arXiv](url) · [Code](url)")

  # ── Sidebar controls ────────────────────────────────────────────
  with st.sidebar:
      st.header("⚙️ Parameters")
      param1 = st.slider(...)
      param2 = st.selectbox(...)
      st.divider()
      st.markdown("### 📖 About")
      st.markdown("Built from: *{{paper.title}}*")

  # ── Main content tabs ───────────────────────────────────────────
  tab_demo, tab_results, tab_about = st.tabs(["🚀 Demo", "📊 Results", "📖 About"])

  with tab_demo:
      col1, col2 = st.columns([1, 1])
      with col1:
          # Input widgets
          ...
      with col2:
          # Output visualization
          ...

  with tab_results:
      # Key results from the paper as interactive charts
      # Metrics comparison, ablation studies
      ...

  with tab_about:
      st.markdown("### Abstract")
      st.markdown(ABSTRACT)
      st.markdown("### BibTeX")
      st.code(BIBTEX, language="bibtex")
      st.markdown("### Method Summary")
      st.markdown(METHOD_SUMMARY)
  ```

REQUIREMENTS.TXT RULES:
  • Always include: `streamlit>=1.38.0`
  • Include `plotly>=5.18` if using st.plotly_chart
  • Include `pandas>=2.0` for data handling
  • Include `numpy>=1.24` if doing numerical computation
  • Include `Pillow>=10.0` if handling images
  • Include `matplotlib>=3.7` only if using st.pyplot
  • Include `transformers>=4.36` and `torch>=2.0` only if loading HF models
  • Include `scikit-learn>=1.3` only if using ML utilities
  • Pin major versions, not exact patches

README.MD FORMAT (HuggingFace Spaces YAML front-matter):
  ```yaml
  ---
  title: Paper Demo Title
  emoji: 🔬
  colorFrom: indigo
  colorTo: purple
  sdk: streamlit
  sdk_version: 1.38.0
  app_file: app.py
  pinned: false
  ---

  # Paper Title — Interactive Demo
  Description of what this demo does…
  ```

STREAMLIT THEME CONFIG (.streamlit/config.toml):
  Create `.streamlit/config.toml` with dark theme matching the project accent color (#6366f1).
  This ensures consistent styling across local and cloud deployments.

ABOUT TAB MUST CONTAIN:
  • Paper abstract (full, formatted as markdown)
  • 3-5 sentence method summary in plain English
  • Key results table using st.dataframe or st.table
  • BibTeX block via st.code(bibtex, language="bibtex")
  • Links as st.link_button: [Paper] [Code] [HuggingFace]

{self._multistep_instructions(demo_form)}

{self._tool_usage_instructions()}
"""

    def get_initial_message(self, paper: Paper, analysis: PaperAnalysis, demo_form: str, demo_type: str) -> str:
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
        return paper_anchor + f"""Build a Streamlit interactive web app for: "{paper.title}"

Contribution: {analysis.contribution}
Demo type: {demo_type}

PRIORITY ORDER:
1. Create app.py with st.set_page_config() as the FIRST call
2. Add sidebar with parameter controls relevant to this paper
3. Build the main Demo tab with interactive visualization of the paper's key contribution
4. Add a Results tab with Plotly charts showing the paper's experimental results
5. Add an About tab with abstract, method summary, and BibTeX
6. Create requirements.txt with all dependencies pinned
7. Create README.md with HuggingFace Spaces YAML front-matter (sdk: streamlit)
8. Create .streamlit/config.toml with dark theme configuration
9. Use @st.cache_data / @st.cache_resource for all expensive operations

The app should feel like a polished data product — not a homework assignment.
Follow the execution plan step by step.
"""

    def get_polish_prompt(self, paper, analysis, demo_form, demo_type, generated_files):
        spec = FORM_SPECS.get(demo_form, {})
        main_file = spec.get("main_file", "app.py")
        return f"""QUALITY REVIEW for Streamlit Demo — generated: {', '.join(generated_files[:12])}

Step 1 — Read {main_file}:
  • Is `st.set_page_config()` the very FIRST Streamlit call? If not, move it to the top.
  • Are all data-loading functions decorated with `@st.cache_data`?
  • Are all model-loading functions decorated with `@st.cache_resource`?
  • Is there a `st.sidebar` with at least 3 parameter controls?
  • Are there at least 3 tabs (Demo, Results, About)?

Step 2 — Visualization quality:
  • Do all Plotly charts use `template="plotly_dark"` for consistency?
  • Are `st.metric()` cards used to highlight key paper results?
  • Is there at least one interactive Plotly chart with hover tooltips?
  • Do charts have clear axis labels, titles, and legends?
  • Replace any deprecated `use_column_width` usage with `use_container_width=True`.

Step 3 — UX and polish:
  • Is there a header with the paper title, authors, and venue?
  • Does the About tab contain the full abstract and a BibTeX block?
  • Is there a `st.spinner()` or `st.progress()` on every slow operation?
  • Are error messages shown via `st.error()` (not bare exceptions)?
  • Is custom CSS injected for professional typography and spacing?

Step 4 — Deployment readiness:
  • Does `requirements.txt` list every imported package with pinned versions?
  • Does `README.md` have correct HuggingFace Spaces YAML front-matter with `sdk: streamlit`?
  • Does `.streamlit/config.toml` exist with dark theme colors?

Step 5 — Code quality:
  • Remove any `print()` debug statements — use `st.write()` if needed
  • Verify no module-level model loading (must be inside cached functions)
  • Test with `execute_python`: `import streamlit` should not error

Fix anything missing. The result should feel like a production Streamlit dashboard."""
