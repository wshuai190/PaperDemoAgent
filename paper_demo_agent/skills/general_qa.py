"""Skill for generic papers — adapts to any demo form."""

from paper_demo_agent.paper.models import Paper, PaperAnalysis
from paper_demo_agent.skills.base import BaseSkill, FORM_SPECS


class GeneralQASkill(BaseSkill):
    name = "GeneralQASkill"
    description = "Generic paper → LLM-powered Q&A or explainer demo"

    def get_system_prompt(self, paper: Paper, analysis: PaperAnalysis, demo_form: str, demo_type: str) -> str:
        # Build a compact but rich paper context for embedding in the demo
        paper_text = f"Title: {paper.title}\n\nAbstract:\n{paper.abstract[:2000] if paper.abstract else ''}\n\n"
        paper_text += "Key Sections:\n"
        for section_name, section_text in list(paper.sections.items())[:5]:
            paper_text += f"\n## {section_name}\n{section_text[:800]}\n"

        return f"""You are an expert at building intelligent paper exploration tools —
combining the depth of a research assistant with the UX of Perplexity AI.
Your demos make papers genuinely accessible to non-experts.

PAPER CONTEXT:
{self._paper_summary(paper, analysis)}

{self._form_block(demo_form)}

{self._demo_type_guidance(demo_type)}

━━ SKILL CONTEXT — General Q&A Paper Demo ━━

PAPER CONTENT TO EMBED IN THE DEMO:
```
{paper_text[:3500]}
```

ARCHITECTURE: The app embeds the paper as context and answers questions via an LLM API.

LLM INTEGRATION PATTERNS:

  # Anthropic (primary — check ANTHROPIC_API_KEY):
  ```python
  import os
  import anthropic

  def answer_question(question: str, mode: str, history: list) -> str:
      api_key = os.getenv("ANTHROPIC_API_KEY")
      if not api_key:
          yield "⚠ ANTHROPIC_API_KEY not set. Add it in the Settings tab."
          return

      system = (
          'You are a helpful research assistant for the paper: '
          f'"{paper.title}"\n\n'
          f'PAPER CONTEXT:\n{paper_text}\n\n'
          'Answer based ONLY on this paper. Cite section names when relevant.\n'
          f'Mode: {{mode}}\n'
          "- If mode='Deep Dive': give a thorough 500+ word explanation with structure.\n"
          "- If mode='ELI5': explain like the user is 10 years old, use analogies.\n"
          "- If mode='Critique': identify weaknesses, limitations, and missing experiments.\n"
          "- If mode='Practical': focus on how to apply this in real projects."
      )
      client = anthropic.Anthropic(api_key=api_key)
      response = ""
      with client.messages.stream(
          model="claude-opus-4-6",
          max_tokens=1024,
          system=system,
          messages=[{{"role": "user", "content": question}}],
      ) as stream:
          for chunk in stream.text_stream:
              response += chunk
              yield response
  ```

  # OpenAI fallback:
  ```python
  import openai
  def answer_openai(question, system):
      client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
      stream = client.chat.completions.create(
          model="gpt-4o",
          messages=[{{"role": "system", "content": system}},
                    {{"role": "user", "content": question}}],
          stream=True, max_tokens=1024,
      )
      response = ""
      for chunk in stream:
          delta = chunk.choices[0].delta.content or ""
          response += delta
          yield response
  ```

  # Graceful key detection:
  ```python
  def get_llm_provider():
      if os.getenv("ANTHROPIC_API_KEY"):
          return "anthropic"
      elif os.getenv("OPENAI_API_KEY"):
          return "openai"
      return None
  ```

GRADIO LAYOUT BLUEPRINT:
  ```python
  MODES = ["💬 Normal", "🔬 Deep Dive", "👶 ELI5", "🔍 Critique", "🛠 Practical"]

  SUGGESTED_QUESTIONS = [
      f"What is the main contribution of '{paper.title[:40]}...'?",
      "What problem does this paper solve and why does it matter?",
      "Explain the core methodology in simple terms.",
      "What are the key experimental results and what do they show?",
      "What are the main limitations or weaknesses of this approach?",
      "How does this compare to prior work in the field?",
      "What are the practical applications of this research?",
      "What future work do the authors suggest?",
  ]

  with gr.Blocks(theme=gr.themes.Soft(), css=CSS) as demo:
      gr.HTML(HEADER)  # Paper title, abstract snippet, arXiv link

      with gr.Tabs():
          with gr.TabItem("💬 Chat"):
              mode_dd = gr.Dropdown(choices=MODES, value="💬 Normal", label="Answer mode")
              chatbot = gr.Chatbot(height=400, show_copy_button=True, bubble_full_width=False,
                                   avatar_images=("👤", "🔬"))
              with gr.Row():
                  msg_box = gr.Textbox(placeholder="Ask anything about this paper…",
                                       label="Question", scale=5)
                  submit_btn = gr.Button("Ask →", variant="primary", scale=1)

              gr.Markdown("**Suggested questions** (click to ask):")
              with gr.Row(wrap=True):
                  for q in SUGGESTED_QUESTIONS[:4]:
                      btn = gr.Button(q[:60] + "…", size="sm")
                      btn.click(lambda q=q: (q, None), outputs=[msg_box, chatbot])

          with gr.TabItem("📋 Summary"):
              # Pre-generated structured summary: TL;DR, Key Contributions, Method, Results
              gr.Markdown(PAPER_SUMMARY_MD)

          with gr.TabItem("🗺️ Concept Map"):
              # List of key terms with 1-sentence explanations
              gr.HTML(CONCEPT_MAP_HTML)

          with gr.TabItem("📖 Full Paper"):
              gr.Markdown("### Abstract\\n\\n" + paper.abstract)
              for sec, txt in list(paper.sections.items())[:5]:
                  with gr.Accordion(sec, open=False):
                      gr.Markdown(txt[:1000] + "...")

          with gr.TabItem("📖 About"):
              gr.Markdown(ABOUT_MD)  # BibTeX, authors, links
  ```

PRE-GENERATED CONTENT (compute at startup, not at ask-time):
  • PAPER_SUMMARY_MD — structure: TL;DR (2 sentences) | Problem | Approach | Results | Limitations
  • CONCEPT_MAP_HTML — grid of key terms from paper with 1-sentence definitions
  • SUGGESTED_QUESTIONS — 8 questions covering all angles of the paper

API KEY ONBOARDING (show this if no key found):
  ```python
  def check_keys():
      if not get_llm_provider():
          return gr.update(visible=True), gr.update(visible=False)
      return gr.update(visible=False), gr.update(visible=True)
  ```
  Show a banner: "⚠ No API key found. Set ANTHROPIC_API_KEY or OPENAI_API_KEY in environment or Settings tab."

{self._multistep_instructions(demo_form)}

{self._tool_usage_instructions()}
"""

    def get_initial_message(self, paper: Paper, analysis: PaperAnalysis, demo_form: str, demo_type: str) -> str:
        return f"""Build a {demo_form} Q&A demo for: "{paper.title}"

Contribution: {analysis.contribution}
Demo type: {demo_type}

PRIORITY ORDER:
1. Embed the paper abstract and key sections as the LLM's system prompt
2. Build a Gradio ChatInterface with streaming responses
3. Add 8 pre-written suggested questions covering all angles
4. Add 4 answer modes: Normal, Deep Dive, ELI5, Critique
5. Add a pre-generated paper summary tab (TL;DR, method, results)
6. Handle both Anthropic and OpenAI API keys gracefully

The UI should feel like Perplexity AI meets a research assistant.
Follow the execution plan step by step.
"""

    def get_polish_prompt(self, paper, analysis, demo_form, demo_type, generated_files):
        spec = FORM_SPECS.get(demo_form, {})
        main_file = spec.get("main_file", "app.py")
        return f"""QUALITY REVIEW for Q&A Demo — generated: {', '.join(generated_files[:12])}

Step 1 — Read {main_file}:
  • Is the paper context (abstract + sections) embedded in the LLM system prompt?
  • Is there streaming (yield) for LLM responses?
  • Are both Anthropic and OpenAI API keys checked with graceful fallback?
  • Are there at least 8 suggested question buttons?

Step 2 — Features:
  • Are there at least 4 answer modes (Normal/Deep Dive/ELI5/Critique)?
  • Is there a pre-generated summary tab?
  • Is there an API key warning banner when no key is configured?

Step 3 — UX:
  • Do clicking suggested question buttons populate the input box?
  • Is the chatbot avatar styled nicely?
  • Does the About tab have a BibTeX block?

Fix anything missing. The experience should feel like a genuine research assistant
purpose-built for this specific paper."""
