# VHS tape file — generates docs/assets/demo.gif
# Install: brew install charmbracelet/tap/vhs (or go install github.com/charmbracelet/vhs@latest)
# Usage:  vhs scripts/demo.tape

Output docs/assets/demo.gif

Set FontFamily "JetBrains Mono"
Set FontSize 16
Set Width 900
Set Height 500
Set Theme { "name": "PaperDemoAgent", "black": "#09090b", "red": "#ef4444", "green": "#22c55e", "yellow": "#f59e0b", "blue": "#3b82f6", "magenta": "#6366f1", "cyan": "#06b6d4", "white": "#fafafa", "brightBlack": "#52525b", "brightRed": "#f87171", "brightGreen": "#4ade80", "brightYellow": "#fbbf24", "brightBlue": "#60a5fa", "brightMagenta": "#818cf8", "brightCyan": "#22d3ee", "brightWhite": "#ffffff", "background": "#09090b", "foreground": "#fafafa", "selection": "#27272a", "cursor": "#6366f1" }
Set Padding 20

# Intro
Type "# Turn any paper into a live demo"
Enter
Sleep 1s

# Install
Type "pip install paper-demo-agent"
Enter
Sleep 2s

# Generate a demo
Type "paper-demo-agent demo 1706.03762 --form presentation"
Enter
Sleep 1s

# Simulated output
Type@50ms "╭─ 🔬 Paper Demo Agent ─╮"
Enter
Type@50ms "│ Source: 1706.03762    │"
Enter
Type@50ms "│ Provider: anthropic   │"
Enter
Type@50ms "│ Form: presentation    │"
Enter
Type@50ms "╰───────────────────────╯"
Enter
Sleep 500ms
Type@30ms "Fetching paper: 1706.03762"
Enter
Sleep 1s
Type@30ms "Paper fetched: \"Attention Is All You Need\""
Enter
Sleep 500ms
Type@30ms "Analyzing paper..."
Enter
Sleep 1s
Type@30ms "Paper type: theory | Demo: presentation / theoretical"
Enter
Sleep 500ms
Type@30ms "▸ Research phase (3 iterations)... done"
Enter
Sleep 500ms
Type@30ms "▸ Build phase (12 iterations)..."
Enter
Sleep 2s
Type@30ms "  wrote demo.html (17 slides, 3 SVG diagrams)"
Enter
Sleep 500ms
Type@30ms "▸ Polish phase... done"
Enter
Sleep 500ms
Type@30ms "▸ Validate phase... ✓ valid presentation"
Enter
Sleep 1s
Type@30ms ""
Enter
Type@30ms "✅ Demo generated: demos/attention_is_all_you_need/"
Enter
Type@30ms "   Main file: demo.html"
Enter
Type@30ms "   Opening in browser..."
Enter
Sleep 3s
