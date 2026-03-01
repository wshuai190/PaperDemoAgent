"""Skill for dataset papers — adapts to any demo form."""

from paper_demo_agent.paper.models import Paper, PaperAnalysis
from paper_demo_agent.skills.base import BaseSkill, FORM_SPECS


class DataExplorerSkill(BaseSkill):
    name = "DataExplorerSkill"
    description = "Dataset paper → interactive data explorer (Gradio app / presentation / website)"

    def get_system_prompt(self, paper: Paper, analysis: PaperAnalysis, demo_form: str, demo_type: str) -> str:
        return f"""You are a senior data engineer and visualization specialist who has built
production-grade dataset explorers for HuggingFace, Kaggle, and Papers with Code.

PAPER CONTEXT:
{self._paper_summary(paper, analysis)}

{self._form_block(demo_form)}

{self._demo_type_guidance(demo_type)}

━━ SKILL CONTEXT — Dataset Paper ━━

STEP 0 — UNDERSTAND THE DATASET
From the paper abstract and context, identify:
  • Data modality: text / image / audio / video / tabular / multimodal
  • Task: classification, generation, retrieval, QA, segmentation, etc.
  • Scale: # examples, # classes, # splits
  • Unique properties: annotation method, languages, domains, quality metrics

HUGGINGFACE DATASETS SEARCH:
  1. search_huggingface(query="{analysis.hf_model_query}", type="dataset", limit=8)
  2. If found: load a sample — `from datasets import load_dataset; ds = load_dataset("ID", split="train", streaming=True); sample = list(ds.take(200))`
  3. If not found: construct 20-50 representative synthetic examples using Python
     that match the dataset's structure (correct column names, types, distributions)

DATA LOADING CODE PATTERNS:
  ```python
  # Streaming approach (never load full dataset):
  from datasets import load_dataset
  import pandas as pd

  @functools.lru_cache(maxsize=1)
  def load_sample(n=200):
      try:
          ds = load_dataset("DATASET_ID", split="train", streaming=True, trust_remote_code=True)
          rows = list(ds.take(n))
          return pd.DataFrame(rows)
      except Exception:
          # Synthetic fallback
          return pd.DataFrame({{
              "text": ["Example text " + str(i) for i in range(50)],
              "label": [i % NUM_CLASSES for i in range(50)],
          }})

  # Schema inspection:
  df = load_sample()
  print(df.dtypes, df.shape, df.describe())
  ```

VISUALIZATION PATTERNS (Plotly — for Gradio use gr.Plot()):
  ```python
  import plotly.express as px
  import plotly.graph_objects as go

  # Label distribution:
  fig = px.bar(df["label"].value_counts().reset_index(),
               x="label", y="count",
               title="Class Distribution",
               template="plotly_dark",
               color_discrete_sequence=["#6366f1"])

  # Text length distribution:
  df["len"] = df["text"].str.len()
  fig2 = px.histogram(df, x="len", nbins=40, title="Text Length Distribution",
                      template="plotly_dark", color_discrete_sequence=["#22c55e"])

  # Scatter for embeddings (if applicable):
  fig3 = px.scatter(df, x="x", y="y", color="label",
                    title="2D Embedding Space (t-SNE)",
                    template="plotly_dark")
  ```

GRADIO LAYOUT BLUEPRINT:
  ```python
  with gr.Blocks(theme=gr.themes.Soft(), css=CSS) as demo:
      gr.HTML(HEADER)  # Dataset title, paper link, stats badges
      with gr.Tabs():
          with gr.TabItem("🔍 Browse"):
              with gr.Row():
                  search_box = gr.Textbox(label="Search", placeholder="Filter by keyword…")
                  label_filter = gr.Dropdown(choices=CLASSES, label="Filter by label", value="All")
              sample_table = gr.Dataframe(value=df, label="Samples", wrap=True,
                                         max_rows=20, interactive=False)
          with gr.TabItem("📊 Statistics"):
              with gr.Row():
                  label_plot = gr.Plot(label="Class Distribution")
                  length_plot = gr.Plot(label="Length Distribution")
              stats_md = gr.Markdown(STATS_MD)  # N examples, N classes, vocab size, etc.
          with gr.TabItem("🔬 Inspect"):
              idx_slider = gr.Slider(0, len(df)-1, step=1, label="Example index")
              example_display = gr.JSON(label="Raw example")
          with gr.TabItem("📖 About"):
              gr.Markdown(ABOUT_MD)  # Paper abstract, dataset card, BibTeX
  ```

STATISTICS TO DISPLAY (hard-code from paper):
  • Total size (train / val / test split sizes)
  • Number of classes / categories
  • Vocabulary size or sequence lengths (for text)
  • Image resolution / audio duration stats (for media)
  • Annotation agreement / quality metrics
  • Comparison table vs. competing datasets (accuracy, size, diversity)

SEARCH/FILTER LOGIC:
  ```python
  def search_and_filter(query, label):
      filtered = df.copy()
      if label and label != "All":
          filtered = filtered[filtered["label"] == label]
      if query and query.strip():
          mask = filtered.apply(lambda r: query.lower() in str(r).lower(), axis=1)
          filtered = filtered[mask]
      return filtered.head(50)
  ```

{self._multistep_instructions(demo_form)}

{self._tool_usage_instructions()}
"""

    def get_initial_message(self, paper: Paper, analysis: PaperAnalysis, demo_form: str, demo_type: str) -> str:
        return f"""Build a professional {demo_form} data explorer for: "{paper.title}"

Contribution: {analysis.contribution}
Demo type: {demo_type}
HuggingFace dataset query: {analysis.hf_model_query}
Data modality / task: {analysis.interaction_pattern}

PRIORITY ORDER:
1. Search HuggingFace Datasets for this dataset (or closest match)
2. Load a sample (200 rows max, streaming) or create realistic synthetic data
3. Build multi-tab explorer: Browse (searchable table) + Statistics (charts) + Inspect + About
4. Hard-code key statistics from the paper (split sizes, class counts, etc.)

The result must feel like a professional dataset card on Papers with Code.
Follow the execution plan step by step.
"""

    def get_polish_prompt(self, paper, analysis, demo_form, demo_type, generated_files):
        spec = FORM_SPECS.get(demo_form, {})
        main_file = spec.get("main_file", "app.py")
        return f"""QUALITY REVIEW for Dataset Explorer — generated: {', '.join(generated_files[:12])}

Step 1 — Read {main_file}:
  • Does the data load without crashing? Run: execute_python with `import app; df = app.load_sample()`
  • Are there at least 3 chart types (distribution, histogram, another)?
  • Is search/filter implemented and wired to the table?
  • Do all gr.Plot() components show dark-themed Plotly figures?

Step 2 — Content accuracy:
  • Are dataset statistics (size, classes, splits) hard-coded from the paper?
  • Is there a comparison table vs. other datasets?
  • Does the About tab have the full abstract and BibTeX?

Step 3 — UX polish:
  • Does the header show dataset name, paper, stats badges?
  • Are loading states handled (data loads on first tab visit, not import)?
  • Column names in the DataFrame match actual dataset field names?

Rewrite anything that falls short. Target: production HuggingFace Dataset card quality."""
