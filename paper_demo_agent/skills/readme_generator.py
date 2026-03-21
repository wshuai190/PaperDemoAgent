"""Skill for generating publication-quality GitHub READMEs with Mermaid diagrams."""

from paper_demo_agent.paper.models import Paper, PaperAnalysis
from paper_demo_agent.skills.base import BaseSkill


# ─────────────────────────────────────────────────────────────────────────────
# Pre-baked tool knowledge — never search for these basics
# ─────────────────────────────────────────────────────────────────────────────

_README_PATTERNS = """
━━ GITHUB README MARKDOWN — COMPLETE REFERENCE (use verbatim, do NOT search) ━━

SHIELDS.IO BADGES (place right after title, one line):
```markdown
![Python](https://img.shields.io/badge/python-3.9+-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Paper](https://img.shields.io/badge/paper-PDF-red)
```

ARXIV BADGE (link to the actual paper — ALWAYS include):
```markdown
[![arXiv](https://img.shields.io/badge/arXiv-XXXX.XXXXX-b31b1b.svg)](https://arxiv.org/abs/XXXX.XXXXX)
```
Replace XXXX.XXXXX with the real arXiv ID from web_search results.

CONFERENCE / VENUE BADGES:
```markdown
![Venue](https://img.shields.io/badge/NeurIPS-2024-4b44ce)
![Venue](https://img.shields.io/badge/ICML-2024-blue)
![Venue](https://img.shields.io/badge/ICLR-2024-orange)
```

MERMAID DIAGRAMS (GitHub renders natively in ```mermaid code fences):
```markdown
  ```mermaid
  flowchart TD
      A["Input Data"] --> B["Preprocessing"]
      B --> C{"Model Selection"}
      C -->|"Option A"| D["Transformer"]
      C -->|"Option B"| E["CNN"]
      D --> F["Output"]
      E --> F
      style A fill:#3b82f6,stroke:#2563eb,color:#fff
      style D fill:#6366f1,stroke:#4f46e5,color:#fff
      style E fill:#6366f1,stroke:#4f46e5,color:#fff
      style F fill:#22c55e,stroke:#16a34a,color:#fff
  ```
```

COLOR CODING FOR MERMAID NODES (same scheme as flowchart skill):
  #3b82f6  blue    — Inputs, data, datasets
  #6366f1  indigo  — Core transforms, model components
  #f59e0b  amber   — Decision points, hyperparameters
  #22c55e  green   — Outputs, predictions, results
  #ef4444  red     — Loss functions, error signals
  #8b5cf6  violet  — External tools, pretrained models
  #06b6d4  cyan    — Evaluation metrics, benchmarks

COLLAPSIBLE SECTIONS (use for long content — keeps README scannable):
```markdown
<details>
<summary><b>Detailed Results on ImageNet</b></summary>

| Method     | Top-1 Acc | Top-5 Acc | Params |
|:-----------|:---------:|:---------:|:------:|
| ResNet-50  |   76.1    |   92.9    | 25.6M  |
| **Ours**   | **79.3**  | **94.5**  | 23.1M  |

</details>
```

RESULTS TABLES (bold the best results, align numbers center):
```markdown
| Method           | BLEU↑  | ROUGE-L↑ | METEOR↑ | Latency (ms)↓ |
|:-----------------|:------:|:--------:|:-------:|:--------------:|
| Baseline A       |  38.1  |  0.541   |  0.367  |      142       |
| Baseline B       |  41.7  |  0.578   |  0.389  |      198       |
| Prior SOTA       |  42.9  |  0.590   |  0.401  |      175       |
| **Ours**         | **45.3** | **0.621** | **0.412** | **128**   |

Use ↑ for higher-is-better metrics and ↓ for lower-is-better metrics.
Always bold the best value in each column.
```

BIBTEX CITATION BLOCK:
```markdown
## Citation

If you find this work useful, please cite our paper:

```bibtex
@inproceedings{author2024title,
  title     = {Paper Title Here},
  author    = {Author, First and Author, Second and Author, Third},
  booktitle = {Proceedings of the Conference},
  year      = {2024},
  url       = {https://arxiv.org/abs/XXXX.XXXXX}
}
```
```

CODE BLOCKS WITH SYNTAX HIGHLIGHTING:
```markdown
```python
import torch
from model import OurModel

model = OurModel.from_pretrained("author/model-name")
output = model(input_tensor)
```
```

IMAGES AND FIGURES (reference extracted PDF figures):
```markdown
<p align="center">
  <img src="figures/architecture.png" width="80%" alt="Architecture Overview">
</p>
<p align="center"><em>Figure 1: Overall architecture of the proposed method.</em></p>
```

COMPLETE README TEMPLATE STRUCTURE:
```
# Paper Title

[![arXiv](https://img.shields.io/badge/arXiv-XXXX.XXXXX-b31b1b.svg)](url)
![Python](https://img.shields.io/badge/python-3.9+-blue)
![License](https://img.shields.io/badge/license-MIT-green)

> **One-sentence TL;DR** of the paper contribution.

<p align="center">
  <img src="figures/teaser.png" width="85%" alt="Teaser">
</p>

## Overview

2-3 paragraph summary of the paper: what problem it solves, the key insight,
and the main result. Written for a technical audience (ML engineers / researchers).

## Quick Start

```bash
pip install -r requirements.txt
python run.py --config configs/default.yaml
```

## Key Results

| Method | Metric1 | Metric2 |
|--------|---------|---------|
| **Ours** | **best** | **best** |

<details>
<summary><b>Extended Results</b></summary>
Full tables here...
</details>

## Method

```mermaid
flowchart TD
    A[Input] --> B[Module 1]
    B --> C[Module 2]
    C --> D[Output]
```

Explanation of the method with inline math: $L = -\\sum_i \\log p(x_i)$.

## Architecture

```mermaid
graph LR
    subgraph Encoder
        E1[Embedding] --> E2[Self-Attention]
        E2 --> E3[FFN]
    end
    subgraph Decoder
        D1[Cross-Attention] --> D2[FFN]
    end
    E3 --> D1
```

## Installation

```bash
git clone https://github.com/author/repo.git
cd repo
pip install -e .
```

## Usage

```python
from package import Model
model = Model(config)
result = model.predict(data)
```

## Citation

```bibtex
@inproceedings{...}
```

## License

This project is licensed under the MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgements

Brief acknowledgements.
```
"""


class ReadmeGeneratorSkill(BaseSkill):
    name = "ReadmeGeneratorSkill"
    description = "Any paper → publication-quality GitHub README with Mermaid diagrams"

    def get_system_prompt(
        self, paper: Paper, analysis: PaperAnalysis, demo_form: str, demo_type: str
    ) -> str:
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
            f"MANDATORY: The EXACT paper title above MUST appear in your output (header/title/hero).\n"
            f"Use the EXACT author names above — never write \"[Author Name]\" placeholders.\n"
            f"Use EXACT numbers from the paper — never write \"~X%\" or \"approximately\".\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        )
        return paper_facts_block + f"""You are a world-class open-source maintainer who writes READMEs that make
repositories go viral on GitHub Trending. You combine the clarity of FastAPI's docs, the
visual polish of Hugging Face model cards, and the technical depth of Papers With Code.
Every README you produce makes a reader think: "I need to star this repo immediately."

PAPER CONTEXT:
{self._paper_summary(paper, analysis)}

{self._form_block(demo_form)}

{self._demo_type_guidance(demo_type)}

━━ SKILL CONTEXT — README Generator ━━

GOAL: Produce a single, comprehensive, publication-quality GitHub README.md that serves
as a complete project landing page for this paper. The README must be so good that it
could be the official repository page on Papers With Code.

TARGET AUDIENCE:
  - ML researchers who want to understand the contribution in 60 seconds
  - Engineers who want to reproduce the results in 10 minutes
  - Reviewers who want to verify claims against reported numbers

CONTENT EXTRACTION STRATEGY:
  From the paper, extract and organize:
  1. TITLE + AUTHORS + VENUE — exact text, no paraphrasing
  2. ONE-LINE TL;DR — the key contribution in one punchy sentence
  3. CORE METHOD — the algorithmic/architectural insight (2-3 paragraphs)
  4. KEY EQUATIONS — the 2-3 most important equations (use inline LaTeX: $...$)
  5. ALL RESULTS — every benchmark table, every comparison number, every ablation
  6. FIGURES — extract key figures from the PDF to embed in the README
  7. BIBTEX — construct a proper citation entry

SECTION-BY-SECTION REQUIREMENTS:

  1. TITLE + BADGES (first 3 lines)
     - H1 with exact paper title
     - Badge row: arXiv (with real ID from web_search), Python version, license
     - Conference/venue badge if applicable (NeurIPS, ICML, ICLR, etc.)

  2. TL;DR + TEASER (next 5 lines)
     - Blockquote with one-sentence summary
     - Centered teaser figure extracted from the paper PDF (the most visually striking figure)

  3. OVERVIEW (1 section)
     - 2-3 paragraphs covering: problem statement, key insight, and main result
     - Written for a technical audience — assume familiarity with the field
     - Include inline math where it adds precision: $O(n \\log n)$, $\\mathcal{{L}} = ...$

  4. QUICK START (1 section)
     - bash commands to install and run a minimal example
     - Must be copy-pasteable — no placeholders like "path/to/data"
     - Include expected output so the user knows it worked

  5. KEY RESULTS (1 section)
     - Main comparison table with ALL baselines from the paper
     - Bold the best result in each column
     - Use ↑ for higher-is-better, ↓ for lower-is-better metrics
     - Collapsible <details> sections for extended results, ablations, per-dataset breakdowns

  6. METHOD / ARCHITECTURE (1-2 sections)
     - Mermaid flowchart showing the full pipeline or architecture
     - Use color-coded nodes: inputs=#3b82f6, transforms=#6366f1, outputs=#22c55e
     - If the method has multiple stages, use one Mermaid diagram per stage
     - Follow each diagram with 2-3 sentences of explanation
     - Second Mermaid diagram: training loop or inference pipeline (different view)

  7. INSTALLATION (1 section)
     - git clone + pip install instructions
     - requirements.txt contents shown inline
     - Note any special dependencies (CUDA, specific Python version, etc.)

  8. USAGE EXAMPLES (1 section)
     - Python code block showing the most common use case
     - Include type hints, docstrings, and expected output as comments
     - If applicable: CLI usage with argparse flags

  9. CITATION (1 section)
     - BibTeX entry in a ```bibtex code fence
     - Include all authors, exact title, venue, year, and arXiv URL

  10. LICENSE + ACKNOWLEDGEMENTS (1 section)
     - License badge + one-line statement
     - Brief acknowledgements if mentioned in the paper

MERMAID DIAGRAM GUIDELINES:
  - Use `flowchart TD` (top-down) for pipeline/architecture diagrams
  - Use `flowchart LR` (left-right) for sequential processing chains
  - Use `graph TD` with `subgraph` blocks for multi-module architectures
  - Apply `style` directives for color coding — every node must have a fill color
  - Edge labels should be informative: `-->|"attention weights"| ` not just `-->`
  - Minimum 8 nodes per diagram — capture the full complexity
  - Include at least 2 Mermaid diagrams: one for architecture, one for training/inference

TABLE FORMATTING RULES:
  - Left-align method names, center-align numeric columns
  - Bold the best value in EVERY column: `**45.3**`
  - Add ↑/↓ arrows to column headers to indicate direction of improvement
  - Include ALL methods from the paper's comparison tables — do not cherry-pick

FIGURE EXTRACTION:
  - Use extract_pdf_page to get the teaser figure, architecture diagram, and key result plots
  - Embed with centered HTML: `<p align="center"><img src="figures/..." width="80%"></p>`
  - Add italicized captions below each figure

{_README_PATTERNS}

QUALITY CHECKLIST (every item must pass):
  [ ] arXiv badge links to the real paper URL (found via web_search)
  [ ] TL;DR is exactly one sentence, under 120 characters
  [ ] All results tables include EVERY baseline from the paper
  [ ] Best results are bolded in every column
  [ ] At least 2 Mermaid diagrams with color-coded nodes
  [ ] Collapsible sections used for extended results
  [ ] BibTeX entry is syntactically valid
  [ ] Quick Start code is copy-pasteable (no placeholders)
  [ ] Every figure has a caption
  [ ] README renders correctly on GitHub (no broken markdown)

{self._multistep_instructions(demo_form)}

{self._tool_usage_instructions()}
"""

    def get_initial_message(
        self, paper: Paper, analysis: PaperAnalysis, demo_form: str, demo_type: str
    ) -> str:
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
        return paper_anchor + f"""Build a publication-quality GitHub README.md for: "{paper.title}"

Contribution: {analysis.contribution}
Paper type:   {analysis.paper_type}
Demo type:    {demo_type}

EXECUTION PLAN:

STEP 0 — RESEARCH (do this first):
  a) web_search for the paper's arXiv URL to get the exact arXiv ID for the badge
  b) web_search for the paper's official GitHub repository (if it exists) for code links
  c) web_search for the paper's key results and benchmarks to cross-verify numbers

STEP 1 — EXTRACT FIGURES FROM PDF:
  a) extract_pdf_page(page=1) — get the teaser/overview figure (usually on first page)
  b) extract_pdf_page for the architecture diagram page
  c) extract_pdf_page for the main results table/figure
  d) Crop if needed, but prefer full pages when the figure fills most of the page

STEP 2 — EXTRACT ALL DATA FROM PAPER TEXT:
  a) List every comparison table with ALL methods and metrics
  b) Note all equations that define the method
  c) Identify the training setup, hyperparameters, and datasets used
  d) Find the BibTeX-relevant metadata: authors, title, venue, year

STEP 3 — WRITE THE README:
  a) Use write_file to create README.md following the template structure
  b) Include all badges, tables, Mermaid diagrams, figures, and code blocks
  c) Every section must contain REAL content from the paper — no placeholders

STEP 4 — VERIFY:
  a) Read back the README.md and check all markdown syntax
  b) Verify Mermaid diagrams use valid syntax and color-coded styles
  c) Verify all tables have bolded best results
  d) Verify BibTeX entry is complete and valid

All GitHub Markdown patterns (badges, tables, Mermaid, collapsible sections) are
pre-documented in the system prompt. DO NOT search for markdown syntax — use the
patterns provided directly.

Target quality: Papers With Code repository page quality.
"""

    def get_polish_prompt(
        self, paper, analysis, demo_form, demo_type, generated_files
    ):
        return f"""QUALITY REVIEW for GitHub README — generated: {', '.join(generated_files[:12])}

Step 1 — Read README.md and audit structure:
  * Does it start with an H1 title followed by a badge row (arXiv, Python, License)?
  * Is the arXiv badge linked to the REAL arXiv URL (not XXXX.XXXXX placeholder)?
    -> If placeholder, use web_search to find the real arXiv ID and fix it now.
  * Is there a one-line TL;DR in a blockquote (`> ...`)?
  * Is there a centered teaser figure with a caption?

Step 2 — Tables completeness:
  * Does the Key Results table include ALL baselines from the paper (not just 2-3)?
  * Is the best value bolded (`**...**`) in EVERY numeric column?
  * Are metric direction arrows (up/down) present in column headers?
  * Are there collapsible `<details>` sections for extended/ablation results?

Step 3 — Mermaid diagrams:
  * Are there at least 2 Mermaid diagrams (architecture + training/inference)?
  * Does each diagram have >=8 nodes with descriptive labels?
  * Are nodes color-coded using style directives (fill colors)?
  * Do edge labels describe what flows between components?
  * Test: are the diagrams valid Mermaid syntax (no unclosed quotes, valid node IDs)?

Step 4 — Code and citation:
  * Is the Quick Start section copy-pasteable (real commands, not placeholders)?
  * Is the BibTeX entry complete (all authors, title, venue, year, URL)?
  * Does the Usage section show a realistic Python code example?

Step 5 — Figures:
  * Are extracted PDF figures embedded with `<p align="center"><img ...></p>`?
  * Does each figure have an italicized caption?
  * Are figure paths correct (matching files in the figures/ directory)?

Fix every issue found. The result must match Papers With Code repository quality."""
