# Tài liệu yêu cầu phần mềm

## Yêu cầu chức năng

| Mã | Tên yêu cầu chức năng | Mô tả |
|---|---|---|
| FR-01 | Quản lý Phim & AI sinh mô tả | Cho phép Admin thêm, sửa, xóa thông tin phim, quản lý thể loại, thời lượng, nhãn độ tuổi và trạng thái phim (đang chiếu, sắp chiếu, ngừng chiếu). Tích hợp AI tự động sinh mô tả phim ngắn gọn (dưới 150 từ) từ tên phim và từ khóa. |
| FR-02 | Quản lý Phòng chiếu & Sơ đồ ghế | Cho phép Admin thêm, sửa, xóa thông tin các phòng chiếu mini, cấu hình số lượng và loại ghế ngồi (ghế đơn tiêu chuẩn, ghế đôi/couple, ghế VIP). |
| FR-03 | Thiết lập Suất chiếu & Ràng buộc lịch | Cho phép Admin tạo và quản lý lịch chiếu phim theo ngày/giờ và phòng chiếu; kiểm soát lịch chiếu chính xác, tránh trùng giờ/phòng; tự động giãn cách 10-15 phút dọn dẹp vệ sinh phòng giữa các suất và tự động khóa bán vé sau khi chiếu 15 phút. |
| FR-04 | Phân loại & Định giá vé | Cho phép Admin thiết lập giá vé cơ bản và chính sách phụ thu theo loại ghế (đơn, đôi, VIP) và khung giờ/ngày chiếu (khung giờ vàng sau 18h, ngày lễ, cuối tuần T6-CN, ngày thường). |
| FR-05 | Xem lịch & Sơ đồ ghế trực quan | Hiển thị danh sách lịch chiếu, phim và sơ đồ ghế ngồi trực quan dạng đồ họa (tọa độ hàng chữ, cột số) theo phòng chiếu thực tế, cập nhật trạng thái ghế theo thời gian thực (Trống, Đang chọn, Đã bán). |
| FR-06 | Chọn ghế, giữ chỗ & gợi ý phim | Cho phép Khách hàng chọn ghế và đặt vé giữ chỗ trực tuyến; tự động khóa ghế tạm thời 5 phút khi thanh toán. Tích hợp AI gợi ý 2-3 bộ phim phù hợp với sở thích của khách kèm kiểm tra suất chiếu còn đủ số ghế trống. |
| FR-07 | Hủy vé đã đặt | Cho phép Khách hàng tự hủy vé trực tuyến trước giờ chiếu ít nhất 60 phút (hoặc Nhân viên hỗ trợ tại quầy) và hệ thống tự động giải phóng ghế trống để mở bán lại. |
| FR-08 | Thanh toán online & phát hành vé QR | Cho phép Khách hàng thực hiện thanh toán trực tuyến thông qua cổng thanh toán trong khoảng thời gian giữ ghế 5 phút. Hệ thống tiếp nhận kết quả giao dịch, cập nhật trạng thái thanh toán và phát hành vé QR khi thanh toán thành công. |
| FR-09 | Quét mã QR soát vé | Cho phép Nhân viên quét mã QR trên vé (vé giấy hoặc vé điện tử trên điện thoại) tại cửa phòng chiếu để kiểm tra tính hợp lệ và cập nhật trạng thái “Đã check-in” vào phòng. |
| FR-10 | Tra cứu vé, phim, suất chiếu | Cho phép Khách hàng và Nhân viên tra cứu lịch sử vé đã mua, suất chiếu và mã QR bằng số điện thoại; hỗ trợ tìm kiếm, lọc danh sách phim và suất chiếu theo thể loại, ngày/giờ chiếu. |
| FR-11 | Thống kê doanh thu & AI tóm tắt | Tổng hợp báo cáo số lượng vé bán ra, tỷ lệ lấp đầy phòng chiếu và doanh thu theo từng bộ phim, từng suất chiếu và theo ngày/tuần/tháng. Tích hợp AI tự động tóm tắt số liệu thành 3-4 câu ngắn gọn gửi quản lý. |
| FR-12 | Kiểm duyệt nội dung AI | Cung cấp giao diện trực quan cho Admin kiểm tra, chỉnh sửa và bấm duyệt toàn bộ nội dung do AI sinh ra (mô tả phim, văn bản tóm tắt doanh thu) trước khi hiển thị cho khách hàng hoặc áp dụng vào hệ thống. |
| FR-13 | Đăng nhập và phân quyền người dùng | Cho phép người dùng đăng nhập hệ thống; phân quyền chặt chẽ: Admin có toàn quyền quản trị cấu hình hệ thống và doanh thu; Nhân viên chỉ thao tác bán vé, in vé, soát vé và tra cứu tại quầy; mã hóa bảo mật thông tin tài khoản người dùng. |

## Yêu cầu phi chức năng

- **NFR-01 – Dễ sử dụng:** Giao diện rõ ràng, sơ đồ ghế có màu phân biệt trạng thái, menu dễ hiểu và thông báo lỗi cụ thể.
- **NFR-02 – Hiệu năng và nhất quán:** Cập nhật trạng thái ghế nhanh; không bán trùng ghế; dữ liệu vé và thanh toán phải đồng bộ.
- **NFR-03 – Bảo mật và riêng tư:** Có đăng nhập, phân quyền, mã hóa dữ liệu nhạy cảm và không hiển thị công khai thông tin cá nhân.
- **NFR-04 – An toàn AI:** AI chỉ sử dụng dữ liệu được cung cấp; không tự tạo phim, suất, ghế hoặc giá; kết quả phải được kiểm tra trước khi hiển thị.
- **NFR-05 – Bảo trì và mở rộng:** Các module phim, vé, báo cáo và AI có thể bảo trì, kiểm thử và mở rộng độc lập.