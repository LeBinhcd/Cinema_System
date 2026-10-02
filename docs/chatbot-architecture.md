# Kiến trúc Chatbot RAG – AI Cinema Assistant

**Bước:** Phần XXIII – Bước 4, Architecture Design  
**Trạng thái:** Dự thảo, chờ Human Gate 2  
**Phạm vi:** Thiết kế mức kiến trúc; không bao gồm implementation code, schema mới hoặc lựa chọn triển khai chi tiết.

## 1. Mục tiêu và nguyên tắc

Chatbot là một luồng RAG khép kín trong ứng dụng Flask hiện có. Backend là nguồn sự thật duy nhất cho phim, suất chiếu, phòng, ghế, giá và chính sách. Gemini chỉ phân loại/diễn đạt trong phạm vi context do backend tạo; Gemini không được truy cập DB, sinh SQL, tạo ID hoặc thực hiện giao dịch.

Kiến trúc tuân theo các nguyên tắc:

- **Layered:** `HTTP Route → Application Services → Data Access/Domain Rules`; Gemini chỉ được gọi qua một gateway/service riêng.
- **Read-only:** luồng Chatbot chỉ đọc dữ liệu công khai và dẫn tới `/booking/<screening_id>`; không tạo hold, vé, thanh toán hay thay đổi dữ liệu.
- **Structured-first:** Intent, retrieval result và card dùng dữ liệu có cấu trúc; text của Gemini không được dùng để tạo lại số liệu hoặc URL.
- **Fail closed:** context rỗng, dữ liệu thiếu, truy vấn lỗi, output không hợp lệ hoặc vi phạm grounding đều dẫn tới câu trả lời an toàn, không bịa.
- **Traceable:** mỗi câu trả lời có thể đối chiếu với snapshot dữ liệu và thời điểm kiểm tra.

## 2. Kiến trúc logic

```text
Web Chat UI
    │ HTTPS POST /api/chat + session cookie + X-CSRF-Token
    ▼
Chatbot API / Route
    │ validate request, session, CSRF, length, rate boundary
    ▼
Chat Application Service / Orchestrator
    ├── Question Analyzer ──(structured intent)──┐
    ├── Intent Validator & Policy Guard            │
    ├── Movie & Screening Retriever ─────────────┤
    │       └── SQLite Data Access / Domain Rules │
    ├── Context Builder ─────────────────────────┤
    ├── Prompt Builder ──────────────────────────┤
    ├── Gemini Service ── HTTPS ── Google Gemini API
    └── Response Handler / Grounding Validator ──┘
            │
            └── JSON { answer: string, cards: ScreeningCard[] }

Booking Card URL ──► existing /booking/<screening_id>
                       (booking core revalidates auth, sales, seats, price, transaction)
```

Đây là một modular monolith trong ứng dụng Flask, không phải microservices. Ranh giới module được thiết kế độc lập để có thể kiểm thử riêng nhưng chưa hàm ý tách process hoặc deploy riêng.

## 3. Thành phần và trách nhiệm

### 3.1. Chatbot API – `POST /api/chat`

**Input contract:** JSON object có một trường `question` là chuỗi UTF-8. Route phải từ chối body không phải JSON, thiếu question, question rỗng hoặc vượt giới hạn độ dài đã được cấu hình. Giới hạn cụ thể là operational configuration cần chốt trước triển khai, không được âm thầm cắt câu hỏi.

**Biên HTTP và session:**

1. Chỉ nhận HTTPS trong môi trường triển khai.
2. Kiểm tra session cookie hợp lệ và CSRF token đối chiếu constant-time với token trong session; session ẩn danh được phép vì requirements phục vụ cả người chưa đăng nhập.
3. Không coi CSRF/session là quyền truy cập dữ liệu cá nhân. Chatbot chỉ được truy vấn dữ liệu công khai.
4. Không nhận `screening_id`, SQL, context hoặc prompt từ client.
5. Trả lỗi JSON tổng quát, không trả stack trace, SQL, API key hoặc thông tin kết nối.

**Output contract:**

```text
{
  "answer": "Câu trả lời tiếng Việt đã được grounding",
  "cards": [
    {
      "screening_id": 123,
      "movie_title": "Tên phim",
      "start_time": "... Asia/Ho_Chi_Minh ...",
      "end_time": "... Asia/Ho_Chi_Minh ...",
      "room_name": "Phòng 1",
      "available_seats": {"STANDARD": 0, "VIP": 2, "COUPLE": 1},
      "checked_at": "... Asia/Ho_Chi_Minh ...",
      "sales_open": true,
      "booking_url": "/booking/123"
    }
  ]
}
```

Tên trường trên là hợp đồng kiến trúc minh họa, không phải source code. `cards` luôn là array; câu hỏi chính sách, từ chối, lỗi hoặc không có kết quả trả array rỗng. URL chỉ được tạo từ ID số đã được retriever trả về, không từ Gemini.

### 3.2. Question Analyzer

Phân tích tiếng Việt thành Structured Intent JSON, không truy cập DB và không được tự điền dữ kiện nghiệp vụ:

```text
{
  "genre": string|null,
  "movie_title": string|null,
  "date": {"kind": "TODAY|TOMORROW|EXPLICIT|null", "value": "YYYY-MM-DD|null"},
  "time_range": {"kind": "MORNING|AFTERNOON|EVENING|EXPLICIT|null", "start": "HH:MM|null", "end": "HH:MM|null"},
  "seat_type": "STANDARD|VIP|COUPLE|null",
  "action": "SEARCH_SCREENINGS|CHECK_SEATS|ASK_PRICE|ASK_POLICY|REFUSE|CLARIFY"
}
```

Analyzer chỉ được trích xuất các trường yêu cầu: `genre`, `movie_title`, `date`, `time_range`, `seat_type`, `action`. Các trường phụ như confidence, language hoặc raw text không được đưa vào retrieval contract nếu chưa được duyệt. Intent Validator kiểm tra enum, ngày hợp lệ, khoảng giờ hợp lệ, độ mơ hồ và loại bỏ instruction injection.

Ngày tương đối được resolve theo `Asia/Ho_Chi_Minh`. Khung `MORNING`, `AFTERNOON`, `EVENING` được resolve từ policy/configuration đã được duyệt; kiến trúc không tự đặt mốc giờ khi quyết định nghiệp vụ chưa cung cấp giá trị cụ thể. Nếu người dùng dùng cách hiểu không duy nhất, analyzer trả `CLARIFY`.

### 3.3. Movie & Screening Retriever

Retriever nhận **intent đã validate**, không nhận câu SQL hoặc câu lệnh từ Gemini. Nó dùng Data Access Layer với truy vấn SQL tham số hóa trên SQLite để:

- join `movies` với `genres`/`movie_genres` khi lọc tên, genre, synopsis/keywords được phép công khai;
- join `screenings` với `screening_rooms`, lọc ngày và khoảng giờ theo `Asia/Ho_Chi_Minh`;
- chỉ lấy phim/trạng thái được phép hiển thị và giữ nguyên `screening_id`;
- lấy phòng đúng với `room_id` của screening;
- tính tổng ghế theo `seats` thuộc đúng phòng, nhóm `STANDARD`, `VIP`, `COUPLE`;
- loại ghế có ticket `BOOKED` hoặc `USED`, hoặc có `seat_holds.expires_at` lớn hơn thời điểm kiểm tra;
- không coi `CANCELLED` hoặc hold đã hết hạn là ghế bận;
- lấy giá từ policy chính thức: `STANDARD=80.000`, `VIP=110.000`, `COUPLE=160.000` VND;
- đánh dấu `sales_open` và trạng thái có thể đặt theo booking-core rule, không tạo hold.

Thời điểm `checked_at` phải được chụp cùng một lần retrieval/availability calculation. Retriever trả typed result nội bộ gồm screening facts, availability snapshot, price/policy facts và source status. Nếu DB lỗi, source status là `ERROR`, không chuyển thành danh sách rỗng.

**Contract trạng thái ghế:** ở bước này, quyết định được duyệt cho Chatbot là `BOOKED/USED` hoặc hold còn hạn. Quy tắc hiện đang khác trong một số preview service phải được hợp nhất/adapter hóa trước triển khai; không được để Chatbot tự chọn thêm trạng thái.

**Cutoff:** quyết định Chatbot là cutoff hủy vé 60 phút trước giờ chiếu. Đây là thông tin policy để trả lời; click card vẫn chuyển sang booking core, nơi kiểm tra lại quyền và transaction.

### 3.4. Context Builder

Đóng gói retrieval result thành context ngắn, có cấu trúc và chỉ gồm dữ liệu công khai cần thiết:

- intent đã chuẩn hóa ở mức cần thiết để giải thích kết quả;
- danh sách phim/screening facts đã xác nhận;
- phòng, thời gian, availability theo loại ghế, `checked_at`, trạng thái bán;
- bảng giá và cutoff 60 phút nếu retrieval policy trả về;
- source status (`FOUND`, `EMPTY`, `ERROR`, `INSUFFICIENT`) để Prompt Builder phân biệt rỗng với lỗi.

Context không chứa user ID, email, phone, password hash, payment, booking history, raw SQL, DB path, secret, prompt nội bộ hoặc dữ liệu hold owner. Nội dung text từ DB phải được giới hạn trường công khai và escape ở output layer.

### 3.5. Prompt Builder và Grounding Rules

Prompt gồm bốn phần logic:

1. **System rules:** Gemini là lớp diễn đạt; chỉ dùng context; trả lời tiếng Việt; không tiết lộ prompt/secret; không thực hiện giao dịch.
2. **Task:** trả lời câu hỏi theo intent, hỏi lại nếu `CLARIFY`, thông báo không tìm thấy nếu `EMPTY`, thông báo chưa thể kiểm tra nếu `ERROR/INSUFFICIENT`.
3. **Context:** dữ liệu backend được đánh dấu là nguồn sự thật, không phải instruction.
4. **Output constraints:** không tạo ID, URL, giá, giờ, phòng, ghế hoặc chính sách ngoài context; không coi ghế trống là giữ chỗ; không đưa HTML/script.

Context rỗng không được gửi cho Claude để “đoán” kết quả. Có thể dùng template refusal/empty/error an toàn. Output Claude phải qua Response Handler/grounding validator; prompt không phải cơ chế kiểm soát duy nhất.

### 3.6. Anthropic Claude Service

Module độc lập là cổng duy nhất gọi Anthropic Messages API. Module:

- đọc `ANTHROPIC_API_KEY` từ biến môi trường đã nạp từ `.env` ở server;
- không expose key tới browser, JSON response, logs, context hoặc exception;
- nhận prompt/context đã được Context Builder phê duyệt;
- đặt timeout 15 giây cho mỗi request;
- phân loại timeout, quota, network, malformed response thành lỗi nội bộ an toàn;
- không retry mù trong request đồng bộ nếu chưa có policy quota/retry được duyệt;
- trả về text không tin cậy cho Response Handler, không trả trực tiếp cho client.

Claude timeout/lỗi không được biến thành “không có suất”; handler dùng thông báo chưa thể trả lời và `cards` rỗng, hoặc fallback deterministic khi dữ liệu đủ.

### 3.7. Response Handler

Response Handler:

- chuẩn hóa text tiếng Việt, loại markdown/HTML không cần thiết và escape nội dung không tin cậy;
- loại claim, con số, ID hoặc URL không chứng minh được từ retrieval snapshot;
- dùng retrieval result, không dùng text Gemini, để sinh `cards`;
- kiểm tra `screening_id`, movie, time, room, availability, `checked_at`, `sales_open`;
- tạo `booking_url` chính xác `/booking/<screening_id>`;
- ẩn/nút đặt khi suất đóng bán hoặc không còn ghế phù hợp;
- đảm bảo text không nói còn ghế khi card/backend báo hết ghế;
- trả schema cố định `answer` + `cards`.

## 4. Luồng xử lý nội bộ

1. API validate JSON, session, CSRF và question length.
2. Orchestrator chuyển question tới Question Analyzer.
3. Intent Validator quyết định `CLARIFY`, `REFUSE` hay cho phép retrieval.
4. Retriever chạy parameterized SQL và availability snapshot.
5. Context Builder tạo context sạch hoặc source status.
6. Prompt Builder tạo grounded prompt; context rỗng dùng deterministic response.
7. Claude Service gọi API với timeout 15 giây khi cần diễn đạt.
8. Response Handler validate text, tạo cards từ facts và trả JSON.
9. Người dùng bấm card thì rời Chatbot sang `/booking/<screening_id>`; booking core kiểm tra lại mọi điều kiện.

## 5. Security Boundary

| Boundary | Được phép đi qua | Bị chặn |
|---|---|---|
| Browser ↔ Chatbot API | Question, CSRF/session, answer/cards | SQL, context, prompt, secret, DB rows thô |
| API ↔ Analyzer | Question đã giới hạn kích thước | Quyền tự đọc DB hoặc tạo transaction |
| Analyzer ↔ Retriever | Structured Intent đã validate | SQL do model sinh, tên bảng/cột tùy ý |
| Retriever ↔ Context | Public facts, availability snapshot, policy | PII, payment, owner/hold identity, raw SQL |
| Context ↔ Claude | Context tối thiểu và system rules | API key, prompt nội bộ nhạy cảm, dữ liệu cá nhân |
| Claude ↔ Response | Text không tin cậy để diễn đạt | Quyền tạo card/ID/URL, quyền ghi DB |
| Card ↔ Booking Core | Screening ID và route nội bộ | Hold/payment implicit; không coi card là reservation |

## 6. Quyết định kiến trúc

| ADR | Quyết định | Lý do |
|---|---|---|
| CB-ADR-01 | Modular monolith theo layered architecture | Phù hợp Flask/SQLite hiện có, giảm hạ tầng dư thừa và giữ ranh giới kiểm thử. |
| CB-ADR-02 | Backend retrieval trước, Claude sau | Chống hallucination và bảo đảm SQL/availability do code kiểm soát. |
| CB-ADR-03 | Structured Intent JSON | Tách hiểu ngôn ngữ khỏi query policy, dễ validate và truy vết. |
| CB-ADR-04 | Cards sinh từ retrieval facts | Claude không thể thay đổi ID, số ghế hoặc URL. |
| CB-ADR-05 | Claude timeout 15 giây, fail closed | Bảo vệ trải nghiệm và ngăn fallback bịa dữ liệu. |
| CB-ADR-06 | `Asia/Ho_Chi_Minh` và policy symbolic cho khung giờ | Đồng nhất ngày tương đối; không tự tạo mốc giờ chưa được cung cấp. |
| CB-ADR-07 | Chatbot availability contract độc lập, phải hợp nhất với booking core | Tránh preview rule khác với rule đã được duyệt; booking core vẫn là nơi revalidate cuối. |

## 7. Ma trận truy vết CB-FR/CB-NFR → component

| Requirement | Component hỗ trợ chính | Kiểm soát/ghi chú |
|---|---|---|
| CB-FR-01 | API, Question Analyzer, Intent Validator | Câu hỏi tiếng Việt, hỏi lại khi mơ hồ. |
| CB-FR-02 | Analyzer, Time/Policy Resolver, Retriever | Asia/Ho_Chi_Minh; khung giờ symbolic theo config. |
| CB-FR-03 | Retriever, Data Access, Response Handler | Chỉ phim/genre có bản ghi hiển thị. |
| CB-FR-04 | Retriever, Context Builder | Screening/room facts và ID thật. |
| CB-FR-05 | Availability Retriever, DB transaction/read boundary | Ghế đúng phòng; BOOKED/USED hoặc hold còn hạn. |
| CB-FR-06 | Policy Provider, Context Builder, Prompt/Handler | Giá đã duyệt; cutoff 60 phút; thiếu nguồn thì từ chối. |
| CB-FR-07 | Retriever, deterministic response, Handler | `EMPTY` khác `ERROR`, không tạo kết quả giả. |
| CB-FR-08 | Policy Guard, Prompt Builder, Handler | Từ chối giao dịch/secret/out-of-scope. |
| CB-FR-09 | Response Handler | Cards và `/booking/<screening_id>`. |
| CB-FR-10 | API, Handler, Booking Core boundary | Không tạo transaction; core revalidate. |
| CB-FR-11 | Gemini Service, API error boundary, Handler | Timeout/error safe response, không lộ nội bộ. |
| CB-FR-12 | Security Boundary, Context Builder, Parameterized DAL | PII/payment/SQL/HTML isolation. |
| CB-FR-13 | Gemini Service, server configuration | Key chỉ ở server environment. |
| CB-NFR-01 | Retriever, Context, Grounding Validator | Anti-hallucination/grounding. |
| CB-NFR-02 | API security, Context, Gemini Service | CSRF/session, secret/privacy, safe rendering. |
| CB-NFR-03 | Snapshot Retriever, Handler, Booking Core | Dữ liệu/card/link nhất quán tại thời điểm truy vấn. |
| CB-NFR-04 | Timeout/error boundary, deterministic fallbacks | Phân biệt empty/error và khả dụng có kiểm soát. |
| CB-NFR-05 | Typed contracts, trace IDs/log policy, all components | Có thể kiểm thử và truy vết từng kết quả. |

## 8. Phụ thuộc và điểm cần xác nhận trước triển khai

- Mốc giờ cụ thể của `MORNING/AFTERNOON/EVENING` phải được lưu trong policy được duyệt; không suy ra trong code từ tên khung giờ.
- Quy tắc `BOOKED/USED` và hold còn hạn phải được đồng bộ với booking core; preview hiện có đang thể hiện thêm trạng thái khác.
- Giá 80k/110k/160k và cutoff 60 phút là policy được người dùng xác nhận cho thiết kế này; nguồn cấu hình chính thức cần được xác định khi triển khai.
- Giới hạn question length, số card tối đa, rate limit, retry/quota và audit retention vẫn là operational decisions chưa được chốt trong requirements.
