---
name: requirements-analysis
description: Analyze software requirements for Cinema Management System with AI integration based on PlantUML Use Case diagrams, generating structured FRs, NFRs, user stories, acceptance criteria, and traceability information.
---

# Requirements Analysis Skill

## Objective
Phân tích yêu cầu phần mềm một cách có hệ thống dựa trên hồ sơ khảo sát và 3 sơ đồ Use Case PlantUML (Nhân viên[cite: 4], Quản trị viên & AI[cite: 5], Khách hàng[cite: 6]); chuẩn hóa thành bộ tài liệu đặc tả phục vụ trực tiếp cho giai đoạn thiết kế kiến trúc, CSDL và lập trình.

## Inputs
- Tệp khảo sát gốc (`Khao_Sat_He_Thong_Chuan.docx`).
- 3 sơ đồ Use Case PlantUML: Phân hệ Nhân viên[cite: 4], Phân hệ Admin[cite: 5], Phân hệ Khách hàng[cite: 6].
- Các ràng buộc dự án (Project constraints - 9 tuần).

## Process (Quy trình bắt buộc)

### 1. Identify stakeholders & actors
Xác định chính xác 5 tác nhân hệ thống từ 3 sơ đồ PlantUML:
- **Khách hàng (Customer)**[cite: 6]
- **Nhân viên (Staff)**[cite: 4]
- **Quản trị viên (Admin)**[cite: 5]
- **Phân hệ AI (hỗ trợ) <<System>>**: Hỗ trợ gợi ý phim, soạn nháp mô tả phim và tóm tắt báo cáo doanh thu[cite: 5, 6].
- **Cổng thanh toán (bên ngoài) <<External>>**: Xác thực kết quả thanh toán[cite: 6].

### 2. Identify functional requirements (FR) & Use Cases (UC)
Trích xuất và ánh xạ chính xác 13 FR từ FR-01 đến FR-13 tương ứng với 13 Use Case:
- **UC01 / FR-01**: Quản lý phim và mô tả AI (Admin thực hiện[cite: 5], AI hỗ trợ soạn nháp[cite: 5]).
- **UC02 / FR-02**: Quản lý phòng chiếu và ghế (Admin thực hiện[cite: 5]).
- **UC03 / FR-03**: Thiết lập suất chiếu (Admin thực hiện[cite: 5]).
- **UC04 / FR-04**: Định giá và hiển thị tổng tiền (Admin và Khách hàng[cite: 5, 6]).
- **UC05 / FR-05**: Xem lịch và sơ đồ ghế (Staff và Khách hàng[cite: 4, 6]).
- **UC06 / FR-06**: Chọn ghế, giữ chỗ và gợi ý phim (Khách hàng thực hiện, AI gợi ý 2-3 phim[cite: 6]).
- **UC07 / FR-07**: Hủy vé đã thanh toán (Khách hàng tự thực hiện, Staff hỗ trợ theo quyền[cite: 4, 6]).
- **UC08 / FR-08**: Thanh toán online và phát hành vé QR (Khách hàng tương tác với Cổng thanh toán[cite: 6]).
- **UC09 / FR-09**: Quét QR check-in (Staff thực hiện[cite: 4]).
- **UC10 / FR-10**: Tra cứu vé và lịch chiếu (Staff và Khách hàng[cite: 4, 6]).
- **UC11 / FR-11**: Báo cáo doanh thu và AI tóm tắt (Admin xem, AI tóm tắt nháp[cite: 5]).
- **UC12 / FR-12**: Kiểm duyệt nội dung AI (Admin duyệt nội dung AI sinh ra[cite: 5]).
- **UC13 / FR-13**: Đăng nhập và phân quyền (Tất cả người dùng hệ thống[cite: 4, 5, 6]).

### 3. Model Relationships & Business Rules
Phải thể hiện chính xác các mối quan hệ và ràng buộc nghiệp vụ từ sơ đồ PlantUML:
- **Quan hệ `<<include>>`**:
  - UC06 include UC05 (Chọn ghế phải xem lịch và sơ đồ ghế)[cite: 6].
  - UC08 include UC04 (Thanh toán phải tính giá và tổng tiền)[cite: 6].
  - UC07, UC08, UC09, UC10, UC12 include UC13 (Yêu cầu đăng nhập / xác thực quyền)[cite: 4, 5, 6].
- **Quan hệ `<<extend>>`**:
  - UC07 extend UC10 (Hủy vé tùy chọn khi đang xem chi tiết vé / tra cứu)[cite: 4, 6].
  - UC12 extend UC01 (Admin kiểm duyệt khi AI tạo bản nháp mô tả phim)[cite: 5].
  - UC12 extend UC11 (Admin kiểm duyệt khi AI tạo bản tóm tắt báo cáo)[cite: 5].
- **Quy tắc nghiệp vụ đặc thù (Note)**:
  - **Giữ ghế (UC06)**: Trạng thái HELD tối đa 5 phút, chưa phải là vé chính thức[cite: 6].
  - **Thanh toán (UC08)**: Chỉ khi Cổng thanh toán trả về trạng thái SUCCESS đã xác thực mới bán ghế và phát hành mã QR[cite: 6].

### 4. Create User Stories
Chuyển đổi từng FR thành User Story theo cú pháp chuẩn:
`Là một <Tác nhân>, tôi muốn <Hành động>, để <Lợi ích đạt được>.`

### 5. Create Acceptance Criteria (Tiêu chí nghiệm thu)
Xây dựng Tiêu chí nghiệm thu cho từng User Story theo chuẩn Gherkin:
`Given [Điều kiện đầu vào] - When [Hành động kích hoạt] - Then [Kết quả mong đợi].`

### 6. Traceability (Truy vết)
Mỗi User Story phải ánh xạ rõ ràng đến ID Requirement (FR/NFR) và Use Case tương ứng.

## Rules (Quy tắc giới hạn của AI)
- TUYỆT ĐỐI KHÔNG viết source code trong giai đoạn này.
- TUYỆT ĐỐI KHÔNG thiết kế database schema hay architecture.
- Không tự phát minh các quy tắc nghiệp vụ ngoài tài liệu và 3 sơ đồ (đặc biệt KHÔNG thêm tính năng bán bắp nước hay đồ ăn).
- Bảo đảm tính nhất quán tuyệt đối về mã ID (FR-01..13, UC01..13) và tên các tác nhân.

## Outputs
Agent phải tạo hoặc cập nhật 3 tệp sau trong thư mục `docs/`:
- `docs/requirements.md`
- `docs/use-cases.md`
- `docs/user-stories.md`

## Verification (Cổng kiểm duyệt của con người)
Trước khi báo cáo hoàn thành task, Agent tự kiểm tra checklist sau:
- [ ] Tất cả 13 FR, 13 UC và 5 Actors đã đầy đủ và khớp với 3 sơ đồ PlantUML chưa?
- [ ] Mối quan hệ include/extend và ghi chú nghiệp vụ (giữ ghế 5 phút, thanh toán SUCCESS) đã thể hiện đúng chưa?
- [ ] User Stories và Acceptance Criteria (Gherkin) đã bao phủ toàn bộ luồng chính và luồng biên chưa?

## Human Gate 1 (Kiểm duyệt bắt buộc từ con người)
Quy trình phân tích yêu cầu BẮT BUỘC phải dừng lại ở bước này. Agent tuyệt đối không được tự động chuyển sang thiết kế Kiến trúc (Architecture) hay CSDL (Database) khi chưa có sự phê duyệt của con người.

Sau khi tạo xong các tài liệu đầu ra, Agent phải in ra màn hình mẫu đánh giá dưới đây và chờ người dùng (Human) phản hồi:

=== HUMAN GATE 1: REQUIREMENTS REVIEW ===
Reviewer: [Tên người duyệt]
Status: [PENDING / APPROVED / REJECTED]

Checklist kiểm tra:
[ ] Functional requirements (FR01-FR13) và Use Cases (UC01-UC13) đã đầy đủ và không bịa thêm?
[ ] Đã thể hiện chính xác quan hệ include/extend và role của AI/Payment Gateway từ 3 sơ đồ PlantUML?
[ ] Non-functional requirements (NFR) đã có mã ID?
[ ] User stories đã ánh xạ đúng với FR và 5 Actors?
[ ] Acceptance criteria đã rõ ràng, viết theo chuẩn Gherkin, có thể test được?
[ ] Các điểm mơ hồ (Ambiguities) đã được báo cáo?

Quy tắc thực thi: 
- Nếu Status là REJECTED: Agent phải sửa lại tài liệu theo góp ý của Human.
- Nếu Status là APPROVED: Agent mới được phép nhận lệnh để tiến hành thiết kế Architecture.