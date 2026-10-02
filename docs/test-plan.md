# Kế hoạch kiểm thử hệ thống Cinema

## 1. Cơ sở, phạm vi và nguyên tắc

- Quy trình: `D:\New folder (7)\Cinema_System\.agents\skills\testing\SKILL.md`.
- Yêu cầu: `D:\New folder (7)\Cinema_System\docs\requirements.md` (FR-01–13, NFR-01–05).
- User Stories: `D:\New folder (7)\Cinema_System\docs\user-stories.md` (US-01–13 và Given–When–Then).
- `D:\New folder (7)\Cinema_System\docs\acceptance-criteria.md` không tồn tại tại thời điểm kiểm tra. Không coi tài liệu này là đã đọc; dùng tiêu chí trong User Stories và `D:\New folder (7)\Cinema_System\docs\chatbot-acceptance-criteria.md` (CB-AC-01–25).
- Thực thi toàn bộ suite hiện có: 13 file `test_*.py` trong `D:\New folder (7)\Cinema_System\tests`. Không thêm/sửa test hoặc sửa nghiệp vụ trong đợt đánh giá này; bước xây dựng tự động hóa của skill được đối chiếu với suite hiện có, các thiếu sót được chuyển thành backlog.
- Phạm vi thực thi: unit tests, Flask test client và integration SQLite; không phải E2E trình duyệt, quét QR bằng thiết bị, benchmark hay tích hợp cổng thanh toán/LLM thật.
- PASS của suite không đồng nghĩa mọi tiêu chí nghiệm thu đã đạt. Ca thiết kế chưa có test được ghi là chưa thực thi, không tính PASS.

## 2. Yêu cầu → Test Scenarios

| Yêu cầu / Story | Kịch bản | Ca chi tiết | Tự động hóa hiện có / phần thiếu |
|---|---|---|---|
| FR-01 / US-01 | TS-01 Quản lý phim, nhãn tuổi, AI dưới 150 từ | AD-01, AD-02 | `test_admin.py`, `test_core.py`; CRUD đầy đủ chưa được chứng minh |
| FR-02 / US-02 | TS-02 Phòng, loại ghế, bảo trì, rollback | AD-03 | `test_admin.py`; sửa/xóa phòng và cấu hình ghế tùy ý còn thiếu |
| FR-03 / US-03 | TS-03 Xung đột lịch, vệ sinh, khóa bán | AD-04, BK-04 | `test_admin.py`, `test_core.py`, `test_business_fixes.py` |
| FR-04 / US-04 | TS-04 Định giá theo ghế/ngày/giờ | AD-05 | Có assert giá Standard/VIP và nhãn Couple; chính sách ngày/giờ chưa có test |
| FR-05 / US-05 | TS-05 Lịch, seat map và trạng thái | BK-01 | `test_auth_seats.py`, `test_business_fixes.py`; cập nhật realtime chưa kiểm thử |
| FR-06 / US-06 | TS-06 Giữ ghế 5 phút, tránh trùng, AI gợi ý | BK-02, BK-03, CB-01 | `test_payment_ticket.py`, RAG tests; TTL chính xác, cạnh tranh đồng thời và 2–3 phim đủ ghế chưa được chứng minh |
| FR-07 / US-07 | TS-07 Hủy trước 60 phút, giải phóng ghế | BK-05, ST-03 | `test_business_fixes.py`, `test_staff.py`; mốc đúng 60 phút còn thiếu |
| FR-08 / US-08 | TS-08 Thanh toán, vé QR và thất bại | PY-01–03 | `test_payment_ticket.py`; callback thật, hold hết hạn và rollback thanh toán còn thiếu |
| FR-09 / US-09 | TS-09 Check-in hợp lệ, chống dùng lại | ST-02 | `test_payment_ticket.py`, `test_staff.py`; không test camera/QR giấy |
| FR-10 / US-10 | TS-10 Tra cứu sở hữu/điện thoại và lọc suất | ST-04, CB-02 | `test_auth_seats.py`, `test_business_fixes.py`, `test_staff.py`, `test_screening_retriever.py` |
| FR-11 / US-11 | TS-11 Doanh thu, occupancy, AI tóm tắt | AD-06 | `test_admin.py`; lọc theo phim/suất/tuần/tháng và workflow duyệt tóm tắt còn thiếu |
| FR-12 / US-12 | TS-12 Nội dung AI chỉ công khai sau duyệt | AD-07 | `test_admin.py`, `test_core.py`; tóm tắt doanh thu chưa có test duyệt đầy đủ |
| FR-13 / US-13 | TS-13 Login, vai trò, CSRF, bảo vệ phiên | AU-01 | `test_auth_seats.py`, `test_core.py`, `test_admin.py`, staff/chat tests |
| NFR-01 | TS-14 Giao diện và thông báo | BK-01, ST-01, CB-05 | Kiểm tra HTML/assets; chưa đánh giá UX trên browser |
| NFR-02 | TS-15 Nhất quán, rollback, tránh bán trùng | BK-03, PY-01, ST-01, AD-03 | Có hồi quy tuần tự; không có tải/cạnh tranh đa client |
| NFR-03 | TS-16 Sở hữu vé, chống injection/rò rỉ | AU-01, CB-03, CB-04 | Có role/CSRF/allowlist/parameterized SQL; không thay thế security audit |
| NFR-04 | TS-17 Grounding và kiểm duyệt AI | AD-02, AD-07, CB-03–04 | Prompt/context/card được kiểm tra; grounding văn bản model cần đối chiếu riêng |
| NFR-05 | TS-18 Module độc lập và migration idempotent | AD-08, CB-01–05 | Có unit tests và migration; không chứng minh toàn bộ khả năng bảo trì |

## 3. Thiết kế Test Cases

Tiền điều kiện chung: database riêng `tmp_path / cinema.db`, schema từ `database/sqlite_schema.sql`, ba tài khoản ADMIN/STAFF/CUSTOMER với mật khẩu fixture `valid-password`. API thay đổi dữ liệu dùng session đúng vai trò và CSRF hợp lệ, trừ ca âm tính. Không dùng dữ liệu khách hàng thật. AI dùng fake SDK hoặc monkeypatch; thanh toán là mô phỏng.

### 3.1. Đặt vé & giữ chỗ

| ID | Tiền điều kiện / Input | Steps | Expected Results | Trạng thái thiết kế |
|---|---|---|---|---|
| BK-01 | Suất có Standard A1, VIP A2; thêm Couple | GET seat map và `/booking/1`; xem ghế trống/giữ/đã bán | Tọa độ/loại/trạng thái đúng; suất không tồn tại 404; GET không ghi nghiệp vụ | Một phần tự động: `test_read_only_seat_map`, `test_empty_history_and_couple_rendering`; realtime chưa thực thi |
| BK-02 | CUSTOMER, ghế trống; đồng hồ cố định T | POST `/api/booking/hold-seat`; kiểm tra expires_at; thử T+299s, T+300s, T+301s | Hold đúng 5 phút; hết hạn mở lại ghế; thanh toán hết hạn bị từ chối | Tạo hold đã có; TTL/biên chưa tự động hóa |
| BK-03 | Một ghế đã bán hoặc hai khách tranh cùng ghế | Giữ/bán ghế; gọi lại; thiết kế hai transaction song song | Một người sở hữu; request trùng 409; không ticket/payment dư | Trùng tuần tự có trong `test_payment_and_ticket_access`, `test_counter_sale_lookup_refund`; đồng thời chưa thực thi |
| BK-04 | Suất bắt đầu cách hiện tại 14/15/16 phút | Bán POS; GET staff; kiểm tra DB nếu bị từ chối | 14 phút: 201; 15/16 phút: 409 và option disabled, không ghi ticket/payment | `test_pos_cutoff_and_disabled_option`; chưa chứng minh cutoff mọi đường bán online |
| BK-05 | Vé thuộc khách, BOOKED, chưa check-in; còn 120/60/59 phút | Xem lịch sử; POST cancel; kiểm tra ghế/payment; thử vé người khác và đã dùng | Hủy khi còn ít nhất 60 phút, hoàn/giải phóng; sai sở hữu/đã dùng/<60 phút bị từ chối | `test_history_ownership_grouping_and_cancel`, `test_history_cancel_eligibility`; đúng 60 phút chưa thực thi |

### 3.2. Thanh toán

| ID | Tiền điều kiện / Input | Steps | Expected Results | Trạng thái thiết kế |
|---|---|---|---|---|
| PY-01 | Hold A1 hợp lệ, VNPAY success=True | GET checkout; POST process thiếu CSRF rồi hợp lệ; mở vé; gửi lại | 403 khi thiếu CSRF; thanh toán 200; payment 80.000, ticket BOOKED, hold xóa; vé có mã; lặp 409; người khác 404 | `test_payment_and_ticket_access` |
| PY-02 | Hold VIP A2, MOMO success=False rồi True | Thanh toán thất bại; giữ lại; thanh toán thành công | Thất bại giải phóng ghế, không vé thành công; lần sau vé giá 110.000 và QR dùng được | `test_cancel_releases_and_checkin_once` |
| PY-03 | Hold đã hết hạn/sai chủ; lỗi DB giữa payment và ticket; callback giả/lặp | Gọi process; mô phỏng lỗi transaction; kiểm tra cả ba bảng | Không QR thành công; atomic rollback; xác thực callback và idempotency không nhân đôi tiền/vé | Chưa có test chuyên biệt; không chạy gateway thật |

### 3.3. Nhân viên: POS / Check-in / Refund

| ID | Tiền điều kiện / Input | Steps | Expected Results | Trạng thái thiết kế |
|---|---|---|---|---|
| ST-01 | STAFF, suất còn 2h, A1+A2, khách Walk-in; CASH/BANKING | POS thiếu CSRF, VNPAY tại quầy, CASH hợp lệ, bán lại; thử seat_ids=['1'] | 403/409 với input không hợp lệ; sale 201 tổng 190.000; bán trùng 409; không nhận ID ghế sai kiểu | `test_counter_sale_lookup_refund`, `test_counter_rejects_invalid_seat_ids` |
| ST-02 | Vé có QR; suất ngày mai rồi cập nhật hôm nay | Check-in thiếu CSRF, sai ngày, QR hợp lệ, check-in lần hai | 403/409 khi sai; hợp lệ 200 và checked_in_at; dùng lại 409 'Vé đã được sử dụng' | `test_cancel_releases_and_checkin_once`, `test_counter_sale_lookup_refund` |
| ST-03 | Vé chưa dùng còn 2h, BANKING; vé đã check-in | Cancel; kiểm tra AVAILABLE; bán lại; hủy vé đã dùng | Cancel 200 và ghế bán lại được; đã check-in 409, không hoàn vé đã dùng | `test_counter_cancel_releases_seats`, `test_counter_sale_lookup_refund`; hoàn tiền gateway chưa thực thi |
| ST-04 | Điện thoại 0987654321 / email fixture / booking code / QR | Tra cứu staff và PreviewService; CUSTOMER mở API staff; xem my-tickets | Chỉ vé phù hợp; CUSTOMER không dùng API staff; lịch sử cá nhân không lộ vé người khác | `test_read_only_seat_map`, `test_counter_sale_lookup_refund`, history tests |

### 3.4. Quản trị và phân quyền

| ID | Tiền điều kiện / Input | Steps | Expected Results | Trạng thái thiết kế |
|---|---|---|---|---|
| AD-01 | ADMIN, duration 0/-1/bad/90; rating P,K,T13,T16,T18,C và R | Thêm phim; duyệt draft; toggle trạng thái; thiết kế sửa/xóa | Invalid bị từ chối; nhãn/keywords lưu đúng; phim chờ duyệt chưa public; status đổi đúng | `test_movies_and_homepage`, age rating tests; sửa/xóa đầy đủ chưa thực thi |
| AD-02 | AI mock mô tả ngắn/rỗng/150 từ/lỗi; title sai kiểu/quá dài | Generate preview; kiểm tra prompt và DB; thêm draft | Tiếng Việt dưới 150 từ; invalid 400, lỗi provider 503; preview chưa ghi phim/draft; chỉ public sau duyệt | generate-description tests trong `test_admin.py` |
| AD-03 | Phòng 5x8; phòng bảo trì; lỗi cưỡng bức sau insert | Tạo phòng; đếm ghế; toggle maintenance; tạo suất; tạo phòng lỗi | 16 Standard+16 VIP+8 Couple=40; bảo trì từ chối suất; rollback không để phòng dư | `test_room_counts_maintenance_and_rollback` |
| AD-04 | Phim 90 phút; suất 12:00; offset ±105, ±104, ±90,0 | Thêm suất trước/sau; kiểm tra end_time, lỗi trên form | ±105 được phép (15 phút vệ sinh); gần hơn bị từ chối; không tin end_time do client gửi | `test_schedule_both_sides`, `test_cleanup_boundary`, browser conflict test |
| AD-05 | Standard/VIP/Couple; 17:59/18:00/18:01, thứ 5/6/CN, ngày lễ | Admin cấu hình giá; mua qua online/POS từng tổ hợp | Giá từ chính sách lưu server, phụ thu đúng và đồng nhất các kênh | Giá Standard/VIP có assert; cấu hình/phụ thu ngày giờ chưa thực thi |
| AD-06 | SUCCESS 200.000+50.000; REFUNDED/FAILED/PENDING; 4 vé hiệu lực, 80 ghế | Report ngày 01/10; report rỗng; gửi total_revenue giả 999999 để AI tóm tắt; ngày sai | 250.000, 4 vé, occupancy 5%; không nhân tiền theo số vé; AI tính từ server, draft nội bộ 3–4 câu, không PII; ngày sai 400 | revenue tests trong `test_admin.py`; phân nhóm phim/suất/tuần/tháng còn thiếu |
| AD-07 | Draft AI; edited_text hợp lệ/rỗng/151 từ; approve/reject | Duyệt/sửa/từ chối rồi duyệt lại; xem public và audit | Chỉ nội dung duyệt public; audit reviewer/time, giữ original; lỗi rollback; reject giữ synopsis cũ; không ghi đè draft đã duyệt | draft-review tests, `test_ai_description_remains_draft`; duyệt AI revenue chưa thực thi |
| AD-08 | Schema legacy thiếu phone/price/status/age_rating | Chạy migration hai lần trên fixture; đọc lại | Cột bổ sung, dữ liệu cũ giữ nguyên, idempotent | migration tests trong admin/payment/auth |
| AU-01 | ADMIN/STAFF/CUSTOMER, password sai/đúng, X-Role giả, thiếu/sai CSRF | Login/logout, truy cập admin/staff/history; tạo hai app thiếu SECRET_KEY từ cấu hình fixture | Đúng role; 401/403 khi sai; header không cấp quyền; logout mất quyền; key ngẫu nhiên khác nhau, không lộ log/không dùng được cookie giữa hai app | auth/core/admin/history tests |

### 3.5. Chatbot RAG

| ID | Tiền điều kiện / Input | Steps | Expected Results | Trạng thái thiết kế |
|---|---|---|---|---|
| CB-01 | 'Tối nay có phim hoạt hình nào sau 19h không?', NOW=30/09/2026 +07; UNKNOWN/AMBIGUOUS | Analyze; pipeline DB cố định với SDK mock | Intent/ngày/thể loại/giờ đúng; timezone đúng; pipeline trả card từ backend; mơ hồ không tự chọn dữ kiện | question analyzer/API tests; hỏi lại ở UI chưa chứng minh (CB-AC-01–02) |
| CB-02 | Phim/genre/date/time/seat filters; tickets BOOKED/USED/CANCELLED; hold live/expired; ghế khác phòng | Retrieve; thử SQL-like/%/_/date sai; DROP bảng fixture để gây lỗi | Đếm distinct đúng phòng/suất, hold hết hạn trả ghế; query tham số; tối đa 5 theo giờ; ValueError/OperationalError không giả thành kết quả rỗng | screening retriever tests (CB-AC-03–07,13,20); tìm theo nội dung/từ khóa còn thiếu |
| CB-03 | Context thiếu giá/chính sách/field bắt buộc, PII, chuỗi injection | Build context/prompt, so sánh input trước/sau | Không đoán giá/chính sách, không lộ PII; field sai fail closed; giữ nguyên dữ liệu bằng quoting; chỉ nguồn retrieved | context/prompt tests (CB-AC-08–09,16,18,23); không phải chứng minh model luôn tuân thủ |
| CB-04 | Question rỗng/301 ký tự/sai kiểu/300 ký tự; model trả 'Phòng B, giá 999999'; provider lỗi | POST chat; kiểm tra status/body/card; đối chiếu cả answer với nguồn | Invalid 400, CSRF sai 403; lỗi an toàn; card/link `/booking/12` không đổi; theo AC-14/25 văn bản bịa phải loại/từ chối | API tests bảo vệ card và lỗi; chưa có assertion loại văn bản bịa. CB-AC-14/25 cần đánh giá riêng, không coi card PASS là toàn bộ AC PASS |
| CB-05 | Anonymous `/`, `/movies`, `/login`; assets CSS/JS; suất hết ghế/đóng bán | Parse HTML/token, chat với token; thiết kế browser XSS và nút booking | Widget một lần, maxlength=300; CSRF hoạt động, assets 200; không thực thi script; ghế có timestamp/cảnh báo; suất đóng không mời đặt | UI rendering tests có; browser XSS, CB-AC-15/22/24 và không ghi qua chatbot AC-17/21 chưa kiểm thử đầy đủ |

## 4. Quy trình thực thi an toàn

1. Đọc toàn bộ tests và dependency kết nối/factory/migration trước chạy. Fixture cung cấp `TESTING=True`, `APP_ENV=testing`, `DB_ENGINE=sqlite`, `SQLITE_PATH=str(tmp_path / 'cinema.db')` trước migration. Test tạo app bổ sung sao chép app.config từ fixture. Unit tests thuần không cần DB.
2. Chỉ chạy từ `D:\New folder (7)\Cinema_System` với lệnh **`python -m pytest tests -v`**. Không chạy pytest root không có đường dẫn; không collect `scripts/test_groq_connection.py` hoặc script live khác.
3. Giữ `D:\New folder (7)\Cinema_System\cinema.db` bằng Windows FileStream FileAccess.Read / FileShare.Read trong suốt pytest, chặn handle mở ghi/xóa. Không đổi quyền, không sửa/copy đè database. Nếu khóa không lấy được thì dừng trước khi test.
4. Lưu SHA-256, size, LastWriteTimeUtc trước/sau; sai khác coi là vi phạm an toàn. Baseline SHA-256: `0F3E206BD9950C394E8BC3C6D50B450A1D531BC846C076EC875A2DA62687BAB4`, size 143360 bytes.
5. Thu stdout/stderr đầy đủ vào `D:\New folder (7)\Cinema_System\docs\test-run.log`; lưu exit code và summary. Không chỉnh test để ép pass, không rerun chọn lọc nhằm che fail.
6. Nếu có fail/error, đọc traceback và code liên quan, phân biệt lỗi product, assertion, môi trường và thiếu coverage; không tự suy đoán root cause khi chưa có bằng chứng.

## 5. Điều kiện kết thúc và giới hạn

- Toàn bộ suite được thực thi hoặc blocker được công bố; mỗi kết quả lấy từ phiên chạy mới, không dùng `pytest-collection.txt` để kết luận pass.
- Báo cáo có tổng collected/PASS/FAIL/ERROR/SKIP, defects và traceability coverage; database chính bất biến.
- Không đo line/branch coverage vì không chạy công cụ coverage; đánh giá ở mức yêu cầu và assertions thực tế.
- Backlog ưu tiên: TTL/expiry và concurrency, giá ngày/giờ, biên hủy 60 phút, callbacks/rollback, CRUD còn thiếu, duyệt AI doanh thu, lọc thống kê, grounding văn bản RAG, browser/XSS/camera và hiệu năng.