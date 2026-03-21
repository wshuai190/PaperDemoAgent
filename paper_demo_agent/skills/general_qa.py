"""Skill for generic papers — adapts to any demo form."""

from paper_demo_agent.paper.models import Paper, PaperAnalysis
from paper_demo_agent.skills.base import BaseSkill, FORM_SPECS


# ─────────────────────────────────────────────────────────────────────────────
# Pre-baked knowledge — domain-specific Q&A patterns
# ─────────────────────────────────────────────────────────────────────────────

_QA_KNOWLEDGE = """
━━ PAPER Q&A KNOWLEDGE PATTERNS (use verbatim, do NOT search) ━━

PAPER COMPREHENSION TAXONOMY — use this to generate thorough suggested questions:
  WHAT questions:  "What is the main contribution?", "What problem does it solve?"
  HOW questions:   "How does the method work?", "How is it evaluated?"
  WHY questions:   "Why is this approach better?", "Why were these baselines chosen?"
  COMPARE questions: "How does this compare to [prior work]?", "What's the key difference from [X]?"
  CRITIQUE questions: "What are the limitations?", "What assumptions might not hold?"
  APPLY questions: "How could I use this in my own project?", "What are real-world applications?"
  EXTEND questions: "What future work do the authors suggest?", "What would you change about this approach?"

ANSWER QUALITY PATTERNS:
  • Always cite specific sections: "As described in Section 3.2, the encoder uses..."
  • Include specific numbers: "The model achieves 94.2% accuracy, which is 2.1pp above the prior SOTA"
  • Use analogies for complex concepts: "Think of attention like a spotlight that..."
  • Structure long answers: use bullet points, numbered steps, or sub-headings
  • When critiquing: be balanced — acknowledge strengths before pointing out limitations

CONCEPT MAP GENERATION:
  ```python
  # Extract key terms and build a concept map from paper sections
  CONCEPTS = {
      "Term A": {
          "definition": "One-sentence definition from the paper.",
          "section": "Section 3.1",
          "related": ["Term B", "Term C"],
          "importance": "high"  # high/medium/low
      },
      # ... extract 10-20 key concepts from the paper
  }
  ```

STRUCTURED SUMMARY TEMPLATE:
  ```python
  PAPER_SUMMARY = {
      "tldr": "One-sentence summary of the contribution.",
      "problem": "What problem does this paper address? (2-3 sentences)",
      "approach": "How does the method work? (3-5 sentences, plain English)",
      "key_results": [
          {"metric": "Accuracy", "value": "94.2%", "comparison": "+2.1pp vs prior SOTA"},
          {"metric": "Speed", "value": "3x faster", "comparison": "vs baseline"},
      ],
      "limitations": ["Limitation 1", "Limitation 2"],
      "future_work": ["Direction 1", "Direction 2"],
  }
  ```
"""


class GeneralQASkill(BaseSkill):
    name = "GeneralQASkill"
    description = "Generic paper → LLM-powered Q&A or explainer demo"

    def get_system_prompt(self, paper: Paper, analysis: PaperAnalysis, demo_form: str, demo_type: str) -> str:
        # Build a compact but rich paper context for embedding in the demo
        paper_text = f"Title: {paper.title}\n\nAbstract:\n{paper.abstract[:2000] if paper.abstract else ''}\n\n"
        paper_text += "Key Sections:\n"
        for section_name, section_text in list(paper.sections.items())[:5]:
            paper_text += f"\n## {section_name}\n{section_text[:800]}\n"

        # Form-specific guidance for non-app forms
        form_specific = self._form_specific_guidance(demo_form)

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
            f"MANDATORY: The EXACT paper title above MUST appear in your output (in the header/title/hero).\n"
            f"Use the EXACT author names above — never write \"[Author Name]\" placeholders.\n"
            f"Use EXACT numbers from the paper — never write \"~X%\" or \"approximately\".\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        )
        return paper_facts_block + f"""You are an expert at building intelligent paper exploration tools —
combining the depth of a research assistant with the UX of Perplexity AI.
Your demos make papers genuinely accessible to non-experts.

PAPER CONTEXT:
{self._paper_summary(paper, analysis)}

{self._form_block(demo_form)}

{self._demo_type_guidance(demo_type)}

━━ SKILL CONTEXT — General Q&A Paper Demo ━━

RESEARCH PHASE — search for these BEFORE writing any code:
  1. web_search("{paper.title} arxiv") → get arXiv URL for citation links
  2. web_search("{paper.title} github code") → find official code repository
  3. web_search("first_author_lastname {paper.title[:30]} results") → cross-verify key numbers
  These searches help you embed accurate metadata and links in the demo.

PAPER CONTENT TO EMBED IN THE DEMO:
```
{paper_text[:3500]}
```

{_QA_KNOWLEDGE}

{form_specific}

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

    def _form_specific_guidance(self, demo_form: str) -> str:
        """Return guidance for adapting Q&A content to non-app forms."""
        if demo_form == "presentation":
            return """FORM ADAPTATION — PRESENTATION (reveal.js):
  Since this is a presentation, NOT a chat app, adapt the Q&A concept into slides:
  • Slide 1: Title + paper metadata
  • Slide 2: "What This Paper Does" (TL;DR)
  • Slides 3-5: "Key Questions Answered" — pick the 3 most insightful Q&A pairs
    and present each as: Question (large heading) → Answer (bullets with fragments)
  • Slide 6-7: Concept map as an inline SVG diagram showing term relationships
  • Slide 8-9: Results summary with key numbers in stat cards
  • Slide 10: "Critical Analysis" — limitations and open questions
  • Slide 11-12: FAQ-style slides addressing common reader questions
  • Slide 13: Conclusion + BibTeX
  • Slide 14: Q&A slide
  Think of it as "the 10 things you need to know about this paper" in slide form."""
        elif demo_form == "website":
            return """FORM ADAPTATION — WEBSITE (static HTML):
  Build an interactive paper exploration page (NOT a chat interface):
  • Hero: paper title, authors, venue, arXiv link buttons
  • Section 1: TL;DR card with key contribution
  • Section 2: Interactive concept map — clickable terms expand definitions
  • Section 3: "Key Questions" — accordion/expandable Q&A pairs (8+ questions)
    Each answer pre-written in the HTML, revealed on click with smooth animation
  • Section 4: Structured summary — Problem | Approach | Results | Limitations
  • Section 5: Results dashboard — key metrics in stat cards, comparison table
  • Section 6: BibTeX + citation copy button
  Use IntersectionObserver for scroll animations, dark mode toggle in nav."""
        elif demo_form == "page_blog":
            return """FORM ADAPTATION — BLOG (Distill.pub):
  Structure the blog as a guided paper walkthrough:
  • Hook: Start with the key question the paper answers
  • Use d-aside for technical term definitions (like a built-in glossary)
  • Structure around the paper's core questions: What? Why? How? So What?
  • Embed a D3.js interactive chart for the main results
  • Use d-footnote for methodological details"""
        elif demo_form in ("slides", "latex"):
            return """FORM ADAPTATION — SLIDES:
  Since this is a slide deck, present the paper as a structured summary:
  • Title slide with paper metadata
  • "What & Why" slides: problem statement and motivation
  • "How" slides: method overview with key equations/diagrams
  • "Results" slides: hard-coded comparison tables and charts
  • "So What" slide: implications and takeaways
  • Q&A slide
  Extract and embed figures from the PDF using extract_pdf_page."""
        return ""

    def get_initial_message(self, paper: Paper, analysis: PaperAnalysis, demo_form: str, demo_type: str) -> str:
        # Adapt priority order based on form
        if demo_form == "app":
            priorities = """PRIORITY ORDER:
1. web_search for the paper's arXiv URL and official code repository
2. Embed the paper abstract and key sections as the LLM's system prompt
3. Build a Gradio ChatInterface with streaming responses
4. Add 8 pre-written suggested questions covering all angles (WHAT/HOW/WHY/COMPARE/CRITIQUE/APPLY/EXTEND)
5. Add 5 answer modes: Normal, Deep Dive, ELI5, Critique, Practical
6. Pre-generate a structured summary tab (TL;DR, problem, approach, results, limitations)
7. Build a concept map tab with 10-20 key terms and relationships
8. Handle both Anthropic and OpenAI API keys gracefully"""
        elif demo_form == "presentation":
            priorities = """PRIORITY ORDER:
1. web_search for the paper's arXiv URL and key results
2. Plan 14 slides: Title → TL;DR → Key Questions (3 slides) → Concept Map → Results → Critical Analysis → FAQ → Conclusion → Q&A
3. Write demo.html with reveal.js, SVG diagrams, and pre-written Q&A content
4. Use inline SVG for concept relationship diagram
5. Include real numbers from the paper in results slides"""
        elif demo_form == "website":
            priorities = """PRIORITY ORDER:
1. web_search for the paper's arXiv URL and official repository
2. Build an interactive paper exploration page with expandable Q&A sections
3. Create a clickable concept map using SVG or CSS grid
4. Pre-write 8+ Q&A pairs covering all angles of the paper
5. Add structured summary section with stat cards for key results
6. Implement dark mode toggle and scroll animations"""
        else:
            priorities = f"""PRIORITY ORDER:
1. web_search for the paper's arXiv URL and key metadata
2. Adapt the Q&A content for {demo_form} format (see form adaptation guidance)
3. Include pre-written answers to the most important questions about this paper
4. Ensure all key results from the paper are accurately presented"""

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
        return paper_anchor + f"""Build a {demo_form} Q&A demo for: "{paper.title}"

Contribution: {analysis.contribution}
Demo type: {demo_type}

{priorities}

The result should make this paper genuinely accessible — a reader should understand
the key contribution, method, and results without reading the full paper.
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
