# Yêu cầu chức năng – Chatbot RAG (AI Cinema Assistant)

**Nguồn:** `docs/chatbot-requirements.md` đã được Human Gate duyệt  
**Bước:** Phần XXIII – Bước 2, Requirements Analysis  
**Trạng thái:** Đã phân tích; không bao gồm source code

## 1. Phạm vi và quy ước ID

Tài liệu này đặc tả Chatbot RAG dành cho khách hàng trên web. Chatbot là tác nhân đọc dữ liệu và tư vấn/dẫn đường; không phải tác nhân thực hiện giao dịch. Các yêu cầu dùng tiền tố `CB-FR` để phân biệt với FR-01–FR-13 của hệ thống Cinema System hiện có.

### 1.1. Tác nhân

| Tác nhân | Vai trò |
|---|---|
| Khách hàng | Nhập câu hỏi tiếng Việt, xem câu trả lời/Screening Cards và bấm liên kết đặt vé. |
| Chatbot RAG | Chuẩn hóa câu hỏi, truy xuất dữ liệu được phép, tạo câu trả lời có căn cứ và từ chối khi không đủ căn cứ. |
| Backend/Service | Xác thực tham số, truy vấn dữ liệu, tính ghế trống và tạo dữ liệu đầu ra an toàn. |
| Gemini AI | Chỉ diễn đạt hoặc phân loại trong ngữ cảnh đã được backend cung cấp; không phải nguồn sự thật nghiệp vụ. |
| Hệ thống lõi đặt vé | Xử lý lại quyền, trạng thái ghế, giữ chỗ, giá, thanh toán và giao dịch khi khách hàng bấm đặt vé. |

## 2. Yêu cầu chức năng

### CB-FR-01 – Tiếp nhận và hiểu câu hỏi tiếng Việt

Chatbot phải nhận câu hỏi tự nhiên về phim, thể loại, nội dung, ngày, khung giờ, phòng, loại ghế, giá vé và quy định được công bố. Chatbot phải nhận diện các tham số có thể suy ra chắc chắn và hỏi lại khi tham số mơ hồ.

**Không bao gồm:** suy đoán ý định ngoài phạm vi rạp hoặc coi kiến thức chung của mô hình là dữ liệu rạp.

### CB-FR-02 – Chuẩn hóa điều kiện tìm kiếm

Chatbot phải chuyển câu hỏi thành các điều kiện có thể kiểm tra: phim/từ khóa, thể loại, ngày, khoảng giờ, loại ghế và số lượng ghế nếu người dùng nêu. “Hôm nay”, “ngày mai”, “tối nay” phải được tính theo múi giờ vận hành đã cấu hình; “buổi sáng” phải dùng định nghĩa đã được duyệt hoặc hỏi lại.

### CB-FR-03 – Tra cứu phim có căn cứ

Chatbot chỉ trả phim có bản ghi hợp lệ trong `movies`, có thể kết hợp `genres`/`movie_genres` và trường mô tả/keywords được phép công khai. Phim không tồn tại, không ở trạng thái được phép hiển thị hoặc không phù hợp điều kiện phải bị loại khỏi kết quả.

### CB-FR-04 – Tra cứu suất chiếu

Chatbot phải dùng `screenings` để lọc theo phim, ngày và khoảng giờ; kết hợp `screening_rooms` để lấy tên phòng. Mỗi kết quả phải giữ đúng `screening_id`, thời điểm bắt đầu/kết thúc và phòng tương ứng.

### CB-FR-05 – Tính và hiển thị ghế trống

Đối với từng suất, backend phải đối chiếu `seats` thuộc đúng phòng với `tickets` và `seat_holds`. Vé đang chiếm chỗ theo trạng thái nghiệp vụ và hold chưa hết hạn được loại khỏi ghế trống; vé `CANCELLED` và hold hết hạn không được coi là đang chiếm chỗ. Kết quả phải nhóm ít nhất theo `STANDARD`, `VIP`, `COUPLE`.

Chatbot phải gắn thời điểm kiểm tra và cảnh báo rằng trạng thái có thể thay đổi. Chatbot không được tạo hold hoặc cam kết ghế sẽ được giữ.

### CB-FR-06 – Tra cứu giá vé và quy định

Chatbot được trả giá và quy định hủy/hoàn tiền chỉ khi backend cung cấp nguồn cấu hình/quy tắc chính thức. Nếu nguồn không có hoặc chính sách chưa đủ chi tiết, chatbot phải nói chưa có thông tin xác nhận và không tự bổ sung điều kiện, mức phí hay thời hạn.

### CB-FR-07 – Trả lời không có kết quả

Khi truy vấn hợp lệ nhưng không có bản ghi phù hợp, chatbot phải nói rõ không tìm thấy kết quả, có thể đề xuất nới ngày/giờ/thể loại nếu lựa chọn đó được truy vấn từ dữ liệu thật. Không được tạo kết quả thay thế giả.

### CB-FR-08 – Từ chối câu hỏi ngoài phạm vi

Chatbot phải từ chối hoặc chuyển hướng câu hỏi yêu cầu thực hiện thanh toán, giữ/chọn ghế, hủy vé, hoàn tiền, phát hành QR, sửa dữ liệu, truy cập thông tin cá nhân, khóa API, SQL hoặc hệ thống nội bộ. Phản hồi phải nêu giới hạn ngắn gọn và hướng tới kênh/luồng chính thức khi phù hợp.

### CB-FR-09 – Xuất Screening Cards

Khi có suất chiếu, đầu ra phải gồm câu trả lời tiếng Việt và các Screening Cards. Mỗi card bắt buộc có tên phim, ngày/giờ, phòng, số ghế trống Standard/VIP/Couple, thời điểm cập nhật và trạng thái bán.

### CB-FR-10 – Dẫn tới luồng đặt vé

Nút “Đặt vé ngay” trên card chỉ dẫn tới route đã chốt:

```text
/booking/<screening_id>
```

`screening_id` phải lấy từ bản ghi `screenings`, không do Gemini hoặc client tự tạo. Bấm nút không tạo hold, thanh toán hay vé; hệ thống lõi phải kiểm tra lại mọi điều kiện.

### CB-FR-11 – Xử lý lỗi nguồn dữ liệu/AI

Nếu backend, cơ sở dữ liệu hoặc Gemini không khả dụng, chatbot phải trả thông báo lỗi có kiểm soát, không biến lỗi thành “không có suất” và không bịa nội dung để lấp chỗ trống. Phải giữ an toàn cho khóa, thông tin truy vấn và chi tiết nội bộ.

### CB-FR-12 – Bảo vệ dữ liệu và prompt

Chatbot chỉ truyền cho model ngữ cảnh công khai tối thiểu cần thiết. Backend phải dùng truy vấn tham số hóa, không cho model sinh/thực thi SQL, không gửi thông tin cá nhân/thanh toán/khóa bí mật và không render HTML/JavaScript không tin cậy.

### CB-FR-13 – Bảo vệ khóa Gemini

`GEMINI_API_KEY` chỉ được đọc phía server từ biến môi trường (môi trường phát triển dùng `.env`), không được hard-code, trả về client, ghi log hoặc commit vào repository.

## 3. Yêu cầu phi chức năng

### CB-NFR-01 – An toàn và chống ảo giác

Mọi dữ kiện nghiệp vụ trong câu trả lời phải truy xuất được từ backend/context hợp lệ. Khi không có căn cứ, dữ liệu lỗi hoặc model sinh giá trị ngoài context, hệ thống phải loại giá trị hoặc từ chối trả lời; không được bịa.

### CB-NFR-02 – Bảo mật và riêng tư

Backend phải bảo vệ `GEMINI_API_KEY`, dùng truy vấn tham số hóa, không gửi dữ liệu cá nhân/thanh toán không cần thiết tới model và không để nội dung model thực thi HTML/JavaScript không tin cậy.

### CB-NFR-03 – Nhất quán dữ liệu

Thông tin phim, suất, phòng, ghế, `screening_id` và link đặt vé phải nhất quán với dữ liệu backend tại thời điểm truy vấn. Luồng đặt vé phải kiểm tra lại tình trạng và quyền trước khi thực hiện giao dịch.

### CB-NFR-04 – Khả dụng có kiểm soát

Khi backend, database hoặc Gemini lỗi/timeout, hệ thống phải trả lỗi an toàn, phân biệt lỗi nguồn với kết quả rỗng và không làm lộ chi tiết nội bộ. Chưa cam kết chỉ tiêu latency/quota khi chưa được duyệt.

### CB-NFR-05 – Khả kiểm thử và truy vết

Các kết quả tra cứu phải có thể đối chiếu với dữ liệu đầu vào và mỗi user story phải truy vết được tới FR/NFR và acceptance criteria tương ứng.

## 4. Những gì Chatbot được làm và không được làm

### Được làm

- Đọc dữ liệu công khai qua backend để tìm phim, suất, phòng, ghế trống, giá và chính sách đã xác nhận.
- Hỏi lại điều kiện chưa rõ.
- Trả lời tiếng Việt và hiển thị dữ liệu truy xuất được trong Screening Cards.
- Dẫn khách hàng tới `/booking/<screening_id>`.
- Từ chối câu hỏi không có căn cứ hoặc vượt phạm vi.

### Không được làm

- Bịa phim, suất, phòng, ghế, giá, diễn viên, khuyến mại hoặc chính sách.
- Tự giữ/chọn ghế, đặt/hủy vé, thanh toán, hoàn tiền, phát hành QR hoặc sửa dữ liệu.
- Khẳng định ghế trống là cam kết giữ chỗ.
- Truy cập trực tiếp DB từ client, thực thi SQL do model sinh hoặc vượt phân quyền.
- Tiết lộ dữ liệu người dùng, dữ liệu thanh toán, prompt nội bộ, API key hoặc lỗi hệ thống chi tiết.

## 5. Truy xuất dữ liệu và quy tắc nguồn sự thật

| Dữ liệu | Mục đích | Quy tắc |
|---|---|---|
| `movies` | Tên, synopsis, keywords, trạng thái | Chỉ dùng bản ghi/phần nội dung được phép hiển thị. |
| `genres`, `movie_genres` | Lọc thể loại | Không gán thể loại không có liên kết dữ liệu. |
| `screenings` | Ngày, giờ, `screening_id`, phim, phòng | Là nguồn duy nhất cho lịch chiếu. |
| `screening_rooms` | Tên phòng, trạng thái phòng | Phải khớp `room_id` của suất. |
| `seats` | Sơ đồ, loại ghế | Chỉ tính ghế thuộc đúng phòng. |
| `tickets` | Ghế đã bán/đang chiếm | Áp dụng trạng thái nghiệp vụ; không coi vé hủy là đang bán. |
| `seat_holds` | Ghế tạm giữ | Chỉ loại hold còn hạn; không biến truy vấn thành thao tác hold. |
| Nguồn giá/chính sách chính thức | Giá, hủy/hoàn tiền | Thiếu nguồn thì từ chối trả lời chắc chắn. |

## 6. Truy vết với hệ thống hiện có

| Chatbot requirement | FR/NFR nền | Use case liên quan |
|---|---|---|
| CB-FR-03, CB-FR-04 | FR-10 | UC05, UC10 |
| CB-FR-05 | FR-05, FR-06, NFR-02 | UC05, UC06 |
| CB-FR-06 | FR-04, FR-07, NFR-04 | UC04, UC07 |
| CB-FR-09, CB-FR-10 | FR-05, FR-06, NFR-04 | UC05, UC06 |
| CB-FR-08, CB-FR-11, CB-FR-12, CB-FR-13 | NFR-03, NFR-04 | UC12, UC13 |

Các NFR riêng của Chatbot được truy vết như sau:

| Chatbot NFR | Phạm vi |
|---|---|
| CB-NFR-01 | CB-FR-03 đến CB-FR-08, CB-AC-08 đến CB-AC-16 |
| CB-NFR-02 | CB-FR-12, CB-FR-13, CB-AC-17 đến CB-AC-21 |
| CB-NFR-03 | CB-FR-04, CB-FR-05, CB-FR-10, CB-AC-05 đến CB-AC-07, CB-AC-11, CB-AC-12 |
| CB-NFR-04 | CB-FR-11, CB-AC-13 |
| CB-NFR-05 | Toàn bộ CB-US/CB-AC và bảng truy vết |

## 7. Giả định và giới hạn chưa phải yêu cầu

- Múi giờ vận hành và khoảng giờ chính xác của “buổi sáng” cần được xác nhận ở bước thiết kế/triển khai; không tự đặt giá trị trong tài liệu này.
- Nguồn cấu hình giá và chính sách hoàn tiền chưa được chỉ rõ trong tài liệu đầu vào; đây là phụ thuộc cần giải quyết, không được thay bằng kiến thức của model.
- Chỉ tiêu latency, quota và số card tối đa chưa được chốt; không coi đây là cam kết nghiệm thu.