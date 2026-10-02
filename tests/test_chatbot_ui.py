"""Shared widget rendering and anonymous CSRF integration checks."""
from html.parser import HTMLParser

import pytest


class WidgetParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.csrf = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.append(attrs["id"])
        if tag == "meta" and attrs.get("name") == "csrf-token":
            self.csrf = attrs.get("content")


@pytest.mark.parametrize("path", ["/", "/movies", "/login"])
def test_shared_widget_on_anonymous_pages(app, path):
    client = app.test_client()
    response = client.get(path)
    assert response.status_code == 200
    page = response.get_data(as_text=True)
    parser = WidgetParser()
    parser.feed(page)
    assert parser.ids.count("cinema-chat") == 1
    assert parser.ids.count("chat-question") == 1
    assert 'maxlength="300"' in page
    assert "Trợ lý Điện ảnh AI" in page
    assert "/static/css/chatbot.css" in page
    assert "/static/js/chatbot.js" in page
    with client.session_transaction() as session:
        assert parser.csrf == session["csrf_token"]
        assert "user_id" not in session


def test_page_csrf_token_works_for_anonymous_chat(app, monkeypatch):
    from app.routes import chatbot

    client = app.test_client()
    parser = WidgetParser()
    parser.feed(client.get("/").get_data(as_text=True))
    monkeypatch.setattr(chatbot, "process_chat", lambda question: {"answer": "Xin chào!", "cards": []})
    response = client.post("/api/chat", json={"question": "Có phim gì?"},
                           headers={"X-CSRF-Token": parser.csrf})
    assert response.status_code == 200
    assert response.json == {"answer": "Xin chào!", "cards": []}


@pytest.mark.parametrize("path,content_type", [
    ("/static/css/chatbot.css", "text/css"),
    ("/static/js/chatbot.js", "javascript"),
])
def test_widget_assets_are_served(app, path, content_type):
    response = app.test_client().get(path)
    assert response.status_code == 200
    assert content_type in response.content_type