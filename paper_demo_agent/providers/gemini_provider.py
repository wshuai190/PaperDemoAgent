"""Google Gemini provider."""

import base64
import json
from typing import Any, Dict, Iterator, List, Optional

from paper_demo_agent.providers.base import BaseLLMProvider, LLMResponse, ToolCall


class GeminiProvider(BaseLLMProvider):
    """LLM provider for Google Gemini models."""

    MODELS = [
        "gemini-2.5-flash",
        "gemini-2.5-pro",
        "gemini-2.0-flash",
        "gemini-2.0-flash-lite",
    ]

    @property
    def default_model(self) -> str:
        return "gemini-2.5-flash"

    def list_models(self) -> List[str]:
        return self.MODELS

    @property
    def supports_native_pdf(self) -> bool:
        return True

    # Curated models to show — no dated snapshots, no experimental, no niche variants
    _CURATED_MODELS = {
        "gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.5-flash-lite",
        "gemini-2.0-flash", "gemini-2.0-flash-lite",
        "gemini-3-pro-preview", "gemini-3-flash-preview",
        "gemini-3.1-pro-preview",
    }

    def list_models_live(self) -> Optional[List[str]]:
        """Fetch curated Gemini models from the API (no experimental/dated variants)."""
        try:
            genai = self._get_genai()
            models = []
            for m in genai.list_models():
                name = m.name.replace("models/", "")
                supported = getattr(m, "supported_generation_methods", []) or []
                if "generateContent" in supported and name in self._CURATED_MODELS:
                    models.append(name)
            # Deduplicate and sort with newest first
            return sorted(set(models), reverse=True) if models else None
        except Exception:
            return None

    def chat_with_pdf(
        self,
        messages: List[Dict],
        pdf_bytes: bytes,
        system: str = "",
        tools: Optional[List[Dict]] = None,
        max_tokens: int = 8192,
    ) -> "LLMResponse":
        """Prepend the PDF as an inline_data part to the first user turn."""
        b64 = base64.standard_b64encode(pdf_bytes).decode()
        pdf_part = {"inline_data": {"mime_type": "application/pdf", "data": b64}}
        augmented = list(messages)
        first_user = next((i for i, m in enumerate(augmented) if m["role"] == "user"), None)
        if first_user is not None:
            orig = augmented[first_user]
            content = orig["content"]
            if isinstance(content, str):
                text_parts = [{"text": content}]
            elif isinstance(content, list):
                text_parts = [{"text": c["text"]} for c in content if c.get("type") == "text"]
            else:
                text_parts = []
            augmented[first_user] = {"role": "user", "content": [pdf_part] + text_parts}
        return self.chat(augmented, system=system, tools=tools, max_tokens=max_tokens)

    @property
    def _is_gemini_cli_token(self) -> bool:
        """Check if the API key is a Gemini CLI JSON credential."""
        if not self.api_key:
            return False
        try:
            data = json.loads(self.api_key)
            return isinstance(data, dict) and "token" in data
        except (json.JSONDecodeError, TypeError):
            return False

    def _get_genai(self):
        try:
            import google.generativeai as genai
        except ImportError:
            raise ImportError("google-generativeai is required: pip install google-generativeai")

        if self.api_key and self._is_gemini_cli_token:
            # Gemini CLI OAuth token — use Bearer auth via google.oauth2.credentials
            # IMPORTANT: credentials and api_key are mutually exclusive in genai.configure()
            data = json.loads(self.api_key)
            access_token = data["token"]
            try:
                from google.oauth2.credentials import Credentials
                credentials = Credentials(token=access_token)
                genai.configure(credentials=credentials, api_key=None)
            except ImportError:
                # Fallback: use the raw access token as an API key
                genai.configure(api_key=access_token)
        elif self.api_key:
            # Standard API key (e.g. from Google AI Studio)
            genai.configure(api_key=self.api_key)
        else:
            # No API key — try Application Default Credentials (gcloud auth)
            try:
                import google.auth
                credentials, _ = google.auth.default(
                    scopes=["https://www.googleapis.com/auth/generativelanguage"]
                )
                genai.configure(credentials=credentials, api_key=None)
            except Exception as exc:
                raise RuntimeError(
                    "No Gemini API key found and Application Default Credentials unavailable.\n"
                    "Fix with one of:\n"
                    "  • paper-demo-agent key set GOOGLE_API_KEY <your-key>\n"
                    "  • gcloud auth application-default login\n"
                    f"ADC error: {exc}"
                ) from exc
        return genai

    def _convert_tools(self, tools: List[Dict]) -> List[Any]:
        """Convert generic tool defs to Gemini FunctionDeclaration format."""
        genai = self._get_genai()
        declarations = []
        for t in tools:
            params = t.get("parameters", {"type": "object", "properties": {}})
            declarations.append(
                genai.protos.FunctionDeclaration(
                    name=t["name"],
                    description=t.get("description", ""),
                    parameters=genai.protos.Schema(
                        type=genai.protos.Type.OBJECT,
                        properties={
                            k: genai.protos.Schema(
                                type=genai.protos.Type[v.get("type", "string").upper()],
                                description=v.get("description", ""),
                            )
                            for k, v in params.get("properties", {}).items()
                        },
                        required=params.get("required", []),
                    ),
                )
            )
        return [genai.protos.Tool(function_declarations=declarations)]

    def _messages_to_gemini(self, messages: List[Dict]) -> List[Dict]:
        """Convert OpenAI-style messages to Gemini format."""
        result = []
        for msg in messages:
            role = msg["role"]
            content = msg.get("content", "")
            if role == "assistant":
                role = "model"
            elif role == "tool":
                # Tool results
                result.append({
                    "role": "user",
                    "parts": [{"function_response": {
                        "name": msg.get("name", "tool"),
                        "response": {"result": content},
                    }}],
                })
                continue

            if isinstance(content, str):
                result.append({"role": role, "parts": [{"text": content}]})
            elif isinstance(content, list):
                parts = []
                for c in content:
                    if isinstance(c, dict):
                        if c.get("type") == "text":
                            parts.append({"text": c["text"]})
                        elif "inline_data" in c:
                            # Pass through inline_data (e.g. PDF bytes) unchanged
                            parts.append(c)
                        elif "text" in c:
                            # Already in Gemini parts format (from chat_with_pdf)
                            parts.append(c)
                result.append({"role": role, "parts": parts})
        return result

    def _parse_response(self, response) -> LLMResponse:
        import google.generativeai as genai

        content_text = ""
        tool_calls = []

        for part in response.parts:
            if hasattr(part, "text") and part.text:
                content_text += part.text
            elif hasattr(part, "function_call") and part.function_call:
                fc = part.function_call
                args = dict(fc.args) if fc.args else {}
                tool_calls.append(ToolCall(
                    id=f"call_{fc.name}_{len(tool_calls)}",
                    name=fc.name,
                    arguments=args,
                ))

        stop_reason = "tool_use" if tool_calls else "end_turn"
        return LLMResponse(
            content=content_text,
            tool_calls=tool_calls,
            stop_reason=stop_reason,
            raw=response,
        )

    def chat(
        self,
        messages: List[Dict],
        system: str = "",
        tools: Optional[List[Dict]] = None,
        max_tokens: int = 8192,
    ) -> LLMResponse:
        genai = self._get_genai()

        model_kwargs: Dict[str, Any] = {"model_name": self.model}
        if system:
            model_kwargs["system_instruction"] = system
        if tools:
            model_kwargs["tools"] = self._convert_tools(tools)

        model = genai.GenerativeModel(**model_kwargs)
        gemini_messages = self._messages_to_gemini(messages)

        response = model.generate_content(
            gemini_messages,
            generation_config={"max_output_tokens": max_tokens},
        )
        return self._parse_response(response)

    def stream_chat(
        self,
        messages: List[Dict],
        system: str = "",
        tools: Optional[List[Dict]] = None,
        max_tokens: int = 8192,
    ) -> Iterator[str]:
        genai = self._get_genai()

        model_kwargs: Dict[str, Any] = {"model_name": self.model}
        if system:
            model_kwargs["system_instruction"] = system

        model = genai.GenerativeModel(**model_kwargs)
        gemini_messages = self._messages_to_gemini(messages)

        response = model.generate_content(
            gemini_messages,
            generation_config={"max_output_tokens": max_tokens},
            stream=True,
        )
        for chunk in response:
            if chunk.text:
                yield chunk.text
