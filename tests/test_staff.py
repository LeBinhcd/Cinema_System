"""Counter issuance, role protection, lookup, check-in and refund."""
from datetime import datetime, timedelta

from app.database import get_connection
from .test_payment_ticket import login, setup_show


def test_counter_sale_lookup_refund(app):
    setup_show(app)
    with app.app_context():
        db = get_connection()
        start = datetime.now().replace(microsecond=0) + timedelta(hours=2)
        db.execute('UPDATE screenings SET start_time=?,end_time=? WHERE id=1',
                   (start.isoformat(sep=' '), (start + timedelta(minutes=90)).isoformat(sep=' ')))
        db.commit()
        db.close()
    staff = app.test_client()
    csrf = login(staff, 'STAFF')
    headers = {'X-CSRF-Token': csrf}
    payload = {'screening_id': 1, 'seat_ids': [1, 2], 'name': 'Walk-in', 'phone': '0987654321', 'payment_method': 'CASH'}
    assert staff.get('/staff').status_code == 200
    assert staff.post('/api/staff/pos/sell', json=payload).status_code == 403
    assert staff.post('/api/staff/pos/sell', json={**payload, 'payment_method': 'VNPAY'}, headers=headers).status_code == 409
    sale = staff.post('/api/staff/pos/sell', json=payload, headers=headers)
    assert sale.status_code == 201
    code = sale.json['booking_code']
    assert staff.post('/api/staff/pos/sell', json=payload, headers=headers).status_code == 409
    assert code.encode() in staff.get('/staff?q=0987654321').data
    assert staff.get('/api/staff/ticket/' + code).json['price'] == 190000
    assert staff.post('/api/staff/check-in', json={'query': code}, headers=headers).status_code == 200
    assert staff.post('/api/staff/cancel', json={'booking_code': code}, headers=headers).status_code == 409
    with app.app_context():
        db = get_connection()
        assert db.execute('SELECT COUNT(*) FROM tickets WHERE booking_code=? AND checked_in_at IS NOT NULL', (code,)).fetchone()[0] == 2
        db.close()
    customer = app.test_client()
    login(customer, 'CUSTOMER')
    assert customer.get('/api/staff/ticket/' + code).status_code == 403


def test_counter_cancel_releases_seats(app):
    setup_show(app)
    with app.app_context():
        db = get_connection()
        start = datetime.now().replace(microsecond=0) + timedelta(hours=2)
        db.execute('UPDATE screenings SET start_time=?,end_time=? WHERE id=1',
                   (start.isoformat(sep=' '), (start + timedelta(minutes=90)).isoformat(sep=' ')))
        db.commit()
        db.close()
    client = app.test_client()
    headers = {'X-CSRF-Token': login(client, 'STAFF')}
    payload = {'screening_id': 1, 'seat_ids': [1], 'name': 'Guest', 'payment_method': 'BANKING'}
    code = client.post('/api/staff/pos/sell', json=payload, headers=headers).json['booking_code']
    assert client.post('/api/staff/cancel', json={'booking_code': code}, headers=headers).status_code == 200
    assert client.get('/api/staff/pos/screening/1/seats').json['seats'][0]['status'] == 'AVAILABLE'
    assert client.post('/api/staff/pos/sell', json=payload, headers=headers).status_code == 201


def test_counter_rejects_invalid_seat_ids(app):
    setup_show(app)
    client = app.test_client()
    headers = {'X-CSRF-Token': login(client, 'STAFF')}
    payload = {'screening_id': 1, 'seat_ids': ['1'], 'name': 'Guest', 'payment_method': 'CASH'}
    response = client.post('/api/staff/pos/sell', json=payload, headers=headers)
    assert response.status_code == 409
    assert 'ghế hợp lệ' in response.json['error']