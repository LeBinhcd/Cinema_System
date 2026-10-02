# Đặc tả yêu cầu người dùng – AI Cinema Assistant

**Phân hệ:** Trợ lý Điện ảnh của Cinema System  
**Giai đoạn:** AI-Augmented SDLC – Phần XXIII, Bước 1: Xác định yêu cầu bài toán Chatbot AI  
**Trạng thái:** Human Gate APPROVED

## 1. Bối cảnh & Mục tiêu (Objective)

Hệ thống rạp chiếu phim cần một Chatbot AI thông minh đặt trên giao diện web để hỗ trợ khách hàng tìm kiếm phim, tra cứu suất chiếu và kiểm tra tình trạng ghế trống theo thời gian thực bằng ngôn ngữ tự nhiên tiếng Việt.

Trợ lý Điện ảnh giúp khách hàng:

- Tìm phim theo thể loại, nội dung hoặc tên phim.
- Lọc suất chiếu theo ngày và khung giờ.
- Kiểm tra ghế trống theo loại Standard (thường), VIP và Couple (ghế đôi).
- Tra cứu giá vé và quy định hủy/hoàn tiền đã được rạp xác nhận.
- Chuyển đến trang đặt vé của suất chiếu phù hợp.

Chatbot phục vụ khách hàng trên web, bao gồm người đang tìm hiểu thông tin trước khi đăng nhập. Việc đặt vé vẫn tuân theo yêu cầu đăng nhập và các quy tắc của hệ thống hiện có. Chatbot chỉ tư vấn/dẫn đường, không thay thế quy trình giữ ghế, thanh toán hay phát hành vé.

## 2. Các kịch bản hỏi đáp thực tế (Sample Inquiries)

| Nhóm nhu cầu | Câu hỏi mẫu | Hành vi kỳ vọng |
|---|---|---|
| Thể loại / nội dung | “Tối nay có phim hành động hoặc hoạt hình nào hay không?” | Tìm phim theo thể loại hoặc mô tả có trong dữ liệu rạp và lọc suất chiếu phù hợp; không tự nhận định phim “hay” là sự thật nếu thiếu căn cứ. |
| Khung giờ & ngày | “Hôm nay có suất chiếu nào sau 19h không?” | Tìm các suất hôm nay có giờ bắt đầu sau 19:00 theo giờ vận hành của rạp. |
| Khung giờ & ngày | “Ngày mai có phim gì chiếu buổi sáng?” | Xác định ngày mai theo giờ rạp; dùng khung giờ buổi sáng đã được thống nhất hoặc hỏi lại nếu chưa rõ. |
| Loại ghế & tình trạng phòng | “Suất chiếu tối nay của phim Conan còn ghế VIP hoặc ghế đôi (Couple) không?” | Tìm phim/suất thực tế, đối chiếu phòng và trả số ghế VIP/Couple còn trống tại thời điểm truy vấn. |
| Giá vé | “Giá vé ghế thường và ghế VIP là bao nhiêu?” | Trả giá theo nguồn cấu hình chính thức; không tự tạo giá hoặc khuyến mại. |
| Quy định rạp | “Chính sách hủy vé trước bao lâu thì được hoàn tiền?” | Trả điều kiện hủy/hoàn tiền được xác nhận; không hứa hoàn tiền nếu chưa kiểm tra các điều kiện nghiệp vụ. |

Nếu tên phim, ngày hoặc khung giờ có nhiều cách hiểu, chatbot cần hỏi lại ngắn gọn thay vì tự áp dụng một điều kiện không rõ ràng.

## 3. Nguyên tắc chống ảo giác & Căn cứ dữ liệu (Grounding & Anti-Hallucination Policy)

### 3.1. Nguồn dữ liệu thực tế

Chatbot **PHẢI** sử dụng thông tin phim, suất chiếu, phòng chiếu và ghế trống thực tế đang có trong cơ sở dữ liệu rạp:

- `movies`: thông tin và mô tả phim được phép công khai.
- `screenings`: suất chiếu, ngày/giờ và liên kết phim/phòng.
- `screening_rooms`: tên và trạng thái phòng chiếu.
- `seats`: ghế thuộc phòng và loại ghế Standard/VIP/Couple.
- `tickets`: trạng thái vé chiếm ghế theo suất chiếu.
- `seat_holds`: ghế đang được giữ tạm thời và thời điểm hết hạn.
- `genres`, `movie_genres`: thể loại phim khi cần lọc theo thể loại.

Backend phải tính ghế trống theo đúng phòng của suất chiếu, loại trừ ghế có vé chiếm chỗ hợp lệ hoặc hold chưa hết hạn theo quy tắc lõi. Hold hết hạn và vé đã hủy không được tính là ghế đang bị chiếm. Không được suy ra số ghế trống chỉ từ tổng số ghế của phòng.

Giá vé và chính sách rạp phải lấy từ nguồn cấu hình/quy tắc nghiệp vụ chính thức của backend, không lấy từ kiến thức suy đoán của mô hình.

### 3.2. Không tìm thấy hoặc thiếu dữ liệu

Nếu không tìm thấy phim hoặc suất chiếu phù hợp, chatbot **PHẢI** thông báo lịch sự rằng không tìm thấy suất chiếu phù hợp, thay vì tự bịa ra phim, diễn viên hoặc giờ chiếu giả mạo. Không được tự tạo tên phòng, số ghế, giá vé hay chính sách hoàn tiền.

Ví dụ phản hồi:

> “Hiện chưa tìm thấy suất chiếu phù hợp với yêu cầu của bạn. Bạn có muốn chọn ngày hoặc khung giờ khác không?”

Khi nguồn dữ liệu không khả dụng, chatbot phải nói rõ chưa thể kiểm tra; không được coi lỗi truy vấn là kết quả “không có suất chiếu”. Nếu thiếu thông tin diễn viên hoặc chính sách, phải thông báo chưa có thông tin xác nhận.

### 3.3. Ngôn ngữ và tính cập nhật

- Luôn phản hồi bằng tiếng Việt thân thiện, súc tích, đúng văn phong rạp chiếu phim.
- Câu trả lời và Screening Cards phải thống nhất với kết quả backend; ID, giờ chiếu và số ghế không do mô hình tự tạo.
- Tình trạng ghế phải được truy vấn cho yêu cầu hiện tại, có thời điểm cập nhật và lời nhắc rằng ghế có thể thay đổi trước khi đặt.
- Số ghế trống là thông tin tra cứu, không phải cam kết giữ chỗ. Luồng đặt vé phải kiểm tra lại tình trạng ghế.
- Chỉ đề xuất lựa chọn thay thế có dữ liệu thực tế và nói rõ lựa chọn đó khác điều kiện ban đầu.

## 4. Yêu cầu bảo mật & Phi chức năng (Non-Functional & Security Constraints)

### 4.1. Bảo mật khóa Gemini

- Khóa API Google Gemini (`GEMINI_API_KEY`) phải đọc từ biến môi trường; môi trường phát triển sử dụng `.env` phía server để cung cấp biến này.
- Tuyệt đối không hard-code khóa trong mã nguồn, commit `.env` chứa bí mật hoặc ghi khóa vào log/response.
- Không để lộ khóa trong template, Client JavaScript, HTML hoặc dữ liệu lưu phía trình duyệt.
- Chỉ backend được gọi Gemini. Khi thiếu khóa hoặc dịch vụ không khả dụng, trả thông báo có kiểm soát, không tiết lộ cấu hình nội bộ.

### 4.2. Truy cập dữ liệu và riêng tư

- Chatbot không được trực tiếp truy cập cơ sở dữ liệu từ giao diện người dùng. Toàn bộ luồng truy vấn phải đi qua API backend, tuân theo Routes → Services → Models.
- SQL phải dùng câu lệnh tham số hóa (Parameterized Query); không nối nội dung người dùng vào SQL hoặc thực thi SQL tùy ý do mô hình sinh.
- Chatbot chỉ được đọc dữ liệu công khai cần thiết cho tra cứu. Không gửi thông tin cá nhân, mật khẩu, khóa bí mật hoặc chi tiết thanh toán của khách hàng tới Gemini hay trả cho người hỏi.
- Chỉ dẫn trong câu hỏi hoặc nội dung phim không được phép vượt qua phân quyền, thay đổi chính sách bảo mật hoặc yêu cầu tiết lộ bí mật.
- Nội dung trả về phải được hiển thị an toàn, không thực thi HTML/JavaScript tùy ý từ người dùng hoặc mô hình.

### 4.3. Ranh giới nghiệp vụ

- Chatbot đóng vai trò tư vấn/dẫn đường, không tự ý trừ tiền hay can thiệp vào luồng thanh toán cốt lõi.
- Không tự tạo hold, mua/hủy vé, hoàn tiền, phát hành QR hoặc sửa dữ liệu phim/phòng/suất/ghế.
- Nút đặt vé chỉ dẫn đến luồng đặt vé hiện có. Các kiểm tra đăng nhập, cutoff, giữ ghế, giá, thanh toán và transaction vẫn do backend lõi thực hiện.
- Suất hết ghế hoặc đã đóng bán phải được ghi rõ và không được mời đặt vé như suất đang mở bán.

### 4.4. Khả dụng và trải nghiệm

- Giao diện có trạng thái đang xử lý, thông báo lỗi dễ hiểu và cho phép thử lại khi phù hợp.
- Khi Gemini hoặc backend gặp lỗi, không bịa dữ liệu để hoàn thành câu trả lời.
- Các giới hạn thời gian chờ, độ dài câu hỏi và tần suất gọi phải được xác định ở bước phân tích; chưa cam kết một chỉ tiêu hiệu năng chưa được đo.

## 5. Định dạng dữ liệu đầu ra kỳ vọng (Expected Output)

Đầu ra gồm **câu trả lời văn bản tiếng Việt** kèm **danh sách Thẻ Suất Chiếu (Screening Cards)** khi có kết quả tra cứu suất chiếu. Với câu hỏi chính sách/giá hoặc không có kết quả, có thể chỉ trả văn bản và danh sách thẻ rỗng.

Mỗi Screening Card phải có:

| Thông tin | Yêu cầu |
|---|---|
| Tên phim | Đúng tên phim trong dữ liệu rạp. |
| Giờ chiếu | Có ngày và giờ bắt đầu để tránh nhầm “hôm nay/ngày mai”. |
| Phòng | Đúng tên phòng của suất chiếu. |
| Ghế trống | Số lượng theo từng loại Standard/thường, VIP và Couple/ghế đôi; hiển thị 0 khi không còn ghế. |
| Thời điểm cập nhật | Thời điểm backend kiểm tra tình trạng ghế. |
| Nút hành động | Nhãn **“Đặt vé ngay”**, chỉ khả dụng khi suất còn mở bán và còn ghế phù hợp. |
| Đích đặt vé | `/booking/<screening_id>`, với `screening_id` thực tế do backend cung cấp, không do mô hình tự tạo. |

**Ánh xạ đã được Human Gate xác nhận:** Nút đặt vé dùng route Flask `/booking/<screening_id>` và truyền `screening_id` thực tế của suất chiếu. Route này render template `booking.html`; không bổ sung route query-string.

Không đưa lịch chiếu hoặc số ghế minh họa vào câu trả lời như dữ liệu thực. Nhấn “Đặt vé ngay” không tự tạo giao dịch hoặc giữ ghế.

## 6. Tiêu chí duyệt Human Gate

- [ ] Đồng ý mục tiêu và phạm vi tư vấn/tra cứu/dẫn đường; không tự động thao tác thanh toán hoặc vé.
- [ ] Các câu hỏi mẫu được đáp ứng bằng dữ liệu backend thực tế; thiếu dữ liệu thì thông báo rõ, không suy đoán.
- [ ] Đồng ý cách tính ghế trống và cảnh báo về thay đổi trạng thái trước khi đặt.
- [ ] Xác nhận nguồn giá vé, chính sách hủy/hoàn tiền và cách hiểu “buổi sáng”, “tối nay”, múi giờ rạp ở bước phân tích.
- [ ] Đồng ý bảo mật `GEMINI_API_KEY`, truy vấn SQL tham số hóa và giới hạn dữ liệu gửi tới Gemini.
- [ ] Duyệt nội dung Screening Cards và quyết định ánh xạ đường dẫn đặt vé.

**Điểm dừng Bước 1:** Human Gate đã duyệt tài liệu này; có thể chuyển sang Requirements Analysis. Chưa thiết kế prompt, API chi tiết hoặc triển khai Chatbot/Gemini.