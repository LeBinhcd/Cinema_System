"""Rule-based Vietnamese question analyzer for the cinema chatbot.

This module deliberately does not call Gemini or access the database. It converts
the user question into a conservative intent contract for a later retriever.
"""
from __future__ import annotations

import re
from datetime import date as date_type, datetime, timedelta, timezone
from typing import Optional
from zoneinfo import ZoneInfo


try:
    VIETNAM_TIMEZONE = ZoneInfo("Asia/Ho_Chi_Minh")
except KeyError:
    # Windows may lack the IANA database. Modern Vietnamese cinema dates use UTC+7.
    VIETNAM_TIMEZONE = timezone(timedelta(hours=7), name="Asia/Ho_Chi_Minh")

_GENRES = (
    ("Hoạt hình", ("hoạt hình", "hoat hinh", "animation", "animated")),
    ("Hành động", ("hành động", "hanh dong", "action")),
    ("Kinh dị", ("kinh dị", "kinh di", "horror")),
    ("Hài", ("hài", "hai", "comedy")),
    ("Tình cảm", ("tình cảm", "tinh cam", "romance", "romantic")),
    ("Khoa học viễn tưởng", ("khoa học viễn tưởng", "khoa hoc vien tuong", "sci-fi", "science fiction")),
    ("Phiêu lưu", ("phiêu lưu", "phieu luu", "adventure")),
    ("Tâm lý", ("tâm lý", "tam ly", "drama")),
)

_SEAT_TYPES = (
    ("VIP", ("ghế vip", "ghe vip", "vip")),
    ("COUPLE", ("ghế đôi", "ghe doi", "ghế couple", "ghe couple", "couple")),
    ("STANDARD", ("ghế thường", "ghe thuong", "ghế standard", "ghe standard", "standard")),
)

UNSAFE_MESSAGE = "Xin lỗi, tôi không thể thực hiện yêu cầu này."

_UNSAFE_TERMS = (
    "xóa database", "xoa database", "drop table", "delete from", "sql injection",
    "mật khẩu", "mat khau", "api key", "secret key", "password_hash",
    "bỏ qua phân quyền", "bo qua phan quyen", "vượt quyền", "vuot quyen",
    "sửa dữ liệu gốc", "sua du lieu goc", "xóa vé người khác", "xoa ve nguoi khac",
    "đọc database", "doc database", "truy cập database", "truy cap database",
    "prompt injection", "bỏ qua quy tắc", "bo qua quy tac",
)
_OUT_OF_SCOPE_TERMS = (

    "thời tiết", "thoi tiet", "chứng khoán", "chung khoan", "bóng đá", "bong da",
    "tin tức", "tin tuc", "lập trình", "lap trinh",
)


def _fold(value: str) -> str:
    """Lowercase and collapse whitespace without removing Vietnamese accents."""
    return " ".join(value.casefold().split())


def _contains(text: str, phrase: str) -> bool:
    return re.search(r"(?<!\w)" + re.escape(phrase) + r"(?!\w)", text) is not None


def _current_local_date(now: Optional[datetime]) -> date_type:
    if now is None:
        return datetime.now(VIETNAM_TIMEZONE).date()
    if now.tzinfo is None:
        return now.replace(tzinfo=VIETNAM_TIMEZONE).date()
    return now.astimezone(VIETNAM_TIMEZONE).date()


def _time_value(hour: str, minute: str = "00") -> str:
    return f"{int(hour):02d}:{int(minute):02d}"


def _extract_explicit_time(text: str) -> tuple[Optional[str], Optional[str]]:
    """Return the first explicit HH:MM/HHh time and its source position."""
    match = re.search(r"(?<!\d)([01]?\d|2[0-3])\s*(?::|h|giờ)\s*([0-5]\d)?", text)
    if not match:
        return None, None
    return _time_value(match.group(1), match.group(2) or "00"), match.group(0)


def _extract_movie_title(question: str, folded: str, genre: Optional[str]) -> Optional[str]:
    """Extract only an explicitly named title; never invent one."""
    patterns = (
        r"(?:phim|suất chiếu|suat chieu)\s+([^?!.;,]+?)(?=\s+(?:có|co|chiếu|chieu|lúc|luc|ngày|ngay|buổi|buoi|tối|toi|hôm|hom|sau|trước|truoc|ghế|ghe|còn|con|không|khong|nào|nao)\b|[?!.;,]|$)",
        r"(?:của|cua)\s+phim\s+([^?!.;,]+)",
    )
    for pattern in patterns:
        match = re.search(pattern, question, flags=re.IGNORECASE)
        if not match:
            continue
        title = " ".join(match.group(1).strip().split())
        if genre and any(_contains(_fold(title), variant) for normalized, variants in _GENRES
                         if normalized == genre for variant in variants):
            return None
        if title and _fold(title) not in {"gì", "gi", "nào", "nao", "này", "nay", "gì đang được", "gi dang duoc"} and not any(_contains(_fold(title), word) for word in ("đang được", "dang duoc", "đang chiếu", "dang chieu")):
            return title
    return None


def _extract_keywords(question: str, genre: Optional[str], movie_title: Optional[str]) -> list[str]:
    """Return explicit search terms, excluding control words and extracted fields."""
    stop_words = {
        "có", "co", "phim", "nào", "nao", "gì", "gi", "hay", "không", "khong", "cho", "tôi", "toi",
        "mình", "minh", "xin", "hỏi", "hoi", "suất", "suat", "chiếu", "chieu", "tối", "toi", "nay",
        "hôm", "hom", "ngày", "ngay", "mai", "sau", "trước", "truoc", "lúc", "luc", "buổi", "buoi",
        "ghế", "ghe", "còn", "con", "bao", "nhiêu", "nhieu", "giá", "gia", "vé", "ve", "hủy", "huy",
        "đang", "duoc", "được", "chiếu", "chieu", "trình", "trinh", "chiếu", "showing",
    }
    result: list[str] = []
    for token in re.findall(r"[\wÀ-ỹ-]+", question, flags=re.UNICODE):
        folded = token.casefold()
        if folded in stop_words or folded.isdigit() or re.fullmatch(r"\d+h\d*", folded) or len(token) < 2:
            continue
        if genre and folded in _fold(genre).split():
            continue
        if movie_title and folded in _fold(movie_title).split():
            continue
        if token not in result:
            result.append(token)
    return result


class QuestionAnalyzer:
    """Analyze one Vietnamese cinema question into a JSON-serializable dict."""

    @staticmethod
    def analyze(question: str, now: Optional[datetime] = None) -> dict:
        if not isinstance(question, str) or not question.strip():
            return QuestionAnalyzer._empty("UNKNOWN")

        original = " ".join(question.strip().split())
        text = _fold(original)
        today = _current_local_date(now)
        result = QuestionAnalyzer._empty()

        if any(term in text for term in _UNSAFE_TERMS):
            result["intent"] = "UNSAFE"
            return result

        if any(term in text for term in _OUT_OF_SCOPE_TERMS):
            result["intent"] = "UNKNOWN"
            result["keywords"] = _extract_keywords(original, None, None)
            return result

        for normalized, variants in _GENRES:
            if any(_contains(text, variant) for variant in variants):
                result["genre"] = normalized
                break

        for normalized, variants in _SEAT_TYPES:
            if any(_contains(text, variant) for variant in variants):
                result["seat_type"] = normalized
                break

        if _contains(text, "hôm nay") or _contains(text, "hom nay"):
            result["date"] = today.isoformat()
        elif _contains(text, "ngày mai") or _contains(text, "ngay mai"):
            result["date"] = (today + timedelta(days=1)).isoformat()

        explicit_time, _ = _extract_explicit_time(text)
        if explicit_time:
            result["min_time"] = explicit_time if any(word in text for word in ("sau", "từ", "tu")) else None
            result["max_time"] = explicit_time if any(word in text for word in ("trước", "truoc", "đến", "den")) else None
            if result["min_time"] is None and result["max_time"] is None:
                result["min_time"] = explicit_time

        if _contains(text, "tối nay") or _contains(text, "toi nay"):
            result["date"] = today.isoformat()
            result["time_of_day"] = "EVENING"
            result["min_time"] = result["min_time"] or "18:00"
        elif _contains(text, "buổi sáng") or _contains(text, "buoi sang"):
            result["time_of_day"] = "MORNING"
            result["min_time"] = max(result["min_time"] or "08:00", "08:00")
            result["max_time"] = min(result["max_time"] or "11:59", "11:59")
        elif _contains(text, "buổi chiều") or _contains(text, "buoi chieu"):
            result["time_of_day"] = "AFTERNOON"
            result["min_time"] = max(result["min_time"] or "12:00", "12:00")
            result["max_time"] = min(result["max_time"] or "17:59", "17:59")
        elif _contains(text, "buổi tối") or _contains(text, "buoi toi"):
            result["time_of_day"] = "EVENING"
            result["min_time"] = result["min_time"] or "18:00"

        result["price_inquiry"] = bool(re.search(r"\b(?:giá|gia|bao nhiêu tiền|bao nhieu tien)\b", text))
        result["policy_inquiry"] = any(term in text for term in ("hủy vé", "huy ve", "hoàn tiền", "hoan tien", "chính sách", "chinh sach"))

        result["movie_title"] = _extract_movie_title(original, text, result["genre"])
        result["keywords"] = _extract_keywords(original, result["genre"], result["movie_title"])

        if result["price_inquiry"]:
            result["intent"] = "ask_price"
        elif result["policy_inquiry"]:
            result["intent"] = "ask_policy"
        elif result["seat_type"] and any(term in text for term in ("ghế", "ghe", "còn", "con", "trống", "trong")):
            result["intent"] = "check_seats"
        elif any(_contains(text, term) for term in ("phim", "suất chiếu", "suat chieu", "rạp", "rap")):
            result["intent"] = "recommend_movie" if any(_contains(text, term) for term in ("nào", "nao", "gì", "gi", "gợi ý", "goi y", "hay")) else "search_screenings"
        else:
            result["intent"] = "AMBIGUOUS"

        if result["min_time"] and result["max_time"] and result["min_time"] > result["max_time"]:
            result["intent"] = "AMBIGUOUS"
        return result

    @staticmethod
    def _empty(intent: str = "AMBIGUOUS") -> dict:
        return {
            "intent": intent,
            "movie_title": None,
            "genre": None,
            "date": None,
            "min_time": None,
            "max_time": None,
            "time_of_day": None,
            "seat_type": None,
            "price_inquiry": False,
            "policy_inquiry": False,
            "keywords": [],
        }


def analyze_question(question: str, now: Optional[datetime] = None) -> dict:
    """Convenience function for application services and future route integration."""
    return QuestionAnalyzer.analyze(question, now=now)
