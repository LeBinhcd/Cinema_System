"""Smoke-test the Groq connection without exposing the full API key."""
import os
import traceback

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))
key = os.getenv("GROQ_API_KEY", "")
model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
print(f"GROQ_API_KEY loaded: {key[:6] + '...' if key else 'NO KEY'}")

try:
    if not key or key.startswith("your-"):
        raise RuntimeError("GROQ_API_KEY is missing or still a placeholder")
    from groq import Groq
    client = Groq(api_key=key, timeout=15, max_retries=0)
    result = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": "Xin chào, bạn là ai?"}],
        temperature=0.3,
        max_tokens=100,
    )
    print("SUCCESS: Groq response received")
    print(result.choices[0].message.content)
except Exception as error:
    detail = str(error).replace(key, "<GROQ_API_KEY_REDACTED>") if key else str(error)
    print(f"GROQ ERROR: {type(error).__name__} - {detail}")
    traceback.print_exc()