"""Provider factory — create providers from name + config."""

from typing import Dict, List, Optional

from paper_demo_agent.providers.base import BaseLLMProvider


PROVIDER_DEFAULTS: Dict[str, Dict] = {
    "anthropic": {
        "key_env": "ANTHROPIC_API_KEY",
        "default_model": "claude-sonnet-4-6",
        "models": [
            "claude-sonnet-4-6",
            "claude-opus-4-6",
            "claude-haiku-4-5-20251001",
        ],
    },
    "openai": {
        "key_env": "OPENAI_API_KEY",
        "default_model": "gpt-5.2",
        "models": [
            "gpt-5.2", "gpt-5.2-pro",
            "gpt-5.1", "gpt-5",
            "gpt-4.1", "gpt-4.1-mini",
            "o3", "o4-mini",
        ],
    },
    "deepseek": {
        "key_env": "DEEPSEEK_API_KEY",
        "default_model": "deepseek-chat",
        "models": ["deepseek-chat", "deepseek-reasoner"],
    },
    "qwen": {
        "key_env": "QWEN_API_KEY",
        "default_model": "qwen-max",
        "models": ["qwen-max", "qwen-plus", "qwen-turbo"],
    },
    "gemini": {
        "key_env": "GOOGLE_API_KEY",
        "default_model": "gemini-2.5-flash",
        # Static fallback — updated dynamically from the API when a key is present
        "models": [
            "gemini-2.5-pro", "gemini-2.5-flash",
            "gemini-2.0-flash",
        ],
    },
    "minimax": {
        "key_env": "MINIMAX_API_KEY",
        "extra_env": "MINIMAX_GROUP_ID",
        "default_model": "abab6.5-chat",
        "models": ["abab6.5-chat", "abab6.5s-chat"],
    },
}


def list_providers() -> List[str]:
    """Return all supported provider names."""
    return list(PROVIDER_DEFAULTS.keys())


def create_provider(
    provider_name: str,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    **kwargs,
) -> BaseLLMProvider:
    """
    Create and return a configured provider instance.

    Args:
        provider_name: One of "anthropic", "openai", "deepseek", "qwen", "gemini", "minimax"
        api_key: API key (falls back to config / environment)
        model: Model name (falls back to provider default)
        **kwargs: Extra arguments (e.g. group_id for MiniMax)

    Returns:
        Configured BaseLLMProvider instance
    """
    from paper_demo_agent.keys.manager import KeyManager

    name = provider_name.lower().strip()
    if name not in PROVIDER_DEFAULTS:
        raise ValueError(
            f"Unknown provider: {name!r}. Valid providers: {list_providers()}"
        )

    info = PROVIDER_DEFAULTS[name]

    # Resolve API key via KeyManager (OpenClaw OAuth > Claude Code > config > env > tools)
    km = KeyManager()
    if api_key:
        key = api_key
    else:
        key, source = km.get_with_source(info["key_env"])
        if source:
            import sys
            if name == "gemini" and source == "gemini-cli":
                print("[paper-demo-agent] Using Gemini CLI OAuth credentials", file=sys.stderr)
            else:
                print(f"[paper-demo-agent] Using {info['key_env']} from {source}", file=sys.stderr)

    # Gemini can authenticate via Google Application Default Credentials — no key required
    if not key and name != "gemini":
        raise RuntimeError(
            f"API key not found for provider '{name}'. "
            f"Set {info['key_env']} via environment or:\n"
            f"  paper-demo-agent key set {info['key_env']} <value>\n"
            f"  Or authenticate via Claude Code (auto-detected from `claude login`)"
        )

    if name == "anthropic":
        from paper_demo_agent.providers.anthropic_provider import AnthropicProvider
        return AnthropicProvider(api_key=key, model=model)

    elif name == "openai":
        from paper_demo_agent.providers.openai_provider import OpenAIProvider
        return OpenAIProvider(api_key=key, model=model)

    elif name == "deepseek":
        from paper_demo_agent.providers.openai_provider import DeepSeekProvider
        return DeepSeekProvider(api_key=key, model=model)

    elif name == "qwen":
        from paper_demo_agent.providers.openai_provider import QwenProvider
        return QwenProvider(api_key=key, model=model)

    elif name == "gemini":
        from paper_demo_agent.providers.gemini_provider import GeminiProvider
        return GeminiProvider(api_key=key, model=model)

    elif name == "minimax":
        group_id = kwargs.get("group_id") or km.get("MINIMAX_GROUP_ID")
        if not group_id:
            raise RuntimeError(
                "MiniMax requires MINIMAX_GROUP_ID. "
                "Set it via environment or `paper-demo-agent key set MINIMAX_GROUP_ID`."
            )
        from paper_demo_agent.providers.minimax_provider import MiniMaxProvider
        return MiniMaxProvider(api_key=key, group_id=group_id, model=model)

    raise ValueError(f"Unhandled provider: {name!r}")
