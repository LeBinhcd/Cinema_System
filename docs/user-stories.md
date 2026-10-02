# User Stories

## User Stories và tiêu chí nghiệm thu

### US-01 — FR-01
**Là một Admin, tôi muốn quản lý phim và dùng AI sinh mô tả dưới 150 từ, để thông tin phim được cập nhật nhanh và rõ ràng.**

- Given Admin cung cấp tên phim và từ khóa, When yêu cầu sinh mô tả, Then hệ thống tạo mô tả ngắn dưới 150 từ để Admin xem xét.
- Given Admin có quyền quản lý, When thêm/sửa/xóa hoặc cập nhật thể loại, thời lượng, nhãn độ tuổi, trạng thái, Then thông tin phim được cập nhật.

### US-02 — FR-02
**Là một Admin, tôi muốn quản lý phòng chiếu và loại ghế, để sơ đồ ghế phản ánh đúng phòng thực tế.**

- Given Admin có quyền, When thêm/sửa/xóa phòng hoặc cấu hình số lượng và loại ghế, Then cấu hình phòng được lưu theo ghế đơn tiêu chuẩn, ghế đôi/couple hoặc ghế VIP.

### US-03 — FR-03
**Là một Admin, tôi muốn thiết lập suất chiếu không trùng phòng và có thời gian vệ sinh, để lịch chiếu chính xác.**

- Given Admin tạo suất chiếu, When lịch cùng phòng bị trùng, Then hệ thống không chấp nhận lịch đó.
- Given hai suất liên tiếp cùng phòng, Then hệ thống bảo đảm khoảng cách dọn dẹp 10–15 phút và khóa bán khi phim đã bắt đầu 15 phút.

### US-04 — FR-04
**Là một Admin, tôi muốn cấu hình giá theo loại ghế và khung giờ/ngày, để áp dụng đúng chính sách giá.**

- Given Admin cấu hình bảng giá, When chọn loại ghế hoặc khung giờ/ngày chiếu, Then hệ thống áp dụng giá cơ bản và phụ thu tương ứng.

### US-05 — FR-05
**Là một Khách hàng, tôi muốn xem lịch và sơ đồ ghế theo trạng thái, để chọn chỗ phù hợp.**

- Given có lịch chiếu, When Khách hàng xem suất, Then hệ thống hiển thị phim, lịch và sơ đồ theo hàng chữ/cột số.
- Then trạng thái Trống, Đang chọn và Đã bán được phân biệt và cập nhật nhanh.

### US-06 — FR-06
**Là một Khách hàng, tôi muốn chọn ghế, giữ chỗ 5 phút và nhận gợi ý phim, để đặt vé thuận tiện.**

- Given ghế còn trống, When Khách hàng chọn ghế, Then ghế được giữ tạm thời 5 phút.
- Given có dữ liệu sở thích và lịch chiếu, When yêu cầu gợi ý, Then hệ thống đề xuất 2–3 phim kèm suất còn đủ ghế trống.

### US-07 — FR-07
**Là một Khách hàng, tôi muốn hủy vé trước ít nhất 60 phút, để ghế được giải phóng khi tôi không thể đi xem.**

- Given còn ít nhất 60 phút trước giờ chiếu, When Khách hàng hoặc Nhân viên thực hiện hủy hợp lệ, Then vé được hủy và ghế được mở bán lại.

### US-08 — FR-08
**Là một Khách hàng, tôi muốn thanh toán online và nhận QR, để vào rạp thuận tiện.**

- Given ghế đang được giữ trong 5 phút, When Cổng thanh toán trả kết quả thành công, Then hệ thống cập nhật thanh toán và phát hành vé QR.
- When giao dịch thất bại hoặc hết thời gian giữ, Then hệ thống không phát hành vé QR thành công.

### US-09 — FR-09
**Là một Nhân viên, tôi muốn quét QR và cập nhật check-in, để kiểm tra vé tại cửa phòng.**

- Given vé giấy hoặc vé điện tử có QR, When Nhân viên quét tại cửa, Then hệ thống kiểm tra hợp lệ và cập nhật trạng thái “Đã check-in” nếu hợp lệ.

### US-10 — FR-10
**Là một Khách hàng hoặc Nhân viên, tôi muốn tra cứu vé và suất chiếu bằng số điện thoại, để xem lại thông tin đã mua hoặc hỗ trợ khách.**

- Given số điện thoại tra cứu, When tìm kiếm, Then hệ thống hiển thị lịch sử vé, suất chiếu và mã QR phù hợp.
- When lọc theo thể loại hoặc ngày/giờ, Then danh sách phim và suất chiếu được lọc tương ứng.

### US-11 — FR-11
**Là một Admin, tôi muốn xem báo cáo và AI tóm tắt doanh thu, để nhanh chóng nắm tình hình kinh doanh.**

- Given dữ liệu vé, When Admin chọn phim, suất hoặc kỳ ngày/tuần/tháng, Then hệ thống tổng hợp số vé, tỷ lệ lấp đầy và doanh thu.
- Then AI tạo bản tóm tắt 3–4 câu từ các số liệu đã tổng hợp.

### US-12 — FR-12
**Là một Admin, tôi muốn kiểm tra, sửa và duyệt nội dung AI, để chỉ nội dung hợp lệ mới được hiển thị hoặc áp dụng.**

- Given có mô tả phim hoặc tóm tắt doanh thu do AI sinh, When Admin kiểm tra và chỉnh sửa, Then nội dung được lưu theo bản đã chỉnh sửa.
- When Admin bấm duyệt, Then nội dung mới được phép hiển thị hoặc áp dụng.

### US-13 — FR-13
**Là một người dùng, tôi muốn đăng nhập theo quyền, để thông tin và thao tác được bảo vệ phù hợp.**

- Given thông tin đăng nhập hợp lệ, When người dùng đăng nhập, Then hệ thống cấp quyền đúng vai trò Khách hàng, Nhân viên hoặc Admin.
- Then Admin được quản trị cấu hình và doanh thu; Nhân viên chỉ thao tác bán/in vé, soát vé và tra cứu tại quầy.

## Bảng truy vết (Traceability)

| User Story | Requirement ID | Use Case |
|---|---|---|
| US-01 | FR-01, NFR-04 | UC01 |
| US-02 | FR-02 | UC02 |
| US-03 | FR-03, NFR-02 | UC03 |
| US-04 | FR-04 | UC04 |
| US-05 | FR-05, NFR-01 | UC05 |
| US-06 | FR-06, NFR-02, NFR-04 | UC06 |
| US-07 | FR-07 | UC07 |
| US-08 | FR-08, NFR-02 | UC08 |
| US-09 | FR-09 | UC09 |
| US-10 | FR-10 | UC10 |
| US-11 | FR-11, NFR-04 | UC11 |
| US-12 | FR-12, NFR-04 | UC12 |
| US-13 | FR-13, NFR-03 | UC13 |

NFR-05 áp dụng xuyên suốt cho việc bảo trì, kiểm thử và mở rộng độc lập các module phim, vé, báo cáo và AI; không tạo User Story chức năng mới ngoài FR đã khảo sát.