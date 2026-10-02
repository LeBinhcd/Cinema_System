"""Direct Groq diagnostic request (does not use the application gateway)."""
from __future__ import annotations

import json
import os
import traceback
from pathlib import Path

from groq import Groq
from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[1]
MODEL = "llama-3.1-8b-instant"


def _redact(value, secret: str):
    """Keep diagnostics useful without echoing the credential."""
    text = str(value)
    if secret:
        text = text.replace(secret, "<API_KEY_REDACTED>")
    return text


def main() -> int:
    load_dotenv(ROOT / ".env", override=False)
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    masked_prefix = "<hidden>" if api_key else "<missing>"
    print(f"GROQ_API_KEY loaded: {'yes' if api_key else 'no'}")
    print(f"API key length: {len(api_key)}; first 6 characters: {masked_prefix}")
    print(f"Model: {MODEL}")
    print("Request: messages=[{'role': 'user', 'content': 'Xin chào'}]")

    if not api_key or api_key.startswith("your-"):
        print("ERROR: GROQ_API_KEY is missing or still a placeholder.")
        return 1

    try:
        client = Groq(api_key=api_key, timeout=15, max_retries=0)
        response = client.chat.completions.create(
            model=MODEL,
            max_tokens=800,
            temperature=0.3,
            messages=[{"role": "user", "content": "Xin chào"}],
        )
        print("SUCCESS: Groq response received")
        print(response)
        return 0
    except Exception as error:
        print("ERROR: Groq request failed")
        print(f"Exception type: {type(error).__name__}")
        print(f"Status code: {getattr(error, 'status_code', None)}")
        body = getattr(error, "body", None)
        if body is not None:
            try:
                body = json.dumps(body, ensure_ascii=False, default=str)
            except Exception:
                body = str(body)
        else:
            body = getattr(getattr(error, "response", None), "text", None)
        print(f"Error body: {_redact(body, api_key)}")
        print("Full traceback:")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())