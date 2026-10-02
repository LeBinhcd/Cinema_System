import sqlite3
from datetime import datetime, timedelta
import pytest
from app.database import get_connection
from app.models.admin import AdminModel
from app.services.admin_service import AdminService


@pytest.fixture
def client(app):
    client = app.test_client()
    with client.session_transaction() as session:
        session.update(user_id=1, role='ADMIN', csrf_token='admin-test')
    return client


def movie_data(**changes):
    return dict(title='Admin movie', genre='Drama', duration='90', release_date='2026-10-01',
                poster_url='https://example.com/poster.jpg', synopsis='Public synopsis', **changes)


def setup_catalog(app):
    with app.app_context():
        movie = AdminService.add_movie(movie_data())
        room = AdminService.add_room({'name': 'Admin room', 'row_count': 5, 'column_count': 8})
    return movie, room


@pytest.mark.parametrize('path', ['/admin/movies/add', '/admin/movies/1/toggle-status',
                                  '/admin/screenings/add', '/admin/rooms/add',
                                  '/admin/rooms/1/toggle-status', '/admin/drafts/1/approved'])
def test_admin_permissions_csrf(app, client, path):
    assert app.test_client().post(path).status_code == 403
    assert client.post(path).status_code == 403
    assert client.post(path, data={'csrf_token': 'wrong'}).status_code == 403
    with client.session_transaction() as session:
        session['role'] = 'CUSTOMER'
    assert client.post(path, data={'csrf_token': 'admin-test'}).status_code == 403


def test_movies_and_homepage(app, client):
    data = movie_data()
    for duration in ('0', '-1', 'bad'):
        response = client.post('/admin/movies/add', data={**data, 'duration': duration, 'csrf_token': 'admin-test'}, follow_redirects=True)
        assert response.status_code == 200
        with app.app_context():
            with AdminModel.transaction() as model:
                assert model.movie_details(1) is None
    response = client.post('/admin/movies/add', data={**data, 'csrf_token': 'admin-test'}, follow_redirects=True)
    assert response.status_code == 200
    assert 'Đã lưu vào danh sách chờ duyệt' in response.get_data(as_text=True)
    assert 'Admin movie' not in client.get('/').get_data(as_text=True)
    assert client.get('/movie/1').status_code == 404
    with app.app_context():
        with AdminModel.transaction() as model:
            assert model.movie_details(1) is None
            assert model.draft(1)['movie_id'] is None
    response = client.post('/admin/drafts/1/approve',
                           data={'csrf_token': 'admin-test', 'edited_synopsis': 'Reviewed synopsis'}, follow_redirects=True)
    assert 'Đã phê duyệt và tạo phim thành công' in response.get_data(as_text=True)
    assert 'Admin movie' in client.get('/').get_data(as_text=True)
    client.post('/admin/movies/1/toggle-status', data={'csrf_token': 'admin-test'})
    assert 'Admin movie' not in client.get('/').get_data(as_text=True)
    client.post('/admin/movies/1/toggle-status', data={'csrf_token': 'admin-test'})
    assert 'Admin movie' in client.get('/').get_data(as_text=True)
    with app.app_context():
        with pytest.raises(sqlite3.IntegrityError):
            AdminService.add_movie(data)


def test_room_counts_maintenance_and_rollback(app, client, monkeypatch):
    movie, room = setup_catalog(app)
    with app.app_context():
        counts = AdminService.rooms()[0]
        assert (counts['standard_seats'], counts['vip_seats'], counts['couple_seats'], counts['total_seats']) == (16, 16, 8, 40)
    response = client.post(f'/admin/rooms/{room}/toggle-status', data={'csrf_token': 'admin-test'}, follow_redirects=True)
    assert response.status_code == 200
    with app.app_context():
        with pytest.raises(ValueError, match='bảo trì'):
            AdminService.add_screening({'movie_id': movie, 'room_id': room, 'start_time': '2026-10-01T10:00'})
        original = AdminModel.add_room
        def fail(model, data, seats):
            original(model, data, seats)
            raise ValueError('Forced rollback')
        monkeypatch.setattr(AdminModel, 'add_room', fail)
        with pytest.raises(ValueError):
            AdminService.add_room({'name': 'Rollback room'})
        assert len(AdminService.rooms()) == 1


@pytest.mark.parametrize('offset,allowed', [(-105, True), (-104, False), (-90, False),
                                            (0, False), (90, False), (104, False), (105, True)])
def test_schedule_both_sides(app, offset, allowed):
    movie, room = setup_catalog(app)
    start = datetime(2026, 10, 1, 12)
    with app.app_context():
        AdminService.add_screening({'movie_id': movie, 'room_id': room, 'start_time': start.isoformat()})
        data = {'movie_id': movie, 'room_id': room, 'start_time': (start + timedelta(minutes=offset)).isoformat(), 'end_time': '2099-01-01'}
        if allowed:
            AdminService.add_screening(data)
        else:
            with pytest.raises(ValueError, match='15 phút'):
                AdminService.add_screening(data)
        connection = get_connection()
        try:
            rows = connection.execute('SELECT * FROM screenings').fetchall()
            assert len(rows) == (2 if allowed else 1)
            for row in rows:
                assert datetime.fromisoformat(row['end_time']) - datetime.fromisoformat(row['start_time']) == timedelta(minutes=90)
        finally:
            connection.close()


def test_draft_review_flash_and_audit(app, client):
    movie, room = setup_catalog(app)
    with app.app_context():
        connection = get_connection()
        connection.execute("INSERT INTO ai_contents(movie_id,content_type,source_text,generated_text) VALUES(?,'MOVIE_DESCRIPTION','source','AI text')", (movie,))
        connection.commit()
        connection.close()
    response = client.post('/admin/drafts/1/approved', data={'csrf_token': 'admin-test'}, follow_redirects=True)
    assert response.status_code == 200
    with app.app_context():
        with AdminModel.transaction() as model:
            draft = model.draft(1)
            assert draft['status'] == 'APPROVED' and draft['reviewed_by'] == 1 and draft['reviewed_at']
            assert model.movie_details(movie)['synopsis'] == 'AI text'
    assert 'đã được duyệt' in client.post('/admin/drafts/1/rejected', data={'csrf_token': 'admin-test'}, follow_redirects=True).get_data(as_text=True)


def test_browser_screening_conflict_and_room_creation(app, client):
    with app.app_context():
        movie = AdminService.add_movie(movie_data())
    response = client.post('/admin/rooms/add', data={'name': 'New room', 'row_count': '5',
                     'column_count': '7', 'csrf_token': 'admin-test'}, follow_redirects=True)
    assert response.status_code == 200
    assert 'Đã tạo phòng' in response.get_data(as_text=True)
    with app.app_context():
        room = AdminService.rooms()[0]
        assert room['total_seats'] == 35
    data = {'movie_id': str(movie), 'room_id': str(room['id']),
            'start_time': '2026-10-01T12:00', 'csrf_token': 'admin-test'}
    response = client.post('/admin/screenings/add', data=data, follow_redirects=True)
    assert 'Đã thêm suất chiếu' in response.get_data(as_text=True)
    response = client.post('/admin/screenings/add', data={**data, 'start_time': '2026-10-01T13:44'}, follow_redirects=True)
    assert 'Xung đột suất #1' in response.get_data(as_text=True)
    with app.app_context():
        connection = get_connection()
        try:
            assert connection.execute('SELECT COUNT(*) FROM screenings').fetchone()[0] == 1
        finally:
            connection.close()


def test_migration_preserves_existing_room(app):
    with app.app_context():
        connection = get_connection()
        connection.execute('DROP TABLE screening_rooms')
        connection.execute('CREATE TABLE screening_rooms(id INTEGER PRIMARY KEY,name TEXT,row_count INTEGER,column_count INTEGER)')
        connection.execute("INSERT INTO screening_rooms VALUES(1,'Legacy room',5,8)")
        connection.commit()
        connection.close()
        AdminModel.migrate()
        AdminModel.migrate()
        room = AdminService.rooms()[0]
        assert room['name'] == 'Legacy room' and room['status'] == 'ACTIVE'


@pytest.mark.parametrize('rating', ['P', 'K', 'T13', 'T16', 'T18', 'C'])
def test_movie_age_rating_and_keywords_saved(app, client, rating):
    response = client.post('/admin/movies/add', data={**movie_data(), 'age_rating': rating,
                           'keywords': 'gia đình, Sài Gòn', 'csrf_token': 'admin-test'})
    assert response.status_code == 302
    with app.app_context():
        with AdminModel.transaction() as model:
            assert model.movie_details(1) is None
            assert model.draft(1)['draft_age_rating'] == rating
            assert model.draft(1)['draft_keywords'] == 'gia đình, Sài Gòn'
    assert client.post('/admin/drafts/1/approve', data={'csrf_token': 'admin-test',
                       'edited_synopsis': 'Public synopsis'}).status_code == 302
    with app.app_context():
        with AdminModel.transaction() as model:
            movie = model.movie_details(1)
            assert movie['age_rating'] == rating
            assert movie['keywords'] == 'gia đình, Sài Gòn'


def test_invalid_movie_age_rating_rejected(app):
    with app.app_context():
        with pytest.raises(ValueError, match='độ tuổi'):
            AdminService.add_movie(movie_data(age_rating='R'))


def test_movie_rating_migration_preserves_legacy_data(app):
    with app.app_context():
        connection = get_connection()
        connection.execute('ALTER TABLE movies DROP COLUMN age_rating')
        connection.execute("INSERT INTO movies(title,duration_minutes,synopsis) VALUES('Legacy movie',90,'Original')")
        connection.commit()
        connection.close()
        AdminModel.migrate()
        AdminModel.migrate()
        with AdminModel.transaction() as model:
            movie = model.movie_details(1)
            assert movie['title'] == 'Legacy movie' and movie['synopsis'] == 'Original'
            assert movie['age_rating'] == 'P'


def test_generate_description_permissions_and_csrf(app, client, monkeypatch):
    def must_not_call(*args):
        pytest.fail('Unauthorized request called the provider')
    monkeypatch.setattr('app.services.movie_service.generate_response', must_not_call)
    path = '/admin/movies/generate-description'
    assert app.test_client().post(path, json={'title': 'Phim'}).status_code == 403
    for token in ('', 'wrong', 'sai-định-dạng'):
        response = client.post(path, json={'title': 'Phim'}, headers={'X-CSRF-Token': token})
        assert response.status_code == 403 and response.json['success'] is False
    for role in ('STAFF', 'CUSTOMER'):
        with client.session_transaction() as session:
            session['role'] = role
        assert client.post(path, json={'title': 'Phim'}, headers={'X-CSRF-Token': 'admin-test'}).status_code == 403


def test_generate_description_preview_and_prompt(app, client, monkeypatch):
    prompts = []
    def generate(prompt):
        prompts.append(prompt)
        return 'Một câu chuyện gia đình giữa lòng Sài Gòn.'
    monkeypatch.setattr('app.services.movie_service.generate_response', generate)
    response = client.post('/admin/movies/generate-description',
                           json={'title': 'Phim mới', 'keywords': 'gia đình, Sài Gòn', 'age_rating': 'T13'},
                           headers={'X-CSRF-Token': 'admin-test'})
    assert response.status_code == 200
    assert response.json == {'success': True, 'description': 'Một câu chuyện gia đình giữa lòng Sài Gòn.'}
    assert all(text in prompts[0] for text in ('Phim mới', 'T13', 'gia đình, Sài Gòn', 'dưới 150 từ', 'tiếng Việt'))
    with app.app_context():
        connection = get_connection()
        try:
            assert connection.execute('SELECT COUNT(*) FROM movies').fetchone()[0] == 0
            assert connection.execute('SELECT COUNT(*) FROM ai_contents').fetchone()[0] == 0
        finally:
            connection.close()
    response = client.post('/admin/movies/add', data={**movie_data(), 'age_rating': 'T13',
                           'synopsis': response.json['description'] + ' Admin chỉnh sửa.', 'csrf_token': 'admin-test'})
    assert response.status_code == 302
    assert client.get('/movie/1').status_code == 404
    client.post('/admin/drafts/1/approve', data={'csrf_token': 'admin-test',
                'edited_synopsis': 'Mô tả qua kiểm duyệt. Admin chỉnh sửa.'})
    assert 'Admin chỉnh sửa.' in client.get('/movie/1').get_data(as_text=True)


@pytest.mark.parametrize('payload', [[], None, {}, {'title': ' '}, {'title': 123},
                                    {'title': 'Phim', 'keywords': []}, {'title': 'Phim', 'age_rating': 'R'},
                                    {'title': 'x' * 256}, {'title': 'Phim', 'keywords': 'x' * 501}])
def test_generate_description_invalid_input(client, monkeypatch, payload):
    def must_not_call(*args):
        pytest.fail('Invalid input called the provider')
    monkeypatch.setattr('app.services.movie_service.generate_response', must_not_call)
    response = client.post('/admin/movies/generate-description', json=payload,
                           headers={'X-CSRF-Token': 'admin-test'})
    assert response.status_code == 400 and response.json['success'] is False


@pytest.mark.parametrize('text,code', [('', 400), ('word ' * 150, 400),
    ('Xin lỗi, hiện chưa thể xử lý yêu cầu. Vui lòng thử lại sau.', 503),
    ('Xin lỗi, dịch vụ tư vấn hiện chưa được cấu hình. Vui lòng thử lại sau.', 503)])
def test_generate_description_provider_errors(client, monkeypatch, text, code):
    monkeypatch.setattr('app.services.movie_service.generate_response', lambda prompt: text)
    response = client.post('/admin/movies/generate-description', json={'title': 'Phim'},
                           headers={'X-CSRF-Token': 'admin-test'})
    assert response.status_code == code
    assert response.json['success'] is False and response.json['error']


def test_admin_movie_form(client):
    html = client.get('/admin').get_data(as_text=True)
    for text in ('movie-age-rating', 'movie-keywords', 'generate-movie-description',
                 'movie-description-spinner', 'Lưu vào Danh sách Chờ Duyệt', '/admin/movies/generate-description',
                 'X-CSRF-Token', 'synopsis.value = result.description'):
        assert text in html


def create_review_draft(app):
    movie, _ = setup_catalog(app)
    with app.app_context():
        connection = get_connection()
        try:
            draft = connection.execute("""INSERT INTO ai_contents(movie_id,content_type,source_text,generated_text)
                VALUES(?,'MOVIE_DESCRIPTION','source','Original AI text')""", (movie,)).lastrowid
            connection.commit()
        finally:
            connection.close()
    return movie, draft


@pytest.mark.parametrize('decision', ['approve', 'approved'])
def test_review_edited_text_audited(app, client, decision):
    movie, draft = create_review_draft(app)
    response = client.post(f'/admin/drafts/{draft}/{decision}',
                           data={'csrf_token': 'admin-test', 'edited_text': ' Admin sửa nội dung. '}, follow_redirects=True)
    assert 'Đã phê duyệt' in response.get_data(as_text=True)
    with app.app_context():
        with AdminModel.transaction() as model:
            assert model.movie_details(movie)['synopsis'] == 'Admin sửa nội dung.'
            row = model.draft(draft)
            assert row['generated_text'] == 'Original AI text'
            assert row['status'] == 'APPROVED' and row['reviewed_by'] == 1 and row['reviewed_at']
    client.post(f'/admin/drafts/{draft}/approve', data={'csrf_token': 'admin-test', 'edited_text': 'Overwrite'})
    with app.app_context():
        with AdminModel.transaction() as model:
            assert model.movie_details(movie)['synopsis'] == 'Admin sửa nội dung.'


@pytest.mark.parametrize('text', ['', ' ', 'word ' * 151])
def test_review_invalid_edit_rolls_back(app, client, text):
    movie, draft = create_review_draft(app)
    response = client.post(f'/admin/drafts/{draft}/approve',
                           data={'csrf_token': 'admin-test', 'edited_text': text}, follow_redirects=True)
    assert '150 từ' in response.get_data(as_text=True)
    with app.app_context():
        with AdminModel.transaction() as model:
            assert model.draft(draft)['status'] == 'DRAFT'
            assert model.movie_details(movie)['synopsis'] == 'Public synopsis'


def test_reject_keeps_synopsis_and_permissions(app, client):
    movie, draft = create_review_draft(app)
    path = f'/admin/drafts/{draft}/reject'
    assert client.post(path, data={'edited_text': 'Rejected'}).status_code == 403
    response = client.post(path, data={'csrf_token': 'admin-test', 'edited_text': ''}, follow_redirects=True)
    assert 'Đã hủy/từ chối' in response.get_data(as_text=True)
    with app.app_context():
        with AdminModel.transaction() as model:
            assert model.draft(draft)['status'] == 'REJECTED'
            assert model.movie_details(movie)['synopsis'] == 'Public synopsis'


def test_revenue_aggregation_no_payment_multiplication(app, client):
    movie, room = setup_catalog(app)
    with app.app_context():
        show = AdminService.add_screening({'movie_id': movie, 'room_id': room, 'start_time': '2026-10-01T10:00'})
        AdminService.add_screening({'movie_id': movie, 'room_id': room, 'start_time': '2026-10-01T14:00'})
        AdminService.add_screening({'movie_id': movie, 'room_id': room, 'start_time': '2026-10-02T10:00'})
        connection = get_connection()
        try:
            for i, (status, amount, created) in enumerate([
                ('SUCCESS', 200000, '2026-10-01 00:00:00'), ('SUCCESS', 50000, '2026-10-01 23:59:59'),
                ('REFUNDED', 90000, '2026-10-01'), ('FAILED', 90000, '2026-10-01'),
                ('PENDING', 90000, '2026-10-01'), ('SUCCESS', 999999, '2026-10-02')]):
                connection.execute("""INSERT INTO payments(booking_id,amount,payment_method,status,transaction_code,created_at)
                    VALUES(?,?,'CASH',?,?,?)""", (f'B{i}', amount, status, f'T{i}', created))
            for i, status in enumerate(('BOOKED', 'USED', 'PAID', 'CHECKED_IN', 'CANCELLED', 'HELD')):
                connection.execute("""INSERT INTO tickets(booking_code,user_id,screening_id,seat_id,status,created_at)
                    VALUES('B0',3,?,?,?,'2026-10-01 23:59:59')""", (show, i + 1, status))
            connection.commit()
        finally:
            connection.close()
    response = client.get('/admin/api/revenue-report?from_date=2026-10-01&to_date=2026-10-01')
    assert response.status_code == 200
    report = response.json['report']
    assert report['total_revenue'] == 250000
    assert report['tickets_sold'] == 4
    assert report['total_seats'] == 80 and report['occupied_seats'] == 4
    assert report['occupancy_rate'] == 5


def test_empty_report_and_ai_recomputes(client, monkeypatch):
    prompts = []
    def generate(prompt):
        prompts.append(prompt)
        return 'Chưa có doanh thu. Chưa có vé bán. Chưa có dữ liệu lấp đầy. Nên rà soát lịch chiếu.'
    monkeypatch.setattr('app.services.admin_service.generate_response', generate)
    payload = {'from_date': '2026-10-01', 'to_date': '2026-10-01', 'total_revenue': 999999}
    response = client.post('/admin/api/revenue-ai-summary', json=payload, headers={'X-CSRF-Token': 'admin-test'})
    assert response.status_code == 200 and response.json['status'] == 'DRAFT'
    assert response.json['report']['total_revenue'] == 0
    assert response.json['report']['occupancy_rate'] == 0
    assert '999999' not in prompts[0] and '3-4 câu' in prompts[0]
    assert 'user_id' not in prompts[0] and 'email' not in prompts[0]


@pytest.mark.parametrize('query', ['', '?from_date=bad&to_date=2026-10-01',
    '?from_date=2026-10-02&to_date=2026-10-01', '?from_date=2026-02-30&to_date=2026-10-01'])
def test_revenue_invalid_dates(client, query):
    response = client.get('/admin/api/revenue-report' + query)
    assert response.status_code == 400 and response.json['success'] is False


def test_revenue_permissions_csrf_and_provider_failure(app, client, monkeypatch):
    path = '/admin/api/revenue-ai-summary'
    payload = {'from_date': '2026-10-01', 'to_date': '2026-10-01'}
    assert app.test_client().get('/admin/api/revenue-report').status_code == 403
    assert app.test_client().post(path, json=payload).status_code == 403
    assert client.post(path, json=payload).status_code == 403
    assert client.post(path, json=payload, headers={'X-CSRF-Token': 'wrong'}).status_code == 403
    for role in ('STAFF', 'CUSTOMER'):
        with client.session_transaction() as session:
            session['role'] = role
        assert client.get('/admin/api/revenue-report').status_code == 403
        assert client.post(path, json=payload, headers={'X-CSRF-Token': 'admin-test'}).status_code == 403
    with client.session_transaction() as session:
        session['role'] = 'ADMIN'
    for payload in ([], {}, {'from_date': '2026-10-02', 'to_date': '2026-10-01'}):
        assert client.post(path, json=payload, headers={'X-CSRF-Token': 'admin-test'}).status_code == 400
    monkeypatch.setattr('app.services.admin_service.generate_response', lambda prompt: '')
    response = client.post(path, json={'from_date': '2026-10-01', 'to_date': '2026-10-01'},
                           headers={'X-CSRF-Token': 'admin-test'})
    assert response.status_code == 503 and response.json['success'] is False


def test_ai_center_review_metadata_and_safe_render(app, client):
    create_review_draft(app)
    html = client.get('/admin').get_data(as_text=True)
    for text in ('TRUNG TÂM KIỂM DUYỆT & TRỢ LÝ AI', 'KIỂM DUYỆT MÔ TẢ PHIM',
                 'BÁO CÁO DOANH THU', 'Drama', 'edited_synopsis', 'draft-word-count',
                 'revenue-ai-spinner', 'summary.textContent = result.summary', 'DRAFT · Nội bộ'):
        assert text in html