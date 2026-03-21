"""Skill for any paper -> interactive Distill.pub-style blog article."""

from paper_demo_agent.paper.models import Paper, PaperAnalysis
from paper_demo_agent.skills.base import BaseSkill, FORM_SPECS


# ─────────────────────────────────────────────────────────────────────────────
# Pre-baked tool knowledge — never search for these basics
# ─────────────────────────────────────────────────────────────────────────────

_DISTILL_PATTERNS = """
━━ DISTILL.PUB V2 REFERENCE (use verbatim, do NOT search) ━━

SKELETON: <!doctype html><meta charset="utf-8">
  <script src="https://distill.pub/template.v2.js"></script>
  <d-front-matter><script id="distill-front-matter" type="text/json">{
    "title":"...","description":"...","published":"YYYY-MM-DD",
    "authors":[{"author":"Name","authorURL":"url",
      "affiliations":[{"name":"Univ","url":"url"}]}],
    "katex":{"delimiters":[{"left":"$$","right":"$$","display":false},
      {"left":"\\\\[","right":"\\\\]","display":true}]}
  }</script></d-front-matter>
  <d-title><h1>Title</h1><p>Subtitle.</p></d-title><d-byline></d-byline>
  <d-article>...</d-article>
  <d-appendix><d-bibliography><script type="text/bibliography">
    @article{key,title={...},author={...},journal={...},year={...}}
  </script></d-bibliography></d-appendix>

COMPONENTS: <d-cite key="k"> | <d-math>inline</d-math> | <d-math block>display</d-math>
  <d-figure id="x"><figure><div id="viz"></div><figcaption>...</figcaption></figure></d-figure>
  <d-aside><p>Margin note.</p></d-aside> | <d-footnote>Detail.</d-footnote>
  <d-code block language="python">code</d-code>

D3 CHART: Load <script src="https://d3js.org/d3.v7.min.js"></script>, use IIFE,
  d3.select('#id').append('svg').attr('viewBox',...), scaleBand/scaleLinear,
  .selectAll('rect').data(data).join('rect') with hover tooltips.
  Proposed=#6366f1, baselines=#64748b. Always use viewBox.

STYLES: .results-table (border-collapse, th bg:#f0f0f5, tr.highlight bg:#eef2ff)
  .concept-box (border-left:4px solid #6366f1, bg:#f8f9ff)
  .key-insight (bg:linear-gradient(135deg,#eef2ff,#e0e7ff), padding:24px)
"""


class BlogExplainerSkill(BaseSkill):
    name = "BlogExplainerSkill"
    description = "Any paper -> interactive Distill.pub-style blog article"

    def get_system_prompt(self, paper: Paper, analysis: PaperAnalysis, demo_form: str, demo_type: str) -> str:
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

        return paper_facts_block + f"""You are a world-class science communicator combining Distill.pub clarity,
Quanta Magazine narrative, and Nature Methods depth. You turn dense papers into
engaging interactive blog articles that researchers bookmark and share.

PAPER CONTEXT:
{self._paper_summary(paper, analysis)}

{self._form_block(demo_form)}

{self._demo_type_guidance(demo_type)}

━━ SKILL CONTEXT — Distill.pub Blog Article ━━

ARTICLE SECTIONS (in order):
  1. HOOK — vivid scenario or surprising stat, end with key claim teaser
  2. PROBLEM — challenge + prior shortcomings, d-aside for jargon, d-figure
  3. BACKGROUND — prerequisite primer, concept-box divs, d-math, d-cite
  4. APPROACH (core) — intuition first (no math), then d-math equations;
     3-5 steps: plain English + formal math + d-aside notes; d-figure, d-code
  5. RESULTS — MANDATORY D3.js chart (proposed=#6366f1, baselines=#64748b)
     with EXACT paper numbers + tooltips; .results-table with .highlight row
  6. IMPLICATIONS — new directions, limitations, future work
  7. CONCLUSION — 3 takeaways, connect back to hook

MINIMUMS: >=5 d-aside, >=3 d-footnote, >=1 D3 chart, all math via d-math,
  figures in d-figure, refs via d-cite + matching d-bibliography entries.

WRITING: active voice, short paragraphs, define terms on first use,
  concrete before abstract, specific numbers ("3.2 pp" not "significantly").

{_DISTILL_PATTERNS}

{self._multistep_instructions(demo_form)}

{self._tool_usage_instructions()}
"""

    def get_initial_message(self, paper: Paper, analysis: PaperAnalysis, demo_form: str, demo_type: str) -> str:
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

        return paper_anchor + f"""Build a Distill.pub-style interactive blog article for: "{paper.title}"

Contribution: {analysis.contribution}
Demo type: {demo_type}
Paper type: {analysis.paper_type}
Core concepts: {analysis.interaction_pattern}

PRIORITY ORDER:
1. web_search for arXiv URL, author names/affiliations, venue, year, numeric results
2. Plan: Hook -> Problem -> Background -> Approach -> Results -> Implications
3. Write index.html with Distill template v2, d-front-matter with real metadata
4. Build >=1 interactive D3.js chart with EXACT paper numbers
5. Use d-cite, d-aside, d-footnote, d-math throughout
6. Styled results table with proposed method highlighted
7. Inline bibliography with BibTeX for all cited works

RULES: real numbers only, define all terms, tell a STORY not a summary,
>=5 d-aside, >=3 d-footnote, >=1 D3 chart, all math via d-math.

Target: indistinguishable from a real distill.pub published article.
"""

    def get_polish_prompt(self, paper, analysis, demo_form, demo_type, generated_files):
        spec = FORM_SPECS.get(demo_form, {})
        main_file = spec.get("main_file", "index.html")
        quality_bar = spec.get("quality_bar", "distill.pub published articles")

        return f"""QUALITY REVIEW for Distill.pub blog article — generated: {', '.join(generated_files[:12])}

Step 1 — Read {main_file} and audit Distill compliance:
  * template.v2.js in head? d-front-matter with authors/affiliations/date?
  * d-cite keys match d-bibliography entries? >=5 d-aside, >=3 d-footnote?
  * All math via d-math / d-math block? Figures in d-figure with figcaption?

Step 2 — D3.js visualization:
  * D3 v7 from d3js.org CDN? >=1 interactive chart with REAL paper numbers?
  * Proposed=#6366f1, baselines=#64748b? Hover tooltips? viewBox for responsive SVG?

Step 3 — Content:
  * Compelling hook (not "In this paper...")? Accurate numeric results?
  * Narrative arc: Hook -> Problem -> Approach -> Results -> Implications?
  * Terms defined on first use? Results table with .highlight row?

Step 4 — No placeholders, no broken d-cite keys, mobile-responsive, CDN links valid.

Fix everything. Target quality: {quality_bar}"""
