# Tác nhân và Use Case

## Tác nhân

1. **Khách hàng:** Xem lịch/sơ đồ ghế, đặt giữ chỗ trực tuyến, thanh toán online, tra cứu vé và tự hủy vé.
2. **Nhân viên:** Quét QR soát vé, hỗ trợ tra cứu và hỗ trợ hủy vé tại quầy.
3. **Quản trị viên (Admin):** Quản lý phim, phòng chiếu, phân loại/định giá vé, suất chiếu, kiểm duyệt nội dung AI và báo cáo doanh thu.
4. **Phân hệ AI (AI Assistant):** Sinh mô tả phim, phân tích sở thích để gợi ý phim và tóm tắt báo cáo doanh thu.
5. **Cổng thanh toán:** Nhận yêu cầu thanh toán, xử lý và trả kết quả thành công/thất bại để hệ thống cập nhật giao dịch và phát hành QR.

## Danh sách và ánh xạ

| UC | Use Case | Tác nhân chính/liên quan |
|---|---|---|
| UC01 | Quản lý Phim | Admin, AI Assistant |
| UC02 | Quản lý Phòng chiếu | Admin |
| UC03 | Thiết lập Suất chiếu | Admin |
| UC04 | Phân loại & Định giá vé | Admin |
| UC05 | Xem lịch & Sơ đồ ghế | Khách hàng |
| UC06 | Đặt giữ chỗ trực tuyến | Khách hàng, AI Assistant |
| UC07 | Hủy vé đã đặt | Khách hàng, Nhân viên |
| UC08 | Thanh toán online & phát hành vé QR | Khách hàng, Cổng thanh toán |
| UC09 | Quét mã QR soát vé | Nhân viên |
| UC10 | Tra cứu vé & Suất chiếu | Khách hàng, Nhân viên |
| UC11 | Thống kê & Báo cáo (AI tóm tắt doanh thu) | Admin, AI Assistant |
| UC12 | Kiểm duyệt nội dung AI | Admin |
| UC13 | Đăng nhập & Xác thực | Khách hàng, Nhân viên, Admin |

Các ràng buộc nghiệp vụ đi kèm được giữ nguyên: giữ ghế 5 phút, hủy trước giờ chiếu ít nhất 60 phút, giãn suất 10–15 phút và khóa bán sau 15 phút kể từ khi bắt đầu chiếu.

## Đặc tả ngắn gọn từng Use Case

| UC | Luồng nghiệp vụ được khảo sát | Requirement liên quan |
|---|---|---|
| UC01 | Admin quản lý thông tin phim; AI hỗ trợ sinh mô tả ngắn để Admin xem xét. | FR-01, FR-12, NFR-04 |
| UC02 | Admin quản lý phòng chiếu mini, số lượng và loại ghế. | FR-02 |
| UC03 | Admin tạo lịch theo phim, ngày/giờ và phòng; không trùng phòng, cách nhau 10–15 phút; khóa bán sau 15 phút kể từ khi chiếu. | FR-03, NFR-02 |
| UC04 | Admin cấu hình giá cơ bản và phụ thu theo loại ghế, khung giờ/ngày. | FR-04 |
| UC05 | Khách hàng xem phim, lịch chiếu và sơ đồ ghế; trạng thái ghế là Trống/Đang chọn/Đã bán. | FR-05, NFR-01 |
| UC06 | Khách hàng chọn ghế và giữ chỗ 5 phút; AI gợi ý 2–3 phim dựa trên sở thích và kiểm tra suất còn ghế. | FR-06, NFR-02, NFR-04 |
| UC07 | Khách hàng tự hủy trước ít nhất 60 phút hoặc Nhân viên hỗ trợ; ghế được giải phóng để bán lại. | FR-07 |
| UC08 | Khách hàng thanh toán qua Cổng thanh toán trong thời gian giữ ghế; hệ thống cập nhật kết quả và phát hành QR khi thành công. | FR-08, NFR-02 |
| UC09 | Nhân viên quét QR vé giấy/điện tử, kiểm tra hợp lệ và cập nhật Đã check-in. | FR-09 |
| UC10 | Khách hàng/Nhân viên tra cứu vé, suất, QR bằng số điện thoại và lọc phim/suất theo thể loại, ngày/giờ. | FR-10 |
| UC11 | Admin xem số vé, tỷ lệ lấp đầy và doanh thu theo phim/suất/ngày-tuần-tháng; AI tóm tắt thành 3–4 câu. | FR-11, FR-12, NFR-04 |
| UC12 | Admin kiểm tra, chỉnh sửa và duyệt nội dung AI trước khi hiển thị hoặc áp dụng. | FR-12, NFR-04 |
| UC13 | Người dùng đăng nhập; hệ thống phân quyền Admin, Nhân viên và Khách hàng. | FR-13, NFR-03 |

## Điểm mơ hồ cần Human Review

- Khảo sát nêu “hoàn tiền” và phí hủy nhưng FR-07 chưa quy định chính sách hoàn tiền, mức phí hoặc thời gian hoàn; không tự suy diễn chính sách này.
- Khảo sát đề cập “kênh rạp hỗ trợ” để thông báo giao dịch nhưng chưa xác định kênh cụ thể.
- FR-13 có nghiệp vụ “bán vé, in vé” cho Nhân viên, trong khi danh sách FR/UC không tách một UC bán vé riêng; phạm vi được giữ trong FR-13, không tạo UC mới.
- Cơ chế xác định sở thích khách hàng cho gợi ý AI/RAG chưa được khảo sát quy định chi tiết.