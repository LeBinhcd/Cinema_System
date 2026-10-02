# Luồng dữ liệu Chatbot RAG – AI Cinema Assistant

**Bước:** Phần XXIII – Bước 4, Architecture Design  
**Trạng thái:** Dự thảo, chờ Human Gate 2  
**Mục tiêu:** Mô tả DFD/sequence flow khép kín từ Web UI tới JSON answer/cards; không bao gồm implementation code.

## 1. Các thực thể và kho dữ liệu

| Ký hiệu | Thành phần | Vai trò |
|---|---|---|
| E1 | Khách hàng/Web Chat UI | Nhập câu hỏi, nhận answer/cards, bấm booking link. |
| P1 | Chatbot API | HTTP boundary, JSON validation, CSRF/session. |
| P2 | Chat Orchestrator | Điều phối các bước RAG. |
| P3 | Question Analyzer | Question → Structured Intent JSON. |
| P4 | Intent/Policy Guard | Validate intent, scope, ambiguity, refusal. |
| P5 | Movie & Screening Retriever | Parameterized retrieval trên SQLite và availability snapshot. |
| P6 | Context/Prompt Builder | Public context → grounded prompt. |
| P7 | Claude Service | Gọi Anthropic bằng server-side key, timeout 15 giây. |
| P8 | Response Handler | Validate text, sinh cards từ facts, tạo URL. |
| D1 | SQLite cinema DB | `movies`, `genres`, `movie_genres`, `screenings`, `screening_rooms`, `seats`, `tickets`, `seat_holds`. |
| D2 | Server environment/.env | `ANTHROPIC_API_KEY`, model/configuration; không gửi ra client. |
| X2 | Anthropic Claude API | Chỉ nhận context tối thiểu để diễn đạt. |
| X2 | Google Gemini API | Chỉ nhận context tối thiểu để diễn đạt. |

## 2. DFD mức ngữ cảnh

```text
       question + session/CSRF
E1 ─────────────────────────────► P1 Chatbot API
                                  │ validated question
                                  ▼
                            P2 Chat Orchestrator
                                  │
                  ┌───────────────┼────────────────┐
                  ▼               ▼                ▼
             P3 Analyzer     P5 Retriever       P6 Context
                                  │                │
                                  ▼                ▼
                               D1 SQLite       P7 Claude Service ───► X2 Claude
                                  │                │                    │
                                  └──── facts ◄────┴──── text ───────────┘
                                                    ▼
                                             P8 Response Handler
                                                    │ answer + cards
                                                    ▼
E1 ◄─────────────────────────────────────────────── P1
                                                    │ booking_url
                                                    ▼
                                      X1 /booking/<screening_id>
```

Không có mũi tên từ E1/Gemini tới D1. Gemini không được nhận quyền truy vấn D1. Card chỉ mang route và ID đã được P5 xác nhận.

## 3. Sequence Flow – đường đi thành công

### 3.1. Request và security boundary

1. Khách hàng nhập câu hỏi tiếng Việt trên Web Chat UI.
2. UI gửi `POST /api/chat` qua HTTPS với JSON `{question}` và session cookie.
3. UI gửi CSRF token theo cơ chế session hiện hữu, ví dụ header `X-CSRF-Token`.
4. P1 kiểm tra content type, JSON shape, question length, session cookie và CSRF token.
5. Nếu không hợp lệ, P1 trả JSON lỗi an toàn; không gọi Analyzer, DB hoặc Gemini.

### 3.2. Analyze và policy

6. P1 chuyển question đã giới hạn cho P2.
7. P2 gọi P3; P3 trích xuất `genre`, `movie_title`, `date`, `time_range`, `seat_type`, `action`.
8. P4 validate enum, ngày, khoảng giờ, phạm vi và prompt-injection. P4 resolve `TODAY/TOMORROW` theo `Asia/Ho_Chi_Minh`.
9. Nếu câu hỏi mơ hồ, P4 trả `CLARIFY`; P2 bỏ qua DB/Gemini và P8 tạo câu hỏi ngắn để khách bổ sung.
10. Nếu yêu cầu giao dịch, bí mật, SQL hoặc ngoài phạm vi, P4 trả `REFUSE`; P8 tạo refusal an toàn và `cards=[]`.

### 3.3. Retrieval và availability snapshot

11. Với intent hợp lệ, P2 chuyển intent đã validate cho P5.
12. P5 chuyển symbolic time range thành khoảng thời gian policy đã duyệt; dùng timezone `Asia/Ho_Chi_Minh`.
13. P5 thực hiện các truy vấn SQL tham số hóa qua Data Access Layer. Không có chuỗi SQL từ user/model.
14. P5 lọc `movies`/genres và `screenings`, join đúng `screening_rooms`.
15. Với từng screening, P5 chỉ lấy `seats` thuộc `room_id` đó.
16. P5 loại ghế có `tickets.status IN (BOOKED, USED)` hoặc `seat_holds.expires_at > checked_at`.
17. P5 đếm ghế còn trống theo `STANDARD`, `VIP`, `COUPLE`, lấy policy giá 80.000/110.000/160.000 VND và cutoff hủy 60 phút từ nguồn policy.
18. P5 ghi `checked_at` theo `Asia/Ho_Chi_Minh`, `sales_open` và source status.
19. P5 trả facts có cấu trúc cho P2; không trả raw rows/PII ra ngoài module.

### 3.4. Context, Claude và response

20. P6 chọn trường công khai, loại user/payment/secret/SQL và tạo context ngắn.
21. Nếu source status là `EMPTY`, P2/P8 trả “không tìm thấy...” và `cards=[]`; không gửi empty context để Gemini đoán.
22. Nếu source status là `ERROR`, P2/P8 trả “chưa thể kiểm tra...” và `cards=[]`; không nói “không có suất”.
23. Nếu source status là `INSUFFICIENT`, P8 nêu phần chưa xác nhận và từ chối cam kết.
24. Nếu cần diễn đạt, P6 tạo system rules + task + context; P7 gọi X2 với timeout 15 giây.
25. P7 không gửi API key trong payload; key chỉ được đọc tại server từ D2.
26. Nếu X2 timeout/error/malformed, P7 báo lỗi nội bộ cho P2; P8 dùng câu trả lời an toàn, không bịa và `cards=[]` hoặc facts-only fallback đã được duyệt.
27. Nếu có text, P8 escape/normalize và kiểm tra text không thêm facts ngoài retrieval snapshot.
28. P8 sinh cards trực tiếp từ facts P5, không parse card từ text Gemini.
29. P8 tạo `booking_url=/booking/<screening_id>` từ screening ID đã xác nhận.
30. P1 trả JSON `{answer, cards}` cho E1.

## 4. Sequence Flow – khách bấm “Đặt vé ngay”

1. E1 chọn một card đã hiển thị.
2. Browser điều hướng tới `/booking/<screening_id>`.
3. Đây là ranh giới sang X1, không phải Chatbot transaction.
4. Booking Core tự kiểm tra lại session/login, screening tồn tại, sales cutoff, trạng thái phòng, ghế, giá và transaction.
5. Chatbot không truyền hold token, payment data hoặc lệnh mua vé; card không phải reservation.

## 5. Nhánh lỗi và hành vi bắt buộc

| Điểm lỗi | Phản hồi | Không được làm |
|---|---|---|
| JSON/question/session/CSRF invalid | HTTP lỗi phù hợp + JSON error tổng quát | Gọi Gemini hoặc trả stack trace. |
| Analyzer không hiểu/mơ hồ | Hỏi lại ngắn, `cards=[]` | Tự đoán ngày/film/time làm đổi kết quả. |
| Out-of-scope/transaction/secret | Refusal an toàn, `cards=[]` | Giữ ghế, thanh toán, tiết lộ key/SQL/PII. |
| DB query lỗi/timeout | “Chưa thể kiểm tra, thử lại” | Biến lỗi thành “không có suất”. |
| Query hợp lệ nhưng không có rows | “Không tìm thấy...” | Tạo phim, giờ, phòng hoặc ghế giả. |
| Thiếu giá/chính sách | Chưa có thông tin xác nhận | Đoán giá/phí/hoàn tiền. |
| Gemini timeout > 8 giây | Lỗi an toàn/facts-only nếu được duyệt | Chờ vô hạn hoặc bịa để lấp câu trả lời. |
| Gemini output ngoài context | Loại claim hoặc refusal | Tin text model hơn facts backend. |
| Suất hết ghế/đóng bán | Card unavailable/ẩn action | Hiển thị như đang mở bán. |
| HTML/script từ input/DB/model | Escape hoặc loại bỏ | Render executable HTML/JavaScript. |

## 6. Dữ liệu đi qua từng bước

| Bước | Input | Output | Dữ liệu bị loại |
|---|---|---|---|
| API validation | HTTP body, session, CSRF | Valid question | Headers/body ngoài contract, malformed data |
| Analyzer | Vietnamese question | Structured Intent | SQL/instructions disguised as intent |
| Policy Guard | Intent | Allowed/clarify/refuse | Invalid enum, ambiguous values, injection |
| Retriever | Validated intent | Screening facts + seat counts + source status | PII, hold owner, raw DB rows |
| Context Builder | Facts | Minimal grounded context | Secret, payment, password, SQL, internal paths |
| Gemini Service | System rules + context | Untrusted text/error | API key in payload/log/response |
| Response Handler | Facts + untrusted text | Safe answer/cards | Unsupported claims, model-generated IDs/URLs |
| Booking Core | Screening ID route | Existing booking page/revalidation | Implicit hold/payment from chatbot |

## 7. Tính nhất quán và snapshot

- `checked_at`, screening facts và counts phải thuộc cùng một retrieval snapshot logic.
- Text và cards phải cùng tham chiếu snapshot; nếu validator phát hiện lệch, ưu tiên facts và loại claim lệch.
- Card không cam kết ghế được giữ; UI phải hiển thị thời điểm kiểm tra và cảnh báo trạng thái có thể thay đổi.
- `booking_url` chỉ được dựng từ `screening_id` backend; không nhận URL do Gemini trả.
- Booking Core phải revalidate vì availability có thể thay đổi sau khi chatbot trả response.

## 8. Dữ liệu nhạy cảm và quan sát hệ thống

Log/audit ở mức kiến trúc chỉ được ghi metadata tối thiểu đã khử dữ liệu: request correlation ID, outcome category (`FOUND/EMPTY/ERROR/REFUSE`), thời gian xử lý, timeout/error class và số card. Không ghi question nguyên văn nếu có nguy cơ chứa PII, không ghi prompt đầy đủ, context nhạy cảm, API key hoặc payment data. Retention và quyền truy cập log cần được Security/Privacy chốt trước triển khai.

## 9. Đối chiếu với acceptance criteria

| Acceptance criteria | Điểm kiểm soát trong flow |
|---|---|
| CB-AC-01/02 | Analyzer + Policy Guard bước 7–10 |
| CB-AC-03/04 | Retriever bước 12–14 |
| CB-AC-05/06/07 | Retriever bước 15–18 |
| CB-AC-08/09 | Policy source + Context status `INSUFFICIENT` |
| CB-AC-10 | Nhánh `EMPTY` bước 21 |
| CB-AC-11/12 | Response Handler bước 27–29 |
| CB-AC-13 | Nhánh DB error bước 22 |
| CB-AC-14/16/25 | Grounding validator bước 27–28 và snapshot section |
| CB-AC-15/22 | `checked_at`, `sales_open`, card state |
| CB-AC-17/21 | Policy Guard refusal |
| CB-AC-18/19/20/23/24 | Security boundaries, Gemini Service và safe rendering |

## 10. Giới hạn của thiết kế Bước 4

Thiết kế này chưa tạo route, service, SQL migration, prompt file, test, rate-limit middleware hoặc Gemini client code. Chưa tạo sub-skills phân tích/truy xuất. Các việc đó chỉ được thực hiện sau khi hai tài liệu này được duyệt tại Human Gate 2 và khi các policy còn thiếu được xác nhận.
