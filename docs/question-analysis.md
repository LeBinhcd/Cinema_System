# Thiết kế Question Analyzer – AI Cinema Assistant

**Skill sử dụng:** `.agents/skills/question-analysis/SKILL.md`  
**Module:** `app/services/question_analyzer.py`  
**Phạm vi:** Phân tích câu hỏi tiếng Việt thành Structured Intent JSON; không gọi Gemini và không truy cập cơ sở dữ liệu.

## 1. Mục tiêu

Question Analyzer là module rule-based ở trước lớp Retriever. Module chỉ hiểu các tín hiệu có trong câu hỏi, chuẩn hóa chúng thành hợp đồng dữ liệu ổn định và để lại `null` khi người dùng không cung cấp thông tin. Module không tự tạo tên phim, thể loại, ngày hoặc giờ.

```text
Vietnamese question
        │
        ▼
QuestionAnalyzer.analyze(question, now?)
        │
        ▼
Structured intent JSON
```

## 2. Input/Output contract

### Input

- Một chuỗi câu hỏi tự nhiên bằng tiếng Việt.
- Tham số `now` tùy chọn dành cho kiểm thử; khi không truyền, module lấy thời gian hiện tại theo `Asia/Ho_Chi_Minh`.
- Module không nhận prompt, SQL, context, model output hoặc dữ liệu người dùng khác.

### Output

JSON-serializable object luôn có đủ các trường:

```json
{
  "intent": "recommend_movie",
  "movie_title": null,
  "genre": "Hoạt hình",
  "date": "2026-09-30",
  "min_time": "19:00",
  "max_time": null,
  "time_of_day": null,
  "seat_type": null,
  "price_inquiry": false,
  "policy_inquiry": false,
  "keywords": []
}
```

`intent` có thể là `recommend_movie`, `search_screenings`, `check_seats`, `ask_price`, `ask_policy`, `AMBIGUOUS` hoặc `UNKNOWN`. Giá trị `UNKNOWN` dùng cho câu hỏi rỗng/ngoài phạm vi đã nhận diện; `AMBIGUOUS` dùng khi chưa đủ tín hiệu để truy xuất an toàn. Các intent nghiệp vụ dùng chữ thường theo ví dụ yêu cầu; hai trạng thái dự phòng giữ chữ hoa theo skill.

## 3. Quy tắc phân tích

### 3.1. Thể loại và tên phim

- Chỉ chuẩn hóa thể loại khi cụm từ đó xuất hiện trong câu hỏi, ví dụ `hoạt hình` → `Hoạt hình`, `hành động` → `Hành động`.
- Không suy ra thể loại từ tên phim hoặc kiến thức bên ngoài.
- Tên phim chỉ được trích xuất từ ngữ cảnh có từ `phim`/`suất chiếu`; không tự tạo tên phim khi người dùng hỏi chung “phim nào”.
- `keywords` chứa các từ khóa tìm kiếm còn lại được nêu trong câu hỏi, không phải dữ liệu được sinh thêm.

### 3.2. Ngày và múi giờ

- `hôm nay` và `tối nay` → ngày hiện tại theo `Asia/Ho_Chi_Minh`, định dạng `YYYY-MM-DD`.
- `ngày mai` → ngày kế tiếp theo `Asia/Ho_Chi_Minh`, định dạng `YYYY-MM-DD`.
- Không có biểu thức ngày → `date = null`.
- Module không tự dùng ngày hệ thống UTC hoặc ngày mặc định của database.

### 3.3. Thời gian

- `sau 19h` → `min_time = "19:00"`.
- Giờ viết dạng `19:30`, `19h30`, `19 giờ 30` được chuẩn hóa về `HH:MM`.
- `buổi sáng` → `time_of_day = "MORNING"`, khoảng `08:00–11:59`.
- `buổi chiều` → `time_of_day = "AFTERNOON"`, khoảng `12:00–17:59`.
- `tối nay`/`buổi tối` → `time_of_day = "EVENING"`, bắt đầu từ `18:00`.
- Không có giờ hoặc khung giờ → các trường thời gian tương ứng là `null`.

Các mốc Sáng/Chiều/Tối được đóng gói tại analyzer theo policy của skill; Retriever vẫn phải kiểm tra lại configuration/policy trước khi tạo SQL nghiệp vụ.

### 3.4. Loại ghế, giá và chính sách

- `ghế VIP` → `VIP`.
- `ghế đôi`/`ghế couple` → `COUPLE`.
- `ghế thường`/`ghế standard` → `STANDARD`.
- Câu hỏi chứa giá vé → `price_inquiry = true`, `intent = ask_price`.
- Câu hỏi chứa hủy vé, hoàn tiền hoặc chính sách → `policy_inquiry = true`, `intent = ask_policy`.
- Analyzer chỉ bật cờ; giá và chính sách phải được Retriever/Policy Provider lấy từ nguồn chính thức.

## 4. Ví dụ bắt buộc

Với `now = 2026-09-30T10:00:00+07:00`:

### Input

```text
Tối nay có phim hoạt hình nào sau 19h không?
```

### Output

```json
{
  "intent": "recommend_movie",
  "movie_title": null,
  "genre": "Hoạt hình",
  "date": "2026-09-30",
  "min_time": "19:00",
  "max_time": null,
  "time_of_day": "EVENING",
  "seat_type": null,
  "price_inquiry": false,
  "policy_inquiry": false,
  "keywords": []
}
```

Lưu ý: ví dụ đầu vào không nêu tên phim, vì vậy `movie_title` phải là `null`. `time_of_day = "EVENING"` là thông tin bắt buộc theo rule `tối nay`; `min_time = "19:00"` được ưu tiên vì người dùng nêu điều kiện cụ thể hơn.

### Các ví dụ khác

| Câu hỏi | Kết quả chính |
|---|---|
| `Ngày mai có phim gì buổi sáng?` | `date = ngày mai`, `time_of_day = MORNING`, `08:00–11:59`, `intent = recommend_movie` |
| `Phim Conan tối nay còn ghế VIP không?` | `movie_title = Conan`, `date = hôm nay`, `seat_type = VIP`, `intent = check_seats` |
| `Giá vé ghế VIP bao nhiêu?` | `price_inquiry = true`, `intent = ask_price` |
| `Hủy vé trước bao lâu được hoàn tiền?` | `policy_inquiry = true`, `intent = ask_policy` |
| `Thời tiết hôm nay thế nào?` | `intent = UNKNOWN` |
| `Cho tôi biết thêm đi.` | `intent = AMBIGUOUS` |

## 5. Ranh giới module

- Không gọi Gemini hoặc bất kỳ model/API bên ngoài nào.
- Không truy vấn SQLite, không sinh SQL và không tạo `screening_id`.
- Không quyết định phim nào thực sự tồn tại.
- Không trả giá, chính sách, ghế trống hoặc lịch chiếu thực tế.
- Không thực hiện hold, đặt vé, hủy vé, hoàn tiền hay thanh toán.
- Retriever/Policy Guard ở bước sau phải validate lại intent trước khi truy vấn.

## 6. Kiểm thử và tích hợp

Module có thể được kiểm thử thuần unit bằng cách truyền `now` cố định, không cần database hay Gemini. Bộ kiểm thử tối thiểu cần bao phủ:

1. Ví dụ hoạt hình/tối nay/sau 19h.
2. Hôm nay và ngày mai theo `Asia/Ho_Chi_Minh`.
3. Ba khung giờ và ba loại ghế.
4. Giá vé và chính sách hủy/hoàn tiền.
5. Câu hỏi rỗng, mơ hồ và ngoài phạm vi.
6. Bảo đảm không sinh `movie_title`/`genre` khi câu hỏi không chứa chúng.

Chạy kiểm thử: `python -m pytest tests/test_question_analyzer.py -q` từ thư mục dự án.

## 7. Giới hạn và cách sử dụng

```python
from datetime import datetime
from app.services.question_analyzer import analyze_question

intent = analyze_question(
    "Tối nay có phim hoạt hình nào sau 19h không?",
    now=datetime.fromisoformat("2026-09-30T10:00:00+07:00"),
)
```

- Khi không truyền `now`, ngày được tính động; `2026-09-30` không bị hard-code.
- `now` không có timezone được hiểu là giờ rạp. Trên Windows không có IANA timezone database, module dùng UTC+7 tương đương giờ Việt Nam hiện đại; không hỗ trợ chuyển đổi lịch sử timezone bằng fallback này.
- Đây là parser rule-based với danh sách thể loại/alias hữu hạn, không phải bộ hiểu tiếng Việt tổng quát. Ngày tuyệt đối, nhiều ngày, nhiều loại ghế/thể loại, nhiều điều kiện giờ và tên phim phức tạp chưa được hỗ trợ đầy đủ; caller cần hỏi lại/validate khi gặp những cấu trúc này. Với nhiều loại ghế/thể loại, hiện chọn giá trị đầu tiên theo danh sách rule, không coi đây là phân tích toàn bộ câu hỏi.
- Hiện chỉ lấy giờ tường minh đầu tiên; giờ không có từ `sau`/`trước` được đưa vào `min_time`, không phải cam kết tìm suất đúng giờ. `sau`/`trước` phải được Retriever diễn giải đúng ngữ nghĩa so sánh.
- Khoảng Sáng/Chiều được giao với điều kiện giờ; khoảng rỗng trả `AMBIGUOUS`. Tên phim lấy bằng regex nên luôn cần đối chiếu catalog ở Retriever.
- Parser không phải security guard: không dùng output để thực thi giao dịch hoặc SQL trực tiếp. Các tài liệu kiến trúc cũ dùng contract khái quát khác; tài liệu này mô tả contract analyzer hiện tại, chưa tích hợp API/Retriever.
