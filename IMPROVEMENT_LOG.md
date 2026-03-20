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

### TODO for next sessions
- [ ] Review demo test output in /tmp/pda-test-demo/
- [ ] Test with different paper types (ViT, GPT-3, GPT-4)
- [ ] Check if graphics templates are actually being used in generated output
- [ ] Add more architecture templates (CNN, RNN, GAN)
- [ ] Validate HTML output quality across forms
- [ ] Consider adding screenshot feedback tool
