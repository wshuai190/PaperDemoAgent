"""
Example: Generate a demo for "Attention Is All You Need" (arXiv:1706.03762)

Usage:
    export ANTHROPIC_API_KEY=sk-ant-...
    python examples/demo_attention_paper.py
"""

from paper_demo_agent import PaperDemoAgent

agent = PaperDemoAgent(provider="anthropic")

print("Generating demo for 'Attention Is All You Need'...\n")

result = agent.run(
    source="1706.03762",
    demo_form="app",      # Interactive Gradio app
    demo_type="user_demo",
    on_progress=print,
)

print(f"\n✓ Demo generated!")
print(f"  Output: {result.output_dir}")
print(f"  Run:    {result.run_command}")
