"""
Example: Generate a data explorer demo for the ImageNet paper

Usage:
    export OPENAI_API_KEY=sk-...
    python examples/demo_imagenet_dataset.py
"""

from paper_demo_agent import PaperDemoAgent

agent = PaperDemoAgent(provider="openai", model="gpt-4o")

print("Generating dataset explorer...\n")

result = agent.run(
    source="https://arxiv.org/abs/1409.0575",  # ImageNet Large Scale Visual Recognition
    demo_form="app",
    demo_type="user_demo",
    on_progress=print,
)

print(f"\n✓ Done! Run: {result.run_command}")
