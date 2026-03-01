"""Configuration management for Paper Demo Agent."""

import json
import os
from pathlib import Path
from typing import Optional


CONFIG_DIR = Path.home() / ".paper-demo-agent"
CONFIG_FILE = CONFIG_DIR / "config.json"

KEY_NAMES = [
    "ANTHROPIC_API_KEY",
    "OPENAI_API_KEY",
    "GOOGLE_API_KEY",
    "DEEPSEEK_API_KEY",
    "QWEN_API_KEY",
    "MINIMAX_API_KEY",
    "MINIMAX_GROUP_ID",
    "HUGGINGFACE_TOKEN",
]


def _load_config() -> dict:
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def _save_config(data: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(data, indent=2))
    CONFIG_FILE.chmod(0o600)


def get_key(name: str) -> Optional[str]:
    """Get an API key — checks environment first, then config file."""
    value = os.environ.get(name)
    if value:
        return value
    config = _load_config()
    return config.get(name)


def set_key(name: str, value: str) -> None:
    """Persist an API key to config file."""
    config = _load_config()
    config[name] = value
    _save_config(config)


def delete_key(name: str) -> None:
    """Remove an API key from config file."""
    config = _load_config()
    config.pop(name, None)
    _save_config(config)


def get_all_keys() -> dict:
    """Return all configured keys (masked values for display)."""
    config = _load_config()
    result = {}
    for name in KEY_NAMES:
        env_val = os.environ.get(name)
        config_val = config.get(name)
        value = env_val or config_val
        if value:
            result[name] = value[:8] + "..." if len(value) > 8 else "***"
        else:
            result[name] = None
    return result


def _find_project_root() -> Path:
    """Walk up from cwd to find the project root (has pyproject.toml or .git)."""
    cwd = Path.cwd()
    for parent in [cwd, *cwd.parents]:
        if (parent / "pyproject.toml").exists() or (parent / ".git").exists():
            return parent
    return cwd  # fallback to cwd


def get_output_dir(name: str = "demo") -> Path:
    """Return a fresh output directory for a generated demo."""
    base = _find_project_root() / "demos"
    base.mkdir(exist_ok=True)
    # Sanitize name
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in name)[:40] or "demo"
    candidate = base / safe
    if not candidate.exists():
        return candidate
    i = 1
    while True:
        candidate = base / f"{safe}_{i}"
        if not candidate.exists():
            return candidate
        i += 1
