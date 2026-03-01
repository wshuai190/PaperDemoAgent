"""
Example: Generate a survey comparison dashboard with Gemini

Usage:
    export GOOGLE_API_KEY=AIza...
    python examples/demo_survey_paper.py
"""

from paper_demo_agent import PaperDemoAgent

agent = PaperDemoAgent(provider="gemini", model="gemini-2.0-flash")

# A survey of transformer models
print("Generating survey comparison dashboard...\n")

result = agent.run(
    source="2106.04554",   # A Survey of Transformers
    demo_form="website",
    demo_type="findings",
    on_progress=print,
)

print(f"\n✓ Done!")
print(f"  Output: {result.output_dir}")
print(f"  Open:   {result.run_command}")
