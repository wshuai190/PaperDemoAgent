"""API key management for Paper Demo Agent."""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from paper_demo_agent import config


class KeyManager:
    """Manage API keys for all providers."""

    KEY_DESCRIPTIONS = {
        "ANTHROPIC_API_KEY": "Anthropic (Claude)",
        "OPENAI_API_KEY": "OpenAI (GPT)",
        "GOOGLE_API_KEY": "Google (Gemini)",
        "DEEPSEEK_API_KEY": "DeepSeek",
        "QWEN_API_KEY": "Qwen (Alibaba)",
        "MINIMAX_API_KEY": "MiniMax",
        "MINIMAX_GROUP_ID": "MiniMax Group ID",
        "HUGGINGFACE_TOKEN": "Hugging Face",
    }

    # ── Third-party tool credential detectors ─────────────────────────────────

    def detect_claude_code(self) -> Optional[str]:
        """Return the Claude Code OAuth access token if available.

        Claude Code stores credentials at ~/.claude/.credentials.json with
        the structure: {"claudeAiOauth": {"accessToken": "sk-ant-oat01-...", ...}}
        The accessToken is accepted by the Anthropic SDK as an API key.
        """
        cred_path = Path.home() / ".claude" / ".credentials.json"
        if not cred_path.exists():
            return None
        try:
            data = json.loads(cred_path.read_text())
            token = (data.get("claudeAiOauth") or {}).get("accessToken")
            return token or None
        except Exception:
            return None

    def detect_openai_codex(self) -> Optional[str]:
        """Return the OpenAI API key from the Codex CLI credential file.

        OpenAI Codex CLI stores credentials at ~/.codex/auth.json with
        the structure: {"OPENAI_API_KEY": "sk-..."}
        """
        auth_path = Path.home() / ".codex" / "auth.json"
        if not auth_path.exists():
            return None
        try:
            data = json.loads(auth_path.read_text())
            return data.get("OPENAI_API_KEY") or None
        except Exception:
            return None

    def detect_aider(self) -> Dict[str, Optional[str]]:
        """Return API keys found in the Aider config file.

        Aider stores keys at ~/.aider.conf.yml with fields:
        anthropic-api-key, openai-api-key (and others via api-key list).
        Returns a dict mapping standard env-var names to values.
        """
        conf_path = Path.home() / ".aider.conf.yml"
        if not conf_path.exists():
            return {}
        try:
            # Minimal YAML parsing — only read simple key: value lines
            # (avoid requiring PyYAML as a hard dependency)
            result: Dict[str, Optional[str]] = {}
            for line in conf_path.read_text().splitlines():
                line = line.strip()
                if line.startswith("anthropic-api-key:"):
                    val = line.split(":", 1)[1].strip().strip('"').strip("'")
                    if val:
                        result["ANTHROPIC_API_KEY"] = val
                elif line.startswith("openai-api-key:"):
                    val = line.split(":", 1)[1].strip().strip('"').strip("'")
                    if val:
                        result["OPENAI_API_KEY"] = val
            return result
        except Exception:
            return {}

    def detect_gemini_adc(self) -> bool:
        """Return True if Google Application Default Credentials are available."""
        adc_path = Path.home() / ".config" / "gcloud" / "application_default_credentials.json"
        return adc_path.exists()

    # ── Core key resolution ────────────────────────────────────────────────────

    def get(self, name: str) -> Optional[str]:
        """Get an API key value (config → env → tool credentials)."""
        val, _ = self.get_with_source(name)
        return val

    def set(self, name: str, value: str) -> None:
        """Save an API key."""
        if name not in self.KEY_DESCRIPTIONS:
            raise ValueError(f"Unknown key: {name!r}. Valid keys: {list(self.KEY_DESCRIPTIONS)}")
        config.set_key(name, value.strip())

    def delete(self, name: str) -> None:
        """Remove an API key."""
        config.delete_key(name)

    def all_status(self) -> Dict[str, Optional[str]]:
        """Return masked values for all keys (for display)."""
        return config.get_all_keys()

    def list_configured(self) -> List[str]:
        """Return names of keys that have values."""
        return [name for name, val in self.all_status().items() if val is not None]

    def is_configured(self, name: str) -> bool:
        """Check if a key is set."""
        return bool(self.get(name))

    def get_with_source(self, name: str) -> Tuple[Optional[str], Optional[str]]:
        """Return (value, source) where source is one of:
        'saved', 'env', 'claude-code', 'codex', 'aider', 'adc', or None.

        Resolution order (highest priority first):
          1. Saved in ~/.paper-demo-agent/config.json
          2. Environment variable
          3. Claude Code credentials  (Anthropic only)
          4. OpenAI Codex credentials (OpenAI only)
          5. Aider config             (Anthropic + OpenAI)
          6. Google ADC               (Google only — flagged in all_status_with_sources)
        """
        # 1. Saved config
        saved = config.get_key(name)
        if saved:
            return saved, "saved"

        # 2. Environment variable
        env_val = os.environ.get(name)
        if env_val:
            return env_val, "env"

        # 3. Claude Code → Anthropic
        if name == "ANTHROPIC_API_KEY":
            token = self.detect_claude_code()
            if token:
                return token, "claude-code"

        # 4. OpenAI Codex → OpenAI
        if name == "OPENAI_API_KEY":
            key = self.detect_openai_codex()
            if key:
                return key, "codex"

        # 5. Aider → Anthropic + OpenAI
        if name in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY"):
            aider_keys = self.detect_aider()
            key = aider_keys.get(name)
            if key:
                return key, "aider"

        return None, None

    def all_status_with_sources(self) -> Dict[str, Dict]:
        """Return detailed status for each key including source and masked value."""
        result = {}
        for key_name, label in self.KEY_DESCRIPTIONS.items():
            val, source = self.get_with_source(key_name)
            masked = "••••••••" if val else ""
            result[key_name] = {"label": label, "value": val, "masked": masked, "source": source}
        # Special case: Gemini can use ADC even without a key
        if not result["GOOGLE_API_KEY"]["value"] and self.detect_gemini_adc():
            result["GOOGLE_API_KEY"]["source"] = "adc"
            result["GOOGLE_API_KEY"]["masked"] = "via gcloud ADC"
        return result

    def require(self, name: str) -> str:
        """Get a key or raise if missing."""
        value = self.get(name)
        if not value:
            desc = self.KEY_DESCRIPTIONS.get(name, name)
            raise RuntimeError(
                f"API key not configured: {name}\n"
                f"Set it with: paper-demo-agent key set {name} <value>\n"
                f"Or export it: export {name}=<value>"
            )
        return value
