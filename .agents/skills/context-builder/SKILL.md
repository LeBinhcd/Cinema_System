---
name: context-builder
description: Convert retrieved screenings and validated intent into compact, faithful textual context for Gemini without adding or changing backend facts.
---

# Context Builder Skill

## Objective

Chuyển danh sách suất chiếu đã được Retrieval Service truy xuất, cùng với Intent tương ứng, thành textual context ngắn gọn và có cấu trúc để Gemini diễn đạt câu trả lời.

## Input

- `Retrieved screenings`: danh sách các suất chiếu được trả về từ Retrieval Service.
- `Intent`: Structured Intent đã được phân tích và kiểm tra hợp lệ.

Context Builder chỉ sử dụng dữ liệu có trong input. Module không truy cập database, không tự truy xuất thêm dữ liệu và không gọi Gemini.

## Output

Compact textual context dành cho Gemini, chỉ bao gồm các thông tin cần thiết để trả lời Intent, ví dụ:

- Tên phim.
- Thời gian bắt đầu và kết thúc suất chiếu.
- Tên phòng chiếu.
- Số ghế trống theo từng loại: `STANDARD`, `VIP`, `COUPLE`.
- Các trường khác chỉ được đưa vào context nếu đã có trong Retrieved screenings và cần thiết cho Intent.

## Rules

- Không thêm dữ liệu không có trong database hoặc không có trong Retrieved screenings.
- Không thay đổi tên phim.
- Không thay đổi tên phòng chiếu.
- Không thay đổi giờ chiếu.
- Không thay đổi số lượng ghế trống theo từng loại.
- Không thêm thông số chưa được truy xuất.
- Không suy đoán, làm tròn, diễn giải hoặc tự sinh thông tin về phim, suất chiếu, phòng chiếu hay ghế.
- Không đưa raw SQL, database path, secret, user ID, email, số điện thoại, thông tin thanh toán hoặc dữ liệu hold owner vào context.
- Context phải gọn gàng, súc tích, dễ đọc và chỉ chứa dữ liệu cần thiết dành cho Gemini.
- Không gửi toàn bộ database cho Gemini.
- Không dùng text do Gemini tạo ra để bổ sung hoặc sửa các dữ liệu retrieval.
- Nếu `Retrieved screenings` là danh sách rỗng, output phải là thông báo rõ ràng rằng không có suất chiếu phù hợp và không được tự tạo kết quả thay thế.

## Empty Result

Khi không có suất chiếu, trả về context rõ ràng, ví dụ:

```text
Không tìm thấy suất chiếu phù hợp với yêu cầu đã truy xuất.
Không có dữ liệu suất chiếu để cung cấp cho Gemini.
```

Không gửi context rỗng để Gemini tự đoán hoặc tự đề xuất suất chiếu.

## Safety Boundary

Context Builder chỉ tạo context đọc dữ liệu cho chatbot. Nó không thực hiện đặt vé, giữ ghế, thanh toán, hủy vé hoặc bất kỳ thao tác ghi nào vào database. Việc xác nhận cuối cùng về suất chiếu, ghế và giao dịch thuộc về Booking Core.

---