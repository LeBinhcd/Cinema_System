"""Staff counter, validation and support use cases."""
from datetime import datetime, timedelta
import secrets
import uuid

from app.models.staff import StaffModel
from app.services.payment_service import BASE_PRICES
from app.services.screening_rules import SALES_CUTOFF_MINUTES, as_datetime, sales_open
from app.services.ticket_service import TicketService


class StaffService:
    @staticmethod
    def screenings_today():
        screenings = StaffModel.todays_screenings()
        now = datetime.now()
        for show in screenings:
            show['sales_open'] = sales_open(show['start_time'], now)
            show['sales_cutoff'] = (as_datetime(show['start_time']) + timedelta(minutes=SALES_CUTOFF_MINUTES)).isoformat()
        return screenings

    @staticmethod
    def sell(screening_id, seat_ids, name, phone, method, staff_id):
        if method not in {'CASH', 'BANKING'}:
            return None, 'Chỉ hỗ trợ Tiền mặt hoặc Chuyển khoản QR.'
        if (not isinstance(seat_ids, list) or not 1 <= len(seat_ids) <= 4
                or any(type(seat_id) is not int or seat_id < 1 for seat_id in seat_ids)
                or len(set(seat_ids)) != len(seat_ids)):
            return None, 'Vui lòng chọn từ 1 đến 4 ghế hợp lệ.'
        if not isinstance(name, str) or not name.strip():
            return None, 'Vui lòng nhập tên khách hàng.'
        with StaffModel.transaction() as model:
            show = model.screening(screening_id)
            now = datetime.now()
            if not show or show['room_status'] != 'ACTIVE' or as_datetime(show['start_time']).date() != now.date():
                return None, 'Chỉ được bán suất chiếu trong ngày hôm nay ở phòng hoạt động.'
            if not sales_open(show['start_time'], now):
                return None, 'Suất chiếu đã quá thời gian mở bán (quá 15 phút kể từ giờ bắt đầu).'
            seats = model.counter_seats(screening_id, seat_ids)
            if len(seats) != len(seat_ids) or any(model.paid(screening_id, s['id']) or model.active_hold(screening_id, s['id']) for s in seats):
                return None, 'Một hoặc nhiều ghế vừa được bán/đang được giữ.'
            code = 'POS-' + uuid.uuid4().hex[:10].upper()
            customer = model.counter_customer(name.strip(), phone.strip() if isinstance(phone, str) and phone.strip() else None, code)
            amount = sum(BASE_PRICES.get(s['seat_type'], 0) for s in seats)
            model.create_payment(code, amount, method, 'SUCCESS', 'POS-' + uuid.uuid4().hex.upper())
            for seat in seats:
                model.create_counter_ticket(customer, screening_id, seat['id'], BASE_PRICES[seat['seat_type']], code, 'CINE-QR-' + secrets.token_urlsafe(20))
            model.store_counter_contact(code, name.strip(), phone.strip() if isinstance(phone, str) and phone.strip() else None, staff_id)
            return {'booking_code': code}, None

    @staticmethod
    def lookup(query):
        query = (query or '').strip()
        if not query:
            return []
        results = []
        with StaffModel.transaction() as model:
            codes = model.lookup_codes(query)
        for code in codes:
            ticket = TicketService.get(code)
            if ticket:
                results.append(ticket)
        return results

    @staticmethod
    def validate(query):
        with StaffModel.transaction() as model:
            codes = model.lookup_checkin_codes((query or '').strip())
        if not codes:
            return None, 'Không tìm thấy mã vé hoặc mã QR.'
        if len(codes) != 1:
            return None, 'Mã không xác định; hãy dùng mã đặt chỗ cụ thể.'
        ticket = TicketService.get(codes[0])
        if not ticket or ticket['payment_status'] != 'SUCCESS':
            return None, 'Vé chưa thanh toán thành công.'
        if any(s['status'] in ('CANCELLED', 'REFUNDED') for s in ticket['seats']):
            return None, 'Vé đã bị hủy.'
        if any(s['status'] == 'USED' for s in ticket['seats']):
            return None, 'Vé đã được sử dụng'
        if as_datetime(ticket['start_time']).date() != datetime.now().date():
            return None, 'Vé không đúng suất chiếu hôm nay.'
        return ticket, None

    @staticmethod
    def check_in(query):
        ticket, error = StaffService.validate(query)
        if error:
            return None, error
        with StaffModel.transaction() as model:
            for seat in ticket['seats']:
                if not model.mark_used(seat['id']):
                    raise RuntimeError('Check-in thất bại; giao dịch đã rollback.')
        return ticket, None

    @staticmethod
    def cancel(code):
        with StaffModel.transaction() as model:
            seats = model.ticket_group(code)
            if not seats:
                return None, 'Không tìm thấy đơn đặt chỗ.'
            if any(s['status'] != 'BOOKED' for s in seats) or any(s['payment_status'] != 'SUCCESS' for s in seats):
                return None, 'Chỉ hỗ trợ hủy vé BOOKED đã thanh toán và chưa check-in.'
            if any(as_datetime(s['start_time']) - datetime.now() < timedelta(minutes=60) for s in seats):
                return None, 'Chỉ được hỗ trợ hủy khi còn ít nhất 60 phút trước giờ chiếu.'
            if not model.refund(code):
                return None, 'Không thể hoàn tiền giao dịch này.'
            model.cancel_group(code)
            return {'booking_code': code, 'message': 'Đã hủy vé và hoàn tiền; ghế đã được mở bán lại.'}, None