#!/usr/bin/env python3
"""Test all demo form variations against a paper using Gemini 2.5 Pro.

Usage:
    python test_variations.py                          # run all 10 variations
    python test_variations.py --only app_streamlit     # run one specific variation
    python test_variations.py --only page_readme,page_blog  # run a few
    python test_variations.py --paper path/to/other.pdf     # use a different paper
"""

import argparse
import os
import sys
import time
import traceback
from pathlib import Path

# ── Configuration ────────────────────────────────────────────────────────────

PROVIDER = "gemini"
DEFAULT_MODEL = "gemini-2.5-pro"
PAPER_PATH = "test_variations/paper.pdf"
OUTPUT_BASE = "test_variations"

# All 10 (category, subtype) combinations
ALL_VARIATIONS = [
    # (directory_name, --form, --subtype)
    ("app_gradio",            "app",          "gradio"),
    ("app_streamlit",         "app",          "streamlit"),
    ("presentation_revealjs", "presentation", "revealjs"),
    ("presentation_beamer",   "presentation", "beamer"),
    ("presentation_pptx",     "presentation", "pptx"),
    ("page_project",          "page",         "project"),
    ("page_readme",           "page",         "readme"),
    ("page_blog",             "page",         "blog"),
    ("diagram_mermaid",       "diagram",      "mermaid"),
    ("diagram_graphviz",      "diagram",      "graphviz"),
]


def run_variation(paper_path: str, dir_name: str, form: str, subtype: str,
                  model: str) -> dict:
    """Run a single variation and return result info."""
    from paper_demo_agent.agent import PaperDemoAgent

    output_dir = os.path.join(OUTPUT_BASE, dir_name)
    os.makedirs(output_dir, exist_ok=True)

    print(f"\n{'='*70}")
    print(f"  {form}/{subtype}  →  {output_dir}")
    print(f"{'='*70}\n")

    start = time.time()
    try:
        agent = PaperDemoAgent(provider=PROVIDER, model=model)
        result = agent.run(
            source=paper_path,
            output_dir=output_dir,
            demo_form=form,
            demo_subtype=subtype,
            max_iter=25,
            on_progress=lambda t: sys.stdout.write(t) or sys.stdout.flush(),
        )
        elapsed = time.time() - start
        files = list(Path(output_dir).rglob("*"))
        file_list = [str(f.relative_to(output_dir)) for f in files if f.is_file()]

        return {
            "variation": f"{form}/{subtype}",
            "dir": output_dir,
            "success": result.success,
            "main_file": result.main_file,
            "demo_form": result.demo_form,
            "run_command": result.run_command,
            "files": file_list,
            "elapsed": elapsed,
            "error": result.error if not result.success else None,
        }
    except Exception as e:
        elapsed = time.time() - start
        traceback.print_exc()
        return {
            "variation": f"{form}/{subtype}",
            "dir": output_dir,
            "success": False,
            "main_file": "",
            "demo_form": "",
            "run_command": "",
            "files": [],
            "elapsed": elapsed,
            "error": str(e),
        }


def print_summary(results: list, model: str):
    """Print a summary table of all results."""
    print(f"\n\n{'='*80}")
    print(f"  RESULTS SUMMARY — {PROVIDER} / {model}")
    print(f"{'='*80}\n")

    max_var = max(len(r["variation"]) for r in results)
    header = f"  {'Variation':<{max_var}}  {'Status':<8}  {'Time':>7}  {'Files':>5}  Main File"
    print(header)
    print(f"  {'-'*len(header)}")

    passed = 0
    failed = 0
    for r in results:
        status = "PASS" if r["success"] else "FAIL"
        emoji = "✓" if r["success"] else "✗"
        time_str = f"{r['elapsed']:.0f}s"
        n_files = len(r["files"])
        print(f"  {r['variation']:<{max_var}}  {emoji} {status:<5}  {time_str:>7}  {n_files:>5}  {r['main_file']}")
        if r["success"]:
            passed += 1
        else:
            failed += 1

    print(f"\n  Total: {passed} passed, {failed} failed out of {len(results)}")
    total_time = sum(r["elapsed"] for r in results)
    print(f"  Total time: {total_time:.0f}s ({total_time/60:.1f}min)")

    if failed:
        print(f"\n  FAILURES:")
        for r in results:
            if not r["success"]:
                print(f"    {r['variation']}: {r['error']}")

    print()


def main():
    parser = argparse.ArgumentParser(description="Test all demo form variations")
    parser.add_argument("--paper", default=PAPER_PATH, help="Path to paper PDF")
    parser.add_argument("--only", default=None,
                        help="Comma-separated list of variation dir names to run (e.g. app_streamlit,page_readme)")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"Gemini model (default: {DEFAULT_MODEL})")
    args = parser.parse_args()

    if not os.path.exists(args.paper):
        print(f"Error: Paper not found at {args.paper}")
        sys.exit(1)

    # Filter variations if --only is specified
    if args.only:
        selected = set(args.only.split(","))
        variations = [v for v in ALL_VARIATIONS if v[0] in selected]
        if not variations:
            print(f"Error: No matching variations for: {args.only}")
            print(f"Available: {', '.join(v[0] for v in ALL_VARIATIONS)}")
            sys.exit(1)
    else:
        variations = ALL_VARIATIONS

    print(f"\n  Paper Demo Agent — Test Variations")
    print(f"  Provider: {PROVIDER} / {args.model}")
    print(f"  Paper:    {args.paper}")
    print(f"  Running:  {len(variations)} variations\n")

    results = []
    for dir_name, form, subtype in variations:
        result = run_variation(args.paper, dir_name, form, subtype, model=args.model)
        results.append(result)

    print_summary(results, model=args.model)


if __name__ == "__main__":
    main()
