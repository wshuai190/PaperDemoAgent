"""Google Gemini provider."""

import base64
import json
import time
import uuid
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

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        super().__init__(api_key=api_key, model=model)
        self._session_id = str(uuid.uuid4())
        self._resolved_code_assist_project: Optional[str] = None
        self._resolved_code_assist_project_loaded = False
        self._last_code_assist_request_at = 0.0

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

        # IMPORTANT: genai.configure() has global state. When switching between
        # api_key and credentials auth, the old state causes
        # "client_options.api_key and credentials are mutually exclusive" errors.
        # Fix: create a fresh _client_manager to clear all previous state.
        try:
            genai._client_manager = type(genai._client_manager)()
        except Exception:
            pass  # If internals change, fall through — configure() may still work

        if self.api_key and self._is_gemini_cli_token:
            # Gemini CLI OAuth token — handled via direct REST in _chat_rest(),
            # but _get_genai() is still called by stream_chat/list_models_live.
            # Configure with a dummy setup so the SDK doesn't error on import.
            import os
            env_backup = os.environ.pop("GOOGLE_API_KEY", None)
            try:
                data = json.loads(self.api_key)
                access_token = data["token"]
                try:
                    from google.oauth2.credentials import Credentials
                    credentials = Credentials(token=access_token)
                    genai.configure(credentials=credentials)
                except ImportError:
                    genai.configure(api_key=access_token)
            finally:
                if env_backup is not None:
                    os.environ["GOOGLE_API_KEY"] = env_backup
        elif self.api_key:
            # Standard API key (e.g. from Google AI Studio)
            # Temporarily clear GOOGLE_API_KEY env var to prevent genai from
            # auto-discovering it AND using the passed api_key (double-auth conflict)
            import os
            env_backup = os.environ.pop("GOOGLE_API_KEY", None)
            try:
                genai.configure(api_key=self.api_key)
            finally:
                if env_backup is not None:
                    os.environ["GOOGLE_API_KEY"] = env_backup
        else:
            # No API key — try Application Default Credentials (gcloud auth)
            try:
                import google.auth
                credentials, _ = google.auth.default(
                    scopes=["https://www.googleapis.com/auth/generativelanguage"]
                )
                genai.configure(credentials=credentials)
            except Exception as exc:
                raise RuntimeError(
                    "No Gemini API key found and Application Default Credentials unavailable.\n"
                    "Fix with one of:\n"
                    "  • paper-demo-agent key set GOOGLE_API_KEY <your-key>\n"
                    "  • gcloud auth application-default login\n"
                    f"ADC error: {exc}"
                ) from exc
        return genai

    def _convert_tools_json(self, tools: List[Dict]) -> List[Dict]:
        """Convert tools to plain JSON format for REST calls."""
        TYPE_MAP = {"string": "STRING", "integer": "INTEGER", "number": "NUMBER",
                    "boolean": "BOOLEAN", "array": "ARRAY", "object": "OBJECT"}
        declarations = []
        for t in tools:
            params = t.get("parameters", {"type": "object", "properties": {}})
            properties = {
                k: {"type": TYPE_MAP.get(v.get("type", "string").lower(), "STRING"),
                    "description": v.get("description", "")}
                for k, v in params.get("properties", {}).items()
            }
            declarations.append({
                "name": t["name"],
                "description": t.get("description", ""),
                "parameters": {
                    "type": "OBJECT",
                    "properties": properties,
                    "required": params.get("required", []),
                },
            })
        return [{"functionDeclarations": declarations}]

    def _parse_rest_response(self, data: Dict) -> LLMResponse:
        """Parse raw JSON response from Gemini REST API."""
        content_text = ""
        tool_calls = []
        for candidate in data.get("candidates", []):
            for part in candidate.get("content", {}).get("parts", []):
                if "text" in part:
                    content_text += part["text"]
                elif "functionCall" in part:
                    fc = part["functionCall"]
                    tool_calls.append(ToolCall(
                        id=f"call_{fc['name']}_{len(tool_calls)}",
                        name=fc["name"],
                        arguments=fc.get("args", {}),
                    ))
        stop_reason = "tool_use" if tool_calls else "end_turn"
        return LLMResponse(content=content_text, tool_calls=tool_calls,
                           stop_reason=stop_reason, raw=data)

    @staticmethod
    def _code_assist_metadata(project_id: Optional[str] = None) -> Dict[str, Any]:
        metadata: Dict[str, Any] = {
            "ideType": "IDE_UNSPECIFIED",
            "platform": "PLATFORM_UNSPECIFIED",
            "pluginType": "GEMINI",
        }
        if project_id:
            metadata["duetProject"] = project_id
        return metadata

    @staticmethod
    def _default_onboard_tier(load_res: Dict[str, Any]) -> Dict[str, Any]:
        for tier in load_res.get("allowedTiers", []) or []:
            if isinstance(tier, dict) and tier.get("isDefault"):
                return tier
        return {
            "id": "legacy-tier",
            "name": "",
            "description": "",
            "userDefinedCloudaicompanionProject": True,
        }

    @staticmethod
    def _code_assist_error_message(load_res: Dict[str, Any]) -> str:
        ineligible = load_res.get("ineligibleTiers", []) or []
        reasons = [tier.get("reasonMessage") for tier in ineligible if isinstance(tier, dict) and tier.get("reasonMessage")]
        if reasons:
            return ", ".join(reasons)
        return (
            "This Gemini CLI account requires a valid Code Assist project, but no managed "
            "project was returned. Set GOOGLE_CLOUD_PROJECT for workspace auth, or run "
            "`gemini` again to refresh personal OAuth setup."
        )

    @staticmethod
    def _extract_operation_project(operation_res: Dict[str, Any]) -> Optional[str]:
        return (
            ((operation_res.get("response") or {}).get("cloudaicompanionProject") or {}).get("id")
        )

    def _code_assist_post(self, client, headers: Dict[str, str], method: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        self._throttle_code_assist_request()
        url = f"https://cloudcode-pa.googleapis.com/v1internal:{method}"
        resp = client.post(url, json=payload, headers=headers)
        if resp.status_code != 200:
            raise RuntimeError(f"Gemini OAuth API error: {resp.status_code} - {resp.text}")
        return resp.json()

    def _code_assist_get_operation(self, client, headers: Dict[str, str], operation_name: str) -> Dict[str, Any]:
        self._throttle_code_assist_request()
        url = f"https://cloudcode-pa.googleapis.com/v1internal/{operation_name}"
        resp = client.get(url, headers=headers)
        if resp.status_code != 200:
            raise RuntimeError(f"Gemini OAuth API error: {resp.status_code} - {resp.text}")
        return resp.json()

    def _throttle_code_assist_request(self) -> None:
        """Pace Gemini CLI requests to reduce free-tier 429s."""
        min_interval_s = 1.2
        now = time.monotonic()
        elapsed = now - self._last_code_assist_request_at
        if elapsed < min_interval_s:
            time.sleep(min_interval_s - elapsed)
        self._last_code_assist_request_at = time.monotonic()

    def _resolve_code_assist_project(
        self,
        client,
        headers: Dict[str, str],
        configured_project: Optional[str],
    ) -> Optional[str]:
        if configured_project:
            return configured_project
        if self._resolved_code_assist_project_loaded:
            return self._resolved_code_assist_project

        load_res = self._code_assist_post(
            client,
            headers,
            "loadCodeAssist",
            {
                "cloudaicompanionProject": configured_project,
                "metadata": self._code_assist_metadata(configured_project),
            },
        )

        current_project = load_res.get("cloudaicompanionProject")
        if current_project:
            self._resolved_code_assist_project = current_project
            self._resolved_code_assist_project_loaded = True
            return current_project

        if load_res.get("currentTier"):
            self._resolved_code_assist_project_loaded = True
            self._resolved_code_assist_project = None
            raise RuntimeError(self._code_assist_error_message(load_res))

        tier = self._default_onboard_tier(load_res)
        tier_id = tier.get("id")
        onboard_payload: Dict[str, Any] = {
            "tierId": tier_id,
            "cloudaicompanionProject": configured_project if tier_id != "free-tier" else None,
            "metadata": self._code_assist_metadata(configured_project if tier_id != "free-tier" else None),
        }

        lro_res = self._code_assist_post(client, headers, "onboardUser", onboard_payload)
        while not lro_res.get("done") and lro_res.get("name"):
            time.sleep(5)
            lro_res = self._code_assist_get_operation(client, headers, lro_res["name"])

        project_id = self._extract_operation_project(lro_res) or configured_project
        self._resolved_code_assist_project = project_id
        self._resolved_code_assist_project_loaded = True
        if not project_id:
            raise RuntimeError(self._code_assist_error_message(load_res))
        return project_id

    @staticmethod
    def _should_retry_without_project(resp) -> bool:
        """Retry without project when Gemini CLI personal auth hits invalid consumer errors."""
        if resp.status_code != 403:
            return False
        try:
            body = resp.json()
        except Exception:
            return False

        error = body.get("error", {})
        message = (error.get("message") or "").lower()
        details = error.get("details", []) or []
        for detail in details:
            if not isinstance(detail, dict):
                continue
            if detail.get("reason") == "CONSUMER_INVALID":
                return True
        return "permission denied on resource project" in message

    def _chat_rest(
        self,
        messages: List[Dict],
        system: str = "",
        tools: Optional[List[Dict]] = None,
        max_tokens: int = 8192,
    ) -> LLMResponse:
        """Direct REST call for Gemini CLI OAuth tokens.

        The Gemini CLI uses cloudcode-pa.googleapis.com (Google Code Assist),
        not generativelanguage.googleapis.com. The cloud-platform scope token
        only works with this endpoint, using a wrapped request body.
        """
        import httpx

        data = json.loads(self.api_key)
        access_token = data["token"]
        project_id = data.get("projectId")
        url = "https://cloudcode-pa.googleapis.com/v1internal:generateContent"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        inner: Dict[str, Any] = {
            "contents": self._messages_to_gemini(messages),
            "generationConfig": {"maxOutputTokens": max_tokens},
        }
        if system:
            inner["systemInstruction"] = {"parts": [{"text": system}]}
        if tools:
            inner["tools"] = self._convert_tools_json(tools)

        # cloudcode-pa wraps the standard GenerateContentRequest. The Gemini CLI
        # includes the active project and a session_id for every request.
        payload: Dict[str, Any] = {
            "model": self.model,
            "user_prompt_id": str(uuid.uuid4()),
            "request": {
                **inner,
                "session_id": self._session_id,
            },
        }
        with httpx.Client(timeout=120.0) as client:
            project_id = self._resolve_code_assist_project(client, headers, project_id)
            if project_id:
                payload["project"] = project_id
            resp = client.post(url, json=payload, headers=headers)
            if project_id and self._should_retry_without_project(resp):
                retry_payload = dict(payload)
                retry_payload.pop("project", None)
                resp = client.post(url, json=retry_payload, headers=headers)
            if resp.status_code != 200:
                raise RuntimeError(f"Gemini OAuth API error: {resp.status_code} - {resp.text}")
            # Response may be wrapped: {"response": {...}} or direct GenerateContentResponse
            body = resp.json()
            return self._parse_rest_response(body.get("response", body))

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
                    "parts": [{"functionResponse": {
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
                        elif c.get("type") == "tool_use":
                            parts.append({
                                "functionCall": {
                                    "name": c["name"],
                                    "args": c.get("input", {}),
                                }
                            })
                        elif c.get("type") == "tool_result":
                            parts.append({
                                "functionResponse": {
                                    "name": c.get("name", "tool"),
                                    "response": {"result": c.get("content", "")},
                                }
                            })
                        elif "inline_data" in c:
                            parts.append({"inlineData": c["inline_data"]})
                        elif "inlineData" in c:
                            parts.append({"inlineData": c["inlineData"]})
                        elif "function_response" in c:
                            parts.append({"functionResponse": c["function_response"]})
                        elif "functionResponse" in c:
                            parts.append({"functionResponse": c["functionResponse"]})
                        elif "text" in c:
                            # Already in Gemini parts format (from chat_with_pdf)
                            parts.append(c)
                if parts:
                    result.append({"role": role, "parts": parts})
        return result

    def _parse_response(self, response) -> LLMResponse:
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
        if self._is_gemini_cli_token:
            return self._chat_rest(messages, system=system, tools=tools, max_tokens=max_tokens)
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
