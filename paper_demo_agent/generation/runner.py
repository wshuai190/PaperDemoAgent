"""Demo runner — launch a generated demo in a subprocess and open in browser."""

import os
import platform
import subprocess
import sys
import time
import webbrowser
from pathlib import Path
from typing import Optional


def _os_open(path: str) -> None:
    """Open a file or URL with the OS default application."""
    system = platform.system()
    if system == "Darwin":
        subprocess.Popen(["open", path])
    elif system == "Windows":
        os.startfile(path)  # type: ignore[attr-defined]
    else:
        subprocess.Popen(["xdg-open", path])


class DemoRunner:
    """Launch a generated demo and optionally open it in a browser."""

    def __init__(self, output_dir: str, main_file: str, demo_form: str = ""):
        self.output_dir = Path(output_dir)
        self.main_file = main_file
        self.demo_form = demo_form
        self._process: Optional[subprocess.Popen] = None

    def run(self, open_browser: bool = True) -> Optional[subprocess.Popen]:
        """
        Start/open the demo appropriately for its form.

        Returns:
            Popen handle for long-running processes, or None for direct file opens.
        """
        main_path = self.output_dir / self.main_file
        ext = main_path.suffix.lower()

        # ── .html — serve via local HTTP server then open in browser ──────────
        # ESM module imports (Mermaid, etc.) require HTTP, not file:// protocol.
        if ext == ".html":
            import http.server
            import functools
            import threading

            port = 8765
            # Kill any existing process on the port
            try:
                import signal
                lsof = subprocess.run(
                    ["lsof", "-ti", f"tcp:{port}"],
                    capture_output=True, text=True, timeout=3,
                )
                for pid_str in lsof.stdout.split():
                    if pid_str.strip().isdigit():
                        try:
                            os.kill(int(pid_str), signal.SIGTERM)
                        except ProcessLookupError:
                            pass
                if lsof.stdout.strip():
                    time.sleep(0.5)
            except (FileNotFoundError, subprocess.TimeoutExpired):
                pass

            handler = functools.partial(
                http.server.SimpleHTTPRequestHandler,
                directory=str(self.output_dir),
            )
            server = http.server.HTTPServer(("127.0.0.1", port), handler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()

            url = f"http://127.0.0.1:{port}/{self.main_file}"
            if open_browser:
                webbrowser.open(url)
            return None

        # ── .pptx — open in PowerPoint / LibreOffice ─────────────────────────
        if ext == ".pptx":
            _os_open(str(main_path.resolve()))
            return None

        # ── .tex — open in default editor or show compile hint ───────────────
        if ext == ".tex":
            _os_open(str(main_path.resolve()))
            return None

        # ── .md — open in default viewer ─────────────────────────────────────
        if ext == ".md":
            _os_open(str(main_path.resolve()))
            return None

        # ── build.py (slides form) — generate .pptx then open it ─────────────
        if ext == ".py" and self.demo_form == "slides":
            # Run build.py to generate presentation.pptx
            pptx_path = self.output_dir / "presentation.pptx"
            if not pptx_path.exists():
                result = subprocess.run(
                    [sys.executable, str(main_path)],
                    cwd=str(self.output_dir),
                    capture_output=True,
                    text=True,
                    timeout=120,
                )
                if result.returncode != 0:
                    raise RuntimeError(
                        f"build.py failed:\n{result.stderr[:500]}"
                    )
            # Now open the generated .pptx
            if pptx_path.exists():
                _os_open(str(pptx_path.resolve()))
            else:
                pptx_files = list(self.output_dir.glob("*.pptx"))
                if pptx_files:
                    _os_open(str(pptx_files[0].resolve()))
                else:
                    raise FileNotFoundError("build.py ran but no .pptx was generated.")
            return None

        # ── build.py (diagram_graphviz form) — generate SVG then open it ──────
        if ext == ".py" and self.demo_form == "diagram_graphviz":
            result = subprocess.run(
                [sys.executable, str(main_path)],
                cwd=str(self.output_dir),
                capture_output=True,
                text=True,
                timeout=120,
            )
            if result.returncode != 0:
                raise RuntimeError(
                    f"build.py failed:\n{result.stderr[:500]}"
                )
            # Open the first generated SVG
            svg_files = sorted(self.output_dir.glob("*.svg"))
            if svg_files:
                _os_open(str(svg_files[0].resolve()))
            else:
                png_files = sorted(self.output_dir.glob("*.png"))
                if png_files:
                    _os_open(str(png_files[0].resolve()))
            return None

        # ── .py — Gradio / Streamlit app ────────────────────────────────────
        if ext == ".py":
            if not main_path.exists():
                raise FileNotFoundError(f"Demo file not found: {main_path}")

            content = main_path.read_text(encoding="utf-8", errors="ignore")

            if "streamlit" in content:
                cmd = [sys.executable, "-m", "streamlit", "run", str(main_path)]
            else:
                cmd = [sys.executable, str(main_path)]

            env = os.environ.copy()
            env["PYTHONPATH"] = str(self.output_dir)

            self._process = subprocess.Popen(
                cmd,
                cwd=str(self.output_dir),
                env=env,
            )

            if open_browser:
                time.sleep(3)
                if "gradio" in content:
                    webbrowser.open("http://localhost:7861")
                elif "streamlit" in content:
                    webbrowser.open("http://localhost:8501")

            return self._process

        raise ValueError(f"Unsupported demo file type: {ext!r}")

    def stop(self) -> None:
        """Terminate the running demo process."""
        if self._process and self._process.poll() is None:
            self._process.terminate()
            try:
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._process.kill()
            self._process = None

    def is_running(self) -> bool:
        return self._process is not None and self._process.poll() is None

    def __enter__(self):
        self.run()
        return self

    def __exit__(self, *args):
        self.stop()
