"""Mock payment orchestration; business rules live here, SQL stays in models."""
from datetime import datetime
import secrets
import uuid
from app.models.payment import PaymentModel
from app.services.screening_rules import as_datetime, sales_open

BASE_PRICES = {"STANDARD": 80000, "VIP": 110000, "COUPLE": 160000}

BOOKING_CODE_PREFIX = "CV-"
BOOKING_CODE_DIGITS = 5
METHODS = {"VNPAY", "MOMO"}



def create_short_booking_code(model):
    """Create a human-friendly code and guard against collisions."""
    for _ in range(20):
        code = BOOKING_CODE_PREFIX + ''.join(secrets.choice('0123456789') for _ in range(BOOKING_CODE_DIGITS))
        exists = model.connection.execute(
            "SELECT 1 FROM payments WHERE booking_id=? UNION SELECT 1 FROM tickets WHERE booking_code=? LIMIT 1",
            (code, code),
        ).fetchone()
        if not exists:
            return code
    raise RuntimeError("Không thể tạo mã đặt chỗ duy nhất.")


class PaymentService:
    @staticmethod
    def checkout(hold_id, user_id):
        with PaymentModel.transaction() as model:
            seats = model.hold_group(hold_id, user_id)
            if not seats or any(as_datetime(s['expires_at']) <= datetime.now()
                                or not sales_open(s['start_time'], datetime.now()) for s in seats):
                return None
            if any(s['seat_type'] not in BASE_PRICES for s in seats):
                return None
            order = dict(seats[0])
            order['id'] = hold_id
            order['seats'] = seats
            order["price"] = sum(BASE_PRICES[s['seat_type']] for s in seats)
            return order

    @staticmethod
    def process(hold_id, user_id, method, success, saved_card_id=None):
        if method not in METHODS:
            return None, "Cổng thanh toán không hợp lệ."
        with PaymentModel.transaction() as model:
            seats = model.hold_group(hold_id, user_id)
            if not seats:
                return None, "Giữ ghế không tồn tại hoặc không thuộc tài khoản."
            if saved_card_id is not None and not model.connection.execute('SELECT 1 FROM saved_cards WHERE id=? AND user_id=?',(saved_card_id,user_id)).fetchone():
                return None, 'Thẻ đã lưu không thuộc tài khoản.'
            code = create_short_booking_code(model)

            if any(as_datetime(s['expires_at']) <= datetime.now()
                   or not sales_open(s['start_time'], datetime.now()) for s in seats):
                for seat in seats:
                    model.release_hold(seat['id'], user_id)
                return None, "Giữ ghế đã hết hạn."
            if any(s['seat_type'] not in BASE_PRICES for s in seats):
                return None, 'Loại ghế chưa có bảng giá.'
            price = sum(BASE_PRICES[s['seat_type']] for s in seats)
            if not success:
                model.create_payment(code, price, method, "FAILED", "MOCK-" + uuid.uuid4().hex.upper())
                for seat in seats:
                    model.release_hold(seat['id'], user_id)
                return {"released": True}, None
            if any(model.paid(s['screening_id'], s['seat_id']) for s in seats):
                return None, "Ghế đã được bán."
            model.create_payment(code, price, method, "SUCCESS", "MOCK-" + uuid.uuid4().hex.upper())
            for seat in seats:
                model.issue_ticket(seat, code, "CINE-QR-" + secrets.token_urlsafe(32), BASE_PRICES[seat['seat_type']])
            return {"booking_code": code}, None