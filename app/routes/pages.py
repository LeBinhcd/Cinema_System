"""Browser pages for the read-only preview."""
from flask import Blueprint, abort, current_app, flash, jsonify, render_template, request, session, redirect, url_for
from sqlite3 import IntegrityError
from hmac import compare_digest
from app.auth import admin_required, staff_required
from app.services.preview_service import PreviewService
from app.services.catalog_service import CatalogService
from app.services.seat_map_service import SeatMapService
from app.services.payment_service import BASE_PRICES, PaymentService
from app.services.ticket_service import TicketService
from app.services.admin_service import AdminService
from app.services.staff_service import StaffService
from app.services.movie_service import MovieService

pages_bp = Blueprint("pages", __name__)


@pages_bp.get("/")
@pages_bp.get("/movies")
def index():
    return render_template("index.html", movies=[m for m in CatalogService.movies() if m["status"] == "SHOWING"],
                           screenings=[s for s in CatalogService.screenings() if s["sales_open"]])


@pages_bp.get("/movie/<int:movie_id>")
def movie(movie_id):
    movie = next((m for m in CatalogService.movies() if m["id"] == movie_id), None)
    if movie is None:
        abort(404)
    return render_template("movie.html", movie=movie, screenings=[s for s in CatalogService.screenings()
                           if s["movie_id"] == movie_id and s["sales_open"]])


@pages_bp.get("/booking/<int:screening_id>")
def booking(screening_id):
    screening = SeatMapService.get_for_screening(screening_id)
    if screening is None:
        abort(404)
    return render_template("booking.html", screening=screening, prices=BASE_PRICES)


@pages_bp.get("/login")
def login():
    return render_template("login.html", show_demo_accounts=current_app.config["APP_ENV"].lower() in ("development", "demo", "testing"))


@pages_bp.get("/admin")
@admin_required
def dashboard():
    return render_template("admin.html", movies=CatalogService.movies(),
                           screenings=CatalogService.screenings(), drafts=CatalogService.drafts(), rooms=AdminService.rooms())


def admin_csrf():
    token = session.get('csrf_token')
    if not token or not compare_digest(request.form.get('csrf_token', ''), token):
        abort(403)


def admin_action(action, message, section):
    admin_csrf()
    try:
        action()
        flash(message, 'success')
    except (ValueError, TypeError, OverflowError) as exc:
        flash(str(exc), 'danger')
    except IntegrityError:
        flash('Dữ liệu bị trùng hoặc tham chiếu không hợp lệ; chưa lưu thay đổi.', 'danger')
    return redirect(url_for('pages.dashboard', _anchor=section))


@pages_bp.post('/admin/movies/add')
@admin_required
def add_movie():
    return admin_action(lambda: AdminService.stage_movie(request.form), 'Đã lưu vào danh sách chờ duyệt.', 'drafts')


@pages_bp.post('/admin/movies/generate-description')
@admin_required
def generate_movie_description():
    token = session.get('csrf_token')
    supplied_token = request.headers.get('X-CSRF-Token', '')
    if not token or not compare_digest(supplied_token.encode('utf-8'), token.encode('utf-8')):
        return jsonify(success=False, error='Mã xác nhận không hợp lệ; hãy tải lại trang.'), 403
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify(success=False, error='Payload JSON không hợp lệ.'), 400
    try:
        description = MovieService.generate_description(
            data.get('title'), data.get('keywords', ''), data.get('age_rating', 'P'))
        return jsonify(success=True, description=description)
    except ValueError as exc:
        return jsonify(success=False, error=str(exc)), 400
    except RuntimeError as exc:
        return jsonify(success=False, error=str(exc)), 503
    except Exception:
        current_app.logger.exception('Movie description generation failed')
        return jsonify(success=False, error='Không thể sinh mô tả lúc này. Vui lòng thử lại sau.'), 503


@pages_bp.post('/admin/movies/<int:movie_id>/toggle-status')
@admin_required
def toggle_movie(movie_id):
    return admin_action(lambda: AdminService.toggle_movie(movie_id), 'Đã đổi trạng thái phim.', 'movies')


@pages_bp.post('/admin/screenings/add')
@admin_required
def add_screening():
    return admin_action(lambda: AdminService.add_screening(request.form), 'Đã thêm suất chiếu.', 'screenings')


@pages_bp.post('/admin/rooms/add')
@admin_required
def add_room():
    return admin_action(lambda: AdminService.add_room(request.form), 'Đã tạo phòng và toàn bộ ghế.', 'rooms')


@pages_bp.post('/admin/rooms/<int:room_id>/toggle-status')
@admin_required
def toggle_room(room_id):
    return admin_action(lambda: AdminService.toggle_room(room_id), 'Đã đổi trạng thái phòng.', 'rooms')


@pages_bp.post("/admin/movies/<int:movie_id>/edit")
@admin_required
def edit_movie(movie_id):
    def update():
        updated = PreviewService.update_movie(movie_id, int(request.form.get("duration_minutes", 0)), request.form.get("status"))
        if not updated:
            raise ValueError('Phim không tồn tại.')
    return admin_action(update, 'Đã cập nhật phim.', 'movies')


@pages_bp.post("/admin/drafts/<int:draft_id>/<decision>")
@admin_required
def review_draft(draft_id, decision):
    decision = {'approve': 'APPROVED', 'reject': 'REJECTED'}.get(decision, decision.upper())
    def review():
        if not PreviewService.review(draft_id, session['user_id'], decision,
                                     request.form.get('edited_synopsis', request.form.get('edited_text'))):
            raise ValueError('Bản nháp không tồn tại, đã được duyệt hoặc quyết định không hợp lệ.')
    message = 'Đã phê duyệt và tạo phim thành công.' if decision == 'APPROVED' else 'Đã hủy/từ chối bản nháp; phim chưa được tạo.'
    return admin_action(review, message, 'drafts')


@pages_bp.get('/admin/api/revenue-report')
@admin_required
def revenue_report():
    try:
        return jsonify(success=True, report=AdminService.revenue_report(
            request.args.get('from_date'), request.args.get('to_date')))
    except ValueError as exc:
        return jsonify(success=False, error=str(exc)), 400


@pages_bp.post('/admin/api/revenue-ai-summary')
@admin_required
def revenue_ai_summary():
    token = session.get('csrf_token')
    supplied = request.headers.get('X-CSRF-Token', '')
    if not token or not compare_digest(supplied.encode('utf-8'), token.encode('utf-8')):
        return jsonify(success=False, error='Mã xác nhận không hợp lệ; hãy tải lại trang.'), 403
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify(success=False, error='Payload JSON không hợp lệ.'), 400
    try:
        report = AdminService.revenue_report(data.get('from_date'), data.get('to_date'))
        return jsonify(success=True, summary=AdminService.revenue_ai_summary(report),
                       report=report, status='DRAFT')
    except ValueError as exc:
        return jsonify(success=False, error=str(exc)), 400
    except RuntimeError as exc:
        return jsonify(success=False, error=str(exc)), 503
    except Exception:
        current_app.logger.exception('Revenue AI summary failed')
        return jsonify(success=False, error='Không thể tạo nhận xét AI lúc này.'), 503


@pages_bp.get("/staff")
@staff_required
def staff():
    query = request.args.get("q", "").strip()
    return render_template("staff.html", query=query, tickets=StaffService.lookup(query), screenings=StaffService.screenings_today(), prices=BASE_PRICES)


def staff_csrf():
    token = session.get('csrf_token')
    if not token or not compare_digest(request.headers.get('X-CSRF-Token', ''), token):
        return jsonify({'error': 'Mã xác nhận không hợp lệ; hãy tải lại trang.'}), 403


@pages_bp.post('/api/staff/pos/sell')
@staff_required
def staff_sell():
    invalid = staff_csrf()
    if invalid:
        return invalid
    data = request.get_json(silent=True) or {}
    try:
        result, error = StaffService.sell(int(data['screening_id']), data['seat_ids'], data.get('name'), data.get('phone'), data.get('payment_method'), session['user_id'])
    except (KeyError, TypeError, ValueError):
        return jsonify({'error': 'Thông tin bán vé chưa hợp lệ.'}), 400
    return jsonify(result or {'error': error}), 201 if result else 409


@pages_bp.get('/api/staff/pos/screening/<int:screening_id>/seats')
@staff_required
def staff_seats(screening_id):
    result = SeatMapService.get_for_screening(screening_id)
    if result is None:
        return jsonify({'error': 'Không tìm thấy suất chiếu.'}), 404
    return jsonify(result)


@pages_bp.post('/api/staff/cancel')
@staff_required
def staff_cancel():
    invalid = staff_csrf()
    if invalid:
        return invalid
    data = request.get_json(silent=True) or {}
    result, error = StaffService.cancel(data.get('booking_code', '').strip())
    return jsonify(result or {'error': error}), 200 if result else 409


@pages_bp.get('/api/staff/ticket/<booking_code>')
@staff_required
def staff_ticket(booking_code):
    ticket_data = TicketService.get(booking_code)
    if not ticket_data:
        return jsonify({'error': 'Không tìm thấy vé.'}), 404
    return jsonify(ticket_data)


@pages_bp.post("/api/booking/hold-seat")
def hold_seat():
    if not session.get("user_id"):
        return jsonify({"error": "Vui lòng đăng nhập để giữ ghế."}), 401
    if not compare_digest(request.headers.get("X-CSRF-Token", ""), session.get("csrf_token", "")):
        return jsonify({"error": "Mã xác nhận không hợp lệ."}), 403
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Yêu cầu JSON object."}), 400
    try:
        screening_id = data.get('screening_id')
        if type(screening_id) is not int or screening_id < 1:
            raise ValueError
    except (TypeError, ValueError):
        return jsonify({"error": "screening_id phải là số nguyên dương."}), 400
    seat_ids = data.get('seat_ids', [data.get('seat_id')])
    result, code = PreviewService.hold(session["user_id"], screening_id, seat_ids)
    return jsonify(result or {"error": "Suất chiếu không tồn tại."}), code


@pages_bp.get("/checkout/<int:hold_id>")
def checkout(hold_id):
    if not session.get("user_id"):
        return redirect(url_for("pages.login"))
    order = PaymentService.checkout(hold_id, session["user_id"])
    if order is None:
        abort(404, description="Giữ ghế không tồn tại hoặc đã hết hạn.")
    return render_template("checkout.html", order=order)


@pages_bp.get("/ticket/<booking_code>")
def ticket(booking_code):
    if not session.get("user_id"):
        return redirect(url_for("pages.login"))
    ticket_data = TicketService.get(booking_code, session["user_id"])
    if ticket_data is None:
        abort(404)
    return render_template("ticket.html", ticket=ticket_data)


@pages_bp.get('/my-tickets')
def my_tickets():
    if not session.get('user_id'):
        return redirect(url_for('pages.login'))
    if session.get('role') != 'CUSTOMER':
        abort(403)
    return render_template('my_tickets.html', tickets=TicketService.history(session['user_id']))


@pages_bp.post("/api/payment/process")
def process_payment():
    if not session.get("user_id"):
        return jsonify({"error": "Vui lòng đăng nhập."}), 401
    if not compare_digest(request.headers.get("X-CSRF-Token", ""), session.get("csrf_token", "")):
        return jsonify({"error": "Mã xác nhận không hợp lệ."}), 403
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or type(data.get("hold_id")) is not int or type(data.get("success")) is not bool or not isinstance(data.get("payment_method"), str):
        return jsonify({"error": "Yêu cầu hold_id số nguyên, success boolean và payment_method."}), 400
    result, error = PaymentService.process(data["hold_id"], session["user_id"], data["payment_method"], data["success"])
    if error:
        return jsonify({"error": error}), 409
    return jsonify(result)


@pages_bp.post('/api/ticket/cancel')
def cancel_ticket():
    if not session.get('user_id'):
        return jsonify({'error': 'Vui lòng đăng nhập.'}), 401
    token = session.get('csrf_token')
    if not token or not compare_digest(request.headers.get('X-CSRF-Token', ''), token):
        return jsonify({'error': 'Mã xác nhận không hợp lệ.'}), 403
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or not isinstance(data.get('booking_code'), str) or not data['booking_code'].strip():
        return jsonify({'error': 'Yêu cầu mã đặt chỗ hợp lệ.'}), 400
    result, error = TicketService.cancel(data['booking_code'].strip(), session['user_id'])
    if error:
        return jsonify({'error': error}), 409
    return jsonify(result)


@pages_bp.post("/api/staff/check-in")
@staff_required
def staff_check_in():
    invalid = staff_csrf()
    if invalid:
        return invalid
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or not isinstance(data.get("query"), str) or not data["query"].strip():
        return jsonify({"error": "Nhập mã vé, QR hoặc số điện thoại."}), 400
    ticket_data, error = StaffService.check_in(data["query"])
    if error:
        return jsonify({"error": error}), 409
    return jsonify({"message": "Check-in thành công.", "ticket": ticket_data})