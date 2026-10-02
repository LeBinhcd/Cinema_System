---
name: testing
description: Lập kế hoạch, thiết kế, triển khai, thực thi và báo cáo kiểm thử tự động một cách có hệ thống dựa trên tài liệu yêu cầu và tiêu chí nghiệm thu phần mềm.
---
# Testing Skill (Kỹ năng Kiểm thử)

## Mục tiêu
Kiểm chứng hệ thống phần mềm tuân thủ nghiêm ngặt các yêu cầu chức năng, quy tắc nghiệp vụ và tiêu chí nghiệm thu đã được phê duyệt thông qua kiểm thử tự động, đồng thời đảm bảo không làm thay đổi hoặc gây ảnh hưởng đến cơ sở dữ liệu thật của hệ thống.

## Đầu vào (Inputs)
Đọc các tài liệu dự án sau khi sẵn sàng:
- `docs/requirements.md`
- `docs/user-stories.md`
- `docs/acceptance-criteria.md`
- Toàn bộ mã nguồn kiểm thử hiện có trong thư mục `tests/`

## Quy trình thực hiện (Process)
### 1. Yêu cầu sang Kịch bản kiểm thử (Requirements → Test Scenario)
Chuyển đổi các yêu cầu chức năng và tiêu chí nghiệm thu đã duyệt thành các kịch bản kiểm thử (test scenarios) có cấu trúc rõ ràng.

### 2. Thiết kế Ca kiểm thử (Test Scenario → Test Case)
Xác định chi tiết các ca kiểm thử cho từng kịch bản:
- Điều kiện tiên quyết (Pre-conditions)
- Dữ liệu đầu vào (Test inputs)
- Các bước thực hiện (Execution steps)
- Kết quả mong đợi (Expected results), bao gồm cả các trường hợp biên và ngoại lệ.

### 3. Xây dựng Kiểm thử tự động (Test Case → Automated Test)
Tổ chức và viết các bài kiểm thử tự động bằng `pytest`:
- Unit tests: Kiểm thử logic nghiệp vụ độc lập, quy tắc tính toán, phân tích câu hỏi (sử dụng mock cho các phụ thuộc bên ngoài).
- Integration tests: Kiểm thử giao dịch cơ sở dữ liệu (Transaction), luồng đặt vé, thanh toán và API.

### 4. Thực thi kiểm thử an toàn (Automated Test → Execution)
- Toàn bộ bài test phải được thực thi độc lập trên cơ sở dữ liệu SQLite tạm thời (`tmp_path`).
- TUYỆT ĐỐI KHÔNG chạy kiểm thử hoặc ghi dữ liệu đè lên cơ sở dữ liệu thật (`cinema.db`).
- Phân biệt rõ giữa các bài test mock (chạy offline) và script chẩn đoán kết nối mạng.

### 5. Kết quả & Phân tích lỗi (Execution → Result → Defect)
- Ghi nhận chi tiết kết quả chạy kiểm thử (Pass / Fail).
- Phân tích và ghi lại các lỗi (Defects) phát hiện được trong quá trình chạy.
- KHÔNG ĐƯỢC sửa code của bài test chỉ nhằm mục đích làm cho test pass.
- Báo cáo rõ ràng nguyên nhân gốc rễ (root cause) của từng lỗi.

### 6. Đánh giá độ bao phủ (Coverage)
Đối chiếu và kiểm tra xem tất cả các yêu cầu chức năng chính đã có ít nhất một ca kiểm thử tương ứng hay chưa.

## Quy tắc bắt buộc (Rules)
- Không sửa bài test chỉ để che giấu lỗi trong mã nguồn nghiệp vụ.
- Bảo vệ tuyệt đối cơ sở dữ liệu thật (`cinema.db`).
- Không gọi các API bên ngoài có trả phí trong quá trình chạy kiểm thử thông thường (sử dụng mock).
- Báo cáo trung thực kết quả kiểm thử và phân loại lỗi rõ ràng.

## Đầu ra (Outputs)
Tạo hoặc cập nhật:
- `docs/test-plan.md`
- `docs/test-report.md`

## Kiểm chứng (Verification)
Trước khi hoàn thành tác vụ, cần xác nhận:
- Toàn bộ nhật ký (log) thực thi test đã được thu thập đầy đủ.
- Kế hoạch kiểm thử bao quát được các User Stories quan trọng.
- Danh sách lỗi phản ánh đúng hiện trạng kỹ thuật thực tế của hệ thống.