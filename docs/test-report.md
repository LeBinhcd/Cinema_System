# Báo cáo kiểm thử hệ thống Cinema

## 1. Nguồn và phiên thực thi

Thực hiện theo `D:\New folder (7)\Cinema_System\.agents\skills\testing\SKILL.md` và kế hoạch `D:\New folder (7)\Cinema_System\docs\test-plan.md`.

- Đã đọc requirements, User Stories (bao gồm Given–When–Then), tiêu chí Chatbot RAG và toàn bộ 13 file test.
- `D:\New folder (7)\Cinema_System\docs\acceptance-criteria.md` không tồn tại. Dùng tiêu chí có thật trong `D:\New folder (7)\Cinema_System\docs\user-stories.md` và `D:\New folder (7)\Cinema_System\docs\chatbot-acceptance-criteria.md`; không tạo lại đặc tả để giả định nghiệm thu.
- Working directory: `D:\New folder (7)\Cinema_System`.
- Lệnh thực thi chính xác: **`python -m pytest tests -v`**.
- Windows, Python 3.11.9, pytest 9.1.1, pluggy 1.6.0, plugin anyio 4.15.1.
- Wrapper bắt đầu: `2026-10-02T18:06:54.8976948+07:00`; kết thúc: `2026-10-02T18:08:26.4077297+07:00`.
- Thời gian pytest báo cáo: **88.03 giây**. Exit code: **0**.
- Log stdout/stderr: `D:\New folder (7)\Cinema_System\docs\test-run.log`.
- Metadata bảo vệ DB: `D:\New folder (7)\Cinema_System\docs\test-run-metadata.txt`.
- Log/metadata được chuyển từ encoding UTF-16 do Windows PowerShell Tee-Object sang UTF-8 để đọc thuận tiện, không thay đổi nội dung kết quả. Không dùng collection cũ để kết luận PASS và không chạy lại chọn lọc.

## 2. Tổng hợp kết quả

| Chỉ số | Số lượng |
|---|---:|
| Tổng test items collected (bao gồm tham số hóa) | 245 |
| PASS | 245 |
| FAIL | 0 |
| ERROR (collection/setup/teardown) | 0 |
| SKIP / XFAIL / XPASS | 0 / 0 / 0 |
| File test thực thi | 13 |
| Tỷ lệ PASS của suite hiện có | 100% |

Kết luận gốc từ log: **`245 passed in 88.03s (0:01:28)`**. Kiểm tra độc lập log đếm được đúng 245 dòng kết quả PASSED.

Các tên file sau đều thuộc `D:\New folder (7)\Cinema_System\tests`:

| File | Tổng | PASS | FAIL |
|---|---:|---:|---:|
| test_admin.py | 56 | 56 | 0 |
| test_auth_seats.py | 4 | 4 | 0 |
| test_business_fixes.py | 11 | 11 | 0 |
| test_chatbot_api.py | 17 | 17 | 0 |
| test_chatbot_ui.py | 6 | 6 | 0 |
| test_context_builder.py | 42 | 42 | 0 |
| test_core.py | 3 | 3 | 0 |
| test_gemini_service.py | 29 | 29 | 0 |
| test_payment_ticket.py | 3 | 3 | 0 |
| test_prompt_builder.py | 9 | 9 | 0 |
| test_question_analyzer.py | 27 | 27 | 0 |
| test_screening_retriever.py | 35 | 35 | 0 |
| test_staff.py | 3 | 3 | 0 |
| **Tổng** | **245** | **245** | **0** |

## 3. Bảo vệ dữ liệu và môi trường

- `D:\New folder (7)\Cinema_System\tests\conftest.py::app(tmp_path)` truyền `TESTING=True`, `APP_ENV=testing`, `DB_ENGINE=sqlite`, `SQLITE_PATH=str(tmp_path / 'cinema.db')` trước khi factory chạy migration. Mỗi test dùng fixture app có DB SQLite riêng. Unit tests thuần không truy cập DB.
- `test_missing_secret_generates_random_key` tạo hai app bổ sung bằng cấu hình sao chép từ fixture, nên vẫn dùng đường dẫn DB tạm, không gọi factory mặc định trỏ DB chính.
- Các seed, transaction, migration và DROP TABLE của integration tests chạy trong app context fixture, với đường dẫn do pytest `tmp_path` cấp.
- Giữ file chính `D:\New folder (7)\Cinema_System\cinema.db` bằng Windows FileStream **FileAccess.Read / FileShare.Read** trong suốt phiên pytest, chặn mở ghi/xóa file. Handle được đóng trong finally; không đổi quyền và không ghi đè/khôi phục database.
- Các đường gọi AI được monkeypatch hoặc fake SDK; thanh toán là mock checkout. Không chạy các script chẩn đoán API thật ngoài tests và không gọi API LLM có trả phí.

| Thuộc tính database chính | Trước | Sau |
|---|---|---|
| SHA-256 | `0F3E206BD9950C394E8BC3C6D50B450A1D531BC846C076EC875A2DA62687BAB4` | `0F3E206BD9950C394E8BC3C6D50B450A1D531BC846C076EC875A2DA62687BAB4` |
| Kích thước (bytes) | 143360 | 143360 |
| LastWriteTime UTC | `2026-10-02T00:01:37.9459800Z` | `2026-10-02T00:01:37.9459800Z` |

**Kết luận an toàn:** Nội dung, kích thước và mtime của database chính không thay đổi trong phiên kiểm thử. Kiểm tra hash khi tiếp tục hoàn tất báo cáo cũng khớp baseline.

## 4. Phân tích lỗi (Defects)

### 4.1. Test thất bại

**Không có test FAIL hoặc ERROR trong phiên này.** Vì vậy không có file/hàm/root cause của test thất bại để liệt kê. Không sửa mã nguồn hoặc code test, không bỏ qua test, không thay đổi assertion để ép PASS.

### 4.2. Phát hiện qua review — không phải pytest FAIL

#### RV-01 — Văn bản chatbot chưa được kiểm tra grounding sau sinh (ưu tiên cao)

- Yêu cầu liên quan: NFR-04, CB-AC-14 và CB-AC-25; ca thiết kế CB-04.
- File/hàm: `D:\New folder (7)\Cinema_System\app\services\chatbot_service.py::process_chat`, dòng 36–38. Kết quả `generate_response(prompt)` được trả thẳng dưới trường `answer`; cards được xây riêng từ retrieval bằng `_card_from_screening`.
- Đường trả API: `D:\New folder (7)\Cinema_System\app\routes\chatbot.py`, trả `result['answer']` trong response JSON.
- Bằng chứng kiểm thử liên quan: `D:\New folder (7)\Cinema_System\tests\test_chatbot_api.py::test_cards_are_not_changed_by_answer` mock model trả **“Phòng B, giá 999999”**, trong khi dữ liệu nguồn là **Phòng A**. Test đã PASS vì chỉ assert `room_name` và `booking_url` của card không đổi; không assert answer bịa bị loại hoặc bị từ chối.
- Root cause ở tầng được review: có prompt/grounding rules và bảo vệ card bằng dữ liệu backend, nhưng thiếu bước đối chiếu/lọc văn bản model trước khi đưa vào API response. Assertion hiện có chỉ bảo vệ cards, không kiểm chứng toàn bộ tiêu chí văn bản và card cùng có căn cứ.
- Tác động: API có thể trả khẳng định ngoài nguồn dù card đúng. Chưa chạy E2E trình duyệt để đánh giá mọi biểu hiện hiển thị; đây là phát hiện code review, không đổi thống kê FAIL=0 và không khẳng định đã chạy một ca nghiệm thu mới.
- Đề xuất: bổ sung ca hồi quy riêng xác nhận văn bản sai nguồn bị loại/từ chối, rồi thiết kế cơ chế grounding output tương ứng. Không sửa test hiện có chỉ để che lỗ hổng.

#### DOC-01 — Thiếu file tiêu chí nghiệm thu toàn dự án

- File: `D:\New folder (7)\Cinema_System\docs\acceptance-criteria.md`; hàm: không áp dụng (tài liệu).
- Hiện trạng/root cause quan sát được: skill tham chiếu file không có trên filesystem; tiêu chí toàn hệ thống đang nằm trong User Stories. Không đủ bằng chứng để quy nguyên nhân cho người hoặc thay đổi cụ thể.
- Tác động: không thể xác nhận bộ tiêu chí riêng đã phê duyệt. Đã dùng nguồn thực tế và công bố giới hạn thay vì giả tạo tài liệu.

## 5. Requirements Coverage

Đánh giá bằng đối chiếu requirements/User Stories với assertions thực tế; **không đo line/branch coverage**. “Một phần” nghĩa là có test liên quan đã PASS, không có nghĩa toàn bộ yêu cầu đã nghiệm thu. Tên hàm bên dưới thuộc các file trong `D:\New folder (7)\Cinema_System\tests`.

| Yêu cầu / Story | Bằng chứng đã PASS | Phần chưa chứng minh / trạng thái |
|---|---|---|
| FR-01 / US-01 | test_admin: movies/homepage, age rating/keywords, generate-description input/provider/preview; test_core: draft | **Một phần:** CRUD sửa/xóa đầy đủ và tổ hợp trạng thái còn thiếu |
| FR-02 / US-02 | room counts, maintenance, transaction rollback, browser room creation | **Một phần:** sửa/xóa phòng, cấu hình ghế tùy ý chưa có ca chuyên biệt |
| FR-03 / US-03 | schedule_both_sides, cleanup_boundary, conflict form, cutoff 14/15/16 phút | **Một phần:** mạnh ở lịch và POS; chưa chứng minh cutoff trên mọi đường bán online; test chọn buffer 15 phút, không đánh giá toàn bộ cách diễn giải khoảng 10–15 phút |
| FR-04 / US-04 | Payment Standard 80.000/VIP 110.000, POS tổng 190.000, nhãn Couple 160k | **Một phần, thiếu lớn:** cấu hình giá Admin, phụ thu sau 18h/T6–CN/ngày lễ và tính tiền Couple chưa có test đầy đủ |
| FR-05 / US-05 | read_only_seat_map, booking HTML/loại ghế, POS map sau cancel | **Một phần:** realtime, màu/trạng thái qua browser và độ trễ chưa kiểm thử |
| FR-06 / US-06 | hold creation, bán/giữ trùng tuần tự; analyzer/retrieval/pipeline mock | **Một phần:** TTL đúng 5 phút và biên, cạnh tranh song song, gợi ý đúng 2–3 phim đủ số ghế theo nhu cầu còn thiếu |
| FR-07 / US-07 | history ownership/cancel, eligibility 120/59 phút, vé USED/check-in; staff releases seats | **Một phần:** biên chính xác 60 phút và hoàn tiền thật chưa thực thi |
| FR-08 / US-08 | payment/ticket access, CSRF, process lặp 409, payment fail release, QR check-in | **Một phần:** gateway/callback thật, hold hết hạn, sai chủ hold và rollback giữa payment/ticket còn thiếu |
| FR-09 / US-09 | QR hợp lệ, sai ngày, check-in một lần, checked_in_at | **Một phần:** QR giấy/camera, dữ liệu QR lỗi và thiết bị chưa thực thi |
| FR-10 / US-10 | lookup email/phone/QR, lịch sử chỉ chủ sở hữu; retrieval genre/date/time filters | **Một phần:** chưa E2E toàn bộ UI tìm kiếm/lọc và tổ hợp dữ liệu |
| FR-11 / US-11 | doanh thu 250.000, 4 vé/80 ghế/5%, loại payment thất bại/refund, report rỗng, AI tính từ server | **Một phần:** theo từng phim/suất/tuần/tháng; kiểm chứng mọi output đúng 3–4 câu chưa đầy đủ |
| FR-12 / US-12 | draft approval/reject/edit, audit, không public trước duyệt, invalid edit rollback | **Một phần:** workflow duyệt tóm tắt doanh thu chưa có test đầy đủ |
| FR-13 / US-13 | login/logout, wrong password, CUSTOMER bị chặn, X-Role giả, CSRF, secret ngẫu nhiên/cookie cách ly | **Một phần:** chưa audit toàn bộ endpoint, dữ liệu nhạy cảm và lifecycle tài khoản |
| NFR-01 | HTML/widget/assets, thông báo nghiệp vụ, Couple rendering | **Một phần:** usability/accessibility/browser/mobile chưa đánh giá |
| NFR-02 | không bán trùng tuần tự, room rollback, payment/ticket/hold nhất quán ở happy path | **Một phần:** tải, latency, deadlock/cạnh tranh và rollback mọi transaction chưa kiểm thử |
| NFR-03 | vai trò, CSRF, ownership, allowlist PII, SQL tham số, lỗi/log provider an toàn | **Một phần:** không thay thế pentest/audit mã hóa/riêng tư toàn hệ thống |
| NFR-04 | prompt/context quoting, không đoán field, backend cards, AI draft | **Một phần + RV-01:** văn bản model thiếu kiểm tra hậu sinh; không kết luận đạt anti-hallucination |
| NFR-05 | pure unit tests theo module, migration legacy idempotent | **Một phần:** có bằng chứng khả năng kiểm thử độc lập; không lượng hóa toàn bộ maintainability/extensibility |

**Bao phủ liên kết:** 13/13 FR và 5/5 NFR có bằng chứng test liên quan trong ma trận (100% ở mức có liên kết). **Không được diễn giải thành 100% tiêu chí được kiểm chứng hoặc 100% hệ thống đạt yêu cầu.** Tất cả hàng đều còn giới hạn; không báo tỷ lệ nghiệm thu đầy đủ khi chưa có mẫu số tiêu chí hợp nhất và test tương ứng.

### 5.1. Tiêu chí Chatbot RAG

| Nhóm CB-AC | Bằng chứng / đánh giá |
|---|---|
| 01–04 | Analyzer tiếng Việt/timezone, filters, pipeline mock PASS; hỏi lại mơ hồ, tìm nội dung/từ khóa chưa chứng minh đầy đủ |
| 05–07 | Retrieval đúng phòng/suất, distinct occupancy, BOOKED/USED, expired holds/CANCELLED PASS trên dữ liệu fixture |
| 08–09 | Context không bịa giá/chính sách và prompt PASS; chưa kiểm chứng hành vi mọi văn bản output model |
| 10–12 | Empty cards, backend card values, `/booking/X` PASS; không đồng nghĩa toàn bộ answer grounded hoặc click E2E không ghi |
| 13 | DB lỗi phát OperationalError (không rỗng giả) và API xử lý lỗi an toàn có test; chưa đầy đủ mọi timeout DB |
| 14,25 | **Không đủ bảo vệ văn bản: RV-01**; test card-only PASS không đáp ứng toàn bộ AC |
| 15–16 | Context có checked_at tùy chọn và không tự dựng field, prompt no-results PASS; cảnh báo timestamp UI và mọi ví dụ/model output chưa kiểm chứng |
| 17–21 | SQL injection, allowlist bí mật/PII, log lỗi và cấu hình key mock có test; chưa đầy đủ các yêu cầu giao dịch/sửa dữ liệu qua chat và audit secrets toàn bundle. Tên module Gemini/Claude cũ nhưng SDK hiện được mock là Groq |
| 22 | Chưa có ca UI hết ghế/đóng bán chuyên biệt |
| 23–24 | Quoting câu hỏi/context và HTML rendering có test; chống injection hành vi model và XSS trên browser chưa kiểm thử đầy đủ |

## 6. Kết luận và ưu tiên tiếp theo

1. **Suite hồi quy hiện có đạt: 245 PASS / 0 FAIL, exit 0; database chính bất biến.** Không sửa source/test để đạt kết quả này.
2. **Chưa thể tuyên bố nghiệm thu toàn bộ hệ thống.** Đợt chạy giới hạn ở tests hiện có, Flask client/SQLite và dependency mock; không có live payment, live LLM, MySQL integration, browser E2E, camera, benchmark hay coverage instrumentation.
3. Ưu tiên cao: grounding văn bản RAG (RV-01), TTL/expiry hold, concurrency chống bán trùng, rollback thanh toán/callbacks và biên hủy 60 phút.
4. Sau đó: giá theo ngày/giờ/loại ghế, CRUD còn thiếu, báo cáo phân nhóm phim/suất/tuần/tháng, duyệt AI doanh thu, E2E/XSS/accessibility và hiệu năng.
5. Hoàn thiện nguồn tiêu chí nghiệm thu toàn hệ thống hoặc thống nhất dùng User Stories; giữ traceability và phân biệt rõ thiết kế/chưa chạy/PASS/FAIL trong mọi đợt tiếp theo.

Kiểm tra cuối: đã đọc lại plan/report, đối chiếu collected và các dòng kết quả trong log, xác nhận lại hash/size/mtime DB. Thư mục dự án không phải Git repository, nên không thể dùng `git status` để chứng minh diff toàn workspace; phiên hoàn tất này chỉ tạo report và chuyển encoding hai artifact log/metadata, không chỉnh source/test và không chạy lại pytest.

Artifacts hoàn tất: `D:\New folder (7)\Cinema_System\docs\test-plan.md` (18 scenarios, 26 ca thiết kế), `D:\New folder (7)\Cinema_System\docs\test-report.md` (kết quả, defects/review và coverage). Các ca thiết kế chưa tự động hóa không được cộng vào 245 PASS.