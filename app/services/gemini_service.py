"""Server-side Groq gateway kept behind the historic Gemini interface."""
from __future__ import annotations

import os
import math
import logging
from typing import Any, Optional


GROQ_TIMEOUT_SECONDS = 15
GEMINI_TIMEOUT_SECONDS = GROQ_TIMEOUT_SECONDS  # Compatibility for old imports.
DEFAULT_GROQ_MODEL = "llama-3.1-8b-instant"
logger = logging.getLogger(__name__)
API_ERROR_MESSAGE = "Xin lỗi, hiện chưa thể xử lý yêu cầu. Vui lòng thử lại sau."
CONFIG_ERROR_MESSAGE = "Xin lỗi, dịch vụ tư vấn hiện chưa được cấu hình. Vui lòng thử lại sau."

# Lazy imports keep application startup and unit tests independent of the SDK.
groq = None


def _get_sdk():
    global groq
    if groq is None:
        import groq as imported_groq
        groq = imported_groq
    return groq


def _text_from_groq_response(response: Any) -> str:
    choices = getattr(response, "choices", None)
    if not isinstance(choices, (list, tuple)) or not choices:
        raise ValueError("Groq returned no choices")
    message = getattr(choices[0], "message", None)
    text = getattr(message, "content", None)
    if not isinstance(text, str) or not text.strip():
        raise ValueError("Groq returned empty content")
    return text.strip()


class GeminiService:
    """Groq implementation preserving the existing provider interface."""

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None,
                 timeout: int = GROQ_TIMEOUT_SECONDS):
        self.api_key = api_key if api_key is not None else os.getenv("GROQ_API_KEY", "")
        self.model_name = model_name if model_name is not None else os.getenv("GROQ_MODEL", DEFAULT_GROQ_MODEL)
        if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not math.isfinite(timeout) or timeout <= 0:
            raise ValueError("timeout must be positive")
        self.timeout = min(timeout, GROQ_TIMEOUT_SECONDS)

    def generate_response(self, prompt: str) -> str:
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("prompt must be a non-empty string")
        if not self.api_key:
            return CONFIG_ERROR_MESSAGE
        if not self.model_name:
            return CONFIG_ERROR_MESSAGE
        try:
            sdk = _get_sdk()
            client = sdk.Groq(api_key=self.api_key, timeout=self.timeout, max_retries=0)
            response = client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=800,
            )
            return _text_from_groq_response(response)
        except Exception as error:
            safe_detail = str(error).replace(self.api_key, "<GROQ_API_KEY_REDACTED>")
            # Provider exceptions can echo request content; do not leak prompts.
            safe_detail = safe_detail.replace(prompt, "<PROMPT_REDACTED>")
            logger.error("[GROQ ERROR DETAIL]: %s - %s", type(error).__name__, safe_detail)
            return API_ERROR_MESSAGE

    def generate(self, prompt: str) -> str:
        """Short alias for integrations that call the service as a generator."""
        return self.generate_response(prompt)


def generate_response(prompt: str) -> str:
    """Use environment configuration to generate one safe response."""
    return GeminiService().generate_response(prompt)