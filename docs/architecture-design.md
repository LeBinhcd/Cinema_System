# Thiết kế kiến trúc

## Kiến trúc phân tầng

Ứng dụng dùng Flask theo mô hình phân tầng, với hướng phụ thuộc từ ngoài vào trong:

```text
Routes (HTTP/UI) -> Services (nghiệp vụ) -> Models (dữ liệu MySQL)
                                      -> Gemini API (AI Gateway)
```

- **Routes:** nhận request, xác thực quyền theo UC13, kiểm tra dữ liệu đầu vào và trả response/template. Routes không chứa quy tắc nghiệp vụ hoặc truy vấn SQL phức tạp.
- **Services:** thực hiện các quy tắc của FR/UC: giữ ghế 5 phút, kiểm tra lịch không trùng, hủy trước 60 phút, thanh toán và báo cáo. Đây là nơi điều phối AI.
- **Models:** ánh xạ các thực thể User, Phim, Phòng chiếu, Ghế, Suất chiếu và Vé tới MySQL; dùng giao dịch để tránh bán trùng ghế.
- **Templates/Static:** giao diện hiển thị lịch, sơ đồ ghế, vé QR và màn hình quản trị.

## Luồng AI với Gemini API

AI chỉ nhận dữ liệu được cung cấp bởi hệ thống, không được tự tạo phim, suất, ghế hoặc giá. Mọi kết quả AI có trạng thái bản nháp và phải qua UC12 trước khi hiển thị/áp dụng.

### UC01 – Sinh mô tả phim

Admin nhập tên phim và từ khóa. Service gọi Gemini với prompt giới hạn mô tả ngắn gọn dưới 150 từ, lưu kết quả ở trạng thái bản nháp. Admin kiểm tra, chỉnh sửa và duyệt trước khi công bố.

### UC06 – Gợi ý phim theo RAG

Service lấy dữ liệu phim và lịch/số ghế còn trống từ MySQL làm ngữ cảnh truy xuất (RAG), kết hợp sở thích khách hàng để yêu cầu Gemini đề xuất 2–3 phim. Kết quả được đối chiếu lại với dữ liệu lịch chiếu và số ghế thực tế trước khi trả về; Gemini không được tự suy đoán lịch hoặc tồn ghế.

### UC11 – Tóm tắt doanh thu

Service tổng hợp số vé, tỷ lệ lấp đầy và doanh thu theo phim/suất/ngày-tuần-tháng. Chỉ các số liệu này được gửi cho Gemini để tạo tóm tắt 3–4 câu. Admin duyệt nội dung qua UC12 trước khi gửi/hiển thị cho quản lý.

## Giao dịch và kiểm soát

Đặt ghế và thanh toán phải dùng transaction/khóa phù hợp ở MySQL để bảo đảm NFR-02. QR chỉ phát hành sau kết quả thanh toán thành công từ Cổng thanh toán. Dữ liệu cá nhân và thông tin xác thực tuân thủ NFR-03; API key Gemini nằm trong biến môi trường.