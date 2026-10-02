from copy import deepcopy

import pytest

from app.services import chatbot_service


SCREENINGS = [{
    "screening_id": 12,
    "movie_title": "Hoạt Hình Sao Mai",
    "room_name": "Phòng A",
    "start_time": "2026-09-30 19:00:00",
    "end_time": "2026-09-30 20:40:00",
    "available_seats": {"STANDARD": 2, "VIP": 1, "COUPLE": 0},
}]


@pytest.fixture
def client(app):
    client = app.test_client()
    with client.session_transaction() as session:
        session["csrf_token"] = "chat-test-token"
    client.environ_base["HTTP_X_CSRF_TOKEN"] = "chat-test-token"
    return client


@pytest.fixture
def mocked_rag(monkeypatch):
    calls = {}
    screenings = deepcopy(SCREENINGS)

    def analyze(question):
        calls["question"] = question
        return {"intent": "search_screenings", "date": "2026-09-30"}

    def retrieve(intent):
        calls["intent"] = intent
        return screenings

    def build_context(rows, intent):
        calls["context_rows"] = rows
        return "CONTEXT TEST"

    def build_prompt(context, question):
        calls["prompt_args"] = (context, question)
        return "PROMPT TEST"

    def generate(prompt):
        calls["prompt"] = prompt
        return "Có suất chiếu phù hợp."

    monkeypatch.setattr(chatbot_service.question_analyzer, "analyze_question", analyze)
    monkeypatch.setattr(chatbot_service.screening_retriever, "retrieve_screenings", retrieve)
    monkeypatch.setattr(chatbot_service.context_builder, "build_context", build_context)
    monkeypatch.setattr(chatbot_service.prompt_builder, "build_prompt", build_prompt)
    monkeypatch.setattr(chatbot_service.gemini_service, "generate_response", generate)
    return calls


def test_valid_question_runs_full_rag_and_returns_backend_cards(client, mocked_rag):
    response = client.post("/api/chat", json={"question": "Tối nay có phim gì?"})

    assert response.status_code == 200
    assert response.json == {
        "answer": "Có suất chiếu phù hợp.",
        "cards": [{
            "screening_id": 12,
            "movie_title": "Hoạt Hình Sao Mai",
            "room_name": "Phòng A",
            "start_time": "2026-09-30 19:00:00",
            "seats_available": {"STANDARD": 2, "VIP": 1, "COUPLE": 0},
            "booking_url": "/booking/12",
        }],
    }
    assert mocked_rag["question"] == "Tối nay có phim gì?"
    assert mocked_rag["prompt_args"] == ("CONTEXT TEST", "Tối nay có phim gì?")
    assert mocked_rag["prompt"] == "PROMPT TEST"


@pytest.mark.parametrize("payload", [{}, {"question": ""}, {"question": "   "}, {"question": "x" * 301}])
def test_invalid_question_is_rejected(client, payload):
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 400
    assert "error" in response.json


def test_non_json_body_is_rejected(client):
    response = client.post("/api/chat", data="question=test", content_type="text/plain")
    assert response.status_code == 400


def test_no_results_returns_empty_cards(client, monkeypatch):
    monkeypatch.setattr(chatbot_service.question_analyzer, "analyze_question", lambda question: {})
    monkeypatch.setattr(chatbot_service.screening_retriever, "retrieve_screenings", lambda intent: [])
    monkeypatch.setattr(chatbot_service.context_builder, "build_context", lambda rows, intent: "EMPTY CONTEXT")
    monkeypatch.setattr(chatbot_service.prompt_builder, "build_prompt", lambda context, question: "PROMPT")
    monkeypatch.setattr(chatbot_service.gemini_service, "generate_response", lambda prompt: "Hiện chưa có suất chiếu phù hợp.")

    response = client.post("/api/chat", json={"question": "Phim không tồn tại"})

    assert response.status_code == 200
    assert response.json["cards"] == []
    assert response.json["answer"] == "Hiện chưa có suất chiếu phù hợp."


def test_gemini_failure_is_safe_500(client, mocked_rag, monkeypatch):
    monkeypatch.setattr(chatbot_service.gemini_service, "generate_response", lambda prompt: (_ for _ in ()).throw(RuntimeError("API key SECRET")))

    response = client.post("/api/chat", json={"question": "Có phim nào?"})

    assert response.status_code == 500
    assert response.json == {"error": "Xin lỗi, hệ thống tư vấn hiện chưa thể xử lý yêu cầu. Vui lòng thử lại sau."}
    assert "SECRET" not in response.get_data(as_text=True)


def test_cards_are_not_changed_by_answer(client, mocked_rag, monkeypatch):
    monkeypatch.setattr(chatbot_service.gemini_service, "generate_response", lambda prompt: "Phòng B, giá 999999")
    response = client.post("/api/chat", json={"question": "Có phim nào?"})
    assert response.json["cards"][0]["room_name"] == "Phòng A"
    assert response.json["cards"][0]["booking_url"] == "/booking/12"


def test_gemini_error_fallback_returns_200(client, mocked_rag, monkeypatch):
    fallback = chatbot_service.gemini_service.API_ERROR_MESSAGE
    monkeypatch.setattr(chatbot_service.gemini_service, "generate_response", lambda prompt: fallback)
    response = client.post("/api/chat", json={"question": "Có phim nào?"})
    assert response.status_code == 200
    assert response.json["answer"] == fallback
    assert response.json["cards"][0]["screening_id"] == 12


def test_csrf_required(client):
    response = client.post("/api/chat", json={"question": "Có phim nào?"}, headers={"X-CSRF-Token": "wrong"})
    assert response.status_code == 403


def test_length_300_is_accepted(client, mocked_rag):
    assert client.post("/api/chat", json={"question": "x" * 300}).status_code == 200


@pytest.mark.parametrize("payload", [[], {"question": None}, {"question": 123}, {"question": True}])
def test_wrong_json_types(client, payload):
    assert client.post("/api/chat", json=payload).status_code == 400


def test_real_pipeline_with_mock_anthropic(client, app, monkeypatch):
    from app.database import get_connection

    with app.app_context():
        db = get_connection()
        db.executescript("""
            INSERT INTO movies(id,title,duration_minutes,status) VALUES(12,'Sao Mai',100,'NOW_SHOWING');
            INSERT INTO screening_rooms(id,name,row_count,column_count,status) VALUES(12,'Phòng A',1,1,'ACTIVE');
            INSERT INTO seats(id,room_id,row_label,seat_number,seat_type) VALUES(12,12,'A',1,'VIP');
            INSERT INTO screenings(id,movie_id,room_id,start_time,end_time)
            VALUES(12,12,12,'2099-09-30 19:00:00','2099-09-30 20:40:00');
        """)
        db.commit()
        db.close()

    from types import SimpleNamespace
    from unittest.mock import MagicMock

    def create(**kwargs):
        prompt = kwargs["messages"][0]["content"]
        assert "Sao Mai" in prompt
        assert "VIP=1" in prompt
        assert kwargs["max_tokens"] == 800
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="Có phim Sao Mai."))])

    sdk = MagicMock()
    sdk.Groq.return_value.chat.completions.create.side_effect = create
    monkeypatch.setattr(chatbot_service.gemini_service, "groq", sdk)
    monkeypatch.setenv("GROQ_API_KEY", "test-only-key")
    response = client.post("/api/chat", json={"question": "Có phim nào?"})
    assert response.status_code == 200
    assert response.json["answer"] == "Có phim Sao Mai."
    assert response.json["cards"][0]["screening_id"] == 12
    assert response.json["cards"][0]["seats_available"] == {"STANDARD": 0, "VIP": 1, "COUPLE": 0}