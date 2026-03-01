#!/usr/bin/env python3
"""
Capture multi-frame animated SVGs for the README gallery.

Each demo gets an SVG that cycles through interaction states:
  - Presentation: slides 1 → architecture → attention eq → results → takeaways
  - Website: scroll through hero → abstract → method → results
  - Flowchart: switch tabs Pipeline → Training → Concepts → Benchmarks
  - App: switch tabs Sentiment → MLM → Results → About

Output: docs/assets/output-{name}.svg (animated SVG with embedded PNG frames)
"""

from __future__ import annotations

import base64
import http.server
import io
import socket
import threading
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
DEMOS = ROOT / "demos"
ASSETS = ROOT / "docs" / "assets"

# Display size for gallery SVGs
SVG_W, SVG_H = 640, 400
VIEWPORT = {"width": 1440, "height": 900}
FRAME_DURATION = 2.5  # seconds per frame


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("", 0))
        return s.getsockname()[1]


def _serve_dir(directory: Path, port: int):
    handler = type(
        "H",
        (http.server.SimpleHTTPRequestHandler,),
        {"__init__": lambda self, *a, **kw: super(type(self), self).__init__(
            *a, directory=str(directory), **kw
        ),
         "log_message": lambda self, *a: None},  # silence logs
    )
    server = http.server.HTTPServer(("127.0.0.1", port), handler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    return server


def capture_frame(page, clip=None) -> bytes:
    """Capture current page state as PNG bytes, scaled down."""
    raw = page.screenshot(type="png", full_page=False)
    img = Image.open(io.BytesIO(raw))
    img = img.resize((SVG_W * 2, SVG_H * 2), Image.LANCZOS)  # 2x for retina
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


def frames_to_b64(frames: list[bytes]) -> list[str]:
    return [base64.b64encode(f).decode() for f in frames]


def build_animated_svg(frames_b64: list[str], label: str = "") -> str:
    """Build an SVG that cycles through PNG frames using CSS animation."""
    n = len(frames_b64)
    total_dur = n * FRAME_DURATION
    w, h = SVG_W, SVG_H

    # Build keyframes: each frame visible for 1/n of total duration
    # Frame i is visible from i/n to (i+1)/n
    pct_per = 100.0 / n
    # Slight overlap for smooth transition
    fade = 2.0  # percent for fade

    parts = []
    parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" '
                 f'xmlns:xlink="http://www.w3.org/1999/xlink" '
                 f'viewBox="0 0 {w} {h}" width="{w}" height="{h}">')

    # Styles
    parts.append('<style>')
    for i in range(n):
        start = i * pct_per
        visible_end = start + pct_per - fade
        fade_end = start + pct_per
        parts.append(f'  @keyframes f{i} {{')
        parts.append(f'    0% {{ opacity: {"1" if i == 0 else "0"}; }}')
        if i > 0:
            parts.append(f'    {start - fade:.1f}% {{ opacity: 0; }}')
            parts.append(f'    {start:.1f}% {{ opacity: 1; }}')
        parts.append(f'    {visible_end:.1f}% {{ opacity: 1; }}')
        parts.append(f'    {fade_end:.1f}% {{ opacity: 0; }}')
        if i == 0:
            # First frame reappears at the end
            parts.append(f'    {100 - fade:.1f}% {{ opacity: 0; }}')
            parts.append(f'    100% {{ opacity: 1; }}')
        else:
            parts.append(f'    100% {{ opacity: 0; }}')
        parts.append(f'  }}')
        parts.append(f'  .frame{i} {{ animation: f{i} {total_dur}s infinite; }}')
    parts.append('</style>')

    # Background
    parts.append(f'<rect width="{w}" height="{h}" rx="8" fill="#09090b"/>')

    # Frames (stacked, animated opacity)
    for i, b64 in enumerate(frames_b64):
        opacity = "1" if i == 0 else "0"
        parts.append(
            f'<image class="frame{i}" x="0" y="0" width="{w}" height="{h}" '
            f'opacity="{opacity}" '
            f'href="data:image/png;base64,{b64}" '
            f'preserveAspectRatio="xMidYMid slice"/>'
        )

    # Navigation dots
    dot_y = h - 14
    dot_start_x = (w - n * 16) / 2
    for i in range(n):
        cx = dot_start_x + i * 16 + 6
        # Dots also animate
        parts.append(
            f'<circle cx="{cx}" cy="{dot_y}" r="4" fill="#fafafa" '
            f'opacity="0.3" class="frame{i}">'
            f'<animate attributeName="opacity" values="'
        )
        vals = []
        for j in range(n):
            vals.append("0.9" if j == i else "0.3")
        vals_str = ";".join(vals + [vals[0]])
        parts.append(f'{vals_str}" dur="{total_dur}s" repeatCount="indefinite"/>')
        parts.append('</circle>')

    parts.append('</svg>')
    return '\n'.join(parts)


def capture_presentation(page, demo_dir: Path) -> list[bytes]:
    """Capture multiple slides from the reveal.js presentation."""
    port = _free_port()
    server = _serve_dir(demo_dir, port)
    frames = []
    try:
        page.goto(f"http://127.0.0.1:{port}/demo.html", wait_until="networkidle", timeout=30_000)
        page.wait_for_timeout(3000)

        # Slide 1: Title
        frames.append(capture_frame(page))

        # Slide 5: Architecture (click right 4 times)
        for _ in range(4):
            page.keyboard.press("ArrowRight")
            page.wait_for_timeout(600)
        frames.append(capture_frame(page))

        # Slide 6: Attention equation
        page.keyboard.press("ArrowRight")
        page.wait_for_timeout(800)
        frames.append(capture_frame(page))

        # Slide 11: Results
        for _ in range(5):
            page.keyboard.press("ArrowRight")
            page.wait_for_timeout(400)
        frames.append(capture_frame(page))

        # Slide 13: Why Transformers Won
        for _ in range(2):
            page.keyboard.press("ArrowRight")
            page.wait_for_timeout(400)
        frames.append(capture_frame(page))

    finally:
        server.shutdown()
    return frames


def capture_website(page, demo_dir: Path) -> list[bytes]:
    """Capture the project page at different scroll positions."""
    port = _free_port()
    server = _serve_dir(demo_dir, port)
    frames = []
    try:
        page.goto(f"http://127.0.0.1:{port}/index.html", wait_until="networkidle", timeout=30_000)
        page.wait_for_timeout(3000)

        # Position 1: Hero
        frames.append(capture_frame(page))

        # Position 2: Abstract + stats cards
        page.evaluate("window.scrollTo({top: 700, behavior: 'instant'})")
        page.wait_for_timeout(800)
        frames.append(capture_frame(page))

        # Position 3: Architecture diagram
        page.evaluate("window.scrollTo({top: 1500, behavior: 'instant'})")
        page.wait_for_timeout(800)
        frames.append(capture_frame(page))

        # Position 4: Results table
        page.evaluate("window.scrollTo({top: 2800, behavior: 'instant'})")
        page.wait_for_timeout(800)
        frames.append(capture_frame(page))

        # Position 5: Impact section
        page.evaluate("window.scrollTo({top: 3600, behavior: 'instant'})")
        page.wait_for_timeout(800)
        frames.append(capture_frame(page))

    finally:
        server.shutdown()
    return frames


def capture_flowchart(page, demo_dir: Path) -> list[bytes]:
    """Capture the flowchart switching between tabs."""
    port = _free_port()
    server = _serve_dir(demo_dir, port)
    frames = []
    try:
        page.goto(f"http://127.0.0.1:{port}/index.html", wait_until="networkidle", timeout=30_000)
        page.wait_for_timeout(6000)  # Mermaid ESM needs time

        # Tab 1: Pipeline (already active)
        frames.append(capture_frame(page))

        # Tab 2: Training
        page.click('[data-tab="training"]')
        page.wait_for_timeout(2000)
        frames.append(capture_frame(page))

        # Tab 3: Concepts
        page.click('[data-tab="concepts"]')
        page.wait_for_timeout(2000)
        frames.append(capture_frame(page))

        # Tab 4: Benchmarks
        page.click('[data-tab="benchmarks"]')
        page.wait_for_timeout(1500)
        frames.append(capture_frame(page))

    finally:
        server.shutdown()
    return frames


def capture_app(page, app_dir: Path) -> list[bytes]:
    """Capture the Gradio app switching between tabs."""
    import os
    import subprocess
    import sys
    import time

    port = _free_port()
    env = os.environ.copy()
    env["GRADIO_SERVER_PORT"] = str(port)
    proc = subprocess.Popen(
        [sys.executable, "app.py"],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        cwd=str(app_dir), env=env,
    )
    frames = []
    try:
        # Wait for Gradio
        for _ in range(30):
            time.sleep(1)
            try:
                page.goto(f"http://127.0.0.1:{port}", timeout=5_000)
                break
            except Exception:
                continue

        page.wait_for_timeout(3000)

        # Tab 1: Sentiment Analysis (default)
        frames.append(capture_frame(page))

        # Use JavaScript clicks to avoid pointer interception issues with Gradio
        tab_names = ["Masked Language Modeling", "Results", "About"]
        for tab_name in tab_names:
            clicked = page.evaluate(f'''() => {{
                const buttons = document.querySelectorAll('button[role="tab"]');
                for (const btn of buttons) {{
                    if (btn.textContent.includes("{tab_name}")) {{
                        btn.click();
                        return true;
                    }}
                }}
                return false;
            }}''')
            page.wait_for_timeout(1500)
            frames.append(capture_frame(page))

    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
    return frames


def main():
    ASSETS.mkdir(parents=True, exist_ok=True)

    demos = {
        "output-presentation": {
            "fn": capture_presentation,
            "dir": DEMOS / "attention_is_all_you_need_presentation",
        },
        "output-website": {
            "fn": capture_website,
            "dir": DEMOS / "attention_is_all_you_need_page",
        },
        "output-diagram": {
            "fn": capture_flowchart,
            "dir": DEMOS / "deep_residual_learning_for_image_recogni",
        },
        "output-app": {
            "fn": capture_app,
            "dir": DEMOS / "bert_app",
        },
    }

    print("Capturing animated gallery SVGs...\n")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport=VIEWPORT, device_scale_factor=2)
        page = context.new_page()

        for name, info in demos.items():
            demo_dir = info["dir"]
            if not demo_dir.exists():
                print(f"  SKIP {name} — {demo_dir.name} not found")
                continue

            print(f"  Capturing {name}...")
            try:
                frames = info["fn"](page, demo_dir)
                print(f"    {len(frames)} frames captured")

                frames_b64 = frames_to_b64(frames)
                svg = build_animated_svg(frames_b64, label=name)

                out_path = ASSETS / f"{name}.svg"
                out_path.write_text(svg)
                print(f"    Saved {out_path.name} ({len(svg) // 1024} KB)")
            except Exception as e:
                print(f"    ERROR: {e}")

        browser.close()

    print(f"\nDone! Files in {ASSETS.relative_to(ROOT)}/")
    for f in sorted(ASSETS.glob("output-*.svg")):
        print(f"   {f.name} ({f.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
