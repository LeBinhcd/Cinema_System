"""Validated browser admin operations on SQLite."""
import json
from datetime import date, datetime, timedelta
from urllib.parse import urlsplit
from app.models.admin import AdminModel
from app.services.screening_rules import validate_schedule
from app.services.movie_service import MovieService
from app.services.gemini_service import generate_response, API_ERROR_MESSAGE, CONFIG_ERROR_MESSAGE


class AdminService:
    @staticmethod
    def _movie_data(data):
        data = dict(data)
        for field in ('title', 'genre', 'release_date', 'synopsis'):
            data[field] = data.get(field, '').strip()
            if not data[field]:
                raise ValueError(f'Vui lòng nhập {field}.')
        data['duration'] = AdminService.positive(data.get('duration'), 'Thời lượng')
        data['age_rating'] = MovieService.validate_age_rating(data.get('age_rating', 'P'))
        data['keywords'] = data.get('keywords', '').strip()
        if len(data['keywords']) > 500:
            raise ValueError('Từ khóa tối đa 500 ký tự.')
        try:
            data['release_date'] = date.fromisoformat(data['release_date']).isoformat()
        except (ValueError, TypeError):
            raise ValueError('Ngày phát hành không hợp lệ.') from None
        poster = data.get('poster_url', '').strip()
        if poster and (urlsplit(poster).scheme not in ('http', 'https') or not urlsplit(poster).netloc):
            raise ValueError('Poster phải là URL http/https hợp lệ.')
        data['metadata_json'] = json.dumps({'poster_url': poster}, ensure_ascii=False)
        data['status'] = data.get('status', 'SHOWING')
        if data['status'] not in ('SHOWING', 'COMING_SOON', 'ENDED'):
            raise ValueError('Trạng thái phim không hợp lệ.')
        return data

    @staticmethod
    def stage_movie(data):
        data = AdminService._movie_data(data)
        if len(data['synopsis'].split()) > 150:
            raise ValueError('Mô tả phải có tối đa 150 từ.')
        with AdminModel.transaction() as model:
            return model.add_movie_draft(data)

    @staticmethod
    def revenue_report(from_date, to_date):
        try:
            start, end = date.fromisoformat(from_date), date.fromisoformat(to_date)
        except (ValueError, TypeError):
            raise ValueError('Chọn ngày bắt đầu và kết thúc hợp lệ (YYYY-MM-DD).') from None
        if start > end:
            raise ValueError('Ngày bắt đầu không được sau ngày kết thúc.')
        report = AdminModel.revenue_report(start.isoformat(), end.isoformat())
        return dict(report, from_date=start.isoformat(), to_date=end.isoformat())

    @staticmethod
    def revenue_ai_summary(report):
        prompt = ('Đóng vai trò chuyên gia vận hành rạp, hãy đưa ra nhận xét ngắn gọn 3-4 câu '
                  'về hiệu quả kinh doanh dựa trên số liệu sau: '
                  + json.dumps(report, ensure_ascii=False) + '. '
                  'total_revenue là VNĐ theo ngày giao dịch SUCCESS; tickets_sold theo ngày tạo vé; '
                  'occupancy_rate là % ghế đã bán trên tổng ghế các suất trong khoảng ngày. '
                  'Đưa ra 1 gợi ý tối ưu suất chiếu bằng tiếng Việt. Đây là nháp nội bộ. '
                  'Chỉ dùng số liệu đã cung cấp, không khẳng định xu hướng tăng/giảm khi không có kỳ so sánh.')
        text = generate_response(prompt)
        if not isinstance(text, str) or not text.strip() or text in (API_ERROR_MESSAGE, CONFIG_ERROR_MESSAGE):
            raise RuntimeError('Không thể tạo nhận xét AI lúc này. Kiểm tra cấu hình Groq hoặc thử lại sau.')
        return text.strip()

    @staticmethod
    def positive(value, label):
        try:
            number = int(value)
        except (ValueError, TypeError):
            raise ValueError(f'{label} phải là số nguyên dương.') from None
        if number <= 0:
            raise ValueError(f'{label} phải lớn hơn 0.')
        return number

    @staticmethod
    def add_movie(data):
        data = AdminService._movie_data(data)
        with AdminModel.transaction() as model:
            return model.add_movie(data)

    @staticmethod
    def toggle_movie(movie_id):
        with AdminModel.transaction() as model:
            movie = model.movie_details(movie_id)
            if not movie:
                raise ValueError('Phim không tồn tại.')
            model.set_movie_status(movie_id, 'ENDED' if movie['status'] == 'SHOWING' else 'SHOWING')

    @staticmethod
    def edit_movie(movie_id, data):
        data = AdminService._movie_data(data)
        if len(data['synopsis'].split()) > 150:
            raise ValueError('Mô tả phải có tối đa 150 từ.')
        with AdminModel.transaction() as model:
            if not model.movie_details(movie_id):
                raise ValueError('Phim không tồn tại.')
            return model.update_movie(movie_id, data)

    @staticmethod
    def rooms():
        return AdminModel.rooms()

    @staticmethod
    def add_room(data):
        name = data.get('name', '').strip()
        rows = AdminService.positive(data.get('row_count', 5), 'Số hàng')
        columns = AdminService.positive(data.get('column_count', 8), 'Số ghế mỗi hàng')
        if not name or rows > 26 or columns > 30:
            raise ValueError('Nhập tên phòng; tối đa 26 hàng và 30 ghế mỗi hàng.')
        seats = [(chr(65 + row), number, 'STANDARD' if row < 2 else 'VIP' if row < 4 else 'COUPLE')
                 for row in range(rows) for number in range(1, columns + 1)]
        with AdminModel.transaction() as model:
            return model.add_room({'name': name, 'row_count': rows, 'column_count': columns}, seats)

    @staticmethod
    def toggle_room(room_id):
        with AdminModel.transaction() as model:
            room = model.room(room_id)
            if not room:
                raise ValueError('Phòng không tồn tại.')
            model.set_room_status(room_id, 'MAINTENANCE' if room['status'] == 'ACTIVE' else 'ACTIVE')

    @staticmethod
    def add_screening(data):
        movie_id = AdminService.positive(data.get('movie_id'), 'Phim')
        room_id = AdminService.positive(data.get('room_id'), 'Phòng')
        try:
            start = datetime.fromisoformat(data.get('start_time', ''))
        except (ValueError, TypeError):
            raise ValueError('Giờ bắt đầu không hợp lệ.') from None
        if start.tzinfo is not None:
            raise ValueError('Sử dụng giờ địa phương không kèm múi giờ.')
        with AdminModel.transaction() as model:
            movie, room = model.movie_details(movie_id), model.room(room_id)
            if not movie or not room:
                raise ValueError('Phim hoặc phòng không tồn tại.')
            if room['status'] != 'ACTIVE':
                raise ValueError('Phòng đang bảo trì; không thể thêm suất chiếu.')
            end = start + timedelta(minutes=movie['duration_minutes'])
            validate_schedule(start, end, model.room_screenings(room_id))
            return model.add_screening(movie_id, room_id, start, end)

    @staticmethod
    def delete_screening(screening_id):
        screening_id = AdminService.positive(screening_id, 'Suất chiếu')
        with AdminModel.transaction() as model:
            screening = model.connection.execute(
                'SELECT id FROM screenings WHERE id=?', (screening_id,)
            ).fetchone()
            if not screening:
                raise ValueError('Suất chiếu không tồn tại.')
            dependencies = model.screening_delete_dependencies(screening_id)
            if dependencies['tickets'] or dependencies['holds']:
                raise ValueError('Không thể xóa suất đã có vé hoặc ghế đang được giữ.')
            if not model.delete_screening(screening_id):
                raise ValueError('Không thể xóa suất chiếu.')

    @staticmethod
    def delete_movie(movie_id):
        movie_id = AdminService.positive(movie_id, 'Phim')
        with AdminModel.transaction() as model:
            if not model.movie_details(movie_id):
                raise ValueError('Phim không tồn tại.')
            dependencies = model.movie_delete_dependencies(movie_id)
            if dependencies['screenings'] or dependencies['tickets'] or dependencies['holds']:
                raise ValueError('Không thể xóa phim còn suất chiếu, vé hoặc ghế đang được giữ.')
            if not model.delete_movie(movie_id):
                raise ValueError('Không thể xóa phim.')