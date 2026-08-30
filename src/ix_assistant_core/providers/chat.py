from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Protocol

from ix_assistant_core.response import ResponseComposer


class ChatProviderError(RuntimeError):
    """Raised when an optional external chat provider fails safely."""


class ChatProvider(Protocol):
    def reply(self, *, user_text: str, system_context: str = "") -> str:
        raise NotImplementedError


@dataclass(slots=True)
class OfflineChatProvider:
    """No-key deterministic responder used by default."""

    composer: ResponseComposer

    def reply(self, *, user_text: str, system_context: str = "") -> str:
        del system_context
        return self.composer.capabilities() if user_text.strip() else "Please say or type a request."


@dataclass(slots=True)
class OpenAICompatibleChatProvider:
    """HTTP client for user-supplied OpenAI-compatible chat-completions endpoints.

    The endpoint, key, and model are read from environment variables so no secret
    is stored in the repository or browser UI.
    """

    endpoint_env: str = "IX_GABRIELLA_CHAT_ENDPOINT"
    api_key_env: str = "IX_GABRIELLA_CHAT_API_KEY"
    model_env: str = "IX_GABRIELLA_CHAT_MODEL"
    timeout_seconds: float = 30.0

    def reply(self, *, user_text: str, system_context: str = "") -> str:
        endpoint = os.environ.get(self.endpoint_env, "").strip()
        api_key = os.environ.get(self.api_key_env, "").strip()
        model = os.environ.get(self.model_env, "").strip()
        if not endpoint or not model:
            raise ChatProviderError("chat endpoint and model must be configured")
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": system_context
                    or "You are Gabriella, a governed assistant that asks before it acts.",
                },
                {"role": "user", "content": user_text},
            ],
            "temperature": 0.2,
        }
        data = json.dumps(payload).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        request = urllib.request.Request(endpoint, data=data, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                raw = response.read().decode("utf-8")
        except urllib.error.URLError as exc:
            raise ChatProviderError(f"chat provider request failed: {exc}") from exc
        try:
            decoded = json.loads(raw)
            content = decoded["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
            raise ChatProviderError("chat provider returned an unsupported response shape") from exc
        clean = " ".join(str(content).strip().split())
        if not clean:
            raise ChatProviderError("chat provider returned an empty response")
        return clean
