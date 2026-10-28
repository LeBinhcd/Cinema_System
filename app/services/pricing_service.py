"""Admin-managed base ticket prices for new bookings."""
from app.database import get_connection
from app.models.admin import AdminModel

SEAT_TYPES = ('STANDARD', 'VIP', 'COUPLE')


class PricingService:
    @staticmethod
    def list_prices():
        return AdminModel.pricing_rules()

    @staticmethod
    def prices(connection=None):
        owns_connection = connection is None
        connection = connection or get_connection()
        try:
            return {row['seat_type']: row['price'] for row in connection.execute(
                'SELECT seat_type, price FROM pricing_rules'
            )}
        finally:
            if owns_connection:
                connection.close()

    @staticmethod
    def update(seat_type, raw_price):
        seat_type = str(seat_type or '').strip().upper()
        if seat_type not in SEAT_TYPES:
            raise ValueError('Loại ghế không hợp lệ.')
        try:
            price = int(raw_price)
        except (TypeError, ValueError):
            raise ValueError('Giá vé phải là số nguyên.') from None
        if price < 0:
            raise ValueError('Giá vé không được âm.')
        with AdminModel.transaction() as model:
            if not model.update_pricing_rule(seat_type, price):
                raise ValueError('Không tìm thấy bảng giá.')
        return {'seat_type': seat_type, 'price': price}

    @staticmethod
    def movie_prices(movie_id):
        return AdminModel.movie_pricing(movie_id)

    @staticmethod
    def update_movie_price(movie_id, seat_type, raw_price):
        try:
            movie_id = int(movie_id)
        except (TypeError, ValueError):
            raise ValueError('Phim không hợp lệ.') from None
        seat_type = str(seat_type or '').strip().upper()
        if seat_type not in SEAT_TYPES:
            raise ValueError('Loại ghế không hợp lệ.')
        try:
            price = int(raw_price)
        except (TypeError, ValueError):
            raise ValueError('Giá vé phải là số nguyên.') from None
        if price < 0:
            raise ValueError('Giá vé không được âm.')
        with AdminModel.transaction() as model:
            if not model.update_movie_pricing(movie_id, seat_type, price):
                raise ValueError('Phim không tồn tại.')
        return {'movie_id': movie_id, 'seat_type': seat_type, 'price': price}

    @staticmethod
    def effective_prices(connection, movie_id):
        defaults = {row['seat_type']: row['price'] for row in connection.execute(
            'SELECT seat_type, price FROM pricing_rules'
        )}
        overrides = {row['seat_type']: row['price'] for row in connection.execute(
            'SELECT seat_type, price FROM movie_pricing_rules WHERE movie_id=?', (movie_id,)
        )}
        defaults.update(overrides)
        return defaults