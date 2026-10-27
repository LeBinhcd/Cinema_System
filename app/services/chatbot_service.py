"""Orchestrate the read-only cinema RAG flow."""
from __future__ import annotations
from collections.abc import Mapping
import re
from app.services import context_builder, gemini_service, prompt_builder, question_analyzer, screening_retriever

def _card_from_screening(screening: Mapping) -> dict:
    sid = screening["screening_id"]
    if type(sid) is not int or sid <= 0: raise ValueError("Invalid screening_id returned by retrieval")
    seats = screening.get("available_seats")
    if not isinstance(seats, Mapping): raise ValueError("Invalid seat availability returned by retrieval")
    return {"screening_id": sid, "movie_title": screening["movie_title"], "room_name": screening["room_name"], "start_time": screening["start_time"], "seats_available": dict(seats), "booking_url": f"/booking/{sid}"}

def _is_movie_list_request(intent): return intent.get("intent") == "recommend_movie" and not intent.get("movie_title")
def _unique(rows):
    seen=set(); out=[]
    for row in rows:
        key=row.get("movie_id") or row.get("movie_title")
        if key not in seen: seen.add(key); out.append(row)
    return out

def _movie_list_answer(rows):
    rows=_unique(rows)
    if not rows: return "Hiện chưa có phim nào phù hợp trong lịch chiếu. Bạn thử chọn ngày hoặc khung giờ khác nhé."
    return f"Hôm nay rạp đang có {len(rows)} phim: {', '.join(row['movie_title'] for row in rows)}. Bạn có thể chọn suất chiếu bên dưới để đặt vé."

def _fallback(rows):
    if not rows: return "Hiện chưa có suất chiếu phù hợp với yêu cầu của bạn. Bạn thử chọn ngày hoặc khung giờ khác nhé."
    return "Mình tìm thấy: " + "; ".join(f"{r['movie_title']} tại {r['room_name']} lúc {r['start_time']} (còn {sum(r['available_seats'].values())} ghế)" for r in rows) + ". Bạn có thể chọn một suất để đặt vé."

def _grounded(answer, rows):
    if not isinstance(answer,str) or not answer.strip() or answer in (gemini_service.API_ERROR_MESSAGE, gemini_service.CONFIG_ERROR_MESSAGE): return False
    if not rows:
        return ('chưa có suất chiếu' in answer.casefold() or 'không có suất chiếu' in answer.casefold())
    if re.search(r"\b\d[\d.,]*\s*(?:vnđ|đ|đồng)\b", answer.casefold()): return False
    known=' '.join(f"{r['movie_title']} {r['room_name']} {r['start_time']} {r['end_time']}" for r in rows).casefold()
    return all(x.strip() in known for x in re.findall(r"(?:phòng|room)\s+[A-Za-zÀ-ỹ0-9 -]+", answer.casefold()))

def _compact_context(screenings: list[dict], intent: Mapping) -> list[dict]:
    """Send only facts relevant to the question; cards remain full backend data."""
    if intent.get("intent") == "recommend_movie" and not intent.get("movie_title"):
        seen = set(); compact = []
        for row in screenings:
            key = row.get("movie_id") or row.get("movie_title")
            if key not in seen:
                seen.add(key)
                compact.append({"screening_id": row["screening_id"], "movie_id": row.get("movie_id"), "movie_title": row["movie_title"]})
        return compact
    return screenings
def process_chat(user_question: str) -> dict:
    if not isinstance(user_question, str) or not user_question.strip():
        raise ValueError("user_question must be a non-empty string")
    intent = question_analyzer.analyze_question(user_question)
    if intent.get("intent") == "UNSAFE":
        return {"answer": question_analyzer.UNSAFE_MESSAGE, "cards": []}
    if intent.get("intent") == "UNKNOWN":
        return {"answer": "Xin lỗi, tôi chỉ hỗ trợ thông tin về phim, suất chiếu, ghế và chính sách của rạp.", "cards": []}
    rows = screening_retriever.retrieve_screenings(intent)
    context = context_builder.build_context(_compact_context(rows, intent), intent)
    prompt = prompt_builder.build_prompt(context, user_question)
    try:
        answer = gemini_service.generate_response(prompt)
    except Exception:
        answer = ""
    if intent.get("intent") == "recommend_movie" and not intent.get("movie_title"):
        answer = _movie_list_answer(rows)
    elif not _grounded(answer, rows):
        answer = _fallback(rows)
    return {"answer": answer, "cards": [_card_from_screening(row) for row in rows]}
