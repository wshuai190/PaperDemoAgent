"""Skill for framework/library papers — adapts to any demo form."""

from paper_demo_agent.paper.models import Paper, PaperAnalysis
from paper_demo_agent.skills.base import BaseSkill, FORM_SPECS


class FrameworkTutorialSkill(BaseSkill):
    name = "FrameworkTutorialSkill"
    description = "Framework/library paper → interactive tutorial (website / Gradio app / slides)"

    def get_system_prompt(self, paper: Paper, analysis: PaperAnalysis, demo_form: str, demo_type: str) -> str:
        return f"""You are a world-class developer advocate and technical writer — think Stripe docs
quality, FastAI tutorial depth, and Anthropic cookbook interactivity.
Your framework tutorials make developers immediately want to use the tool.

PAPER CONTEXT:
{self._paper_summary(paper, analysis)}

{self._form_block(demo_form)}

{self._demo_type_guidance(demo_type)}

━━ SKILL CONTEXT — Framework / Library Paper ━━

RESEARCH PHASE — search for these BEFORE writing any code:
  1. web_search("{paper.title} github") → find official repository, README, docs
  2. web_search("{paper.title} pip install") → find package name and install command
  3. web_search("{paper.title} tutorial quickstart") → find official examples
  4. web_search("{paper.title} benchmark comparison") → verify performance claims
  5. search_huggingface(query="{analysis.hf_model_query}", type="model", limit=5)
     → Check if the framework has models/datasets on HuggingFace

STEP 0 — UNDERSTAND THE FRAMEWORK
From the paper, identify:
  • What problem does it solve? What's the core abstraction?
  • What does a minimal working example look like?
  • What are the 3 most compelling features / improvements over alternatives?
  • Who is the target user? (ML researchers / app developers / data scientists?)

TUTORIAL STRUCTURE (use this exact order):
  1. **Hero** — One-sentence value proposition + "Install in 30 seconds" code snippet
  2. **Problem** — What was painful/impossible before? (code showing the old way)
  3. **Solution** — The same task with THIS framework (dramatic improvement visible)
  4. **Quick Start** — Copy-pasteable working example in < 20 lines
  5. **Core Concepts** — 3-5 key abstractions, each with minimal example
  6. **Real Example** — End-to-end worked example on a real use case
  7. **Performance** — Benchmark comparison (hardcoded from paper)
  8. **API Reference** — Key functions/classes with signatures and descriptions
  9. **FAQ / Gotchas** — 5+ common mistakes and how to avoid them

BEFORE/AFTER CODE COMPARISON PATTERN (essential):
  ```html
  <div class="comparison">
    <div class="before">
      <h4>❌ Without {{framework_name}}</h4>
      <pre><code class="language-python">
  # 50 lines of boilerplate just to...
  import numpy as np
  model = ComplexSetup(...)
  # lots of configuration
      </code></pre>
    </div>
    <div class="after">
      <h4>✅ With {{framework_name}}</h4>
      <pre><code class="language-python">
  # 3 lines to accomplish the same thing
  from framework import AutoSolve
  result = AutoSolve.run(data)
      </code></pre>
    </div>
  </div>
  ```

SYNTAX HIGHLIGHTING (for website form):
  • Use Prism.js from CDN: https://cdn.jsdelivr.net/npm/prismjs@1.29.0/prism.min.js
  • Theme: https://cdn.jsdelivr.net/npm/prismjs@1.29.0/themes/prism-tomorrow.min.css
  • Language: https://cdn.jsdelivr.net/npm/prismjs@1.29.0/components/prism-python.min.js
  • Copy button pattern:
    ```javascript
    document.querySelectorAll('pre code').forEach(block => {{
      const btn = document.createElement('button');
      btn.textContent = 'Copy';
      btn.className = 'copy-btn';
      btn.onclick = () => navigator.clipboard.writeText(block.textContent)
        .then(() => {{ btn.textContent = 'Copied!'; setTimeout(() => btn.textContent='Copy', 2000); }});
      block.parentNode.style.position = 'relative';
      block.parentNode.appendChild(btn);
    }});
    ```

PERFORMANCE TABLE (hardcode from paper):
  | Method | Metric | Speed | Memory |
  |--------|--------|-------|--------|
  | This framework | XX | YY ms | ZZ MB |
  | Baseline A     | AA | BB ms | CC MB |
  Use real numbers. Always show this framework wins on at least 2 dimensions.

GRADIO APP PATTERN (for app form):
  ```python
  with gr.Tabs():
      with gr.TabItem("📦 Install"):
          gr.Markdown("```bash\\npip install framework-name\\n```")
      with gr.TabItem("🚀 Quick Start"):
          code_in  = gr.Code(value=QUICKSTART_CODE, language="python", label="Edit & Run")
          code_out = gr.Textbox(label="Output", lines=10)
          run_btn  = gr.Button("▶ Run", variant="primary")
          run_btn.click(fn=execute_code, inputs=code_in, outputs=code_out)
      with gr.TabItem("📚 Examples"):
          example_selector = gr.Dropdown(choices=list(EXAMPLES.keys()), label="Example")
          example_code = gr.Code(language="python", label="Code")
          example_out  = gr.Textbox(label="Output", lines=8)
      with gr.TabItem("⚡ Benchmarks"):
          perf_plot = gr.Plot(label="Performance vs. Alternatives")
  ```

CODE EXECUTION (for Gradio app only):
  ```python
  import subprocess, sys, tempfile, os

  def execute_code(code):
      with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
          f.write(code)
          fname = f.name
      try:
          result = subprocess.run([sys.executable, fname],
                                  capture_output=True, text=True, timeout=15)
          out = result.stdout or "(no output)"
          if result.returncode != 0:
              out += f"\\n[ERROR]\\n{{result.stderr[:500]}}"
          return out
      except subprocess.TimeoutExpired:
          return "[Timed out after 15s]"
      finally:
          os.unlink(fname)
  ```

WEBSITE DESIGN REQUIREMENTS (for website form):
  • sticky nav: Install | Quick Start | Concepts | Examples | Performance | API
  • Hero gradient background with terminal/code window mockup showing key example
  • Responsive two-column layout for before/after comparisons
  • Dark code blocks with copy buttons — Prism.js for syntax highlighting
  • NO Tailwind — write all CSS as custom properties in <style> tags
  • Installation command in a styled terminal block with copy button

FORM ADAPTATION — when the demo form is NOT 'app' or 'website':

  PRESENTATION (reveal.js):
    • Slide 1: Framework name + tagline + "Install in 30 seconds"
    • Slide 2: The Problem — code showing the painful old way (before)
    • Slide 3: The Solution — same task with this framework (after) → dramatic diff
    • Slide 4: Quick Start — copy-pasteable 10-line example
    • Slide 5-7: Core Concepts — one concept per slide with code + explanation
    • Slide 8: Architecture diagram (inline SVG showing framework modules)
    • Slide 9: Performance benchmarks (comparison table from paper)
    • Slide 10-11: Real-world examples and use cases
    • Slide 12: Ecosystem — integrations, community, roadmap
    • Slide 13: Conclusion + links → Slide 14: Q&A

  SLIDES / LATEX:
    • Extract code examples and architecture figures from PDF using extract_pdf_page
    • Show before/after code comparison as side-by-side columns
    • Include performance benchmark table with ALL baselines from paper
    • TikZ diagram for framework architecture

FIGURE INTEGRATION (for slides/latex/presentation forms):
  • Use extract_pdf_page to get architecture diagrams and benchmark figures
  • Code examples should be typeset (not screenshot images)
  • Performance tables must be structured data (add_table / tabular), not images

{self._multistep_instructions(demo_form)}

{self._tool_usage_instructions()}
"""

    def get_initial_message(self, paper: Paper, analysis: PaperAnalysis, demo_form: str, demo_type: str) -> str:
        return f"""Build a compelling {demo_form} tutorial for the framework in: "{paper.title}"

Contribution: {analysis.contribution}
Demo type: {demo_type}
Interaction: {analysis.interaction_pattern}

PRIORITY ORDER:
1. Write a minimal working example (< 20 lines) that shows the core value
2. Build a before/after comparison showing what this framework replaces
3. Add interactive code execution (Gradio) or working code snippets (website)
4. Include performance benchmarks from the paper
5. Make a developer reading this WANT to try the framework right now

Follow the execution plan. The result should be Stripe-docs quality.
"""

    def get_polish_prompt(self, paper, analysis, demo_form, demo_type, generated_files):
        spec = FORM_SPECS.get(demo_form, {})
        main_file = spec.get("main_file", "app.py")
        figures_available = [f for f in generated_files if f.startswith("figures/")]

        base_checks = f"""QUALITY REVIEW for Framework Tutorial — generated: {', '.join(generated_files[:12])}

Step 1 — Read {main_file} and verify core content:
  • Is there a before/after code comparison showing the framework's value?
  • Does the Quick Start example actually work (< 20 lines, correct imports)?
  • Is there a performance/benchmark table from the paper (real numbers)?"""

        if demo_form in ("app", "website"):
            return base_checks + """
Step 2 — Code quality:
  • Are copy-to-clipboard buttons on all code blocks?
  • Is Prism.js (or highlight.js) used for syntax highlighting?
  • Are there at least 3 progressively complex examples?
  • Does the FAQ section cover at least 5 common gotchas?

Step 3 — UX:
  • Can a developer copy the Quick Start code and run it in < 60 seconds?
  • Does the nav work and scroll smoothly to each section?
  • Are all code blocks visually distinct from prose?

Rewrite anything that falls short. Target: Stripe / FastAI documentation quality."""
        elif demo_form == "presentation":
            return base_checks + """
Step 2 — Slide-specific:
  • Is there a dramatic before/after code comparison (2 consecutive slides)?
  • Are there inline SVG diagrams for the framework architecture?
  • Does the performance slide have a styled comparison table?
  • Are code blocks properly syntax-highlighted and readable at slide size?
  • Do all slides use class="fragment" for bullet reveals?

Step 3 — Content completeness:
  • Is there a Quick Start slide with copy-pasteable code?
  • Are there >=14 slides covering the full tutorial arc?

Fix everything. Target: framework launch keynote quality."""
        elif demo_form in ("slides", "latex"):
            figs_line = f"  • Pre-extracted figures: {', '.join(figures_available)}\n" if figures_available else ""
            return base_checks + f"""
Step 2 — Slide content:
{figs_line}  • Are extracted figures embedded in relevant slides?
  • Is there a side-by-side before/after code comparison?
  • Are benchmark numbers hard-coded as structured tables?

Fix everything. Target: conference tutorial presentation quality."""
        else:
            return base_checks + """

Rewrite anything that falls short. Target: Stripe / FastAI documentation quality."""
