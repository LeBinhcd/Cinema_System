"""Question-analysis skill contract tests; no Gemini or database required."""
from datetime import datetime

import pytest

from app.services.question_analyzer import analyze_question


NOW = datetime.fromisoformat("2026-09-30T10:00:00+07:00")


def test_required_example():
    assert analyze_question("Tối nay có phim hoạt hình nào sau 19h không?", NOW) == {
        "intent": "recommend_movie", "movie_title": None, "genre": "Hoạt hình",
        "date": "2026-09-30", "min_time": "19:00", "max_time": None,
        "time_of_day": "EVENING", "seat_type": None, "price_inquiry": False,
        "policy_inquiry": False, "keywords": [],
    }


@pytest.mark.parametrize("question,field,expected", [
    ("Hôm nay có phim gì?", "date", "2026-09-30"),
    ("Ngày mai có phim gì?", "date", "2026-10-01"),
    ("Phim nào buổi sáng?", "min_time", "08:00"),
    ("Phim nào buổi sáng?", "max_time", "11:59"),
    ("Phim nào buổi chiều?", "max_time", "17:59"),
    ("Phim nào buổi tối?", "time_of_day", "EVENING"),
    ("Phim nào sau 19h30?", "min_time", "19:30"),
    ("Phim nào trước 20:30?", "max_time", "20:30"),
    ("Phim Conan tối nay còn ghế VIP không?", "movie_title", "Conan"),
    ("Còn ghế VIP không?", "seat_type", "VIP"),
    ("Còn ghế đôi không?", "seat_type", "COUPLE"),
    ("Còn ghế thường không?", "seat_type", "STANDARD"),
    ("Giá vé bao nhiêu?", "price_inquiry", True),
    ("Hủy vé được hoàn tiền không?", "policy_inquiry", True),
    ("", "intent", "UNKNOWN"),
    ("Thời tiết hôm nay thế nào?", "intent", "UNKNOWN"),
    ("Cho tôi biết thêm đi.", "intent", "AMBIGUOUS"),
    ("Phim nào?", "movie_title", None),
    ("Phim nào?", "genre", None),
    ("Phim nào?", "date", None),
    ("Phim nào?", "min_time", None),
    ("Phim nào buổi sáng sau 10h?", "min_time", "10:00"),
    ("Phim nào buổi sáng sau 19h?", "intent", "AMBIGUOUS"),
])
def test_skill_rules(question, field, expected):
    assert analyze_question(question, NOW)[field] == expected


def test_timezone_conversion():
    utc_now = datetime.fromisoformat("2026-09-30T20:00:00+00:00")
    assert analyze_question("Hôm nay có phim gì?", utc_now)["date"] == "2026-10-01"


def test_word_boundaries():
    assert analyze_question("Phim Shanghai chiếu lúc nào?", NOW)["genre"] is None


def test_json_serializable():
    import json
    result = analyze_question("Phim nào?", NOW)
    assert json.loads(json.dumps(result, ensure_ascii=False)) == result