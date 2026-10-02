# Chạy bản xem trước CineVista không cần MySQL

Trong PowerShell:

```powershell
cd 'D:\New folder (7)\Cinema_System'
python -m pip install -r requirements.txt
python seed.py
python app.py
```

Mở http://127.0.0.1:5000 hoặc http://127.0.0.1:5000/login.
`seed.py` tạo `cinema.db` trong thư mục dự án, nạp dữ liệu mẫu, chạy lại không tạo bản sao. Seed chỉ cho phép `APP_ENV=development`, `demo` hoặc `testing`; không chạy seed khi triển khai production. Không cần MySQL cho demo. Nếu có `.env`, đặt `DB_ENGINE=sqlite`, `SQLITE_PATH=cinema.db`, `APP_ENV=development` và `SECRET_KEY` riêng. Nếu thiếu secret, ứng dụng sinh khóa ngẫu nhiên và cảnh báo; session sẽ hết hiệu lực sau restart. DB SQLite cũ cần chạy `python -m database.migrate_sqlite_phone` trước khi tra cứu vé (không xóa dữ liệu); nhập số điện thoại riêng cho khách muốn tìm theo phone. Không dùng DB cũ đã seed tài khoản demo khi triển khai; tắt trang login nhanh không tự vô hiệu hóa mật khẩu demo cũ.

| Vai trò | Email | Mật khẩu |
|---|---|---|
| Admin | admin@cinema.com | admin123 |
| Staff | staff@cinema.com | staff123 |
| Customer | customer@gmail.com | cust123 |

Admin xem `/admin`, cập nhật trạng thái phim/thời lượng (không cho đổi thời lượng phim đã có lịch), duyệt hoặc từ chối bản nháp mô tả phim. Staff tra cứu vé ở `/staff` bằng email/số điện thoại/mã QR; dữ liệu mẫu chưa có vé. `users.phone` là tùy chọn, email đăng nhập vẫn bắt buộc. Customer chọn ghế tại `/booking/1`, giữ 5 phút; ghế tự trống sau khi hết hạn. Thanh toán, phát hành vé, check-in chưa khả dụng. Giữ ghế dùng bảng `seat_holds` riêng, **không** tạo vé với giá giả hoặc giả lập thanh toán.

Ảnh poster mẫu lấy từ Unsplash và CSS Bootstrap từ CDN, vì vậy ảnh/Bootstrap cần kết nối internet; dữ liệu phim, lịch, ghế và các màn hình vẫn hoạt động offline (CSS cục bộ vẫn áp dụng).

`database/sqlite_schema.sql` là schema riêng cho SQLite có `users.email` và `users.phone` tùy chọn; schema MySQL gốc trong `database/schema.sql` không được chỉnh sửa. Các API quản trị MySQL cũ không đăng ký khi chạy chế độ SQLite. Bản demo này và tài khoản/mật khẩu mẫu chỉ dùng trên máy cục bộ; không đưa ra Internet hay dùng trong production. Muốn nạp lại dữ liệu hoàn toàn, dừng server và xóa `cinema.db` rồi chạy `python seed.py` (thao tác này xóa toàn bộ dữ liệu SQLite hiện có).