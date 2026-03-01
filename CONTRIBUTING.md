# Contributing to Paper Demo Agent

Thanks for your interest in contributing! Paper Demo Agent turns scientific papers into live demos, and we'd love your help making it better.

## Quick Links

- [Issues](https://github.com/wshuai190/PaperDemoAgent/issues) — bug reports, feature requests
- [Discussions](https://github.com/wshuai190/PaperDemoAgent/discussions) — questions, ideas, show & tell

## Getting Started

```bash
git clone https://github.com/wshuai190/PaperDemoAgent
cd PaperDemoAgent
pip install -e ".[dev]"
pytest tests/
```

You'll need at least one LLM API key to test demo generation:

```bash
paper-demo-agent key set ANTHROPIC_API_KEY sk-ant-...
# or
paper-demo-agent key set OPENAI_API_KEY sk-...
```

## Project Structure

```
paper_demo_agent/
├── agent.py              # Main orchestrator (parse → analyze → route → generate)
├── config.py             # API key storage (~/.paper-demo-agent/config.json)
├── cli.py                # Click CLI entry point
├── ui/app.py             # Gradio web interface
├── providers/            # LLM providers (Anthropic, OpenAI, Gemini, DeepSeek, Qwen, MiniMax)
├── paper/                # Paper parsing (arXiv API, PDF extraction)
├── analysis/             # Paper classification + skill routing
├── skills/               # Demo generation skills (one per output type)
└── generation/           # Multi-phase generator + tool definitions
```

## Good First Issues

These are great starting points for new contributors:

- **Add a new LLM provider** — subclass `BaseLLMProvider` in `providers/`, register in `factory.py`. Good candidates: Groq, Together AI, Ollama (local).
- **Improve skill prompts** — each skill in `skills/` has a system prompt. Try generating a demo, identify issues, and improve the prompt.
- **Add test cases** — we have 79 tests but coverage can always improve. Unit tests for parsing, analysis, and config are especially welcome.
- **Fix output quality issues** — generate a demo for a paper you know well, then fix any content/layout issues in the relevant skill.
- **Improve the Gradio UI** — the UI is in `ui/app.py`. Accessibility improvements, better mobile layout, or new features are all welcome.

## How to Add a New Skill

1. Create `paper_demo_agent/skills/your_skill.py`
2. Subclass `BaseSkill` from `skills/base.py`
3. Implement `get_system_prompt()`, `get_initial_message()`, and optionally `get_polish_prompt()`
4. Register your skill in the router (`analysis/router.py`)
5. Add tests in `tests/`

Look at `skills/model_inference.py` or `skills/flowchart_generator.py` for examples.

## How to Add a New Provider

1. Create `paper_demo_agent/providers/your_provider.py`
2. Subclass `BaseLLMProvider`
3. Implement `chat()` (streaming) and `chat_with_tools()` (tool use)
4. Register in `providers/factory.py`
5. Add the env variable name to `config.py`

Look at `providers/openai_provider.py` for a clean example.

## Development Workflow

1. **Fork** the repo and create a branch (`git checkout -b feature/my-feature`)
2. **Make changes** — follow existing code style, no need for docstrings on internal functions
3. **Test** — run `pytest tests/` and make sure all tests pass
4. **Commit** — write a clear commit message describing *why*, not just *what*
5. **Push** and open a Pull Request

## Code Style

- Python 3.9+ compatible
- No strict formatter enforced — just follow the existing style
- Keep functions focused and avoid over-engineering
- Prefer editing existing files over creating new ones
- Type hints appreciated but not required

## Reporting Bugs

When reporting a bug, please include:

- The **arXiv ID** or paper source you used
- The **provider** and **model** (e.g., `anthropic / claude-sonnet-4-6`)
- The **form** you requested (e.g., `--form presentation`)
- The **error message** or description of what went wrong
- Your **Python version** and **OS**

## Submitting Demos to the Gallery

Generated a great demo? We'd love to feature it!

1. Open an issue with the title `[Gallery] Paper Name — form type`
2. Attach a screenshot of the output
3. Include the arXiv ID and the command you ran
4. We'll add it to the README gallery

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
