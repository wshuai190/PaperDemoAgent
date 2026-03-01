#!/usr/bin/env python3
"""
Generate an animated SVG terminal recording for the README hero image.

This creates a lightweight SVG animation that simulates a terminal session
showing the paper-demo-agent CLI in action. No external tools needed.

Usage:
    python scripts/record_demo.py

Output:
    docs/assets/demo.svg
"""

from pathlib import Path
import html

ASSETS = Path(__file__).resolve().parent.parent / "docs" / "assets"

LINES = [
    (0.0,  "$ ", "#6366f1", False),
    (0.2,  "pip install paper-demo-agent", "#fafafa", True),
    (1.5,  "Successfully installed paper-demo-agent-0.3.0", "#22c55e", False),
    (2.5,  "", None, False),
    (2.7,  "$ ", "#6366f1", False),
    (2.9,  "paper-demo-agent demo 1706.03762 --form presentation", "#fafafa", True),
    (4.5,  "╭─ 🔬 Paper Demo Agent ─────────────────────────╮", "#6366f1", False),
    (4.7,  "│ Source: 1706.03762  Provider: anthropic       │", "#a1a1aa", False),
    (4.9,  "│ Form: presentation  Model: claude-sonnet-4-6  │", "#a1a1aa", False),
    (5.1,  "╰──────────────────────────────────────────────╯", "#6366f1", False),
    (5.5,  "Fetching paper: 1706.03762", "#a1a1aa", False),
    (6.5,  'Paper: "Attention Is All You Need"', "#fafafa", False),
    (7.0,  "Paper type: theory → presentation / theoretical", "#f59e0b", False),
    (7.5,  "", None, False),
    (8.0,  "▸ Research   ████████████████████ done (3 iters)", "#3b82f6", False),
    (9.0,  "▸ Build      ████████████████████ done (12 iters)", "#6366f1", False),
    (10.5, "  → wrote demo.html (17 slides, 3 SVG diagrams)", "#a1a1aa", False),
    (11.0, "▸ Polish     ████████████████████ done", "#8b5cf6", False),
    (11.5, "▸ Validate   ████████████████████ ✓ valid", "#22c55e", False),
    (12.0, "", None, False),
    (12.5, "✅ Demo generated!", "#22c55e", False),
    (12.7, "   Output: demos/attention_is_all_you_need/", "#fafafa", False),
    (12.9, "   Main:   demo.html", "#fafafa", False),
    (13.1, "   Run:    open demo.html", "#a1a1aa", False),
]

TOTAL_DURATION = 16.0
W, H = 720, 520
LINE_H = 18
PAD = 20
FONT_SIZE = 13


def build_svg() -> str:
    parts = []
    parts.append(f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">
  <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500&amp;display=swap');
    .term {{ font-family: 'JetBrains Mono', monospace; font-size: {FONT_SIZE}px; }}
    .cursor {{ animation: blink 1s step-end infinite; }}
    @keyframes blink {{ 50% {{ opacity: 0; }} }}
  </style>
  <!-- Background -->
  <rect width="{W}" height="{H}" rx="12" fill="#09090b"/>
  <!-- Title bar -->
  <rect width="{W}" height="36" rx="12" fill="#111113"/>
  <rect y="24" width="{W}" height="12" fill="#111113"/>
  <circle cx="18" cy="18" r="6" fill="#ef4444" opacity="0.8"/>
  <circle cx="38" cy="18" r="6" fill="#f59e0b" opacity="0.8"/>
  <circle cx="58" cy="18" r="6" fill="#22c55e" opacity="0.8"/>
  <text x="{W//2}" y="22" text-anchor="middle" class="term" fill="#71717a" font-size="12">paper-demo-agent</text>
  <line x1="0" y1="36" x2="{W}" y2="36" stroke="#27272a"/>
''')

    y_start = 36 + PAD
    for i, (t, text, color, is_typed) in enumerate(LINES):
        if not text:
            continue
        y = y_start + i * LINE_H
        escaped = html.escape(text)
        # Fade-in animation
        dur = "0.3s"
        parts.append(f'  <text x="{PAD}" y="{y}" class="term" fill="{color}" opacity="0">')
        parts.append(f'    {escaped}')
        parts.append(f'    <animate attributeName="opacity" from="0" to="1" dur="{dur}" begin="{t}s" fill="freeze"/>')
        parts.append(f'  </text>')

    # Blinking cursor at the end
    last_y = y_start + (len(LINES) + 1) * LINE_H
    last_t = LINES[-1][0] + 0.5
    parts.append(f'''  <rect x="{PAD}" y="{last_y - 12}" width="8" height="16" fill="#6366f1" class="cursor" opacity="0">
    <animate attributeName="opacity" from="0" to="1" dur="0.1s" begin="{last_t}s" fill="freeze"/>
  </rect>''')

    parts.append('</svg>')
    return '\n'.join(parts)


def main():
    ASSETS.mkdir(parents=True, exist_ok=True)
    svg = build_svg()
    out = ASSETS / "demo.svg"
    out.write_text(svg)
    print(f"Created {out} ({len(svg)} bytes)")

    # Also try VHS if available
    tape = Path(__file__).parent / "demo.tape"
    if tape.exists():
        import shutil
        if shutil.which("vhs"):
            import subprocess
            print("VHS found — generating GIF...")
            subprocess.run(["vhs", str(tape)], check=True)
            print(f"Created docs/assets/demo.gif")
        else:
            print("VHS not found — skipping GIF generation.")
            print("Install VHS: brew install charmbracelet/tap/vhs")
            print("Then run: vhs scripts/demo.tape")


if __name__ == "__main__":
    main()
