# User Stories – Chatbot RAG (AI Cinema Assistant)

**Nguồn:** `docs/chatbot-functional-requirements.md`  
**Trạng thái:** Dự thảo Bước 2; chờ Human Gate Requirements Review

## 1. User Stories và truy vết

### CB-US-01 – Hiểu câu hỏi tiếng Việt

**Là một Khách hàng, tôi muốn hỏi bằng tiếng Việt tự nhiên về phim và suất chiếu, để không phải nhớ cú pháp tìm kiếm.**

**Truy vết:** CB-FR-01, CB-FR-02

### CB-US-02 – Tìm phim theo điều kiện

**Là một Khách hàng, tôi muốn tìm phim theo tên, thể loại, nội dung, ngày và khung giờ, để nhanh chóng tìm lựa chọn phù hợp.**

**Truy vết:** CB-FR-03, CB-FR-04

### CB-US-03 – Kiểm tra ghế theo loại

**Là một Khách hàng, tôi muốn xem số ghế Standard, VIP và Couple còn trống của từng suất, để chọn suất phù hợp trước khi đặt vé.**

**Truy vết:** CB-FR-05, CB-NFR-03; FR-05, FR-06, NFR-02

### CB-US-04 – Tra cứu giá và quy định có căn cứ

**Là một Khách hàng, tôi muốn biết giá vé và quy định hủy/hoàn tiền chính thức, để đưa ra quyết định không dựa trên thông tin sai.**

**Truy vết:** CB-FR-06, CB-NFR-01; FR-04, FR-07, NFR-04

### CB-US-05 – Nhận thông báo không có kết quả

**Là một Khách hàng, tôi muốn được thông báo rõ khi không có suất phù hợp, để có thể điều chỉnh ngày hoặc khung giờ.**

**Truy vết:** CB-FR-07

### CB-US-06 – Được hỏi lại khi yêu cầu mơ hồ

**Là một Khách hàng, tôi muốn chatbot hỏi lại phần chưa rõ, để kết quả không bị dựa trên giả định sai.**

**Truy vết:** CB-FR-01, CB-FR-02

### CB-US-07 – Dẫn tới đặt vé

**Là một Khách hàng, tôi muốn bấm “Đặt vé ngay” trên suất đã xem, để tiếp tục trong luồng đặt vé chính thức.**

**Truy vết:** CB-FR-09, CB-FR-10; FR-05, FR-06

### CB-US-08 – Biết giới hạn của chatbot

**Là một Khách hàng, tôi muốn chatbot nói rõ khi không thể thanh toán, giữ ghế, hủy vé hoặc hoàn tiền, để tôi không nhầm tư vấn với giao dịch thật.**

**Truy vết:** CB-FR-08, CB-FR-10

### CB-US-09 – Nhận câu trả lời an toàn khi hệ thống lỗi

**Là một Khách hàng, tôi muốn nhận thông báo rõ ràng khi dữ liệu hoặc AI tạm thời không khả dụng, để không bị cung cấp thông tin bịa đặt.**

**Truy vết:** CB-FR-11, CB-NFR-04; NFR-02, NFR-04

### CB-US-10 – Bảo vệ dữ liệu và bí mật hệ thống

**Là một Chủ hệ thống, tôi muốn Chatbot chỉ dùng dữ liệu cần thiết và giữ `GEMINI_API_KEY` ở server, để bảo vệ khách hàng và hệ thống.**

**Truy vết:** CB-FR-12, CB-FR-13, CB-NFR-02; NFR-03, NFR-04

## 2. Ranh giới hành vi

| Chatbot có thể | Chatbot không thể |
|---|---|
| Tra cứu và diễn đạt lại dữ liệu phim/suất/ghế được backend cung cấp. | Tạo dữ liệu khi backend không có bản ghi. |
| Hỏi lại ngày, giờ, phim hoặc loại ghế chưa rõ. | Tự chọn một diễn giải có thể làm thay đổi kết quả mà không báo người dùng. |
| Đưa link `/booking/<screening_id>`. | Tự tạo `screening_id`, hold, vé hoặc giao dịch. |
| Trả lời giá/chính sách nếu có nguồn chính thức. | Đoán giá, khuyến mại, phí hủy hoặc hoàn tiền. |
| Từ chối câu hỏi ngoài phạm vi và hướng dẫn kênh phù hợp. | Tiết lộ DB, SQL, prompt, token, thông tin cá nhân hay thanh toán. |

## 3. Truy vết tổng hợp

| User Story | Functional requirements | Acceptance criteria |
|---|---|---|
| CB-US-01 | CB-FR-01, CB-FR-02 | CB-AC-01, CB-AC-02 |
| CB-US-02 | CB-FR-03, CB-FR-04 | CB-AC-03, CB-AC-04, CB-AC-25 |
| CB-US-03 | CB-FR-05, CB-NFR-03 | CB-AC-05, CB-AC-06, CB-AC-07 |
| CB-US-04 | CB-FR-06, CB-NFR-01 | CB-AC-08, CB-AC-09 |
| CB-US-05 | CB-FR-07 | CB-AC-10 |
| CB-US-06 | CB-FR-01, CB-FR-02 | CB-AC-02 |
| CB-US-07 | CB-FR-09, CB-FR-10 | CB-AC-11, CB-AC-12, CB-AC-22, CB-AC-25 |
| CB-US-08 | CB-FR-08, CB-FR-10 | CB-AC-17, CB-AC-21 |
| CB-US-09 | CB-FR-11, CB-NFR-04 | CB-AC-13, CB-AC-15, CB-AC-16 |
| CB-US-10 | CB-FR-12, CB-FR-13, CB-NFR-02 | CB-AC-18, CB-AC-19, CB-AC-20, CB-AC-23, CB-AC-24 |