"""Authentication and read-only availability tests without external services."""
from werkzeug.security import generate_password_hash

from app import create_app


def test_login_admin_and_logout(app, monkeypatch):
    from app.models.user import UserModel
    from app.services.catalog_service import CatalogService

    password_hash = generate_password_hash("valid-password")
    monkeypatch.setattr(UserModel, "find_by_email", lambda email: {
        "id": 4, "role": "ADMIN", "password_hash": password_hash
    } if email == "admin@example.com" else None)
    monkeypatch.setattr(CatalogService, "movies", lambda: [])
    client = app.test_client()
    assert client.get("/admin", headers={"X-Role": "ADMIN"}).status_code == 403
    assert client.post("/api/auth/login", json={"email": "admin@example.com", "password": "wrong"}).status_code == 401
    assert client.post("/api/auth/login", json={"email": "admin@example.com", "password": "valid-password"}).status_code == 200
    assert client.get("/admin").status_code == 200
    assert client.post("/api/auth/logout").status_code == 200
    assert client.get("/admin").status_code == 403


def test_customer_cannot_access_admin(app, monkeypatch):
    from app.models.user import UserModel

    monkeypatch.setattr(UserModel, "find_by_email", lambda email: {
        "id": 5, "role": "CUSTOMER", "password_hash": generate_password_hash("password")
    })
    client = app.test_client()
    assert client.post("/api/auth/login", json={"email": "customer@example.com", "password": "password"}).status_code == 200
    assert client.get("/admin").status_code == 403
    assert client.get("/staff").status_code == 403


def test_missing_secret_generates_random_key(app, caplog):
    config = dict(app.config, SECRET_KEY=None)
    first, second = create_app(config), create_app(config)
    assert len(first.secret_key) == 64
    assert first.secret_key != second.secret_key
    assert "generated an ephemeral key" in caplog.text
    assert first.secret_key not in caplog.text
    client = first.test_client()
    assert client.post("/api/auth/login", json={"email": "admin@example.com", "password": "valid-password"}).status_code == 200
    other = second.test_client()
    cookie = client.get_cookie(first.config["SESSION_COOKIE_NAME"])
    other.set_cookie(second.config["SESSION_COOKIE_NAME"], cookie.value)
    assert other.get("/admin").status_code == 403


def test_read_only_seat_map(app, monkeypatch):
    from app.services.seat_map_service import SeatMapService

    monkeypatch.setattr(SeatMapService, "get_for_screening", lambda screening_id: {
        "id": screening_id, "seats": [{"id": 1, "status": "AVAILABLE"}]
    } if screening_id == 1 else None)
    client = app.test_client()
    assert client.get("/api/screenings/1/seats").json["seats"][0]["status"] == "AVAILABLE"
    assert client.get("/api/screenings/2/seats").status_code == 404
    from app.database import get_connection
    from app.services.preview_service import PreviewService
    from database.migrate_sqlite_phone import migrate_phone
    with app.app_context():
        connection = get_connection()
        connection.executescript("""INSERT INTO movies(id,title,duration_minutes) VALUES(1,'Test movie',90);
            INSERT INTO screening_rooms(id,name,row_count,column_count) VALUES(1,'Test room',1,1);
            INSERT INTO seats(id,room_id,row_label,seat_number,seat_type) VALUES(1,1,'A',1,'STANDARD');
            INSERT INTO screenings(id,movie_id,room_id,start_time,end_time) VALUES(1,1,1,'2026-10-01 10:00:00','2026-10-01 11:30:00');
            INSERT INTO tickets(user_id,screening_id,seat_id,status,amount,qr_code)
                VALUES(3,1,1,'PAID',100,'TEST-QR');""")
        connection.close()
        migrate_phone()
        assert len(PreviewService.lookup("customer@example.com")) == 1
        assert len(PreviewService.lookup("0900000003")) == 1
        assert len(PreviewService.lookup("TEST-QR")) == 1
        assert PreviewService.lookup("0900000002") == []