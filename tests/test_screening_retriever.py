from datetime import datetime
import sqlite3

import pytest

from app.database import get_connection
from app.services.screening_retriever import retrieve_screenings


def _seed_catalog(app):
    with app.app_context():
        db = get_connection()
        db.executescript("""
            INSERT INTO movies(id,title,duration_minutes,status) VALUES
                (10,'Hoạt Hình Sao Mai',100,'NOW_SHOWING'),
                (11,'Phim Khác',90,'NOW_SHOWING');
            INSERT INTO genres(id,name) VALUES (10,'Hoạt hình'),(11,'Hành động');
            INSERT INTO movie_genres(movie_id,genre_id) VALUES (10,10),(11,11);
            INSERT INTO screening_rooms(id,name,row_count,column_count,status) VALUES
                (10,'Phòng A',2,3,'ACTIVE'),(11,'Phòng B',1,2,'ACTIVE');
            INSERT INTO seats(id,room_id,row_label,seat_number,seat_type) VALUES
                (101,10,'A',1,'STANDARD'),(102,10,'A',2,'STANDARD'),
                (103,10,'B',1,'VIP'),(104,10,'B',2,'VIP'),(105,10,'C',1,'COUPLE'),
                (106,10,'C',2,'COUPLE'),(201,11,'A',1,'STANDARD'),(202,11,'A',2,'VIP');
            INSERT INTO screenings(id,movie_id,room_id,start_time,end_time) VALUES
                (100,10,10,'2026-09-30 19:00:00','2026-09-30 20:40:00'),
                (101,11,11,'2026-09-30 20:00:00','2026-09-30 21:30:00'),
                (102,10,10,'2026-10-01 09:00:00','2026-10-01 10:40:00');
            INSERT INTO tickets(id,user_id,screening_id,seat_id,status) VALUES
                (1001,3,100,101,'BOOKED'),(1002,3,100,103,'USED'),
                (1003,3,100,105,'CANCELLED');
            INSERT INTO seat_holds(id,user_id,screening_id,seat_id,expires_at) VALUES
                (1001,3,100,102,'2026-09-30 19:30:00'),
                (1002,3,100,104,'2026-09-30 18:30:00');
        """)
        db.commit()
        db.close()


def test_retrieves_filters_and_exact_availability(app):
    _seed_catalog(app)
    with app.app_context():
        result = retrieve_screenings({
            "movie_title": "Hoạt Hình Sao Mai", "genre": "Hoạt hình",
            "date": "2026-09-30", "min_time": "19:00", "max_time": "19:00",
        }, now=datetime.fromisoformat("2026-09-30T19:00:00"))
    assert len(result) == 1
    assert result[0]["screening_id"] == 100
    assert result[0]["available_seats"] == {"STANDARD": 0, "VIP": 1, "COUPLE": 2}


def test_expired_holds_are_available_and_date_time_filters_work(app):
    _seed_catalog(app)
    with app.app_context():
        result = retrieve_screenings({"date": "2026-09-30", "time_of_day": "EVENING"}, now=datetime.fromisoformat("2026-09-30T19:00:00"))
    assert [item["screening_id"] for item in result] == [100, 101]
    assert result[0]["available_seats"] == {"STANDARD": 0, "VIP": 1, "COUPLE": 2}


def test_empty_result_and_limit(app):
    _seed_catalog(app)
    with app.app_context():
        assert retrieve_screenings({"movie_title": "does-not-exist"}) == []
        result = retrieve_screenings({}, now=datetime.fromisoformat("2026-09-30T19:00:00"))
        future = retrieve_screenings({}, now=datetime.fromisoformat("2026-09-30T19:00:00.500000"))
        historical = retrieve_screenings({"date": "2026-09-30"},
                                         now=datetime.fromisoformat("2026-10-01T12:00:00"))
    assert len(result) == 3
    assert [row["screening_id"] for row in future] == [101, 102]
    assert [row["screening_id"] for row in historical] == [100, 101]


def test_intent_values_are_parameters_not_sql(app):
    _seed_catalog(app)
    with app.app_context():
        result = retrieve_screenings({"movie_title": "' OR 1=1 --", "genre": "Hoạt hình"})
    assert result == []


def test_limit_is_five_and_sorted(app):
    _seed_catalog(app)
    with app.app_context():
        db = get_connection()
        for index in range(8):
            db.execute("INSERT INTO screenings(movie_id,room_id,start_time,end_time) VALUES(?,?,?,?)",
                       (10, 10, f"2026-10-02 {20-index:02d}:00:00", f"2026-10-02 {21-index:02d}:00:00"))
        db.commit()
        db.close()
        result = retrieve_screenings({"date": "2026-10-02"})
    assert len(result) == 5
    assert [row["start_time"] for row in result] == [f"2026-10-02 {hour:02d}:00:00" for hour in range(13, 18)]


@pytest.mark.parametrize("filters,expected", [
    ({"genre": "Hoạt hình"}, [100, 102]),
    ({"movie_title": "Sao Mai"}, [100, 102]),
    ({"date": "2026-10-01", "time_of_day": "MORNING"}, [102]),
    ({"time_of_day": "AFTERNOON"}, []),
    ({"seat_type": "COUPLE"}, [100, 102]),
    ({"date": "2026-09-30", "min_time": "20:00"}, [101]),
    ({"date": "2026-09-30", "max_time": "19:00"}, [100]),
    ({"genre": "' OR 1=1 --"}, []),
    ({"movie_title": "%"}, []),
    ({"movie_title": "_"}, []),
    ({"intent": "UNKNOWN"}, []),
    ({"intent": "AMBIGUOUS"}, []),
    ({"intent": "ask_policy"}, []),
    ({"min_time": "20:00", "max_time": "19:00"}, []),
])
def test_filter_combinations(app, filters, expected):
    _seed_catalog(app)
    with app.app_context():
        result = retrieve_screenings(filters, now=datetime.fromisoformat("2026-09-30T19:00:00"))
    assert [row["screening_id"] for row in result] == expected


@pytest.mark.parametrize("filters", [
    {"date": "2026-02-30"}, {"date": "' OR 1=1 --"},
    {"min_time": "25:00"}, {"max_time": "00:60"},
    {"seat_type": "invalid"}, {"time_of_day": "invalid"},
    {"movie_title": ["unexpected"]},
])
def test_invalid_filters_are_not_silently_ignored(app, filters):
    with app.app_context(), pytest.raises(ValueError):
        retrieve_screenings(filters)


def test_counts_are_distinct_scoped_and_holds_are_read_only(app):
    _seed_catalog(app)
    with app.app_context():
        db = get_connection()
        # Duplicate tickets and a hold on the same seat must only block it once.
        db.execute("INSERT INTO tickets(user_id,screening_id,seat_id,status) VALUES(3,100,101,'USED')")
        db.execute("INSERT INTO seat_holds(user_id,screening_id,seat_id,expires_at) VALUES(3,100,101,?)",
                   ("2026-09-30T20:00:00",))
        # Other screening's tickets do not affect screening 100.
        db.execute("INSERT INTO tickets(user_id,screening_id,seat_id,status) VALUES(3,102,106,'BOOKED')")
        # Different room's seat does not reduce this screening's capacity.
        db.execute("INSERT INTO tickets(user_id,screening_id,seat_id,status) VALUES(3,100,201,'BOOKED')")
        db.commit()
        db.close()
        result = retrieve_screenings({"date": "2026-09-30", "genre": "Hoạt hình"},
                                     now=datetime.fromisoformat("2026-09-30T19:30:00+07:00"))
        assert result[0]["available_seats"] == {"STANDARD": 1, "VIP": 1, "COUPLE": 2}
        db = get_connection()
        assert db.execute("SELECT COUNT(*) FROM seat_holds").fetchone()[0] == 3
        db.close()


def test_nonblocking_statuses_and_missing_seat_type(app):
    _seed_catalog(app)
    with app.app_context():
        db = get_connection()
        for status in ("CANCELLED", "HELD", "PAID", "CHECKED_IN"):
            db.execute("INSERT INTO tickets(user_id,screening_id,seat_id,status) VALUES(3,101,201,?)", (status,))
        db.commit()
        db.close()
        result = retrieve_screenings({"movie_title": "Phim Khác"},
                                     now=datetime.fromisoformat("2026-09-30T19:00:00"))
    assert result[0]["available_seats"] == {"STANDARD": 1, "VIP": 1, "COUPLE": 0}


@pytest.mark.parametrize("status", ["SHOWING", "NOW_SHOWING", "COMING_SOON", "DANG_CHIEU", "SAP_CHIEU"])
def test_public_movies_and_active_rooms_only(app, status):
    _seed_catalog(app)
    with app.app_context():
        db = get_connection()
        db.execute("UPDATE movies SET status=? WHERE id=10", (status,))
        db.commit()
        result = retrieve_screenings({"genre": "Hoạt hình"},
                                     now=datetime.fromisoformat("2026-09-30T19:00:00"))
        assert [row["screening_id"] for row in result] == [100, 102]
        db.execute("UPDATE movies SET status='DRAFT' WHERE id=10")
        db.execute("UPDATE screening_rooms SET status='MAINTENANCE' WHERE id=11")
        db.commit()
        db.close()
        assert retrieve_screenings({}, now=datetime.fromisoformat("2026-09-30T19:00:00")) == []


def test_timezone_and_analyzer_integration(app):
    from app.services.question_analyzer import analyze_question
    _seed_catalog(app)
    with app.app_context():
        clock = datetime.fromisoformat("2026-09-30T12:00:00+00:00")
        intent = analyze_question("Tối nay có phim hoạt hình nào sau 19h không?", now=clock)
        result = retrieve_screenings(intent, now=clock)
    assert [row["screening_id"] for row in result] == [100]
    assert result[0]["checked_at"] == "2026-09-30 19:00:00.000000"


def test_database_errors_are_not_empty_results(app):
    with app.app_context():
        db = get_connection()
        db.execute("DROP TABLE seat_holds")
        db.commit()
        db.close()
        with pytest.raises(sqlite3.OperationalError):
            retrieve_screenings({})