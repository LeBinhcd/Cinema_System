import secrets
import uuid

"""Browser pages for the read-only preview."""
from pathlib import Path
from flask import send_from_directory

from flask import Blueprint, abort, current_app, flash, jsonify, render_template, request, session, redirect, url_for
from sqlite3 import IntegrityError
from hmac import compare_digest
from app.auth import admin_required, staff_required, customer_required
from app.services.preview_service import PreviewService
from app.services.external_movie_metadata import ExternalMetadataError
from app.services.catalog_service import CatalogService

from app.services.seat_map_service import SeatMapService
from app.services.payment_service import BASE_PRICES, PaymentService
from app.services.ticket_service import TicketService
from app.services.admin_service import AdminService
from app.services.staff_service import StaffService
from app.database import get_connection
from app.services.movie_service import MovieService

from app.services.auth_service import AuthService

pages_bp = Blueprint("pages", __name__)


def spa_index():
    frontend_index = Path(current_app.root_path) / 'frontend' / 'dist' / 'index.html'
    if frontend_index.exists():
        return send_from_directory(frontend_index.parent, 'index.html')
    return None


@pages_bp.get('/api/checkout/<int:hold_id>')
@customer_required
def checkout_api(hold_id):
    if not session.get('user_id'):
        return jsonify({'error': 'Vui lòng đăng nhập.'}), 401
    order = PaymentService.checkout(hold_id, session['user_id'])
    if order is None:
        return jsonify({'error': 'Giữ ghế không tồn tại hoặc đã hết hạn.'}), 404
    for key in ('expires_at', 'start_time'):
        if hasattr(order.get(key), 'isoformat'):
            order[key] = order[key].isoformat(sep=' ')
    return jsonify(order)


@pages_bp.get('/api/tickets')
@customer_required
def tickets_api():
    if not session.get('user_id'):
        return jsonify({'error': 'Vui lòng đăng nhập.'}), 401
    if session.get('role') != 'CUSTOMER':
        return jsonify({'error': 'Chỉ khách hàng mới có lịch sử vé.'}), 403
    return jsonify({'tickets': TicketService.history(session['user_id'])})

@pages_bp.get('/api/ticket/<booking_code>')
@customer_required
def ticket_api(booking_code):
    if not session.get('user_id'):
        return jsonify({'error': 'Vui lòng đăng nhập.'}), 401
    ticket_data = TicketService.get(booking_code, session['user_id'])
    if ticket_data is None:
        return jsonify({'error': 'Không tìm thấy vé.'}), 404
    return jsonify(ticket_data)



@pages_bp.get("/")
@pages_bp.get("/movies")
def index():
    frontend = spa_index()
    if frontend is not None:
        return frontend
    abort(503, description="React frontend chưa được build. Hãy chạy npm run build.")






@pages_bp.get('/api/saved-cards')
@customer_required
def saved_cards():
    if not session.get('user_id'):
        return jsonify(error='Vui lòng đăng nhập.'), 401
    with get_connection() as db:
        rows=db.execute('SELECT id,cardholder_name,brand,last4,created_at FROM saved_cards WHERE user_id=? ORDER BY id DESC',(session['user_id'],)).fetchall()
    return jsonify({'cards':[dict(row) for row in rows]})

@pages_bp.post('/api/saved-cards')
@customer_required
def add_saved_card():
    if not session.get('user_id'):
        return jsonify(error='Vui lòng đăng nhập.'), 401
    if not compare_digest(request.headers.get('X-CSRF-Token',''),session.get('csrf_token','')):
        return jsonify(error='Mã xác nhận không hợp lệ.'),403
    data=request.get_json(silent=True) or {}; cardholder=str(data.get('cardholder_name','')).strip(); brand=str(data.get('brand','')).strip().upper(); last4=str(data.get('last4','')).strip()
    if len(cardholder)<2 or brand not in {'VISA','MASTERCARD','JCB','NAPAS'} or not last4.isdigit() or len(last4)!=4:
        return jsonify(error='Thông tin thẻ demo không hợp lệ.'),400
    token='CARD-'+secrets.token_urlsafe(24)
    with get_connection() as db:
        row=db.execute('INSERT INTO saved_cards(user_id,cardholder_name,brand,last4,token) VALUES(?,?,?,?,?)',(session['user_id'],cardholder,brand,last4,token));db.commit(); card_id=row.lastrowid
    return jsonify({'id':card_id,'cardholder_name':cardholder,'brand':brand,'last4':last4}),201

@pages_bp.delete('/api/saved-cards/<int:card_id>')
@customer_required
def delete_saved_card(card_id):
    if not session.get('user_id'):
        return jsonify(error='Vui lòng đăng nhập.'),401
    if not compare_digest(request.headers.get('X-CSRF-Token',''),session.get('csrf_token','')):
        return jsonify(error='Mã xác nhận không hợp lệ.'),403
    with get_connection() as db:
        deleted=db.execute('DELETE FROM saved_cards WHERE id=? AND user_id=?',(card_id,session['user_id'])).rowcount;db.commit()
    return jsonify({'deleted':bool(deleted)}) if deleted else (jsonify(error='Không tìm thấy thẻ.'),404)

@pages_bp.get('/api/catalog')
def catalog_api():
    movies=CatalogService.movies(); screenings=CatalogService.screenings()
    for item in movies: item.pop('metadata_json',None)
    for item in screenings:
        for key in ('start_time','end_time'):
            if item.get(key) is not None: item[key]=item[key].isoformat(sep=' ')
    return jsonify({'movies':[m for m in movies if m.get('status') in ('SHOWING','COMING_SOON')],'screenings':[s for s in screenings if s.get('sales_open')],'csrf_token':session.get('csrf_token'),'user':({'id':session.get('user_id'),'name':session.get('full_name'),'email':session.get('email'),'user_code':session.get('user_code'),'role':session.get('role')} if session.get('user_id') else None)})

@pages_bp.get('/assets/<path:filename>')
def frontend_assets(filename):
    assets_dir = Path(current_app.root_path) / 'frontend' / 'dist' / 'assets'
    return send_from_directory(assets_dir, filename)


@pages_bp.get("/movie/<int:movie_id>")
def movie(movie_id):
    movie_data = next((m for m in CatalogService.movies() if m["id"] == movie_id), None)
    if movie_data is None:
        abort(404)
    if spa_index():
        return spa_index()
    abort(503, description="React frontend chưa được build. Hãy chạy npm run build trong app/frontend.")


@pages_bp.get("/booking/<int:screening_id>")
def booking(screening_id):
    if spa_index():
        return spa_index()
    if spa_index():
        return spa_index()
    abort(503, description="React frontend chưa được build. Hãy chạy npm run build trong app/frontend.")


@pages_bp.get("/login")
def login():
    frontend_index = Path(current_app.root_path) / 'frontend' / 'dist' / 'index.html'
    if spa_index():
        return spa_index()
    abort(503, description="React frontend chưa được build. Hãy chạy npm run build trong app/frontend.")


@pages_bp.get("/admin")
@admin_required
def dashboard():
    if spa_index():
        return spa_index()
    abort(503, description="React frontend chưa được build. Hãy chạy npm run build trong app/frontend.")


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
    except ExternalMetadataError as exc:
        return jsonify(success=False, error=str(exc), code='EXTERNAL_METADATA_ERROR'), 503
    except RuntimeError as exc:
        return jsonify(success=False, error=str(exc)), 503
    except Exception:
        current_app.logger.exception('Movie description generation failed')
        return jsonify(success=False, error='Không thể sinh mô tả lúc này. Vui lòng thử lại sau.'), 503


@pages_bp.post('/admin/movies/<int:movie_id>/update')
@admin_required
def update_movie_react(movie_id):
    token = session.get('csrf_token')
    supplied = request.headers.get('X-CSRF-Token', '')
    if not token or not compare_digest(supplied.encode(), token.encode()):
        return jsonify(success=False, error='Mã xác nhận không hợp lệ; hãy tải lại trang.'), 403
    data = request.get_json(silent=True) or {}
    try:
        AdminService.edit_movie(movie_id, data)
        return jsonify(success=True, message='Đã cập nhật phim.')
    except ValueError as exc:
        return jsonify(success=False, error=str(exc)), 400

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



@pages_bp.get('/api/staff/lookup')
@staff_required
def staff_lookup_api():
    return jsonify({'tickets': StaffService.lookup(request.args.get('q', ''))})

@pages_bp.get('/api/staff/screenings')
@staff_required
def staff_screenings_api():

    return jsonify({'screenings': StaffService.screenings_today()})

@pages_bp.post('/api/admin/staff')
@admin_required
def create_staff_api():
    data=request.get_json(silent=True) or {}
    try:
        account=AuthService.create_staff(data.get('full_name'),data.get('email'),data.get('password'))
        return jsonify(account),201
    except ValueError as exc:
        return jsonify(error=str(exc)),400

@pages_bp.get('/api/admin/dashboard')
@admin_required
def admin_dashboard_api():
    return jsonify({'movies': CatalogService.movies(), 'screenings': CatalogService.screenings(), 'rooms': AdminService.rooms(), 'drafts': CatalogService.drafts()})
@pages_bp.get("/staff")
@staff_required
def staff():
    if spa_index():
        return spa_index()
    abort(503, description="React frontend chưa được build. Hãy chạy npm run build trong app/frontend.")


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
@customer_required
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
@customer_required
def checkout(hold_id):
    if not session.get("user_id"):
        return redirect(url_for("pages.login"))
    if spa_index():
        return spa_index()
    if spa_index():
        return spa_index()
    abort(503, description="React frontend chưa được build. Hãy chạy npm run build trong app/frontend.")


@pages_bp.get("/ticket/<booking_code>")
@customer_required
def ticket(booking_code):
    if not session.get("user_id"):
        return redirect(url_for("pages.login"))
    if spa_index():
        return spa_index()
    if spa_index():
        return spa_index()
    abort(503, description="React frontend chưa được build. Hãy chạy npm run build trong app/frontend.")


@pages_bp.get('/my-tickets')
@customer_required
def my_tickets():
    if session.get('user_id') and session.get('role') == 'CUSTOMER' and spa_index():
        return spa_index()
    if not session.get('user_id'):
        return redirect(url_for('pages.login'))
    if spa_index():
        return spa_index()
    abort(503, description="React frontend chưa được build. Hãy chạy npm run build trong app/frontend.")



@pages_bp.post("/api/payment/process")
@customer_required
def process_payment():
    if not session.get("user_id"):
        return jsonify({"error": "Vui lòng đăng nhập."}), 401
    if not compare_digest(request.headers.get("X-CSRF-Token", ""), session.get("csrf_token", "")):
        return jsonify({"error": "Mã xác nhận không hợp lệ."}), 403
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or type(data.get("hold_id")) is not int or type(data.get("success")) is not bool or not isinstance(data.get("payment_method"), str):
        return jsonify({"error": "Yêu cầu hold_id số nguyên, success boolean và payment_method."}), 400
    result, error = PaymentService.process(data["hold_id"], session["user_id"], data["payment_method"], data["success"], data.get('saved_card_id'))
    if error:
        return jsonify({"error": error}), 409
    return jsonify(result)


@pages_bp.get('/api/refund-requests')
def refund_requests_api():
    if not session.get('user_id'):
        return jsonify(error='Vui lòng đăng nhập.'), 401
    with get_connection() as db:
        if session.get('role') == 'ADMIN':
            rows=db.execute('''SELECT r.*,u.full_name,u.email FROM refund_requests r JOIN users u ON u.id=r.user_id WHERE r.status='PENDING' ORDER BY r.created_at DESC''').fetchall()
        else:
            rows=db.execute('SELECT * FROM refund_requests WHERE user_id=? ORDER BY created_at DESC',(session['user_id'],)).fetchall()
    return jsonify({'requests':[dict(x) for x in rows]})

@pages_bp.post('/api/refund-requests')
@customer_required
def create_refund_request():
    if not session.get('user_id'):
        return jsonify(error='Vui lòng đăng nhập.'), 401
    if not compare_digest(request.headers.get('X-CSRF-Token',''),session.get('csrf_token','')):
        return jsonify(error='Mã xác nhận không hợp lệ.'),403
    data=request.get_json(silent=True) or {}; code=str(data.get('booking_code','')).strip(); reason=str(data.get('reason','')).strip()
    if not code:return jsonify(error='Thiếu mã đặt chỗ.'),400
    with get_connection() as db:
        ticket=db.execute('SELECT booking_code FROM tickets WHERE booking_code=? AND user_id=? LIMIT 1',(code,session['user_id'])).fetchone()
        if not ticket:return jsonify(error='Vé không tồn tại hoặc không thuộc tài khoản.'),404
        pending=db.execute("SELECT 1 FROM refund_requests WHERE booking_code=? AND status='PENDING'",(code,)).fetchone()
        if pending:return jsonify(error='Vé đã có yêu cầu đang chờ xử lý.'),409
        req='RF-'+uuid.uuid4().hex[:8].upper();db.execute('INSERT INTO refund_requests(request_code,booking_code,user_id,reason) VALUES(?,?,?,?)',(req,code,session['user_id'],reason));db.commit()
    return jsonify({'request_code':req,'booking_code':code,'status':'PENDING','message':'Đã gửi yêu cầu; chờ Admin xác minh hoàn tiền.'}),201

@pages_bp.post('/api/admin/refund-requests/<int:request_id>/decision')
@admin_required
def refund_decision(request_id):
    if not compare_digest(request.headers.get('X-CSRF-Token',''),session.get('csrf_token','')):
        return jsonify(error='Mã xác nhận không hợp lệ.'),403
    data=request.get_json(silent=True) or {}; decision=data.get('decision')
    if decision not in ('APPROVED','REJECTED'):return jsonify(error='Quyết định không hợp lệ.'),400
    with get_connection() as db:
        req=db.execute("SELECT * FROM refund_requests WHERE id=? AND status='PENDING'",(request_id,)).fetchone()
        if not req:return jsonify(error='Yêu cầu không tồn tại hoặc đã xử lý.'),404
        if decision=='APPROVED':
            db.execute("UPDATE payments SET status='REFUNDED' WHERE booking_id=? AND status='SUCCESS'",(req['booking_code'],))
            db.execute("UPDATE tickets SET status='CANCELLED' WHERE booking_code=? AND status='BOOKED'",(req['booking_code'],))
        db.execute("UPDATE refund_requests SET status=?,reviewed_by=?,reviewed_at=datetime('now','localtime') WHERE id=?", (decision, session['user_id'], request_id)); db.commit()
    return jsonify({'request_id':request_id,'status':decision,'booking_code':req['booking_code']})

@pages_bp.post('/api/ticket/cancel')
@customer_required
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