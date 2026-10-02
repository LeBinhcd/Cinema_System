"""SQLite regressions for POS cutoff, customer history and seat types."""
from datetime import datetime, timedelta

import pytest

from app.database import get_connection
from app.services.ticket_service import TicketService
from .test_payment_ticket import login, setup_show


@pytest.mark.parametrize('elapsed,expected', [(14, 201), (15, 409), (16, 409)])
def test_pos_cutoff_and_disabled_option(app, monkeypatch, elapsed, expected):
    setup_show(app)
    now = datetime.now().replace(hour=12, minute=0, second=0, microsecond=0)
    class Clock(datetime):
        @classmethod
        def now(cls):
            return now
    monkeypatch.setattr('app.services.staff_service.datetime', Clock)
    with app.app_context():
        db = get_connection()
        start = now - timedelta(minutes=elapsed)
        db.execute('UPDATE screenings SET start_time=?,end_time=? WHERE id=1',
                   (start.isoformat(sep=' '), (start + timedelta(minutes=90)).isoformat(sep=' ')))
        db.commit()
        db.close()
    client = app.test_client()
    token = login(client, 'STAFF')
    html = client.get('/staff').get_data(as_text=True)
    assert ('disabled data-closed="true"' in html) == (expected == 409)
    result = client.post('/api/staff/pos/sell', json={'screening_id': 1, 'seat_ids': [1],
                         'name': 'Guest', 'payment_method': 'CASH'}, headers={'X-CSRF-Token': token})
    assert result.status_code == expected
    if expected == 409:
        assert result.json['error'] == 'Suất chiếu đã quá thời gian mở bán (quá 15 phút kể từ giờ bắt đầu).'
        with app.app_context():
            db = get_connection()
            assert db.execute('SELECT COUNT(*) FROM tickets').fetchone()[0] == 0
            assert db.execute('SELECT COUNT(*) FROM payments').fetchone()[0] == 0
            db.close()


def seed_history(app):
    setup_show(app)
    with app.app_context():
        db = get_connection()
        for code, user, seats, status, created in (
            ('OLD', 3, [1], 'USED', '2026-01-01 10:00:00'),
            ('NEW', 3, [1, 2], 'BOOKED', '2026-02-01 10:00:00'),
            ('OTHER-USER', 2, [2], 'BOOKED', '2026-03-01 10:00:00'),
        ):
            db.execute("INSERT INTO payments(booking_id,amount,payment_method,status,transaction_code) VALUES(?,?,'MOMO','SUCCESS',?)",
                       (code, sum(80000 if seat == 1 else 110000 for seat in seats), code))
            for seat in seats:
                price = 80000 if seat == 1 else 110000
                db.execute('INSERT INTO tickets(booking_code,user_id,screening_id,seat_id,status,price,amount,created_at) VALUES(?,?,1,?,?,?,?,?)',
                           (code, user, seat, status, price, price, created))
        db.commit()
        db.close()


def test_history_ownership_grouping_and_cancel(app):
    seed_history(app)
    client = app.test_client()
    assert client.get('/my-tickets').status_code == 302
    token = login(client, 'CUSTOMER')
    html = client.get('/my-tickets').get_data(as_text=True)
    assert html.index('Mã đặt chỗ: <strong>NEW') < html.index('Mã đặt chỗ: <strong>OLD')
    assert 'OTHER-USER' not in html
    assert '/ticket/NEW' in html and 'data-code="NEW"' in html
    assert 'data-code="OLD"' not in html
    assert 'A1, A2' in html and '190,000 VNĐ' in html
    with app.app_context():
        history = TicketService.history(3)
        assert len(history) == 2 and len(history[0]['seats']) == 2
    assert client.get('/ticket/OTHER-USER').status_code == 404
    headers = {'X-CSRF-Token': token}
    assert client.post('/api/ticket/cancel', json={'booking_code': 'OTHER-USER'}, headers=headers).status_code == 409
    assert client.post('/api/ticket/cancel', json={'booking_code': 'NEW'}).status_code == 403
    assert client.post('/api/ticket/cancel', json={'booking_code': 'NEW'}, headers=headers).status_code == 200
    html = client.get('/my-tickets').get_data(as_text=True)
    assert 'CANCELLED' in html and 'REFUNDED' in html and 'data-code="NEW"' not in html


@pytest.mark.parametrize('role', ['STAFF', 'ADMIN'])
def test_history_customer_only(app, role):
    client = app.test_client()
    login(client, role)
    assert client.get('/my-tickets').status_code == 403


@pytest.mark.parametrize('minutes,status,checked_in,can_cancel', [
    (120, 'BOOKED', None, True), (59, 'BOOKED', None, False),
    (120, 'USED', '2026-01-01', False), (120, 'BOOKED', '2026-01-01', False),
])
def test_history_cancel_eligibility(app, minutes, status, checked_in, can_cancel):
    seed_history(app)
    with app.app_context():
        db = get_connection()
        start = datetime.now() + timedelta(minutes=minutes)
        db.execute('UPDATE screenings SET start_time=?,end_time=? WHERE id=1',
                   (start.isoformat(sep=' '), (start + timedelta(minutes=90)).isoformat(sep=' ')))
        db.execute('UPDATE tickets SET status=?,checked_in_at=? WHERE booking_code=?', (status, checked_in, 'NEW'))
        db.commit()
        db.close()
        assert TicketService.history(3)[0]['can_cancel'] is can_cancel


def test_empty_history_and_couple_rendering(app):
    setup_show(app)
    with app.app_context():
        db = get_connection()
        db.execute("UPDATE seats SET seat_type='COUPLE' WHERE id=2")
        db.commit()
        db.close()
    customer = app.test_client()
    login(customer, 'CUSTOMER')
    assert 'Bạn chưa có vé nào.' in customer.get('/my-tickets').get_data(as_text=True)
    assert 'Vé của tôi' in customer.get('/').get_data(as_text=True)
    html = customer.get('/booking/1').get_data(as_text=True)
    assert 'class="seat seat-available couple"' in html
    for label in ('Ghế Thường (80k)', 'Ghế VIP (110k)', 'Ghế Đôi (160k)'):
        assert label in html
    staff = app.test_client()
    login(staff, 'STAFF')
    html = staff.get('/staff').get_data(as_text=True)
    assert 'escapeHtml(s.seat_type).toLowerCase()' in html and 'Ghế Đôi (160k)' in html
    assert 'escapeHtml(t.movie_title)' in html and 'escapeHtml(t.room_name)' in html
    assert staff.get('/api/staff/pos/screening/1/seats').json['seats'][1]['seat_type'] == 'COUPLE'