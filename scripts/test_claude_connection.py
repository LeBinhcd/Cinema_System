"""Manual live Groq smoke test; imports do not make network requests."""
from pathlib import Path
import logging
import sys

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.services.gemini_service import GeminiService, API_ERROR_MESSAGE, CONFIG_ERROR_MESSAGE


def main() -> int:
    load_dotenv(ROOT / ".env")
    logging.basicConfig(level=logging.ERROR)
    service = GeminiService()
    if not service.api_key.strip() or service.api_key.startswith("your-"):
        print("FAIL: Chưa đặt GROQ_API_KEY thật trong .env phía server.")
        return 1
    print(f"Testing Groq model={service.model_name}; timeout={service.timeout}s")
    answer = service.generate_response("Xin chào, bạn là ai?")
    if answer in {API_ERROR_MESSAGE, CONFIG_ERROR_MESSAGE}:
        print(f"FAIL: {answer} Xem loại lỗi và mã HTTP trong log.")
        return 1
    print("PASS: Groq API đã phản hồi.")
    print(answer)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())