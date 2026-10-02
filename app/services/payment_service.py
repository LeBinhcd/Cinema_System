"""Mock payment orchestration; business rules live here, SQL stays in models."""
from datetime import datetime
import secrets
import uuid
from app.models.payment import PaymentModel
from app.services.screening_rules import as_datetime, sales_open

BASE_PRICES = {"STANDARD": 80000, "VIP": 110000, "COUPLE": 160000}
METHODS = {"VNPAY", "MOMO", "DOMESTIC_CARD"}


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
    def process(hold_id, user_id, method, success):
        if method not in METHODS:
            return None, "Cổng thanh toán không hợp lệ."
        with PaymentModel.transaction() as model:
            seats = model.hold_group(hold_id, user_id)
            if not seats:
                return None, "Giữ ghế không tồn tại hoặc không thuộc tài khoản."
            code = seats[0]['group_code'] or "CV-" + uuid.uuid4().hex.upper()
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