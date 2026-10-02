# LỊCH SỬ DÙNG PROMPT (PROMPT LOG)

## Thông tin dự án

- **Tên dự án:** Hệ thống quản lý rạp phim có tích hợp AI
- **Quy trình:** AI-Augmented SDLC
- **Thời gian thực hiện:** 9 tuần
- **Vai trò thực hiện:** AI Engineering Lead / System Analyst
- **Phạm vi nhật ký:** Quy trình phân tích, chuẩn hóa và kiểm duyệt yêu cầu dựa trên 3 sơ đồ Use Case PlantUML bằng Prompt

---

## GIAI ĐOẠN 1: TẠO SKILL PHÂN TÍCH YÊU CẦU

### Mục tiêu

Tạo tệp `.agents/skills/requirements-analysis/SKILL.md` đóng vai trò là System Prompt điều phối toàn bộ quy trình Requirements Engineering cho dự án.

Skill phải cấu trúc theo chuẩn Markdown với các mục: `## Objective`, `## Inputs`, `## Process`, `## Rules`, `## Outputs`, `## Verification`, `## Human Gate 1`.

Hướng dẫn AI Agent:
- Đọc tài liệu khảo sát đầu vào `Khao_Sat_He_Thong_Chuan.docx` và 3 sơ đồ PlantUML (Nhân viên[cite: 4], Admin & AI[cite: 5], Khách hàng[cite: 6]).
- Trích xuất chính xác 13 yêu cầu chức năng (FR-01 đến FR-13) tương ứng với 13 Use Case (UC01 đến UC13)[cite: 4, 5, 6].
- Nhận diện đúng 5 tác nhân: Khách hàng, Nhân viên, Admin, Phân hệ AI (hỗ trợ) và Cổng thanh toán (bên ngoài)[cite: 4, 5, 6].
- Ánh xạ đầy đủ quan hệ `<<include>>`, `<<extend>>` và các ghi chú nghiệp vụ (giữ ghế HELD tối đa 5 phút[cite: 6], thanh toán SUCCESS mới phát hành QR[cite: 6], AI soạn nháp & Admin kiểm duyệt[cite: 5]).
- Xuất bộ tài liệu đầu ra chuẩn gồm 3 file trong thư mục `docs/`: `docs/requirements.md`, `docs/use-cases.md`, `docs/user-stories.md`.
- Chuyển đổi FR thành User Stories theo mẫu: `Là một <Tác nhân>, tôi muốn <Hành động>, để <Lợi ích đạt được>.`
- Tạo Acceptance Criteria theo chuẩn Gherkin: `Given [Điều kiện đầu vào] - When [Hành động kích hoạt] - Then [Kết quả mong đợi].`
- Thực hiện quy tắc kiểm soát phạm vi: Tuyệt đối không viết source code, không thiết kế CSDL/Architecture, không tự phát minh quy tắc nghiệp vụ ngoài tài liệu (đặc biệt không thêm tính năng bán bắp nước hay đồ ăn).
- Tích hợp cổng kiểm duyệt con người `=== HUMAN GATE 1: REQUIREMENTS REVIEW ===` bắt buộc dừng quy trình chờ phê duyệt.

### Prompt đã dùng

> Đóng vai trò là một AI Architect/System Analyst chuyên nghiệp. Hãy viết nội dung cho tệp cấu hình kỹ năng `.agents/skills/requirements-analysis/SKILL.md` dưới dạng Markdown (bao gồm các mục: `## Objective`, `## Inputs`, `## Process`, `## Rules`, `## Outputs`, `## Verification`, `## Human Gate 1`).
>
> Skill hướng dẫn AI Agent phân tích tài liệu khảo sát `Khao_Sat_He_Thong_Chuan.docx` cùng 3 sơ đồ PlantUML (Phân hệ Nhân viên[cite: 4], Admin & AI[cite: 5], Khách hàng[cite: 6]) để tạo bộ tài liệu đặc tả chuẩn gồm `docs/requirements.md`, `docs/use-cases.md`, `docs/user-stories.md`.
>
> Bắt buộc trích xuất đúng 13 FR (FR-01..FR-13), 13 Use Case (UC01..UC13) và 5 tác nhân (Khách hàng, Nhân viên, Admin, Phân hệ AI, Cổng thanh toán)[cite: 4, 5, 6]. Thể hiện chính xác quan hệ include/extend và ghi chú giữ ghế HELD tối đa 5 phút[cite: 6], thanh toán SUCCESS[cite: 6], AI soạn nháp & Admin duyệt[cite: 5].
>
> Viết User Stories theo cú pháp chuẩn và Acceptance Criteria theo định dạng Gherkin (`Given - When - Then`). Quy định nghiêm ngặt: TUYỆT ĐỐI KHÔNG viết source code, KHÔNG thiết kế CSDL/Architecture, KHÔNG thêm tính năng bán bắp nước.
>
> Cuối tệp SKILL, thêm phần `=== HUMAN GATE 1: REQUIREMENTS REVIEW ===` với checklist đánh giá chi tiết và quy tắc không được chuyển sang bước tiếp theo khi chưa có sự phê duyệt của con người.

### Kết quả đầu ra

- Đã khởi tạo `.agents/skills/requirements-analysis/SKILL.md`.
- Cấu trúc chuẩn hóa theo các mục `## Objective`, `## Inputs`, `## Process`, `## Rules`, `## Outputs`, `## Verification`, `## Human Gate 1`.
- Quy định chính xác 5 tác nhân, 13 FR/UC, 5 NFR, quan hệ include/extend và bộ tiêu chí Gherkin chuẩn hóa.

---

## GIAI ĐOẠN 2: THỰC THI SKILL VÀ SINH TÀI LIỆU BAN ĐẦU

### Mục tiêu

Kích hoạt skill để đọc `Khao_Sat_He_Thong_Chuan.docx` và 3 sơ đồ PlantUML để tự động sinh 3 file artifacts trong thư mục `docs/`.

### Prompt đã dùng

> Hãy thực hiện Requirements Engineering cho project này bằng requirements-analysis skill. Đọc file Khao_Sat_He_Thong_Chuan.docx và 3 sơ đồ PlantUML (Nhân viên[cite: 4], Admin & AI[cite: 5], Khách hàng[cite: 6]). Thực hiện đúng quy trình trong skill. Không viết source code hay thiết kế CSDL. Tạo 3 file: docs/requirements.md, docs/use-cases.md, docs/user-stories.md.

### Quy trình thực thi

1. AI Agent đọc tài liệu khảo sát và phân tích 3 sơ đồ PlantUML[cite: 4, 5, 6].
2. AI Agent trích xuất 13 Yêu cầu chức năng (FR-01..13), 13 Use Case (UC01..13) và 5 tác nhân[cite: 4, 5, 6].
3. AI Agent xác định đầy đủ mối quan hệ `<<include>>`, `<<extend>>` và các nốt nghiệp vụ[cite: 4, 5, 6].
4. AI Agent xác định các NFR (NFR-01..05).
5. AI Agent tạo User Stories theo cú pháp: `Là một <Tác nhân>, tôi muốn <Hành động>, để <Lợi ích đạt được>.`
6. AI Agent xây dựng Acceptance Criteria bằng định dạng Gherkin (`Given - When - Then`).
7. AI Agent thực hiện ánh xạ TRACEABILITY giữa User Stories với FR/NFR/UC.

### Artifacts dự kiến sinh ra

- `docs/requirements.md`
- `docs/use-cases.md`
- `docs/user-stories.md`

---

## GIAI ĐOẠN 3: HUMAN GATE 1 - CON NGƯỜI ĐÁNH GIÁ VÀ PHÁT HIỆN LỖI

### Mục tiêu

Kiểm duyệt bộ tài liệu do AI tạo ra dựa trên mẫu `=== HUMAN GATE 1: REQUIREMENTS REVIEW ===` trước khi cấp phép chuyển sang giai đoạn Thiết kế.

### Kết quả kiểm tra của con người

1. **UC06 / FR-06 (Giữ ghế & Gợi ý phim):** Đã thể hiện AI gợi ý phim[cite: 6], nhưng kịch bản Gherkin chưa làm rõ điều kiện tự động giải phóng ghế về trạng thái **Trống** khi quá 5 phút HELD mà chưa thanh toán[cite: 6].
2. **UC08 / FR-08 (Thanh toán online):** Cần làm rõ kịch bản Gherkin chỉ khi Cổng thanh toán trả về **SUCCESS** đã xác thực thì mới đổi trạng thái ghế sang "Đã bán" và phát hành mã QR vé[cite: 6].
3. **UC11 & UC12 (AI tóm tắt & Kiểm duyệt):** Cần làm rõ luồng Admin kiểm duyệt (UC12 extend UC11 & UC01) trước khi hiển thị chính thức nội dung AI sinh ra[cite: 5].
4. **Phạm vi dự án:** Đã tuân thủ tốt quy tắc không bịa thêm tính năng ngoài 3 sơ đồ PlantUML (không có bán bắp nước hay thức ăn).

### Kết luận Human Gate 1

=== HUMAN GATE 1: REQUIREMENTS REVIEW ===  
Reviewer: System Analyst  
Status: **REJECTED**  

Checklist kiểm tra:
- [x] Functional requirements (FR) và Use Cases (UC) đã đầy đủ (FR01-FR13, UC01-UC13) và không bịa thêm?  
- [ ] Đã thể hiện chính xác quan hệ include/extend và role của AI/Payment Gateway từ 3 sơ đồ PlantUML? (Cần bổ sung chi tiết luồng kiểm duyệt UC12 cho UC01 và UC11)  
- [x] Non-functional requirements (NFR) đã có mã ID?  
- [x] User stories đã ánh xạ đúng với FR và 5 Actors?  
- [ ] Acceptance criteria đã rõ ràng, có thể test được? (Cần bổ sung kịch bản hết 5 phút HELD và phản hồi SUCCESS từ Gateway)  
- [x] Các điểm mơ hồ (Ambiguities) đã được báo cáo?  

---

## GIAI ĐOẠN 4: PROMPT SỬA ĐỔI VÀ BỔ SUNG (FEEDBACK LOOP)

### Mục tiêu

Cập nhật lại đồng bộ bộ tài liệu `docs/` theo góp ý từ Human Gate 1.

### Prompt đã dùng

> Sau khi kiểm tra tài liệu tại Human Gate 1, Status là REJECTED. Hãy sửa lại bộ tài liệu theo góp ý sau:
>
> 1. Bổ sung kịch bản Gherkin cho UC06/FR-06: Khi ghế ở trạng thái HELD quá 5 phút mà chưa chuyển sang thanh toán SUCCESS, hệ thống tự động trả trạng thái ghế về "Trống" và báo hết hạn giữ chỗ[cite: 6].
> 2. Bổ sung kịch bản Gherkin cho UC08/FR-08: Chỉ khi Cổng thanh toán trả về tín hiệu SUCCESS đã xác thực thì mới cập nhật đặt ghế thành công và phát hành vé QR[cite: 6].
> 3. Làm rõ luồng UC12 (Kiểm duyệt nội dung AI): Admin xem bản nháp do AI gợi ý (mô tả phim ở UC01, tóm tắt báo cáo ở UC11) và thực hiện duyệt/sửa trước khi công bố[cite: 5].
> 4. Giữ nguyên quy tắc nghiêm ngặt: Tuyệt đối không thêm tính năng bán bắp nước hay đồ ăn.
>
> Cập nhật đồng bộ cả 3 file: `docs/requirements.md`, `docs/use-cases.md` và `docs/user-stories.md`.

### Nội dung cập nhật chính

1. **Gherkin cho UC06 (Giữ ghế 5 phút):**
   - **Given:** Khách hàng đang chọn ghế ở trạng thái HELD (tối đa 5 phút)[cite: 6].
   - **When:** Thời gian giữ chỗ vượt quá 5 phút mà hệ thống chưa nhận được phản hồi thanh toán thành công.
   - **Then:** Hệ thống hủy trạng thái HELD, đưa ghế về trạng thái **Trống** và thông báo cho Khách hàng chọn lại[cite: 6].

2. **Gherkin cho UC08 (Thanh toán & Mã QR):**
   - **Given:** Khách hàng thực hiện thanh toán giao dịch qua Cổng thanh toán bên ngoài[cite: 6].
   - **When:** Cổng thanh toán trả về phản hồi **SUCCESS** đã xác thực[cite: 6].
   - **Then:** Hệ thống ghi nhận bán ghế thành công, phát hành vé điện tử chứa mã QR và chuyển sang trạng thái "Đã thanh toán"[cite: 6].

3. **Gherkin cho UC12 (Kiểm duyệt AI):**
   - **Given:** Phân hệ AI tạo bản nháp mô tả phim [FR-01] hoặc bản tóm tắt báo cáo doanh thu [FR-11][cite: 5].
   - **When:** Admin truy cập màn hình kiểm duyệt nội dung AI (UC12)[cite: 5].
   - **Then:** Admin có thể phê duyệt, chỉnh sửa hoặc yêu cầu AI tạo lại bản nháp trước khi hiển thị công khai[cite: 5].

---

## GIAI ĐOẠN 5: CHỐT KẾT QUẢ CUỐI CÙNG (FINAL APPROVAL)

### Trạng thái phê duyệt

=== HUMAN GATE 1: REQUIREMENTS REVIEW ===  
Reviewer: AI Engineering Lead / System Analyst  
Status: **APPROVED**  

Checklist kiểm tra:
- [x] Functional requirements (FR01-FR13) và Use Cases (UC01-UC13) đã đầy đủ và không bịa thêm?  
- [x] Đã thể hiện chính xác quan hệ include/extend và role của AI/Payment Gateway từ 3 sơ đồ PlantUML?  
- [x] Non-functional requirements (NFR) đã có mã ID (NFR-01..NFR-05)?  
- [x] User stories đã ánh xạ đúng với FR và 5 tác nhân?  
- [x] Acceptance criteria đã rõ ràng, viết theo chuẩn Gherkin, bao phủ logic HELD 5 phút, thanh toán SUCCESS, AI kiểm duyệt?  
- [x] Các điểm mơ hồ (Ambiguities) đã được làm rõ?  

### Bộ tài liệu hoàn thiện đã lưu vết

- `docs/requirements.md`
- `docs/use-cases.md`
- `docs/user-stories.md`

### Kết luận

Giai đoạn Requirements Engineering đã hoàn tất đầy đủ quy trình trong `SKILL.md`, khớp 100% với 3 sơ đồ PlantUML. Hệ thống đủ điều kiện được cấp phép chuyển sang giai đoạn Thiết kế Kiến trúc (Architecture) và Cơ sở dữ liệu (Database).