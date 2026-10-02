# LỊCH SỬ DÙNG PROMPT (PROMPT LOG)

## Thông tin dự án

- **Tên dự án:** Hệ thống quản lý rạp phim có tích hợp AI
- **Quy trình:** AI-Augmented SDLC
- **Thời gian thực hiện:** 9 tuần
- **Vai trò thực hiện:** AI Engineering Lead / System Analyst
- **Phạm vi nhật ký:** Quy trình phân tích, chuẩn hóa và kiểm duyệt yêu cầu bằng Prompt

---

## GIAI ĐOẠN 1: TẠO SKILL PHÂN TÍCH YÊU CẦU

### Mục tiêu

Tạo tệp `.agents/skills/requirements-analysis/SKILL.md` đóng vai trò là System Prompt điều phối toàn bộ quy trình Requirements Engineering cho dự án.

Skill phải cấu trúc theo chuẩn Markdown với các mục: `## Objective`, `## Inputs`, `## Process`, `## Rules`, `## Outputs`, `## Verification`, `## Human Gate 1`.

Hướng dẫn AI Agent:
- Đọc tài liệu khảo sát đầu vào `Khao_Sat_He_Thong_Chuan.docx` và các ràng buộc dự án.
- Trích xuất chính xác 13 yêu cầu chức năng từ FR-01 đến FR-13 và 13 Use Case từ UC01 đến UC13.
- Nhận diện đúng 5 tác nhân: Khách hàng, Nhân viên, Admin, Phân hệ AI và Cổng thanh toán.
- Xuất bộ tài liệu đầu ra chuẩn gồm 3 file trong thư mục `docs/`: `docs/requirements.md`, `docs/use-cases.md`, `docs/user-stories.md`.
- Chuyển đổi FR thành User Stories theo mẫu: `Là một <Tác nhân>, tôi muốn <Hành động>, để <Lợi ích được đạt>.`
- Tạo Acceptance Criteria theo chuẩn Gherkin: `Given [Điều kiện đầu vào] - When [Hành động kích hoạt] - Then [Kết quả mong đợi].`
- Thực hiện quy tắc kiểm soát phạm vi: Tuyệt đối không viết source code, không thiết kế CSDL/Architecture, không tự phát minh quy tắc nghiệp vụ ngoài tài liệu (đặc biệt không thêm tính năng bán bắp nước hay đồ ăn).
- Đưa các quy tắc nghiệp vụ lõi (tự động giữ ghế tối đa 5 phút - hết giờ trả về "Trống", hủy vé trực tuyến trước giờ chiếu ít nhất 60 phút, giãn cách dọn phòng 10–15 phút, khóa bán vé sau 15 phút, AI sinh mô tả phim dưới 150 từ, AI tóm tắt doanh thu 3–4 câu, check-in QR) vào Acceptance Criteria.
- Tích hợp cổng kiểm duyệt con người `=== HUMAN GATE 1: REQUIREMENTS REVIEW ===` bắt buộc dừng quy trình chờ phê duyệt.

### Prompt đã dùng

> Đóng vai trò là một AI Architect/System Analyst chuyên nghiệp. Hãy viết nội dung cho tệp cấu hình kỹ năng `.agents/skills/requirements-analysis/SKILL.md` dưới dạng Markdown (bao gồm các mục: `## Objective`, `## Inputs`, `## Process`, `## Rules`, `## Outputs`, `## Verification`, `## Human Gate 1`).
>
> Skill hướng dẫn AI Agent phân tích tài liệu đầu vào `Khao_Sat_He_Thong_Chuan.docx` và tạo bộ tài liệu đặc tả chuẩn gồm `docs/requirements.md`, `docs/use-cases.md`, `docs/user-stories.md`.
>
> Bắt buộc trích xuất đúng 13 FR (FR-01..FR-13), 13 Use Case (UC01..UC13) và 5 tác nhân (Khách hàng, Nhân viên, Admin, Phân hệ AI, Cổng thanh toán). Viết User Stories theo chuẩn và Acceptance Criteria theo định dạng Gherkin (`Given - When - Then`).
>
> Quy định nghiêm ngặt các quy tắc: TUYỆT ĐỐI KHÔNG viết source code, KHÔNG thiết kế database schema/architecture, KHÔNG tự thêm tính năng bán bắp nước hay thức ăn. Đưa đầy đủ các kịch bản giữ ghế 5 phút, hủy vé trước 60 phút, check-in QR, AI mô tả < 150 từ, AI tóm tắt 3-4 câu vào tiêu chí nghiệm thu.
>
> Cuối tệp SKILL, thêm phần `=== HUMAN GATE 1: REQUIREMENTS REVIEW ===` với đầy đủ checklist kiểm tra và quy tắc không chuyển sang bước tiếp theo khi chưa có sự phê duyệt của con người.

### Kết quả đầu ra

- Đã khởi tạo `.agents/skills/requirements-analysis/SKILL.md`.
- Cấu trúc chuẩn hóa theo các mục `## Objective`, `## Inputs`, `## Process`, `## Rules`, `## Outputs`, `## Verification`, `## Human Gate 1`.
- Quy định chính xác 5 tác nhân, 13 FR/UC, 5 NFR và bộ tiêu chí Gherkin cho nghiệp vụ rạp phim.

---

## GIAI ĐOẠN 2: THỰC THI SKILL VÀ SINH TÀI LIỆU BAN ĐẦU

### Mục tiêu

Kích hoạt skill để đọc `Khao_Sat_He_Thong_Chuan.docx` và tự động sinh 3 file artifacts theo đúng khai báo trong SKILL.md.

### Prompt đã dùng

> Hãy thực hiện Requirements Engineering cho project này bằng requirements-analysis skill. Đọc file Khao_Sat_He_Thong_Chuan.docx. Thực hiện đúng quy trình trong skill. Không viết source code hay thiết kế CSDL. Tạo 3 file: docs/requirements.md, docs/use-cases.md, docs/user-stories.md.

### Quy trình thực thi

1. AI Agent đọc tài liệu `Khao_Sat_He_Thong_Chuan.docx`.
2. AI Agent trích xuất 13 Yêu cầu chức năng (FR-01..13), 13 Use Case (UC01..13) và 5 tác nhân.
3. AI Agent xác định các NFR (NFR-01..05).
4. AI Agent tạo User Stories theo cú pháp: `Là một <Tác nhân>, tôi muốn <Hành động>, để <Lợi ích được đạt>.`
5. AI Agent xây dựng Acceptance Criteria bằng định dạng Gherkin (`Given - When - Then`).
6. AI Agent thực hiện ánh xạ TRACEABILITY giữa User Stories với FR/NFR.

### Artifacts dự kiến sinh ra

- `docs/requirements.md`
- `docs/use-cases.md`
- `docs/user-stories.md`

---

## GIAI ĐOẠN 3: HUMAN GATE 1 - CON NGƯỜI ĐÁNH GIÁ VÀ PHÁT HIỆN LỖI

### Mục tiêu

Kiểm duyệt bộ tài liệu do AI tạo ra dựa trên mẫu `=== HUMAN GATE 1: REQUIREMENTS REVIEW ===` trước khi cấp phép chuyển sang giai đoạn Thiết kế.

### Kết quả kiểm tra của con người

1. **FR-11 (Báo cáo doanh thu & AI tóm tắt):** Thiếu chi tiết kịch bản nghiệm thu Gherkin cho việc AI sinh bản tóm tắt 3–4 câu.
2. **Kịch bản biên giữ ghế:** Chưa làm rõ điều kiện hệ thống tự động giải phóng ghế về trạng thái **Trống** khi hết đúng 5 phút mà khách chưa thanh toán thành công.
3. **FR-09 (Check-in QR):** Cần bổ sung chi tiết điều kiện vé hợp lệ và cập nhật trạng thái "Đã check-in" khi Nhân viên quét mã QR.
4. **Phạm vi dự án:** Đã tuân thủ tốt quy tắc không bịa thêm tính năng bán bắp nước hay đồ ăn.

### Kết luận Human Gate 1

=== HUMAN GATE 1: REQUIREMENTS REVIEW ===  
Reviewer: System Analyst  
Status: **REJECTED**  

Checklist kiểm tra:
- [x] Functional requirements (FR) đã đầy đủ và không bịa thêm?  
- [x] Non-functional requirements (NFR) đã có mã ID?  
- [ ] User stories đã ánh xạ đúng với FR? (Cần cập nhật bổ sung luồng FR-11 và FR-09)  
- [ ] Acceptance criteria đã rõ ràng, có thể test được? (Cần bổ sung kịch bản hết 5 phút giữ ghế)  
- [x] Các điểm mơ hồ (Ambiguities) đã được báo cáo?  

---

## GIAI ĐOẠN 4: PROMPT SỬA ĐỔI VÀ BỔ SUNG (FEEDBACK LOOP)

### Mục tiêu

Cập nhật lại đồng bộ bộ tài liệu `docs/` theo góp ý từ Human Gate 1.

### Prompt đã dùng

> Sau khi kiểm tra tài liệu tại Human Gate 1, Status là REJECTED. Hãy sửa lại bộ tài liệu theo góp ý sau:
>
> 1. Bổ sung User Story và Acceptance Criteria (dạng Given-When-Then) cho FR-11 (Báo cáo doanh thu và AI tóm tắt 3-4 câu).
> 2. Bổ sung kịch bản Given-When-Then xử lý trường hợp hết 5 phút giữ ghế, hệ thống tự động trả ghế về trạng thái Trống.
> 3. Làm rõ nghiệp vụ Nhân viên quét mã QR soát vé (FR-09) kèm điều kiện cập nhật trạng thái "Đã check-in".
> 4. Giữ nguyên quy tắc nghiêm ngặt: Tuyệt đối không thêm tính năng bán bắp nước hay đồ ăn.
>
> Cập nhật đồng bộ cả 3 file: `docs/requirements.md`, `docs/use-cases.md` và `docs/user-stories.md`.

### Nội dung cập nhật chính

1. **Gherkin cho thời gian giữ ghế:**
   - **Given:** Khách hàng đã chọn ghế và chuyển sang màn hình thanh toán (trạng thái ghế: HELD).
   - **When:** Thời gian giữ chỗ vượt quá 5 phút mà chưa nhận được tín hiệu thanh toán SUCCESS.
   - **Then:** Hệ thống tự động hủy lượt giữ chỗ, chuyển trạng thái ghế về **Trống** và hiển thị thông báo hết thời gian cho khách hàng.

2. **Gherkin cho FR-09 (Check-in QR):**
   - **Given:** Nhân viên sử dụng thiết bị quét mã QR tại cửa phòng chiếu.
   - **When:** Nhận mã QR từ vé của Khách hàng.
   - **Then:** Hệ thống đối soát thông tin (đúng suất, đúng phòng, đã thanh toán, chưa check-in) và đổi trạng thái vé thành **Đã check-in**.

3. **Gherkin cho FR-11 (AI tóm tắt doanh thu):**
   - **Given:** Quản trị viên truy cập màn hình báo cáo doanh thu.
   - **When:** Hệ thống tổng hợp số liệu doanh thu theo khoảng thời gian.
   - **Then:** Phân hệ AI tự động trích xuất bản tóm tắt 3–4 câu phân tích xu hướng doanh thu để hiển thị cho Admin.

---

## GIAI ĐOẠN 5: CHỐT KẾT QUẢ CUỐI CÙNG (FINAL APPROVAL)

### Trạng thái phê duyệt

=== HUMAN GATE 1: REQUIREMENTS REVIEW ===  
Reviewer: AI Engineering Lead / System Analyst  
Status: **APPROVED**  

Checklist kiểm tra:
- [x] Functional requirements (FR) đã đầy đủ (FR-01..FR-13) và không bịa thêm?  
- [x] Non-functional requirements (NFR) đã có mã ID (NFR-01..NFR-05)?  
- [x] User stories đã ánh xạ đúng với FR và 5 tác nhân?  
- [x] Acceptance criteria đã rõ ràng, viết theo chuẩn Gherkin, có thể test được?  
- [x] Các điểm mơ hồ (Ambiguities) đã được làm rõ?  

### Bộ tài liệu hoàn thiện đã lưu vết

- `docs/requirements.md`
- `docs/use-cases.md`
- `docs/user-stories.md`

### Kết luận

Giai đoạn Requirements Engineering đã hoàn tất đầy đủ quy trình trong `SKILL.md`. Hệ thống đủ điều kiện được cấp phép chuyển sang giai đoạn Thiết kế Kiến trúc (Architecture) và Cơ sở dữ liệu (Database).