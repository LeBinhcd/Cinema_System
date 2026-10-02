"""Orchestrate the read-only cinema RAG flow."""
from __future__ import annotations

from collections.abc import Mapping

from app.services import context_builder, gemini_service, prompt_builder, question_analyzer, screening_retriever


def _card_from_screening(screening: Mapping) -> dict:
    """Create a client card only from validated retrieval facts."""
    screening_id = screening["screening_id"]
    if type(screening_id) is not int or screening_id <= 0:
        raise ValueError("Invalid screening_id returned by retrieval")
    seats = screening.get("available_seats")
    if not isinstance(seats, Mapping):
        raise ValueError("Invalid seat availability returned by retrieval")
    return {
        "screening_id": screening_id,
        "movie_title": screening["movie_title"],
        "room_name": screening["room_name"],
        "start_time": screening["start_time"],
        "seats_available": dict(seats),
        "booking_url": f"/booking/{screening_id}",
    }


def process_chat(user_question: str) -> dict:
    """Run analyzer -> retrieval -> context -> prompt -> Claude -> cards."""
    if not isinstance(user_question, str) or not user_question.strip():
        raise ValueError("user_question must be a non-empty string")

    intent = question_analyzer.analyze_question(user_question)
    screenings = screening_retriever.retrieve_screenings(intent)
    context = context_builder.build_context(screenings, intent)
    prompt = prompt_builder.build_prompt(context, user_question)
    answer = gemini_service.generate_response(prompt)
    cards = [_card_from_screening(screening) for screening in screenings]
    return {"answer": answer, "cards": cards}