"""React chatbot shell and anonymous CSRF integration checks."""

import pytest


@pytest.mark.parametrize("path", ["/", "/movies", "/login"])
def test_shared_widget_on_anonymous_pages(app, path):
    client = app.test_client()
    response = client.get(path)
    assert response.status_code == 200
    page = response.get_data(as_text=True)
    assert '<div id="root"></div>' in page
    assert "/assets/" in page
    with client.session_transaction() as session:
        assert session["csrf_token"]
        assert "user_id" not in session


def test_page_csrf_token_works_for_anonymous_chat(app, monkeypatch):
    from app.routes import chatbot

    client = app.test_client()
    client.get("/")
    with client.session_transaction() as session:
        csrf = session["csrf_token"]
    monkeypatch.setattr(chatbot, "process_chat", lambda question: {"answer": "Xin chào!", "cards": []})
    response = client.post("/api/chat", json={"question": "Có phim gì?"},
                           headers={"X-CSRF-Token": csrf})
    assert response.status_code == 200
    assert response.json == {"answer": "Xin chào!", "cards": []}