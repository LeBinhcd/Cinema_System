---
name: architecture-design
description: Design software architecture from approved requirements while preserving traceability and documenting architectural decisions.
---

# Architecture Design Skill

## Objective
Chuyển đổi các yêu cầu phần mềm đã được phê duyệt thành một bản thiết kế kiến trúc phần mềm mạch lạc, rõ ràng.

## Inputs
Chỉ đọc các tài liệu đã được phê duyệt (Approved):
- docs/requirements.md
- docs/user-stories.md
- docs/acceptance-criteria.md

## Process
1. Identify architectural style (Ví dụ: Layered Architecture, Microservices).
2. Identify major components (Ví dụ: Product Service, Auth Service, RAG/Chatbot Service).
3. Define responsibility of each component.
4. Define dependencies & communication between components.
5. Define data flow.
6. Identify external systems (Ví dụ: Gemini API, Cổng thanh toán).
7. Identify security boundaries.
8. Document architectural decisions (Lý do chọn công nghệ/kiến trúc).
9. Check requirements-to-architecture traceability.

## Rules
- TUYỆT ĐỐI KHÔNG viết implementation source code.
- TUYỆT ĐỐI KHÔNG sửa đổi các yêu cầu đã được phê duyệt ở bước trước.
- Không đưa vào các công nghệ dư thừa không cần thiết.
- Mọi quyết định kiến trúc lớn đều phải có lý do (rationale) rõ ràng.

## Outputs
Tạo các tệp sau trong thư mục `docs/`:
- `docs/architecture.md`
- `docs/architecture-decisions.md`

## Verification & Human Gate 2
Trước khi hoàn thành, hãy đối chiếu: Mỗi FR quan trọng có được support bởi ít nhất một architectural component không?
Sau khi xuất file, phải DỪNG LẠI và in ra biểu mẫu sau để chờ phê duyệt:

=== HUMAN GATE 2: ARCHITECTURE REVIEW ===
Reviewer: [Tên người duyệt]
Status: [PENDING / APPROVED / REJECTED]

Checklist kiểm tra:
[ ] Các component đã phủ kín toàn bộ Functional Requirements chưa?
[ ] Luồng dữ liệu (Data flow) tích hợp AI (Gemini) đã hợp lý chưa?
[ ] Có đảm bảo an toàn/bảo mật thông tin thanh toán không?