# Thiết kế kiến trúc phần mềm

## Phạm vi và nguồn đầu vào

Tài liệu này chuyển đổi các FR/NFR, User Stories, tiêu chí nghiệm thu và Use Case đã có thành thiết kế kiến trúc ở mức khái niệm. Không bổ sung yêu cầu nghiệp vụ mới. Tiêu chí nghiệm thu hiện được ghi trong `docs/user-stories.md`; chưa có tệp riêng `docs/acceptance-criteria.md`.

## Phong cách kiến trúc

Chọn **Layered Architecture** cho ứng dụng Flask:

```text
Client/UI
    -> Routes / Controllers
    -> Application Services
    -> Domain Models / Repositories
    -> MySQL

Application Services -> AI Gateway -> Google Gemini API
Application Services -> Payment Gateway Adapter -> Cổng thanh toán
```

Kiến trúc phân tầng phù hợp với phạm vi một hệ thống rạp, giúp tách giao tiếp HTTP, nghiệp vụ đặt vé/thanh toán/báo cáo và truy cập dữ liệu. Không chọn Microservices vì yêu cầu hiện tại không đòi hỏi triển khai phân tán.

## Thành phần chính

| Thành phần | Trách nhiệm | Truy vết |
|---|---|---|
| Presentation/Routes | Tiếp nhận request, hiển thị lịch/sơ đồ ghế, nhận thao tác Admin/Nhân viên/Khách hàng, chuyển kết quả thành response. | FR-05, FR-09, FR-10, FR-13; NFR-01 |
| Authentication & Authorization | Đăng nhập, xác thực, phân quyền Admin/Nhân viên/Khách hàng và bảo vệ thông tin tài khoản. | FR-13; NFR-03 |
| Movie Management Service | Quản lý phim, thể loại, thời lượng, nhãn độ tuổi, trạng thái và quy trình mô tả AI chờ duyệt. | FR-01, FR-12; NFR-04 |
| Room & Seat Service | Quản lý phòng chiếu, số lượng và loại ghế; cung cấp sơ đồ ghế và trạng thái ghế. | FR-02, FR-05; NFR-01, NFR-02 |
| Screening & Pricing Service | Quản lý suất chiếu, tránh trùng phòng, giãn cách 10–15 phút, khóa bán sau 15 phút và tính giá/phụ thu. | FR-03, FR-04; NFR-02 |
| Booking Service | Chọn ghế, giữ ghế 5 phút, giải phóng ghế và kiểm soát trạng thái đặt chỗ. | FR-06, FR-07; NFR-02 |
| Payment & Ticket Service | Điều phối thanh toán, cập nhật giao dịch, phát hành QR sau thành công và xử lý trạng thái vé. | FR-08; NFR-02, NFR-03 |
| Check-in Service | Kiểm tra QR và cập nhật trạng thái “Đã check-in” cho Nhân viên. | FR-09 |
| Search & Ticket Query Service | Tra cứu vé, phim, suất chiếu bằng số điện thoại và lọc theo thể loại/ngày/giờ. | FR-10 |
| Reporting Service | Tổng hợp vé bán, tỷ lệ lấp đầy và doanh thu theo phim, suất, ngày/tuần/tháng. | FR-11 |
| AI Gateway / AI Review Workflow | Gọi Gemini cho mô tả, gợi ý và tóm tắt; lưu kết quả chờ Admin kiểm duyệt. | FR-01, FR-06, FR-11, FR-12; NFR-04 |
| Data Access Layer | Đọc/ghi dữ liệu nghiệp vụ và thực hiện giao dịch nhất quán với MySQL. | Toàn bộ FR dữ liệu; NFR-02, NFR-05 |

## Phụ thuộc và giao tiếp

- Routes chỉ gọi Application Services, không chứa quy tắc nghiệp vụ hoặc gọi trực tiếp hệ thống ngoài.
- Các Service dùng Data Access Layer để truy cập dữ liệu; transaction bao quanh thao tác giữ ghế và cập nhật thanh toán.
- AI Gateway là cổng duy nhất tới Gemini API; không gửi thông tin thẻ và chỉ gửi dữ liệu cần thiết cho từng tác vụ.
- Payment & Ticket Service là cổng duy nhất tới Cổng thanh toán; QR chỉ được phát hành khi nhận kết quả thành công.
- Reporting Service cung cấp số liệu đã tổng hợp cho AI Gateway; Gemini không tự tạo số liệu.

## Luồng dữ liệu chính

### Đặt ghế và thanh toán (UC05, UC06, UC08)

1. Khách hàng xem lịch và sơ đồ ghế qua Routes.
2. Booking Service kiểm tra trạng thái ghế và tạo giữ chỗ 5 phút trong giao dịch dữ liệu.
3. Payment & Ticket Service gửi yêu cầu tới Cổng thanh toán.
4. Kết quả thành công cập nhật vé/thanh toán và phát hành QR; thất bại hoặc hết hạn giữ ghế không phát hành vé QR thành công.
5. Trạng thái ghế được trả lại cho giao diện theo FR-05/NFR-02.

### AI sinh mô tả (UC01, UC12)

1. Admin cung cấp tên phim và từ khóa.
2. AI Gateway gửi dữ liệu này tới Gemini với ràng buộc mô tả dưới 150 từ.
3. Kết quả được lưu ở trạng thái chờ duyệt.
4. Admin kiểm tra/chỉnh sửa/duyệt; chỉ nội dung được duyệt mới được hiển thị hoặc áp dụng.

### Gợi ý phim (UC06)

1. AI Gateway nhận dữ liệu sở thích được cung cấp và truy xuất danh sách phim/lịch/số ghế còn trống.
2. Gemini tạo đề xuất 2–3 phim dựa trên ngữ cảnh đã cung cấp.
3. Service đối chiếu lại kết quả với dữ liệu hệ thống trước khi hiển thị; AI không được tự tạo lịch, ghế hoặc giá.

### Báo cáo và tóm tắt doanh thu (UC11, UC12)

1. Admin chọn phạm vi phim, suất hoặc ngày/tuần/tháng.
2. Reporting Service tổng hợp số vé, tỷ lệ lấp đầy và doanh thu.
3. AI Gateway gửi các số liệu tổng hợp cho Gemini để tạo 3–4 câu tóm tắt.
4. Admin kiểm duyệt trước khi nội dung được hiển thị hoặc áp dụng.

## Ranh giới bảo mật

- **Ranh giới người dùng:** Authentication & Authorization kiểm tra quyền trước các thao tác Admin/Nhân viên/Khách hàng.
- **Ranh giới dữ liệu:** thông tin cá nhân, mật khẩu và giao dịch không hiển thị công khai; mật khẩu phải được xử lý dưới dạng an toàn.
- **Ranh giới thanh toán:** hệ thống chỉ lưu kết quả/tham chiếu giao dịch cần thiết; không lưu thông tin thẻ nếu không cần thiết. Dữ liệu thanh toán đi qua Payment Gateway Adapter.
- **Ranh giới AI:** API key Gemini nằm ngoài mã nguồn; dữ liệu gửi đi được giới hạn, kết quả không được tự động áp dụng trước kiểm duyệt.
- **Ranh giới dữ liệu:** mọi thay đổi ghế/vé/thanh toán cần nhất quán để không bán trùng ghế.

## Ma trận truy vết FR → component

| FR | Component hỗ trợ |
|---|---|
| FR-01 | Movie Management, AI Gateway, AI Review Workflow |
| FR-02 | Room & Seat Service |
| FR-03 | Screening & Pricing Service, Data Access Layer |
| FR-04 | Screening & Pricing Service |
| FR-05 | Routes, Room & Seat Service |
| FR-06 | Booking Service, AI Gateway, Room & Seat Service |
| FR-07 | Booking Service, Authentication & Authorization |
| FR-08 | Payment & Ticket Service, Payment Gateway Adapter |
| FR-09 | Check-in Service, Authentication & Authorization |
| FR-10 | Search & Ticket Query Service, Routes |
| FR-11 | Reporting Service, AI Gateway |
| FR-12 | AI Review Workflow, Movie Management/Reporting Services |
| FR-13 | Authentication & Authorization, Routes |

NFR-01 được hỗ trợ bởi Routes/UI; NFR-02 bởi Booking, Payment, Data Access; NFR-03 bởi Authentication, ranh giới thanh toán; NFR-04 bởi AI Gateway/Review Workflow; NFR-05 bởi các layer và component tách biệt.