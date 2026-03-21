# PaperDemoAgent Improvement Log

## Session 1 — 2026-03-20 15:00-19:50 (Brisbane)

### Auth System
- Added Claude Code OAuth detection (macOS Keychain + ~/.claude/)
- Bearer auth with Claude Code identity headers (anthropic-beta, user-agent, x-app)
- System prompt as array blocks (required for OAuth)
- Added Gemini CLI detection (Keychain + OpenClaw auth-profiles, token refresh)
- Priority: Claude Code → saved config → env → Codex → Aider
- Removed OpenClaw fallback per Dylan's request

### UI Improvements
- Prominent auth cards for Claude Code + Gemini CLI on Settings page
- Provider dropdown shows ✓/✗ credential status
- Status hints update on provider change

### Graphics Module (paper_demo_agent/graphics/)
- svg_primitives.py: rounded_box, arrow, flow_arrow, layer_stack, parallel_blocks, etc.
- architecture_templates.py: encoder_decoder, transformer_block, pipeline_flow, comparison_diagram, attention_visualization
- chart_templates.py: Chart.js bar/radar, D3 grouped bars, result cards, comparison tables
- tikz_templates.py: flow diagrams, block diagrams, tables
- mermaid_patterns.py: tested Mermaid v11 patterns
- GRAPHICS_REFERENCE constant for skill prompt injection
- render_svg tool for programmatic composition

### Prompt Caching
- cache_control ephemeral on system blocks + last tool def
- Verified: 3291 tokens cached, read from cache on subsequent calls

### Pipeline Optimizations
- HTML/JS validation tool (validate_output)
- Context compaction (every 4 iters, truncate old tool results)
- Skeleton-first strategy for large-file forms
- Parallel tool execution (ThreadPoolExecutor for side-effect-free tools)
- Form-specific iteration budgets (README: 6, presentation: 15, etc.)

### Skill Improvements (via Claude Code)
- Research phase instructions with specific search queries per skill
- Form adaptation guidance for all skills
- Pre-baked knowledge blocks
- Error recovery patterns

### Tests
- 119/119 passing (79 original + 40 graphics)
- All changes committed

### TODO from Session 1
- [x] Review demo test output in /tmp/pda-test-demo/ — 50KB reveal.js deck for "Attention Is All You Need", CDN correct, Chart.js loaded, inline SVGs present but handwritten (before toolkit injection)
- [x] Check if graphics templates are actually being used — they weren't before; fixed by injecting toolkit into _tool_usage_instructions()
- [x] Add more architecture templates (CNN, RNN, GAN) — done in Session 2
- [ ] Test with ViT paper (2010.11929) — blocked by expired Claude Code OAuth token
- [ ] Validate HTML output quality across forms
- [ ] Consider adding screenshot feedback tool

---

## Session 2 — 2026-03-21 04:00 (Brisbane)

### Graphics Module Expansion

**Architecture Templates (architecture_templates.py):**
- `cnn_architecture(layers_config)` — CNN with featuremap-style stacked boxes for conv/pool layers
- `rnn_cell(cell_type='lstm')` — LSTM/GRU cell with gate annotations (forget/input/cell/output for LSTM, update/reset/new for GRU)
- `residual_block(num_layers=2)` — Skip connection block (BasicBlock=2 layers, Bottleneck=3 layers) with dashed skip path
- `multi_head_attention_detail(num_heads, d_k, d_v)` — Detailed MHA with Q/K/V inputs, per-head boxes, Concat+Linear
- `gan_architecture(gen_layers, disc_layers)` — Generator vs Discriminator side-by-side with fake image routing arrow

**Chart Templates (chart_templates.py):**
- `line_chart_js(data_series, labels, title, y_label)` — Chart.js multi-line for training curves / metrics over epochs
- `heatmap_d3(matrix, row_labels, col_labels, title, color_scheme)` — D3.js heatmap with auto-normalisation (attention, confusion, similarity)
- `metric_dashboard_html(metrics_dict)` — Responsive grid of metric cards with delta badges (positive/negative colour-coded)

**Mermaid Patterns (mermaid_patterns.py):**
- `mermaid_training_loop(steps=None)` — Standard data→forward→loss→backward→update pipeline with automatic loop-back when last step ends with "?"
- `mermaid_comparison(method_a_steps, method_b_steps, labels)` — Parallel subgraphs comparing baseline vs proposed (muted vs accent colour)

### Skill Prompt Improvements
- Added comprehensive **GRAPHICS TOOLKIT** section to `BaseSkill._tool_usage_instructions()`
- All 13+ skills now inherit the toolkit reference automatically — no per-skill edits needed
- Section lists all functions by category (architecture/chart/mermaid/tikz) with usage examples
- Strong directive: "Do NOT write raw SVG path data from scratch — use the toolkit"

### Tests
- 146/146 passing (was 128) — added 18 new test cases across architecture, chart, and mermaid modules
- All new functions tested for: SVG validity, key label presence, color checks, empty inputs

### Issues Found
- `page_blog` is not a valid form type (correct is `--form page --subtype blog`) — note for future test scripts
- Claude Code OAuth token is expired — ViT demo could not be fully tested end-to-end
  - **Action needed**: `claude login` to refresh token

### TODO for next sessions
- [x] Refresh Claude Code OAuth token auto-refresh — done in Session 3
- [ ] Test ViT paper (2010.11929) end-to-end with refreshed token
- [ ] Verify the new graphics toolkit is actually used in generated output (check generated HTML for render_svg calls vs raw SVG)
- [ ] Add screenshot feedback tool (playwright screenshot → validate_output vision check)
- [ ] Consider adding `mermaid_gantt(tasks)` for timeline/schedule diagrams
- [ ] Consider `treemap_d3(hierarchy_data)` for model/dataset breakdown charts
- [ ] Profile token usage: are the longer system prompts causing cost increases?

---

## Session 3 — 2026-03-21 07:20 (Brisbane)

### Priority 1: Hard-enforce write_file size limit ✅
- `tool_write_file()` now counts lines and rejects writes >300 lines with a clear error:
  `"ERROR: File too large (N lines). Maximum 300 lines per write. Split into separate files (CSS, JS, HTML)."`
- Added `_WRITE_FILE_MAX_LINES = 300` constant (easy to adjust later)
- Updated TOOLS list description to surface the hard limit to the model
- 7 new tests in `tests/test_tools.py` covering: exact limit accepted, 1-over rejected, far-over reports correct count, dispatch enforcement

### Priority 2: Math rendering section in _tool_usage_instructions() ✅
- Added `━━ MATH RENDERING (KaTeX) ━━` section to `BaseSkill._tool_usage_instructions()`
- Covers: CDN links, `renderMathInElement` call with delimiters, inline/display syntax examples
- Strong directive that it's CRITICAL for papers with equations
- Note about reveal.js using RevealMath.KaTeX plugin instead

### Priority 3: Section structure templates ✅
- Created `paper_demo_agent/skills/templates.py` with:
  - `PRESENTATION_STRUCTURE` — 12 slides: Title → ... → Conclusion
  - `WEBSITE_STRUCTURE` — 7 sections: Hero → ... → Citation
  - `BLOG_STRUCTURE` — 8 sections: Hook → ... → References
- Injected into all skills via `BaseSkill._tool_usage_instructions()` (one place, all skills inherit)
- Added `━━ SECTION STRUCTURES ━━` section showing numbered lists per form type
- 4 tests in `tests/test_tools.py` for structure correctness

### Priority 4: Figure extraction + page listing tools ✅
- `tool_extract_figure(output_dir, pdf_path, page, x1, y1, x2, y2, dpi=200, filename=None)`
  - Separate tool from `extract_pdf_page`: takes explicit pdf_path + flat x1/y1/x2/y2 params
  - Default 200 DPI (vs 150 for full pages) for crisper figure crops
  - Auto-generates filename as `figures/figure_p{page}_{x1}_{y1}_{x2}_{y2}.png`
- `tool_list_pdf_pages(output_dir, pdf_path='paper.pdf')`
  - Returns total page count + 150-char text snippet per page
  - Lets model quickly scan for specific figures/tables without guessing page numbers
- Both registered in TOOLS list + dispatch_tool + 6 tests

### Priority 5: Table extraction tool ✅
- `tool_extract_tables(output_dir, pdf_path, page)` using PyMuPDF block extraction
  - Clusters text blocks by y-position proximity (±5px = same row)
  - Filters to rows with 2+ columns
  - Groups contiguous rows into table segments (>30px gap = new table)
  - Returns JSON: `[{"headers": [...], "rows": [[...], ...]}, ...]`
- Model can render as HTML table or Chart.js bar chart
- Registered in TOOLS list + dispatch_tool + 3 tests

### Priority 6: Auto-refresh Claude Code OAuth token ✅
- `_detect_claude_code_keychain()` promoted from `@staticmethod` to instance method
- Now reads `expiresAt` and `refreshToken` from `claudeAiOauth` keychain data
- If expired (5-min buffer): POSTs to `https://claude.ai/oauth/token` with `grant_type=refresh_token`
- On success: updates in-memory credentials + writes back to Keychain via `security add-generic-password -U`
- On 403 (both tokens expired): logs warning "Run `claude login` to re-authenticate", returns None
- On other errors: logs warning, falls back to returning existing (possibly expired) token
- `_CC_CLIENT_ID` and `_CC_TOKEN_URL` stored as class constants

### Tests
- **173/173 passing** (was 146, +27 new in tests/test_tools.py)
- All priorities fully covered

### TODO for next sessions
- [ ] Test ViT paper end-to-end to verify new tools are exercised correctly
- [ ] Add screenshot feedback tool (playwright screenshot → validate_output vision check)
- [ ] Consider `mermaid_gantt(tasks)` for timelines
- [ ] Consider `treemap_d3(hierarchy_data)` for model/dataset breakdown
- [ ] Profile: do longer system prompts (math + structure sections) meaningfully increase cost?

---

## Session 4 — 2026-03-21 08:13 (Brisbane) — v2 Post-file-splitting Test

### Test 1: Transformer 1706.03762 --form presentation
- **Status: PARTIAL** — Build timed out at iteration 6/15 (cron job 5-min limit)
- demo.html: ✅ generated (22KB, 324 lines)
- reveal.js: ✅ referenced (3 occurrences)
- Inline SVGs: ✅ 2 found
- `<section>` tags: 6 (6 slides written before timeout)
- Figures extracted: ✅ 5 (fig1-5.png from heuristic fallback — Docling unavailable) + 2 table page screenshots
- Figure extraction: Docling unavailable (`No module named 'docling_core'`), fell back to heuristic method
- Root issue: build budget is 15 iterations but cron job allows ~5 min — build was cut mid-way
- **Fix needed**: Either reduce build iteration budget for faster models, or raise cron timeout

### Test 2: BERT 1810.04805 --form website
- **`--form website` is INVALID** — valid forms: `app`, `presentation`, `page`, `diagram`
  - CLI rejects with: "Error: Invalid value for '--form' / '-f': 'website' is not 'app', 'presentation', 'page', 'diagram'"
  - Ran with `--form page` as nearest equivalent
- **Status: FAILED** — crash at build iter 6/12 with API error
- index.html: ❌ NOT generated
- styles.css: ✅ generated (14KB, 231 lines) — CSS bar chart styles present
- script.js: ✅ generated (12KB, 297 lines) — dark mode, scroll reveal, tab switching
- Chart.js: ❌ not used — CSS bar charts in styles.css instead
- KaTeX: ❌ not used
- **Crash cause**: Anthropic API 400 error: "tool_use ids found without tool_result blocks"
  - Tool call at iter 6 wrote styles.css, then model tried to write index.html but first attempted a redundant search (hitting consecutive search limit), which forced a write — but the tool call ID was not matched with a result before the next iteration, causing API malformed conversation error
  - This is an agentic loop bug: when `↻ Search limit hit — forcing write` triggers mid-iteration, the tool_use/tool_result pairing can get out of sync
- **Fix needed**: Ensure forced-write nudge doesn't orphan pending tool_use IDs; validate message history before each API call

### Bugs to fix
1. **Orphaned tool_use IDs on forced-write**: The "search limit → force write" nudge can create unpaired tool_use/tool_result pairs → API 400 crash
2. **Build timeout**: 15 build iterations × ~30s each ≈ 7.5 min, exceeds 5-min cron limit; consider reducing default budget or adding early exit when main file is done
3. **`--form website` not a valid CLI option**: Either add it as alias for `page`, or update docs/tests that reference it

---

## Session 5 — 2026-03-21 (Brisbane) — v0.4.0: flowchart_pro + vector figures

### New form: `flowchart_pro` (Cytoscape.js draw.io-quality diagrams)
- Added `flowchart_pro` as a 7th demo form alongside the existing 6
- Technology: Cytoscape.js 3.30.2 + dagre layout (same engine draw.io uses for hierarchical layout)
- `FlowchartGeneratorSkill` extended with `_CYTOSCAPE_PATTERNS` (~150 lines of reference patterns):
  - CDN load order: dagre → cytoscape → cytoscape-dagre
  - Tab isolation: each tab has its own `<div id="cy-{tabId}">` container initialized lazily on first show
  - Node/edge JSON declaration, dark-theme stylesheet, compound parent nodes
  - Click handler, zoom/fit, search, walkthrough, SVG/PNG export
  - `get_polish_prompt()` has separate Mermaid vs Cytoscape review checklists
- Full routing wired across all 5 relevant files:
  - `paper/models.py`: `("diagram", "cytoscape") → "flowchart_pro"` in COMPOSITE_KEY
  - `skills/router.py`: FlowchartGeneratorSkill locked to `{flowchart, flowchart_pro}`
  - `generation/generator.py`: detect_main_file candidates, form compliance check (validates `cytoscape` in HTML), FORM_BUDGETS (build=12, polish=3)
  - `cli.py`: `flowchart_pro` added to click.Choice
  - `ui/app.py`: `"Interactive (Cytoscape)"` in DIAGRAM_OPTIONS + DIAGRAM_META + _resolve_form_type + open-browser message

### Vector figure extraction
- `tools.py`: `extract_pdf_page` now defaults to `format="svg"` using PyMuPDF `page.get_svg_image()`
- SVG crop implemented via `viewBox` injection
- PNG DPI raised from 150 → 300 for fallback raster mode

### Tests
- **236/236 passing** — all existing tests pass with new changes

### Version bump
- `0.3.3` → `0.4.0` in `pyproject.toml` and `paper_demo_agent/__init__.py`
