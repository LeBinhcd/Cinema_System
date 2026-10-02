---
name: requirements-analysis
description: Analyze software requirements and transform natural-language requirements into structured functional requirements, non-functional requirements, user stories, acceptance criteria, and traceability information.
---

# Requirements Analysis Skill

## Objective
Phân tích yêu cầu phần mềm một cách có hệ thống và tạo ra một bản đặc tả có cấu trúc chuẩn, phục vụ trực tiếp cho các giai đoạn thiết kế kiến trúc, cơ sở dữ liệu, lập trình và kiểm thử.

## Inputs
Đọc kỹ các tài liệu đầu vào sau:
- Tệp khảo sát gốc (ví dụ: Khao_Sat_He_Thong_Chuan.docx hoặc text tương đương).
- Các ràng buộc dự án (Project constraints).

## Process (Quy trình bắt buộc)

### 1. Identify stakeholders & actors
Xác định rõ các tác nhân tương tác với hệ thống (Ví dụ: Khách hàng, Nhân viên, Admin, AI Assistant, Cổng thanh toán).

### 2. Identify functional requirements (FR)
Trích xuất và chuẩn hóa các yêu cầu chức năng từ tài liệu thô.
Bắt buộc sử dụng định dạng ID: FR-01, FR-02, FR-03...

### 3. Identify non-functional requirements (NFR)
Xác định các yêu cầu phi chức năng liên quan đến: hiệu năng, bảo mật, độ tin cậy, an toàn AI.
Bắt buộc sử dụng định dạng ID: NFR-01, NFR-02...

### 4. Create User Stories
Chuyển đổi các FR thành User Stories.
Bắt buộc sử dụng cú pháp chuẩn: `Là một <Tác nhân>, tôi muốn <Hành động>, để <Lợi ích đạt được>.`

### 5. Create Acceptance Criteria (Tiêu chí nghiệm thu)
Mỗi User Story quan trọng phải đi kèm tiêu chí nghiệm thu có thể kiểm thử được.
Khuyến khích dùng định dạng Gherkin: `Given [Điều kiện đầu vào] - When [Hành động kích hoạt] - Then [Kết quả mong đợi].`

### 6. Traceability (Truy vết)
Mỗi User Story phải được ánh xạ (trace) rõ ràng đến một hoặc nhiều ID yêu cầu (FR/NFR) tương ứng để đảm bảo không bỏ sót tính năng.

## Rules (Quy tắc giới hạn của AI)
- TUYỆT ĐỐI KHÔNG viết source code trong giai đoạn này.
- TUYỆT ĐỐI KHÔNG thiết kế database schema hay architecture.
- Không được tự phát minh ra các quy tắc nghiệp vụ (business rules) không được ghi chép trong tài liệu đầu vào (ví dụ: không tự vẽ ra tính năng bán bắp nước nếu khảo sát không có).
- Phân biệt rõ ràng giữa "Yêu cầu thực tế" và "Giả định".

## Outputs
Agent phải tạo hoặc cập nhật các tệp sau trong thư mục `docs/`:
- `docs/requirements.md`
- `docs/use-cases.md`
- `docs/user-stories.md`

## Verification (Cổng kiểm duyệt của con người)
Trước khi báo cáo hoàn thành task, Agent tự kiểm tra checklist sau:
- [ ] Tất cả FR và NFR đều đã có ID định danh rõ ràng chưa?
- [ ] Các User Stories đã truy vết về đúng Requirement chưa?
- [ ] Tiêu chí nghiệm thu có khả năng test thực tế không?

## Human Gate 1 (Kiểm duyệt bắt buộc từ con người)
Quy trình phân tích yêu cầu BẮT BUỘC phải dừng lại ở bước này. Agent tuyệt đối không được tự động chuyển sang thiết kế Kiến trúc (Architecture) hay CSDL (Database) khi chưa có sự phê duyệt của con người.

Sau khi tạo xong các tài liệu đầu ra, Agent phải in ra màn hình mẫu đánh giá dưới đây và chờ người dùng (Human) phản hồi:

=== HUMAN GATE 1: REQUIREMENTS REVIEW ===
Reviewer: [Tên người duyệt]
Status: [PENDING / APPROVED / REJECTED]

Checklist kiểm tra:
[ ] Functional requirements (FR) đã đầy đủ và không bịa thêm?
[ ] Non-functional requirements (NFR) đã có mã ID?
[ ] User stories đã ánh xạ đúng với FR?
[ ] Acceptance criteria đã rõ ràng, có thể test được?
[ ] Các điểm mơ hồ (Ambiguities) đã được báo cáo?

Quy tắc thực thi: 
- Nếu Status là REJECTED: Agent phải sửa lại tài liệu theo góp ý của Human.
- Nếu Status là APPROVED: Agent mới được phép nhận lệnh để tiến hành thiết kế Architecture.