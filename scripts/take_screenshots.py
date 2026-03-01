#!/usr/bin/env python3
"""
Capture screenshots of all demo examples + the Gradio UI for README gallery.

Usage:
    python scripts/take_screenshots.py

Outputs PNGs to docs/assets/:
    - ui-screenshot.png        Gradio web interface (hero image)
    - output-diagram.png       ResNet Mermaid flowchart
    - output-presentation.png  Attention reveal.js slides
    - output-website.png       Attention project page
    - output-app.png           BERT Gradio app (static preview)
"""

from __future__ import annotations

import http.server
import os
import signal
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
DEMOS = ROOT / "demos"
ASSETS = ROOT / "docs" / "assets"

VIEWPORT = {"width": 1440, "height": 900}


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("", 0))
        return s.getsockname()[1]


def _serve_dir(directory: Path, port: int) -> http.server.HTTPServer:
    """Start a simple HTTP server in a background thread. Returns the server."""
    handler = type(
        "H",
        (http.server.SimpleHTTPRequestHandler,),
        {"__init__": lambda self, *a, **kw: super(type(self), self).__init__(
            *a, directory=str(directory), **kw
        )},
    )
    server = http.server.HTTPServer(("127.0.0.1", port), handler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    return server


def screenshot_html(page, html_dir: Path, main_file: str, out_path: Path,
                    wait_ms: int = 3000):
    """Serve an HTML directory over HTTP and screenshot it."""
    port = _free_port()
    server = _serve_dir(html_dir, port)
    try:
        url = f"http://127.0.0.1:{port}/{main_file}"
        page.goto(url, wait_until="networkidle", timeout=30_000)
        page.wait_for_timeout(wait_ms)  # let JS render (Mermaid, reveal.js, KaTeX)
        page.screenshot(path=str(out_path), full_page=False)
        print(f"  ✓ {out_path.name} ({out_path.stat().st_size // 1024} KB)")
    finally:
        server.shutdown()


def screenshot_gradio_ui(page, out_path: Path):
    """Launch paper-demo-agent ui, screenshot it, then kill."""
    port = _free_port()
    proc = subprocess.Popen(
        [sys.executable, "-m", "paper_demo_agent.cli", "ui", "--port", str(port)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        cwd=str(ROOT),
    )
    try:
        # Wait for Gradio to start
        for _ in range(60):
            time.sleep(1)
            try:
                page.goto(f"http://127.0.0.1:{port}", timeout=5_000)
                break
            except Exception:
                continue
        else:
            print("  ✗ Gradio UI did not start in 60s")
            return

        page.wait_for_timeout(4000)  # let Gradio fully render
        page.screenshot(path=str(out_path), full_page=False)
        print(f"  ✓ {out_path.name} ({out_path.stat().st_size // 1024} KB)")
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


def screenshot_gradio_app(page, app_dir: Path, out_path: Path):
    """Launch a Gradio app.py, screenshot it, then kill."""
    port = _free_port()
    env = os.environ.copy()
    env["GRADIO_SERVER_PORT"] = str(port)
    proc = subprocess.Popen(
        [sys.executable, "app.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        cwd=str(app_dir),
        env=env,
    )
    try:
        for _ in range(60):
            time.sleep(1)
            try:
                page.goto(f"http://127.0.0.1:{port}", timeout=5_000)
                break
            except Exception:
                continue
        else:
            print(f"  ✗ Gradio app at {app_dir.name} did not start in 60s")
            return

        page.wait_for_timeout(4000)
        page.screenshot(path=str(out_path), full_page=False)
        print(f"  ✓ {out_path.name} ({out_path.stat().st_size // 1024} KB)")
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


def main():
    ASSETS.mkdir(parents=True, exist_ok=True)

    demos_to_capture = {
        "output-diagram.png": {
            "dir": DEMOS / "deep_residual_learning_for_image_recogni",
            "file": "index.html",
            "wait": 5000,  # Mermaid ESM needs extra time
        },
        "output-presentation.png": {
            "dir": DEMOS / "attention_is_all_you_need_presentation",
            "file": "demo.html",
            "wait": 4000,
        },
        "output-website.png": {
            "dir": DEMOS / "attention_is_all_you_need_page",
            "file": "index.html",
            "wait": 3000,
        },
    }

    print("📸 Taking screenshots...\n")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport=VIEWPORT,
            device_scale_factor=2,  # retina-quality
        )
        page = context.new_page()

        # ── HTML demos ──
        for filename, info in demos_to_capture.items():
            demo_dir = info["dir"]
            if not demo_dir.exists():
                print(f"  ✗ {filename} — demo dir not found: {demo_dir.name}")
                continue
            print(f"  📷 {filename}...")
            screenshot_html(page, demo_dir, info["file"], ASSETS / filename, info["wait"])

        # ── BERT Gradio app ──
        bert_dir = DEMOS / "bert_app"
        if bert_dir.exists():
            print(f"  📷 output-app.png...")
            screenshot_gradio_app(page, bert_dir, ASSETS / "output-app.png")

        # ── Gradio UI (paper-demo-agent ui) ──
        print(f"  📷 ui-screenshot.png...")
        screenshot_gradio_ui(page, ASSETS / "ui-screenshot.png")

        browser.close()

    print(f"\n✅ Done! Screenshots saved to {ASSETS.relative_to(ROOT)}/")
    for f in sorted(ASSETS.glob("*.png")):
        print(f"   {f.name} ({f.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
