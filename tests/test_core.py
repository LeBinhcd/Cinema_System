from datetime import datetime, timedelta

import pytest

from app import create_app
from app.services.movie_service import MovieService
from app.services.screening_service import ScreeningService


def test_admin_header_does_not_grant_access(app):
    client = app.test_client()
    assert client.get("/").status_code == 200
    assert client.get("/admin", headers={"X-Role": "ADMIN"}).status_code == 403
    assert client.post("/admin/movies/1/edit", headers={"X-Role": "ADMIN"}, json={}).status_code == 403
    assert client.get("/staff", headers={"X-Role": "STAFF"}).status_code == 403


def test_ai_description_remains_draft(monkeypatch):
    captured = {}

    def save(data, source, generated):
        captured.update(data=data, source=source, generated=generated)
        return 42

    monkeypatch.setattr(MovieService, "generate_description", lambda title, keywords: "Mô tả tạm.")
    monkeypatch.setattr("app.models.movie.MovieModel.create_with_draft", save)
    assert MovieService.create({"title": "Phim", "duration_minutes": 90}, generate_ai=True) == 42
    assert captured["data"].get("synopsis") is None
    assert captured["generated"] == "Mô tả tạm."


def test_cleanup_boundary(app):
    start = datetime(2026, 10, 1, 10)
    end = start + timedelta(minutes=90)
    ScreeningService.validate_schedule(start, end, [{"start_time": end + timedelta(minutes=15), "end_time": end + timedelta(hours=2)}])
    with pytest.raises(ValueError):
        ScreeningService.validate_schedule(start, end, [{"start_time": end + timedelta(minutes=9), "end_time": end + timedelta(hours=2)}])
    assert ScreeningService.sales_open(start, start + timedelta(minutes=14))
    assert not ScreeningService.sales_open(start, start + timedelta(minutes=15))
    from app.database import get_connection
    from app.models.screening import ScreeningModel
    with app.app_context():
        connection = get_connection()
        connection.execute("INSERT INTO movies(id,title,duration_minutes) VALUES(1,'Test movie',90)")
        connection.execute("INSERT INTO screening_rooms(id,name,row_count,column_count) VALUES(1,'Test room',1,1)")
        connection.commit()
        connection.close()
        first = {"movie_id": 1, "room_id": 1, "start_time": start.isoformat(sep=" "), "end_time": end.isoformat(sep=" ")}
        assert ScreeningService.create(first) == 1
        with pytest.raises(ValueError):
            ScreeningModel.create({**first, "start_time": (end + timedelta(minutes=9)).isoformat(sep=" "),
                                   "end_time": (end + timedelta(minutes=99)).isoformat(sep=" ")})
        assert ScreeningModel.create({**first, "start_time": (end + timedelta(minutes=15)).isoformat(sep=" "),
                                      "end_time": (end + timedelta(minutes=105)).isoformat(sep=" ")}) == 2