"""SQLite-only preview operations with atomic holds and auditable AI decisions."""
from datetime import datetime, timedelta
import uuid
from app.models.preview import PreviewModel
from app.models.hold_cleanup import cleanup_expired_holds
from app.services.screening_rules import SEAT_HOLD_MINUTES, sales_open


class PreviewService:
    @staticmethod
    def update_movie(movie_id, duration, status):
        if duration <= 0 or status not in ('SHOWING', 'COMING_SOON', 'ENDED'):
            raise ValueError("Thời lượng/trạng thái không hợp lệ")
        with PreviewModel.transaction() as model:
            current = model.movie(movie_id)
            if current and model.has_screenings(movie_id) and current["duration_minutes"] != duration:
                raise ValueError("Phim đã có lịch chiếu: không đổi thời lượng khi chưa điều chỉnh lịch.")
            return model.update_movie(movie_id, duration, status)

    @staticmethod
    def hold(user_id, screening_id, seat_ids):
        if type(seat_ids) is int:
            seat_ids = [seat_ids]
        if (not isinstance(seat_ids, list) or not 1 <= len(seat_ids) <= 4
                or any(type(seat_id) is not int or seat_id < 1 for seat_id in seat_ids)
                or len(set(seat_ids)) != len(seat_ids)):
            return {'error': 'Chọn từ 1 đến 4 ghế khác nhau, ID là số nguyên dương.'}, 400
        with PreviewModel.transaction() as model:
            now = datetime.now()
            cleanup_expired_holds(model.connection, now)
            show = model.screening(screening_id)
            if show is None:
                return None, 404
            if not sales_open(show["start_time"], now):
                return {"error": "Suất chiếu đã đóng đặt ghế."}, 409
            # Validate every seat before inserting any hold under the write lock.
            for seat_id in seat_ids:
                if not model.seat_in_room(seat_id, show['room_id']):
                    return {'error': f'Ghế ID {seat_id} không thuộc phòng chiếu.'}, 400
                if model.sold(screening_id, seat_id):
                    return {'error': f'Ghế ID {seat_id} đã bán; chưa giữ bất kỳ ghế nào.'}, 409
                if model.hold(screening_id, seat_id):
                    return {'error': f'Ghế ID {seat_id} đang được giữ; chưa giữ bất kỳ ghế nào.'}, 409
            expiry = (now + timedelta(minutes=SEAT_HOLD_MINUTES)).isoformat(sep=" ", timespec="seconds")
            group_code = 'CV-' + uuid.uuid4().hex.upper()
            hold_ids = [model.save_hold(user_id, screening_id, seat_id, expiry, group_code)
                        for seat_id in seat_ids]
            hold_id = hold_ids[0]
            return {"seat_ids": seat_ids, "screening_id": screening_id, "expires_at": expiry,
                    "booking_code": group_code,
                    "hold_id": hold_id, "checkout_url": f"/checkout/{hold_id}",
                    "message": "Đã giữ ghế 5 phút; vui lòng thanh toán trước khi hết hạn."}, 201

    @staticmethod
    def review(draft_id, reviewer_id, decision, edited_text=None):
        if decision not in ("APPROVED", "REJECTED"):
            return False
        with PreviewModel.transaction() as model:
            draft = model.draft(draft_id)
            if not draft or draft["status"] != "DRAFT" or draft["content_type"] != "MOVIE_DESCRIPTION":
                return False
            if decision == "APPROVED":
                text = draft['generated_text'] if edited_text is None else edited_text
                if not isinstance(text, str) or not text.strip() or len(text.split()) > 150:
                    raise ValueError('Mô tả phải có nội dung và không vượt quá 150 từ.')
                if draft["movie_id"]:
                    if not model.movie(draft['movie_id']):
                        return False
                    model.update_synopsis(draft["movie_id"], text.strip())
                else:
                    model.publish_draft(draft, text.strip())
            model.review(draft_id, reviewer_id, decision, datetime.now().isoformat(sep=" "))
            return True

    @staticmethod
    def lookup(query):
        if not isinstance(query, str) or not query.strip():
            return []
        return PreviewModel.lookup(query.strip())