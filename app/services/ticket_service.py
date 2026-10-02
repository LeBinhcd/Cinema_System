"""Ticket presentation and staff check-in orchestration."""
from datetime import datetime, timedelta
from app.models.payment import PaymentModel
from app.services.screening_rules import as_datetime


class TicketService:
    @staticmethod
    def _present(seats, now):
        ticket = dict(seats[0])
        ticket['seats'] = [dict(s) for s in seats]
        ticket['price'] = sum(s['price'] if s['price'] is not None else (s['amount'] or 0) for s in seats)
        ticket['can_cancel'] = (all(s['status'] == 'BOOKED' and not s['checked_in_at'] for s in seats)
                                and ticket['payment_status'] == 'SUCCESS'
                                and all(as_datetime(s['start_time']) - now >= timedelta(minutes=60) for s in seats))
        return ticket

    @staticmethod
    def history(user_id):
        with PaymentModel.transaction() as model:
            rows = model.tickets_for_user(user_id)
        groups = {}
        for row in rows:
            groups.setdefault(row['booking_code'], []).append(row)
        now = datetime.now()
        return [TicketService._present(sorted(seats, key=lambda s: s['id']), now)
                for seats in groups.values()]

    @staticmethod
    def get(booking_code, user_id=None):
        with PaymentModel.transaction() as model:
            seats = model.ticket_group(booking_code)
            if not seats or (user_id is not None and any(s['user_id'] != user_id for s in seats)):
                return None
            return TicketService._present(seats, datetime.now())

    @staticmethod
    def cancel(booking_code, user_id):
        with PaymentModel.transaction() as model:
            seats = model.ticket_group(booking_code)
            if not seats or any(s['user_id'] != user_id for s in seats):
                return None, 'Vé không tồn tại hoặc không thuộc tài khoản của bạn.'
            if any(s['status'] != 'BOOKED' or s['checked_in_at'] for s in seats):
                return None, 'Chỉ được hủy vé BOOKED, chưa check-in và chưa bị hủy.'
            if any(as_datetime(s['start_time']) - datetime.now() < timedelta(minutes=60) for s in seats):
                return None, 'Chỉ được hủy khi còn ít nhất 60 phút trước giờ chiếu.'
            if not model.refund(booking_code):
                return None, 'Thanh toán không ở trạng thái SUCCESS; không thể hoàn tiền.'
            model.cancel_group(booking_code)
            return {'booking_code': booking_code, 'status': 'CANCELLED',
                    'payment_status': 'REFUNDED', 'message': 'ĐÃ HỦY / ĐÃ HOÀN TIỀN (giả lập)'}, None

    @staticmethod
    def lookup(query):
        with PaymentModel.transaction() as model:
            return [dict(row) for row in model.find_tickets(query.strip())] if query and query.strip() else []

    @staticmethod
    def check_in(query):
        with PaymentModel.transaction() as model:
            rows = model.check_in_candidates(query.strip())
            if not rows:
                return None, "Không tìm thấy vé."
            if len({r['booking_code'] for r in rows}) > 1:
                return None, "Số điện thoại có nhiều vé; hãy chọn mã đặt chỗ cụ thể."
            # A seat QR identifies the same whole booking as its booking code.
            rows = model.check_in_candidates(rows[0]['booking_code']) if rows[0]['booking_code'] else rows
            row = rows[0]
            if any(r['status'] in ('USED', 'CHECKED_IN') for r in rows):
                return None, "Vé đã được sử dụng"
            if any(r['status'] not in ('BOOKED', 'PAID') for r in rows):
                return None, "Vé không hợp lệ hoặc đã bị hủy."
            if str(row["start_time"])[:10] != datetime.now().date().isoformat():
                return None, "Vé không đúng suất chiếu hôm nay."
            for item in rows:
                if not model.mark_used(item['id']):
                    raise RuntimeError('Atomic check-in failed')
            result = dict(row)
            result["status"] = "USED"
            return result, None