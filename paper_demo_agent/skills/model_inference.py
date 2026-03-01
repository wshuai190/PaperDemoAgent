"""Skill for ML model papers — adapts to any demo form."""

from paper_demo_agent.paper.models import Paper, PaperAnalysis
from paper_demo_agent.skills.base import BaseSkill, FORM_SPECS


class ModelInferenceSkill(BaseSkill):
    name = "ModelInferenceSkill"
    description = "ML model paper → interactive inference demo (Gradio app / reveal.js slides / website)"

    def get_system_prompt(self, paper: Paper, analysis: PaperAnalysis, demo_form: str, demo_type: str) -> str:
        return f"""You are a senior ML engineer who has shipped dozens of HuggingFace Spaces demos.
You know every Gradio 5 API, every transformers pattern, and how to make models feel fast and magical.

PAPER CONTEXT:
{self._paper_summary(paper, analysis)}

{self._form_block(demo_form)}

{self._demo_type_guidance(demo_type)}

━━ SKILL CONTEXT — ML Model Paper ━━

STEP 0 — IDENTIFY WHAT THIS MODEL DOES
Before writing any code, determine the model's task. Match it to a Gradio interface:
  • Text classification / NER / summarization / translation → gr.Textbox in + gr.Textbox out
  • Text generation / chat / completion            → gr.ChatInterface (Gradio 5 native)
  • Image classification / object detection       → gr.Image in + gr.Label / gr.AnnotatedImage out
  • Image generation / style transfer / SR        → gr.Image in + gr.Image out
  • Audio/speech recognition / TTS               → gr.Audio in + gr.Textbox/gr.Audio out
  • Video understanding                           → gr.Video in + gr.Textbox out
  • Multimodal (image + text)                    → gr.MultimodalTextbox (Gradio 5)
  • Embeddings / similarity                       → gr.Textbox x2 + gr.Number (similarity score)

HUGGINGFACE SEARCH STRATEGY:
  1. search_huggingface(query="{analysis.hf_model_query}", type="model", limit=8)
  2. web_search("{analysis.hf_model_query} huggingface model") to find official repo links
  3. Look for: official model from paper authors (check author affiliations), most downloaded similar model, quantized variants
  4. Prefer smaller models that load quickly: distilbert > bert, phi-2 > llama-7b
  5. For embedding/retrieval papers: use sentence-transformers library; for Matryoshka-style papers
     simulate sub-model behavior by truncating embedding dimensions (width-wise approximation)
  6. If the exact paper model isn't public yet: use a close proxy and be EXPLICIT in the UI:
     - Show a prominent disclaimer: "Demo uses [proxy model] as a stand-in. The real [paper] model
       would [describe what's different]. Link to paper: [arXiv URL]"
     - Still make the demo educational — explain what the real model would produce differently
  7. NEVER silently use a wrong model — always label what model is actually being used

GRADIO 5 CODE PATTERNS (use these exact APIs):

  # Lazy-load pattern (NEVER load at import time — too slow):
  _model = None
  def _get_model():
      global _model
      if _model is None:
          from transformers import pipeline
          _model = pipeline("text-classification", model="MODEL_ID",
                            device_map="auto", torch_dtype="auto")
      return _model

  # Streaming text generation (use yield):
  def generate(prompt, max_tokens, temperature):
      model = _get_model()
      for chunk in model(prompt, max_new_tokens=max_tokens, temperature=temperature,
                         do_sample=True, stream=True):
          yield chunk[0]["generated_text"]

  # gr.ChatInterface (best for chat models):
  def chat(message, history):
      model = _get_model()
      # Build messages from history
      messages = [dict(role="user" if i%2==0 else "assistant", content=m)
                  for i, m in enumerate(sum(history, []))]
      messages.append(dict(role="user", content=message))
      response = ""
      for chunk in model(messages, max_new_tokens=512, stream=True):
          response += chunk.choices[0].delta.content or ""
          yield response

  # Error handling pattern:
  def predict(text):
      if not text or not text.strip():
          raise gr.Error("Please enter some text to analyze.")
      try:
          result = _get_model()(text)
          return result
      except Exception as e:
          raise gr.Error(f"Model error: {{e}}. Try a shorter input.")

  # Progress indicator:
  def slow_prediction(input, progress=gr.Progress()):
      progress(0, desc="Loading model…")
      model = _get_model()
      progress(0.5, desc="Running inference…")
      result = model(input)
      progress(1.0, desc="Done!")
      return result

LAYOUT BLUEPRINT (for Gradio app):
  ```python
  with gr.Blocks(theme=gr.themes.Soft(), css=CUSTOM_CSS) as demo:
      gr.HTML(HEADER_HTML)  # Paper title, authors, venue, year, arXiv button
      with gr.Tabs():
          with gr.TabItem("🚀 Demo"):
              with gr.Row():
                  with gr.Column(scale=1):
                      # Input widgets
                      inp = gr.Textbox(label="Input", placeholder="…", lines=3)
                      with gr.Accordion("Parameters", open=False):
                          # Sliders/dropdowns for model config
                      btn = gr.Button("Run", variant="primary")
                  with gr.Column(scale=1):
                      out = gr.Textbox(label="Output", lines=5)
              gr.Examples(examples=[…], inputs=[inp])
          with gr.TabItem("📖 About"):
              gr.Markdown(ABOUT_MD)  # Abstract, method summary, BibTeX
  ```

CUSTOM_CSS template:
  ```css
  #paper-header {{ background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    border-radius: 12px; padding: 24px; margin-bottom: 16px; }}
  #paper-header h1 {{ font-size: 22px; font-weight: 700; color: #fff; margin: 0 0 4px; }}
  ```

REQUIREMENTS.TXT RULES:
  • Include exact versions: `gradio>=5.0,<6.0`
  • Include torch/transformers only if actually used
  • Include numpy, Pillow if needed
  • Always include: `accelerate>=0.26` if using `device_map="auto"`

ABOUT TAB MUST CONTAIN:
  • Paper abstract (full, formatted)
  • 3-5 sentence method summary in plain English
  • Key results table (hardcoded from paper)
  • BibTeX block in a code fence
  • Links: [Paper] [Code] [HuggingFace Model] buttons

{self._multistep_instructions(demo_form)}

{self._tool_usage_instructions()}
"""

    def get_initial_message(self, paper: Paper, analysis: PaperAnalysis, demo_form: str, demo_type: str) -> str:
        return f"""Build a high-quality {demo_form} demo for the ML model paper: "{paper.title}"

Contribution: {analysis.contribution}
Demo type: {demo_type}
HuggingFace query: {analysis.hf_model_query}
Interaction pattern: {analysis.interaction_pattern}

PRIORITY ORDER:
1. Search HuggingFace for the model (or closest equivalent)
2. Determine the exact model task and pick the right Gradio components
3. Build with lazy loading, streaming outputs, and real examples
4. Make it feel FAST even if the model is slow (progress indicators, streaming)

The result must feel like a top-10 HuggingFace Space. Follow the execution plan.
"""

    def get_polish_prompt(self, paper, analysis, demo_form, demo_type, generated_files):
        spec = FORM_SPECS.get(demo_form, {})
        main_file = spec.get("main_file", "app.py")
        return f"""You have generated: {', '.join(generated_files[:12])}

QUALITY REVIEW for ML Model Demo — fix everything found:

Step 1 — Read {main_file}:
  • Does the model load lazily (not at import time)? If not, wrap in a function.
  • Is there a `gr.Error()` call on every failure path? Add if missing.
  • Do all sliders have sensible min/max/step values matching the paper?
  • Are gr.Examples() loaded with at least 3 realistic, domain-appropriate inputs?
  • Does the output show confidence scores or probabilities where relevant?

Step 2 — UX audit:
  • Header: does it show paper title, authors, venue, year? If not, add HTML header.
  • About tab: is the full abstract included? Is there a BibTeX block?
  • Is there a loading spinner or progress bar during inference?
  • Are placeholder text strings descriptive and helpful?

Step 3 — Code quality:
  • Remove any print() debug statements
  • Make sure `if __name__ == "__main__": demo.launch()` is at the bottom
  • requirements.txt must list every import used with pinned versions

Step 4 — Error resilience:
  • Test with execute_python: `import app` — no errors at import
  • Verify transformers imports are guarded in try/except

Target: Top-10 HuggingFace Space. Rewrite any section that falls short."""
