<div align="center">

# Paper Demo Agent

**Turn any scientific paper into a live interactive demo — with one command.**

[![PyPI version](https://img.shields.io/pypi/v/paper-demo-agent.svg)](https://pypi.org/project/paper-demo-agent/)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Downloads](https://img.shields.io/pypi/dm/paper-demo-agent.svg)](https://pypi.org/project/paper-demo-agent/)

![Paper Demo Agent Demo](docs/assets/demo.svg)

![Paper Demo Agent UI](docs/assets/ui-screenshot.svg)

[Quick Start](#quick-start) · [Features](#features) · [Output Formats](#output-formats) · [Providers](#supported-providers) · [CLI Reference](#cli-reference) · [Python API](#python-api)

</div>

---

## What's New in v0.3.1

- **Claude Code OAuth** — Use your Claude Pro/Max subscription directly. Auto-detected from the macOS Keychain or `~/.claude/` after `claude auth login`. No API key needed.
- **`claude setup-token` support** — Generate a long-lived token with `claude setup-token` and save it with `paper-demo-agent key set ANTHROPIC_API_KEY <token>`.
- **Gemini CLI auto-detection** — Auto-detects credentials from `~/.gemini/oauth_creds.json` after running `gemini`. No Google API key needed.

---

## Quick Start

**No API key needed** — authenticate with Claude Code or Gemini CLI:

```bash
pip install paper-demo-agent

# Option A: Use Claude Pro/Max subscription (free — no API billing)
claude auth login               # one-time: sign into claude.ai
paper-demo-agent demo 1706.03762

# Option B: Use Gemini CLI (free tier)
gemini                          # one-time: sign into Google
paper-demo-agent demo 1706.03762 --provider gemini

# Option C: Traditional API key
paper-demo-agent key set ANTHROPIC_API_KEY sk-ant-...
paper-demo-agent demo 1706.03762
```

Or launch the web UI:

```bash
paper-demo-agent ui
# → Opens http://localhost:7860
```

No `pip` needed (with pipx):

```bash
pipx run paper-demo-agent ui
```

### System Dependencies (optional)

Most output formats are pure Python/HTML and need no extra setup. For **Graphviz diagrams** (`--form diagram --subtype graphviz`), the system-level Graphviz binary is required:

```bash
# macOS
brew install graphviz

# Ubuntu / Debian
sudo apt-get install graphviz
```

For **LaTeX/Beamer** output (`--form presentation --subtype beamer`), a TeX distribution is needed:

```bash
# macOS
brew install --cask mactex-no-gui

# Ubuntu / Debian
sudo apt-get install texlive-latex-recommended texlive-fonts-extra
```

---

## Features

| | Feature | Description |
|---|---|---|
| 🧠 | **Smart Routing** | AI reads the paper and picks the best demo type — model inference, data explorer, slides, diagram, and more |
| 📦 | **10 Output Formats** | Gradio apps, Streamlit dashboards, reveal.js slides, PowerPoint, LaTeX/Beamer, project pages, blog articles, READMEs, Mermaid flowcharts, Graphviz diagrams |
| 🤖 | **Multi-Phase Agent** | 4-phase pipeline (Research → Build → Polish → Validate) with tool use, prior-work analysis, and self-correction |
| 🔌 | **6 LLM Providers** | Anthropic, OpenAI, Google Gemini, DeepSeek, Qwen, MiniMax — switch with one flag |
| 🔑 | **Zero-Config Auth** | Auto-detects credentials from Claude Code (OAuth), Gemini CLI (OAuth), OpenAI Codex CLI, Aider, and gcloud ADC — no API keys needed |
| 📄 | **Any Input** | arXiv ID, arXiv URL, any URL, local PDF, or raw text |
| 🌐 | **Web UI** | Dark-themed Gradio interface with real-time progress streaming, phase stepper, file preview, and one-click demo launch |
| ⚡ | **One Command** | `paper-demo-agent demo 1706.03762` — that's it |

---

## How It Works

```mermaid
flowchart LR
    A[Paper Input] --> B[Parse]
    B --> C[Analyze]
    C --> D{Route to Skill}
    D --> E[Research Phase]
    E --> F[Build Phase]
    F --> G[Polish Phase]
    G --> H[Validate Phase]
    H --> I[Live Demo]

    style A fill:#6366f1,stroke:#4f46e5,color:#fff
    style I fill:#22c55e,stroke:#16a34a,color:#fff
```

1. **Parse** — Fetches the paper from arXiv, URL, or local PDF. Extracts title, abstract, full text, and figures.
2. **Analyze** — AI classifies the paper type (model, dataset, algorithm, framework, survey, theory, empirical) and recommends the best output format.
3. **Route** — Maps paper type + user preferences to one of 15 specialized skills.
4. **Research** — Finds the paper's official resources (GitHub, HuggingFace, project page) and identifies foundational prior work to give the build agent a bigger picture. Library docs are pre-baked in the skill prompts.
5. **Build** — Multi-iteration code generation with 7 tools (write_file, read_file, list_files, web_search, run_python, extract_pdf_page, execute_command).
6. **Polish** — Quality review pass with skill-specific checklists.
7. **Validate** — Form-compliance check ensures the output matches the requested format, with auto-correction if needed.

---

## Output Formats

### Apps

| Format | Technology | Best For |
|---|---|---|
| **Gradio App** | Gradio 5 (Python) | Model inference, interactive demos, HuggingFace Spaces |
| **Streamlit App** | Streamlit (Python) | Data dashboards, exploration tools, widgets |

### Presentations

| Format | Technology | Best For |
|---|---|---|
| **HTML Slides** | reveal.js 5.2.1 | Animated talks with KaTeX math and speaker notes |
| **PowerPoint** | python-pptx 1.0.0 | Conference presentations, offline sharing |
| **LaTeX / Beamer** | Beamer + Metropolis | Academic talks with TikZ diagrams and booktabs |

### Pages

| Format | Technology | Best For |
|---|---|---|
| **Project Page** | HTML/CSS/JS | Nerfies/Distill.pub-style research landing pages |
| **Blog Article** | HTML + D3.js + KaTeX | Interactive explainers with visualizations |
| **GitHub README** | Markdown + Mermaid | Publication-quality README with badges and diagrams |

### Diagrams

| Format | Technology | Best For |
|---|---|---|
| **Mermaid Flowchart** | Mermaid.js v11 (ESM) | Interactive architecture diagrams, step-by-step walkthroughs |
| **Graphviz Diagram** | Python graphviz | Publication-quality SVG/PNG architecture diagrams |

### Gallery

| Interactive Diagram | reveal.js Presentation | Project Website | Gradio App |
|---|---|---|---|
| ![Diagram](docs/assets/output-diagram.svg) | ![Presentation](docs/assets/output-presentation.svg) | ![Website](docs/assets/output-website.svg) | ![App](docs/assets/output-app.svg) |
| ResNet — Mermaid flowchart | Attention — HTML slides | Attention — project page | BERT — Gradio demo |

<details>
<summary><strong>Made with Paper Demo Agent</strong> — community showcase</summary>

| Paper | arXiv | Format | Command |
|-------|-------|--------|---------|
| Attention Is All You Need | [1706.03762](https://arxiv.org/abs/1706.03762) | Presentation | `paper-demo-agent demo 1706.03762 --form presentation` |
| Attention Is All You Need | [1706.03762](https://arxiv.org/abs/1706.03762) | Project Page | `paper-demo-agent demo 1706.03762 --form page` |
| Deep Residual Learning | [1512.03385](https://arxiv.org/abs/1512.03385) | Flowchart | `paper-demo-agent demo 1512.03385 --form diagram` |
| BERT | [1810.04805](https://arxiv.org/abs/1810.04805) | Gradio App | `paper-demo-agent demo 1810.04805 --form app` |

**Want to add yours?** Open an [issue](https://github.com/wshuai190/PaperDemoAgent/issues) with the title `[Gallery] Paper Name — format` and a screenshot!

</details>

---

## Supported Providers

| Provider | Default Model | Env Variable | Notes |
|---|---|---|---|
| **Anthropic** | `claude-opus-4-6` | `ANTHROPIC_API_KEY` | Best quality. Auto-detected from Claude Code |
| **OpenAI** | `gpt-5.2` | `OPENAI_API_KEY` | Also supports o3, o4-mini. Auto-detected from Codex CLI |
| **Gemini** | `gemini-2.5-flash` | `GOOGLE_API_KEY` | Auto-detected from Gemini CLI or gcloud ADC |
| **DeepSeek** | `deepseek-chat` | `DEEPSEEK_API_KEY` | Also supports deepseek-reasoner |
| **Qwen** | `qwen-max` | `QWEN_API_KEY` | Also supports qwen-plus, qwen-turbo |
| **MiniMax** | `abab6.5-chat` | `MINIMAX_API_KEY` | Also requires `MINIMAX_GROUP_ID` |

### Zero-Config Authentication

Paper Demo Agent automatically detects credentials from CLI tools you already use — **no API keys needed**:

| Tool | Auth Method | Provides | Setup |
|---|---|---|---|
| **Claude Code** | OAuth (macOS Keychain / `~/.claude/`) | `ANTHROPIC_API_KEY` | `claude auth login` — uses your Pro/Max subscription |
| **Gemini CLI** | OAuth (`~/.gemini/oauth_creds.json`) | `GOOGLE_API_KEY` | `gemini` — free tier: 60 req/min, 1000 req/day |
| **OpenAI Codex CLI** | `~/.codex/auth.json` | `OPENAI_API_KEY` | Auto-detected |
| **Aider** | `~/.aider.conf.yml` | `ANTHROPIC_API_KEY`, `OPENAI_API_KEY` | Auto-detected |
| **gcloud ADC** | Application Default Credentials | Gemini auth | `gcloud auth application-default login` |

**Priority order:** saved config → environment variables → Claude Code / Codex / Aider.

If you use any of these tools, Paper Demo Agent works immediately — no key setup required.

> **💡 Recommended:** Install [Claude Code](https://github.com/anthropics/claude-code) (`npm i -g @anthropic-ai/claude-code && claude auth login`) for the fastest zero-config experience with your Claude Pro/Max subscription.

---

## CLI Reference

```bash
# Generate a demo (AI picks the best format)
paper-demo-agent demo 1706.03762

# Specify provider and model
paper-demo-agent demo arxiv:1706.03762 \
    --provider anthropic \
    --model claude-opus-4-6

# Specify output format
paper-demo-agent demo 1706.03762 --form presentation
paper-demo-agent demo 1706.03762 --form app --subtype streamlit
paper-demo-agent demo 1706.03762 --form presentation --subtype beamer
paper-demo-agent demo 1706.03762 --form page --subtype readme
paper-demo-agent demo 1706.03762 --form diagram --subtype graphviz

# From a local PDF
paper-demo-agent demo paper.pdf --provider openai

# Custom output directory
paper-demo-agent demo 1706.03762 --output ./my-demo

# Launch the web UI
paper-demo-agent ui
paper-demo-agent ui --port 8080 --share

# Manage API keys
paper-demo-agent key set ANTHROPIC_API_KEY sk-ant-...
paper-demo-agent key set OPENAI_API_KEY sk-...
paper-demo-agent key list

# List available providers
paper-demo-agent providers

# HuggingFace (for gated models)
paper-demo-agent login   # Browser-based HF login
paper-demo-agent logout
```

---

## Python API

```python
from paper_demo_agent import PaperDemoAgent

agent = PaperDemoAgent(provider="anthropic")

# Full pipeline: parse → analyze → generate
result = agent.run(
    source="1706.03762",
    demo_form="app",           # or: presentation, slides, latex, website, flowchart, ...
    demo_type="user_demo",     # or: findings, theoretical
    on_progress=print,
)

print(f"Output:  {result.output_dir}")
print(f"Main:    {result.main_file}")
print(f"Run:     {result.run_command}")
```

### Step-by-Step

```python
# Parse only
paper = agent.parse("1706.03762")
print(f"Title: {paper.title}")
print(f"Abstract: {paper.abstract[:200]}...")

# Analyze
analysis = agent.analyze(paper)
print(f"Paper type: {analysis.paper_type}")
print(f"Recommended form: {analysis.demo_form}")
print(f"Recommended type: {analysis.demo_type}")
```

---

## Architecture

```mermaid
graph TB
    subgraph Input
        A1[arXiv ID/URL]
        A2[PDF Upload]
        A3[Text/URL]
    end

    subgraph Core
        B[PaperDemoAgent]
        C[Paper Parser]
        D[Paper Analyzer]
        E[Skill Router]
    end

    subgraph Skills
        S1[ModelInferenceSkill]
        S2[DataExplorerSkill]
        S3[AlgorithmVisualizerSkill]
        S4[FrameworkTutorialSkill]
        S5[SurveyDashboardSkill]
        S6[TheoreticalExplainerSkill]
        S7[FindingsDashboardSkill]
        S8[FlowchartGeneratorSkill]
        S9[GraphvizDiagramSkill]
        S10[ReadmeGeneratorSkill]
        S11[BlogExplainerSkill]
        S12[StreamlitDemoSkill]
        S13[GeneralQASkill]
    end

    subgraph Generator["Multi-Phase Generator"]
        G1[Research Phase]
        G2[Build Phase]
        G3[Polish Phase]
        G4[Validate Phase]
    end

    subgraph Providers
        P1[Anthropic]
        P2[OpenAI]
        P3[Gemini]
        P4[DeepSeek]
        P5[Qwen]
        P6[MiniMax]
    end

    A1 & A2 & A3 --> B
    B --> C --> D --> E
    E --> S1 & S2 & S3 & S4 & S5 & S6 & S7 & S8 & S9 & S10 & S11 & S12 & S13
    S1 & S2 & S3 & S4 & S5 & S6 & S7 & S8 & S9 & S10 & S11 & S12 & S13 --> G1 --> G2 --> G3 --> G4
    G1 & G2 & G3 & G4 -.-> P1 & P2 & P3 & P4 & P5 & P6

    style B fill:#6366f1,stroke:#4f46e5,color:#fff
    style G2 fill:#6366f1,stroke:#4f46e5,color:#fff
```

## Project Structure

```
paper_demo_agent/
├── agent.py              # Main orchestrator (parse → analyze → route → generate)
├── config.py             # ~/.paper-demo-agent/config.json key storage
├── cli.py                # CLI entry point (click)
├── ui/app.py             # Gradio web interface
├── providers/            # LLM providers (Anthropic, OpenAI, Gemini, DeepSeek, Qwen, MiniMax)
├── paper/                # Paper parsing (arXiv API, PDF extraction, URL fetching)
├── analysis/             # Paper classification + routing
├── skills/               # 13 specialized demo generation skills
│   ├── model_inference.py
│   ├── data_explorer.py
│   ├── algorithm_visualizer.py
│   ├── framework_tutorial.py
│   ├── survey_dashboard.py
│   ├── theoretical_explainer.py
│   ├── findings_dashboard.py
│   ├── flowchart_generator.py
│   ├── graphviz_diagram.py
│   ├── readme_generator.py
│   ├── blog_explainer.py
│   ├── streamlit_demo.py
│   ├── general_qa.py
│   └── ...
└── generation/           # Multi-phase generator + tool definitions
    ├── generator.py      # 4-phase pipeline (Research → Build → Polish → Validate) + prior-work analysis
    ├── tools.py          # 7 agent tools (write_file, read_file, web_search, ...)
    └── runner.py         # Demo launcher (open in browser / run app server)
```

---

## Performance Benchmarks

Measured on `claude-sonnet-4-6` with standard arxiv papers (approximate, varies by paper complexity):

| Form | Typical Time | Approx. Tokens | Output Size |
|------|-------------|----------------|-------------|
| `presentation` (reveal.js) | 3–6 min | ~35k | 25–60 KB HTML |
| `slides` (python-pptx) | 4–7 min | ~40k | 20–50 KB build.py + .pptx |
| `page` (project page) | 4–7 min | ~40k | 30–80 KB HTML + CSS + JS |
| `page --subtype blog` | 5–8 min | ~45k | 40–90 KB |
| `app` (Gradio) | 3–5 min | ~25k | 8–25 KB Python |
| `diagram` (Mermaid) | 2–4 min | ~15k | 5–15 KB HTML |
| `page --subtype readme` | 2–3 min | ~10k | 3–8 KB Markdown |

**Notes:**
- Research phase (~2 iterations) runs first and accounts for ~1 min of the above
- Figure pre-extraction (for slides/latex/presentation) adds 30–90s depending on PDF size
- `claude-opus-4-6` produces higher quality but takes ~2× longer and costs ~5× more tokens
- Token estimates include system prompt, tool calls, and generated output

---

## Troubleshooting

### Write truncation (file is empty or cut off)

If a generated file is shorter than expected, the model tried to write too much at once:
- The 300-line-per-write limit is enforced; the model is instructed to use `append_file` for large files.
- If you see truncated output, try `--max-iter 30` to give the agent more budget to complete the file.
- For `presentation` form, the skeleton-first strategy (write ~8 slides, then append more) is automatic.

### CDN failures (blank page or JS errors)

All CDN URLs are pinned to verified versions. If a CDN is unreachable:
- Reveal.js: unpkg.com hosts 5.2.1 reliably; no known outages
- Chart.js 4.4.7 and D3 v7: served from jsDelivr and d3js.org respectively
- Run `validate_output` manually: `paper-demo-agent validate /tmp/my-demo/index.html`

### Orphaned tool_use IDs (API 400 error)

Rare bug: occurs when the "search limit → force write" nudge fires mid-iteration.
- Symptom: crash with `"tool_use ids found without tool_result blocks"`
- Fix: re-run with `--max-iter 20`; the loop now validates message history before each API call.
- This was a known issue as of Session 4 and is tracked for a future fix.

### Figure extraction fails

If figures are blank or missing:
- Docling (deep learning layout model) is the primary method. Install with: `pip install docling`
- Fallback: heuristic PyMuPDF extraction (always available if `pymupdf` is installed)
- If both fail, the model will call `extract_pdf_page()` manually during build

### Model stalls without writing files

Symptom: many "calling model..." lines with only `web_search` calls.
- The search-limit nudge fires after 2 consecutive search-only iterations and forces a write.
- If stalling persists, the model may be confused about form requirements; try adding `--subtype`.

---

## Development

```bash
git clone https://github.com/wshuai190/PaperDemoAgent
cd paper-demo-agent
pip install -e ".[dev]"
pytest tests/
```

See [IMPROVEMENT_LOG.md](IMPROVEMENT_LOG.md) for a detailed record of all improvements across development sessions.

## Contributing

Contributions are welcome! See **[CONTRIBUTING.md](CONTRIBUTING.md)** for the full guide.

- **Bug reports** — include the arXiv ID and provider used
- **New skills** — subclass `BaseSkill` and register in the router
- **New providers** — subclass `BaseLLMProvider` and add to `factory.py`
- **Gallery submissions** — generated a great demo? Open an issue with a screenshot!

---

## License

MIT — see [LICENSE](LICENSE)

---

<div align="center">

**If Paper Demo Agent saved you time, give it a star!**

[![Star on GitHub](https://img.shields.io/github/stars/wshuai190/PaperDemoAgent?style=social)](https://github.com/wshuai190/PaperDemoAgent)

</div>
