<div align="center">

# Paper Demo Agent

**Turn any scientific paper into a live interactive demo.**

[![PyPI version](https://img.shields.io/pypi/v/paper-demo-agent.svg)](https://pypi.org/project/paper-demo-agent/)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Downloads](https://img.shields.io/pypi/dm/paper-demo-agent.svg)](https://pypi.org/project/paper-demo-agent/)

![Paper Demo Agent Demo](docs/assets/demo.svg)

![Paper Demo Agent UI](docs/assets/ui-screenshot.svg)

[Quick Start](#quick-start) | [What's In 0.3.2](#whats-new-in-v032) | [Forms](#forms-and-subtypes) | [Providers](#supported-providers) | [CLI](#cli-reference) | [UI](#web-ui) | [Python API](#python-api)

</div>

---

## What's New in v0.3.2

- README and UI copy now match the current category/subtype model used by the CLI and agent.
- Version bumped to `0.3.2`.
- Docs now reflect the current zero-config auth paths: Claude Code, Gemini CLI, `gcloud` ADC, OpenAI Codex CLI, and Aider.
- README now documents the current generation stack: 13 routed skills, 15 generation tools, the graphics toolkit, and PDF figure/table extraction utilities.

---

## Quick Start

Install:

```bash
pip install paper-demo-agent
```

Generate a demo from an arXiv paper:

```bash
paper-demo-agent demo 1706.03762
```

Use Claude Code credentials if you already have them:

```bash
npm install -g @anthropic-ai/claude-code
claude login
paper-demo-agent demo 1706.03762 --provider anthropic
```

Use Gemini CLI credentials instead:

```bash
npm install -g @google/gemini-cli
gemini
paper-demo-agent demo 1706.03762 --provider gemini
```

Or set API keys directly:

```bash
paper-demo-agent key set ANTHROPIC_API_KEY <token>
paper-demo-agent key set OPENAI_API_KEY <token>
paper-demo-agent demo 1706.03762 --provider openai
```

Launch the UI:

```bash
paper-demo-agent ui
```

With `pipx`:

```bash
pipx run paper-demo-agent ui
```

---

## What It Does

Paper Demo Agent reads a paper, classifies its contribution, routes it to a specialized skill, and generates one of 10 output formats across 4 top-level categories:

- `app`: Gradio or Streamlit
- `presentation`: HTML slides, PowerPoint, or LaTeX/Beamer
- `page`: project page, README, or blog article
- `diagram`: Mermaid or Graphviz

Current repo highlights:

- 13 routed skills for model, dataset, algorithm, framework, theory, survey, findings, README, blog, Streamlit, Mermaid, and Graphviz generation
- 15 generation tools including `append_file`, `validate_output`, `render_svg`, `extract_pdf_page`, `extract_figure`, `extract_tables`, and `list_pdf_pages`
- 6 providers: Anthropic, OpenAI, Gemini, DeepSeek, Qwen, and MiniMax
- Gradio UI with auth status, progress streaming, phase stepper, file preview, ZIP download, and one-click open
- Expanded graphics toolkit for SVG, Mermaid, Chart.js, D3, and TikZ-based outputs

---

## How It Works

1. Parse the source from arXiv, URL, local PDF, or raw text.
2. Analyze the paper to infer paper type, demo type, and best form.
3. Route to a specialized skill.
4. Run the generation loop: Research, Build, Polish, Validate.
5. Return runnable output under `demos/` by default.

The generator uses form-specific budgets. Current defaults in code include:

- `presentation`: build 15, polish 3
- `website`, `app`, `app_streamlit`: build 12, polish 3
- `page_blog`, `slides`, `latex`: build 14, polish 3
- `flowchart`: build 8, polish 2
- `page_readme`, `diagram_graphviz`: build 6, polish 2

---

## Forms And Subtypes

Preferred CLI usage is category + subtype:

| Category | Subtypes | Internal Output |
|---|---|---|
| `app` | `gradio`, `streamlit` | `app.py` |
| `presentation` | `revealjs`, `pptx`, `beamer` | `demo.html`, `build.py`, `presentation.tex` |
| `page` | `project`, `readme`, `blog` | `index.html`, `README.md` |
| `diagram` | `mermaid`, `graphviz` | `index.html`, `build.py` |

Examples:

```bash
paper-demo-agent demo 1706.03762 --form app --subtype streamlit
paper-demo-agent demo 1706.03762 --form presentation --subtype revealjs
paper-demo-agent demo 1706.03762 --form presentation --subtype pptx
paper-demo-agent demo 1706.03762 --form presentation --subtype beamer
paper-demo-agent demo 1706.03762 --form page --subtype project
paper-demo-agent demo 1706.03762 --form page --subtype readme
paper-demo-agent demo 1706.03762 --form page --subtype blog
paper-demo-agent demo 1706.03762 --form diagram --subtype mermaid
paper-demo-agent demo 1706.03762 --form diagram --subtype graphviz
```

Legacy flat aliases are still accepted for compatibility:

- `website` = `page/project`
- `slides` = `presentation/pptx`
- `latex` = `presentation/beamer`
- `flowchart` = `diagram/mermaid`

---

## Input Sources

`paper-demo-agent demo SOURCE` accepts:

- arXiv ID: `1706.03762`
- arXiv-prefixed ID: `arxiv:1706.03762`
- arXiv URL
- local PDF path
- raw text

---

## Supported Providers

| Provider | Default Model | Key | Notes |
|---|---|---|---|
| Anthropic | `claude-sonnet-4-6` | `ANTHROPIC_API_KEY` | Supports Claude Code auto-detection |
| OpenAI | `gpt-5.2` | `OPENAI_API_KEY` | Supports Codex CLI auto-detection |
| Gemini | `auto-gemini-2.5` | `GOOGLE_API_KEY` | Supports Gemini CLI and `gcloud` ADC |
| DeepSeek | `deepseek-chat` | `DEEPSEEK_API_KEY` | OpenAI-compatible provider |
| Qwen | `qwen-max` | `QWEN_API_KEY` | DashScope-backed |
| MiniMax | `abab6.5-chat` | `MINIMAX_API_KEY` | Also needs `MINIMAX_GROUP_ID` |

### Credential Resolution

Current key resolution is source-specific:

- Anthropic: Claude Code -> saved config -> environment -> Aider
- Gemini: Gemini CLI -> saved config -> environment -> `gcloud` ADC
- OpenAI: saved config -> environment -> OpenAI Codex CLI -> Aider

Supported auto-detected sources:

- Claude Code: `~/.claude/.credentials.json` or macOS Keychain
- Gemini CLI: `~/.gemini/oauth_creds.json`, macOS Keychain, or OpenClaw profile
- Google ADC: `~/.config/gcloud/application_default_credentials.json`
- OpenAI Codex CLI: `~/.codex/auth.json`
- Aider: `~/.aider.conf.yml`

---

## Web UI

Run:

```bash
paper-demo-agent ui
```

Optional flags:

```bash
paper-demo-agent ui --port 8080
paper-demo-agent ui --share
paper-demo-agent ui --auth admin:secret
paper-demo-agent ui --no-browser
```

The UI includes:

- quick auth cards for Claude Code and Gemini CLI
- provider dropdown with credential status
- output category and subtype selectors
- live progress split by Parse, Analyze, Research, Build, Polish, and Validate
- generated file list, preview, ZIP download, and open/run actions

---

## System Dependencies

Most outputs are pure Python or HTML.

Graphviz diagrams need the system `dot` binary:

```bash
# macOS
brew install graphviz

# Ubuntu / Debian
sudo apt-get install graphviz
```

LaTeX / Beamer output needs a TeX distribution:

```bash
# macOS
brew install --cask mactex-no-gui

# Ubuntu / Debian
sudo apt-get install texlive-latex-recommended texlive-fonts-extra
```

---

## CLI Reference

```bash
# Auto-pick the output
paper-demo-agent demo 1706.03762

# Pick provider and model
paper-demo-agent demo 1706.03762 --provider anthropic --model claude-opus-4-6
paper-demo-agent demo 1706.03762 --provider openai --model gpt-5.2

# Pick category + subtype
paper-demo-agent demo 1706.03762 --form app --subtype streamlit
paper-demo-agent demo 1706.03762 --form presentation --subtype beamer
paper-demo-agent demo 1706.03762 --form page --subtype readme
paper-demo-agent demo 1706.03762 --form diagram --subtype graphviz

# Local PDF
paper-demo-agent demo ./paper.pdf --form presentation --subtype pptx

# Output directory
paper-demo-agent demo 1706.03762 --output ./my-demo

# Provider list
paper-demo-agent providers

# Key management
paper-demo-agent key set ANTHROPIC_API_KEY <token>
paper-demo-agent key list
paper-demo-agent key delete ANTHROPIC_API_KEY

# Hugging Face login for gated assets
paper-demo-agent login
paper-demo-agent logout
```

---

## Python API

```python
from paper_demo_agent import PaperDemoAgent

agent = PaperDemoAgent(provider="anthropic")

result = agent.run(
    source="1706.03762",
    demo_form="page",
    demo_subtype="project",
    max_iter=25,
    on_progress=print,
)

print(result.output_dir)
print(result.main_file)
print(result.run_command)
```

You can also use the lower-level steps:

```python
paper = agent.parse("1706.03762")
analysis = agent.analyze(paper)
print(analysis.paper_type)
print(analysis.demo_form)
print(analysis.demo_subtype)
```

`run_from_pdf()` is available for UI-style byte uploads.

---

## Project Structure

```text
paper_demo_agent/
|-- agent.py
|-- cli.py
|-- config.py
|-- ui/app.py
|-- analysis/
|-- paper/
|-- providers/
|-- generation/
|   |-- generator.py
|   |-- runner.py
|   `-- tools.py
|-- graphics/
`-- skills/
```

Important top-level docs:

- `IMPROVEMENT_LOG.md`
- `CONTRIBUTING.md`

Examples:

- `examples/demo_attention_paper.py`
- `examples/demo_imagenet_dataset.py`
- `examples/demo_survey_paper.py`

---

## Notes And Troubleshooting

- Large single-file outputs are handled with `write_file` plus `append_file`; the hard 300-line write limit described in older docs is no longer enforced.
- `validate_output` exists as an internal generation tool, not as a public CLI command.
- Figure and table extraction are available to the generator through `extract_pdf_page`, `extract_figure`, `extract_tables`, and `list_pdf_pages`.
- Generated demos are written under `demos/` unless `--output` is provided.

---

## Development

```bash
git clone https://github.com/wshuai190/PaperDemoAgent
cd PaperDemoAgent
pip install -e ".[dev]"
pytest tests/
```

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

---

## License

MIT. See [LICENSE](LICENSE).
