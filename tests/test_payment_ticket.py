"""Mock checkout, ticket issuance and staff validation on isolated SQLite."""
from datetime import datetime, timedelta
from pathlib import Path
import sqlite3

from app.database import get_connection
from database.migrate_sqlite_phone import migrate_phone


def login(client, role):
    response = client.post('/api/auth/login', json={'email': role.lower() + '@example.com', 'password': 'valid-password'})
    assert response.status_code == 200
    with client.session_transaction() as session:
        return session['csrf_token']


def setup_show(app):
    start = datetime.now().replace(hour=20, minute=0, second=0, microsecond=0) + timedelta(days=1)
    with app.app_context():
        db = get_connection()
        db.execute("INSERT INTO movies(id,title,duration_minutes) VALUES(1,'Movie',90)")
        db.execute("INSERT INTO screening_rooms(id,name,row_count,column_count) VALUES(1,'Room',1,2)")
        db.execute("INSERT INTO seats(id,room_id,row_label,seat_number,seat_type) VALUES(1,1,'A',1,'STANDARD')")
        db.execute("INSERT INTO seats(id,room_id,row_label,seat_number,seat_type) VALUES(2,1,'A',2,'VIP')")
        db.execute("INSERT INTO screenings(id,movie_id,room_id,start_time,end_time) VALUES(1,1,1,?,?)", (start.isoformat(sep=' '), (start + timedelta(minutes=90)).isoformat(sep=' ')))
        db.commit()
        db.close()


def test_payment_and_ticket_access(app):
    setup_show(app)
    customer = app.test_client()
    csrf = login(customer, 'CUSTOMER')
    hold = customer.post('/api/booking/hold-seat', json={'screening_id': 1, 'seat_id': 1}, headers={'X-CSRF-Token': csrf})
    assert hold.status_code == 201
    hold_id = hold.json['hold_id']
    assert customer.get('/checkout/' + str(hold_id)).status_code == 200
    assert customer.post('/api/payment/process', json={'hold_id': hold_id, 'payment_method': 'VNPAY', 'success': True}).status_code == 403
    payload = {'hold_id': hold_id, 'payment_method': 'VNPAY', 'success': True}
    result = customer.post('/api/payment/process', json=payload, headers={'X-CSRF-Token': csrf})
    assert result.status_code == 200
    code = result.json['booking_code']
    assert code.encode() in customer.get('/ticket/' + code).data
    assert customer.post('/api/payment/process', json=payload, headers={'X-CSRF-Token': csrf}).status_code == 409
    assert customer.post('/api/booking/hold-seat', json={'screening_id': 1, 'seat_id': 1}, headers={'X-CSRF-Token': csrf}).status_code == 409
    stranger = app.test_client()
    with stranger.session_transaction() as session:
        session['user_id'] = 1
        session['role'] = 'CUSTOMER'
    assert stranger.get('/ticket/' + code).status_code == 404
    with app.app_context():
        db = get_connection()
        assert db.execute('SELECT amount,status FROM payments WHERE booking_id=?', (code,)).fetchone()['amount'] == 80000
        assert db.execute('SELECT price,status FROM tickets WHERE booking_code=?', (code,)).fetchone()['status'] == 'BOOKED'
        assert db.execute('SELECT COUNT(*) FROM seat_holds WHERE id=?', (hold_id,)).fetchone()[0] == 0
        db.close()


def test_cancel_releases_and_checkin_once(app):
    setup_show(app)
    customer = app.test_client()
    csrf = login(customer, 'CUSTOMER')
    headers = {'X-CSRF-Token': csrf}
    hold = customer.post('/api/booking/hold-seat', json={'screening_id': 1, 'seat_id': 2}, headers=headers).json['hold_id']
    cancel = customer.post('/api/payment/process', json={'hold_id': hold, 'payment_method': 'MOMO', 'success': False}, headers=headers)
    assert cancel.status_code == 200 and cancel.json['released']
    hold = customer.post('/api/booking/hold-seat', json={'screening_id': 1, 'seat_id': 2}, headers=headers).json['hold_id']
    code = customer.post('/api/payment/process', json={'hold_id': hold, 'payment_method': 'MOMO', 'success': True}, headers=headers).json['booking_code']
    staff = app.test_client()
    staff_csrf = login(staff, 'STAFF')
    assert code.encode() in staff.get('/staff?q=' + code).data
    assert staff.post('/api/staff/check-in', json={'query': code}).status_code == 403
    check = lambda q: staff.post('/api/staff/check-in', json={'query': q}, headers={'X-CSRF-Token': staff_csrf})
    assert check(code).status_code == 409  # tomorrow is not today
    with app.app_context():
        db = get_connection()
        db.execute('UPDATE screenings SET start_time=?,end_time=? WHERE id=1', (datetime.now().isoformat(sep=' '), (datetime.now() + timedelta(minutes=90)).isoformat(sep=' ')))
        db.commit()
        qr = db.execute('SELECT qr_code FROM tickets WHERE booking_code=?', (code,)).fetchone()[0]
        assert db.execute('SELECT price FROM tickets WHERE booking_code=?', (code,)).fetchone()[0] == 110000
        db.close()
    assert check(qr).status_code == 200
    repeated = check(code)
    assert repeated.status_code == 409 and repeated.json['error'] == 'Vé đã được sử dụng'
    assert check('0900000003').status_code == 409


def test_migration_existing_schema_is_idempotent(app):
    with app.app_context():
        db = get_connection()
        db.execute('DROP TABLE payments')
        db.execute('DROP TABLE tickets')
        db.execute('CREATE TABLE tickets (id INTEGER PRIMARY KEY, user_id INTEGER, screening_id INTEGER, seat_id INTEGER, status TEXT, amount NUMERIC, qr_code TEXT, created_at TEXT)')
        db.commit()
        db.close()
        migrate_phone()
        migrate_phone()
        db = get_connection()
        assert {'booking_code', 'price'} <= {row['name'] for row in db.execute('PRAGMA table_info(tickets)')}
        assert db.execute("SELECT name FROM sqlite_master WHERE name='payments'").fetchone()
        db.close()