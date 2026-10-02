# Thiết kế cơ sở dữ liệu MySQL

## Phạm vi và nguyên tắc

Thiết kế này sử dụng các yêu cầu và kiến trúc đã được tạo ở các giai đoạn trước, không bổ sung nghiệp vụ mới. Schema đạt tối thiểu 3NF: dữ liệu phim, thể loại, phòng, ghế, suất chiếu, người dùng, vé và thanh toán được tách theo thực thể; quan hệ nhiều-nhiều Phim–Thể loại dùng bảng liên kết.

## Thực thể và quan hệ

| Bảng | Vai trò | Quan hệ chính |
|---|---|---|
| `users` | Khách hàng, Nhân viên và Admin; phân quyền qua `role`. | 1-N với `tickets`, `payments`; 1-N với nội dung AI được duyệt |
| `movies` | Phim, trạng thái, thời lượng, nhãn độ tuổi, synopsis và metadata cho RAG. | N-N với `genres`; 1-N với `screenings`, `ai_contents` |
| `genres` | Danh mục thể loại. | N-N với `movies` qua `movie_genres` |
| `movie_genres` | Bảng liên kết chuẩn hóa phim–thể loại. | FK tới `movies`, `genres` |
| `screening_rooms` | Phòng chiếu mini. | 1-N với `seats`, `screenings` |
| `seats` | Ghế theo hàng, số và loại ghế. | N-1 với `screening_rooms`; 1-N với `tickets` |
| `screenings` | Suất chiếu của một phim tại một phòng. | N-1 với `movies`, `screening_rooms`; 1-N với `tickets` |
| `pricing_rules` | Giá cơ bản/phụ thu theo loại ghế và khung giờ/ngày. | Được áp dụng khi tính vé; không lưu lặp trong phim/phòng |
| `tickets` | Giữ chỗ, vé đã thanh toán, hủy và check-in. | N-1 với user/suất/ghế; 1-N với `payments` |
| `payments` | Kết quả/tham chiếu giao dịch từ Cổng thanh toán. | N-1 với `tickets`; không lưu thông tin thẻ |
| `ai_contents` | Nội dung AI sinh cho mô tả phim/tóm tắt doanh thu, trạng thái kiểm duyệt. | N-1 với phim hoặc user duyệt; không thay thế dữ liệu nghiệp vụ |
| `revenue_summaries` | Văn bản tóm tắt doanh thu theo phạm vi báo cáo và trạng thái duyệt. | N-1 với user duyệt; dùng dữ liệu tổng hợp, không chứa giao dịch thẻ |

## Chuẩn hóa và ràng buộc

- Khóa chính dùng `BIGINT UNSIGNED`; mọi FK đều chỉ rõ và không dùng `ON DELETE CASCADE` cho vé/thanh toán.
- `users.phone` duy nhất; mật khẩu chỉ lưu `password_hash`.
- `movie_genres` có khóa chính kép, không cho trùng thể loại trên một phim.
- `seats` duy nhất theo `(room_id, row_label, seat_number)`.
- `screenings` có `CHECK (end_time > start_time)`; chống trùng phòng và khoảng dọn 10–15 phút cần được kiểm tra trong Screening Service cùng transaction.
- `tickets` lưu `HELD`, `PAID`, `CANCELLED`, `CHECKED_IN`; `hold_expires_at` phục vụ giữ ghế 5 phút. Trạng thái vé còn hiệu lực được kiểm tra trong transaction để cho phép bán lại vé đã hủy.
- `payments` có mã tham chiếu duy nhất theo cổng; chỉ lưu trạng thái, số tiền và thời điểm, không lưu PAN/CVV/thông tin thẻ.
- Nội dung AI có `DRAFT`, `EDITED`, `APPROVED`, `REJECTED`; chỉ bản `APPROVED` mới được sử dụng/hiển thị.

## RAG và tìm kiếm

`movies.synopsis` lưu phần giới thiệu ngắn; `keywords` lưu từ khóa tìm kiếm; `metadata_json` lưu metadata cung cấp cho truy hồi như nhãn độ tuổi, thời lượng hoặc thuộc tính phim đã được hệ thống cung cấp. Các trường này là dữ liệu nguồn, không phải dữ liệu do AI tự tạo. Index phục vụ tìm theo tiêu đề, thể loại, trạng thái và lịch chiếu theo thời gian.

## Index chiến lược

- `movies(title)`, `movies(status, release_date)` cho quản lý/tìm phim.
- `movie_genres(genre_id, movie_id)` cho lọc thể loại.
- `screenings(room_id, start_time, end_time)` cho lịch phòng và kiểm tra giao nhau.
- `screenings(start_time, movie_id)` cho lọc ngày/giờ và báo cáo.
- `tickets(screening_id, seat_id, status, hold_expires_at)` cho kiểm tra trạng thái ghế.
- `tickets(user_id, created_at)` cho lịch sử vé và `tickets(qr_code)` cho soát vé.
- `payments(provider_reference)` cho đối soát giao dịch.

## Truy vết UC01–UC13 → bảng

| UC | Bảng hỗ trợ |
|---|---|
| UC01 | `movies`, `genres`, `movie_genres`, `ai_contents` |
| UC02 | `screening_rooms`, `seats` |
| UC03 | `movies`, `screening_rooms`, `screenings` |
| UC04 | `pricing_rules` |
| UC05 | `movies`, `screenings`, `screening_rooms`, `seats`, `tickets` |
| UC06 | `movies`, `screenings`, `seats`, `tickets`, `ai_contents` |
| UC07 | `tickets`, `payments`, `seats` |
| UC08 | `tickets`, `payments` |
| UC09 | `tickets`, `users` |
| UC10 | `users`, `movies`, `screenings`, `tickets` |
| UC11 | `tickets`, `payments`, `screenings`, `revenue_summaries`, `ai_contents` |
| UC12 | `ai_contents`, `revenue_summaries`, `users` |
| UC13 | `users` |

## Giới hạn kiểm chứng

MySQL `CHECK` không đủ để kiểm tra chồng lấn thời gian giữa hai dòng suất chiếu hoặc điều kiện “ghế còn hiệu lực” theo nhiều dòng vé. Các điều kiện này phải được thực hiện bởi Screening/Booking Service trong transaction, đúng với kiến trúc đã duyệt; schema cung cấp FK, index và trạng thái cần thiết để hỗ trợ.