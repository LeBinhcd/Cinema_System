from types import SimpleNamespace

import pytest

import app.services.gemini_service as module
from app.services.gemini_service import (
    API_ERROR_MESSAGE,
    CONFIG_ERROR_MESSAGE,
    GeminiService,
    generate_response,
)


class FakeModel:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return self.response


class FakeSDK:
    def __init__(self, model):
        self.model = model
        self.chat = SimpleNamespace(completions=model)
        self.options = None

    def Groq(self, **kwargs):
        self.options = kwargs
        return self



@pytest.fixture(autouse=True)
def mocked_sdk(monkeypatch):
    monkeypatch.setattr(module, "groq", None)


def response_text(text):
    return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=text))])


def test_success_uses_env_key_model_and_fifteen_second_timeout(monkeypatch):
    fake_model = FakeModel(response_text("  Có suất chiếu.  "))
    sdk = FakeSDK(fake_model)
    monkeypatch.setattr(module, "groq", sdk)
    service = GeminiService(api_key="test-key", model_name="test-model", timeout=30)

    assert service.generate_response("prompt") == "Có suất chiếu."
    assert sdk.options == {"api_key": "test-key", "timeout": 15, "max_retries": 0}
    assert fake_model.calls == [{"model": "test-model", "messages": [{"role": "user", "content": "prompt"}],
                                 "temperature": 0.3, "max_tokens": 800}]


def test_missing_key_returns_safe_message(monkeypatch):
    monkeypatch.setattr(module, "groq", None)
    assert GeminiService(api_key="").generate_response("prompt") == CONFIG_ERROR_MESSAGE


@pytest.mark.parametrize("error", [TimeoutError(), RuntimeError("quota exceeded"), ConnectionError()])
def test_provider_errors_are_safe(monkeypatch, error):
    sdk = FakeSDK(FakeModel(error=error))
    monkeypatch.setattr(module, "groq", sdk)
    assert GeminiService(api_key="secret-key").generate_response("prompt") == API_ERROR_MESSAGE


def test_empty_provider_response_is_safe(monkeypatch):
    monkeypatch.setattr(module, "groq", FakeSDK(FakeModel(response_text("  "))))
    assert GeminiService(api_key="secret-key").generate_response("prompt") == API_ERROR_MESSAGE


@pytest.mark.parametrize("prompt", [None, "", "   "])
def test_invalid_prompt_fails_before_provider_call(prompt):
    with pytest.raises(ValueError):
        GeminiService(api_key="secret-key").generate_response(prompt)


def test_function_wrapper_uses_environment(monkeypatch):
    fake_model = FakeModel(response_text("Được rồi."))
    sdk = FakeSDK(fake_model)
    monkeypatch.setattr(module, "groq", sdk)
    monkeypatch.setenv("GROQ_API_KEY", "environment-key")
    monkeypatch.setenv("GROQ_MODEL", "environment-model")
    assert generate_response("prompt") == "Được rồi."
    assert sdk.options["api_key"] == "environment-key"
    assert fake_model.calls[0]["model"] == "environment-model"


@pytest.mark.parametrize("timeout", [0, -1, None, True, "8", float("nan"), float("inf")])
def test_invalid_timeout(timeout):
    with pytest.raises(ValueError):
        GeminiService(timeout=timeout)


def test_smaller_timeout_and_alias(monkeypatch):
    model = FakeModel(response_text("Xin chào."))
    sdk = FakeSDK(model)
    monkeypatch.setattr(module, "groq", sdk)
    assert GeminiService(api_key="test", timeout=3).generate("prompt") == "Xin chào."
    assert sdk.options["timeout"] == 3
    assert sdk.options["max_retries"] == 0


@pytest.mark.parametrize("response", [None, object(), SimpleNamespace(text=123)])
def test_malformed_response_is_safe(monkeypatch, response):
    monkeypatch.setattr(module, "groq", FakeSDK(FakeModel(response)))
    assert GeminiService(api_key="test").generate_response("prompt") == API_ERROR_MESSAGE


def test_provider_exception_details_never_leak(monkeypatch, caplog):
    details = "secret-key private prompt payment data"
    monkeypatch.setattr(module, "groq", FakeSDK(FakeModel(error=RuntimeError(details))))
    result = GeminiService(api_key="secret-key").generate_response("private prompt")
    assert result == API_ERROR_MESSAGE
    assert details not in caplog.text


def test_missing_model_does_not_call_sdk(monkeypatch):
    monkeypatch.setattr(module, "_get_sdk", lambda: pytest.fail("SDK must not be called"))
    assert GeminiService(api_key="test", model_name="").generate_response("prompt") == CONFIG_ERROR_MESSAGE


def test_sdk_initialization_error_is_safe(monkeypatch):
    def broken_sdk():
        raise ImportError("SDK unavailable")
    monkeypatch.setattr(module, "_get_sdk", broken_sdk)
    assert GeminiService(api_key="test").generate_response("prompt") == API_ERROR_MESSAGE


def test_default_model_and_no_gemini_key_fallback(monkeypatch):
    monkeypatch.delenv("GROQ_MODEL", raising=False)
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.setenv("GEMINI_API_KEY", "expired-key")
    monkeypatch.setattr(module, "_get_sdk", lambda: pytest.fail("No provider should be called"))
    assert GeminiService().model_name == "llama-3.1-8b-instant"
    assert generate_response("prompt") == CONFIG_ERROR_MESSAGE


def test_multiple_text_blocks(monkeypatch):
    response = response_text("Có phim. Mời bạn chọn suất.")
    monkeypatch.setattr(module, "groq", FakeSDK(FakeModel(response)))
    assert GeminiService(api_key="test").generate_response("prompt") == "Có phim. Mời bạn chọn suất."


@pytest.mark.parametrize("error_name", ["AuthenticationError", "RateLimitError", "APIConnectionError"])
def test_groq_exceptions_are_logged_safely(monkeypatch, caplog, error_name):
    import groq
    import httpx
    request = httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions")
    if error_name == "APIConnectionError":
        error = groq.APIConnectionError(request=request, message="secret-key private prompt")
    else:
        response = httpx.Response(401 if error_name == "AuthenticationError" else 429, request=request)
        error = getattr(groq, error_name)("secret-key private prompt", response=response, body=None)
    monkeypatch.setattr(module, "groq", FakeSDK(FakeModel(error=error)))
    assert GeminiService(api_key="secret-key").generate_response("private prompt") == API_ERROR_MESSAGE
    assert "[GROQ ERROR DETAIL]" in caplog.text
    assert error_name in caplog.text
    assert "secret-key" not in caplog.text
    assert "private prompt" not in caplog.text