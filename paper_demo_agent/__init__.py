"""Paper Demo Agent — AI agent that reads any scientific paper and builds a live demo."""

__version__ = "0.1.0"

from paper_demo_agent.agent import PaperDemoAgent
from paper_demo_agent.paper.models import Paper, PaperAnalysis, DemoResult

__all__ = ["PaperDemoAgent", "Paper", "PaperAnalysis", "DemoResult", "__version__"]
