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
- [ ] Refresh Claude Code OAuth token, test ViT paper (2010.11929) end-to-end
- [ ] Verify the new graphics toolkit is actually used in generated output (check generated HTML for render_svg calls vs raw SVG)
- [ ] Add screenshot feedback tool (playwright screenshot → validate_output vision check)
- [ ] Consider adding `mermaid_gantt(tasks)` for timeline/schedule diagrams
- [ ] Consider `treemap_d3(hierarchy_data)` for model/dataset breakdown charts
- [ ] Profile token usage: are the longer system prompts causing cost increases?
