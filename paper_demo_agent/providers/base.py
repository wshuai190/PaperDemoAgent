"""Base LLM provider abstractions."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Iterator, List, Optional


@dataclass
class ToolCall:
    """A normalized tool call from any LLM provider."""
    id: str
    name: str
    arguments: Dict[str, Any]


@dataclass
class LLMResponse:
    """A normalized response from any LLM provider."""
    content: str
    tool_calls: List[ToolCall] = field(default_factory=list)
    stop_reason: str = "end_turn"   # "end_turn" | "tool_use" | "max_tokens"
    raw: Any = None                  # Provider-specific raw response


class BaseLLMProvider(ABC):
    """Abstract base for all LLM providers."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key
        self.model = model or self.default_model

    @property
    @abstractmethod
    def default_model(self) -> str:
        """Return the default model name for this provider."""
        ...

    @abstractmethod
    def list_models(self) -> List[str]:
        """Return available models for this provider."""
        ...

    @abstractmethod
    def chat(
        self,
        messages: List[Dict],
        system: str = "",
        tools: Optional[List[Dict]] = None,
        max_tokens: int = 8192,
    ) -> LLMResponse:
        """Send a chat request and return a normalized response."""
        ...

    @abstractmethod
    def stream_chat(
        self,
        messages: List[Dict],
        system: str = "",
        tools: Optional[List[Dict]] = None,
        max_tokens: int = 8192,
    ) -> Iterator[str]:
        """Stream a chat response, yielding text chunks."""
        ...

    @property
    def supports_native_pdf(self) -> bool:
        """Whether this provider can receive raw PDF bytes alongside the prompt."""
        return False

    def list_models_live(self) -> Optional[List[str]]:
        """Fetch the current list of available models from the provider API.
        Returns None if not supported or if the request fails.
        """
        return None

    def chat_with_pdf(
        self,
        messages: List[Dict],
        pdf_bytes: bytes,
        system: str = "",
        tools: Optional[List[Dict]] = None,
        max_tokens: int = 8192,
    ) -> "LLMResponse":
        """Send a chat request that includes a PDF document as context.
        Providers without native PDF support fall back to text-only chat.
        """
        return self.chat(messages, system=system, tools=tools, max_tokens=max_tokens)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(model={self.model!r})"
