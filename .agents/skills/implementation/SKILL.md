---
name: implementation
description: Implement software modules using Python Flask and MySQL based strictly on approved requirements, architecture, and database designs.
---

# Implementation Skill

## Objective
Hiện thực hóa mã nguồn hệ thống "Hệ thống quản lý rạp chiếu phim có tích hợp AI" một cách chính xác, bảo mật và tuân thủ tuyệt đối các tài liệu đặc tả đã được phê duyệt.

## Inputs
Trước khi viết code, bắt buộc phải đọc và tuân thủ các tài liệu:
- docs/requirements.md (Danh sách FR và NFR)
- docs/use-cases.md (13 Use Cases từ UC01 đến UC13)
- docs/architecture.md (Kiến trúc phân tầng và luồng dữ liệu)
- docs/database-design.md và database/schema.sql (Cấu trúc CSDL chuẩn 3NF)

## Process (Quy trình lập trình chuẩn)
1. **Read Specification:** Đọc kỹ tài liệu thiết kế của module cần triển khai.
2. **Understand Architecture:** Đảm bảo code tuân thủ mô hình phân tầng (Routes/Controllers -> Services -> Models).
3. **Understand Database:** Sử dụng đúng các bảng, trường dữ liệu và câu lệnh SQL (có sử dụng parameterized query để chống SQL Injection).
4. **Implement Code:** Viết mã nguồn Python Flask sạch sẽ, modular, có xử lý ngoại lệ (Exception Handling) và ghi log đầy đủ. Không bao giờ hardcode secrets hoặc Gemini API key trong mã nguồn (bắt buộc dùng biến môi trường qua `.env`).
5. **Run Linter & Tests:** Kiểm tra lỗi cú pháp và chạy các bài kiểm thử liên quan.
6. **Review Diff:** Tự kiểm tra các thay đổi (diff) trước khi hoàn tất để đảm bảo không vi phạm kiến trúc.

## Rules (Quy tắc giới hạn nghiêm ngặt)
- TUYỆT ĐỐI KHÔNG tự ý thay đổi yêu cầu (Requirements) hoặc kiến trúc (Architecture) đã chốt.
- **Dừng lại khi thiếu thông tin:** Nếu thông số kỹ thuật hoặc tài liệu thiết kế không đủ để triển khai một tính năng, Agent PHẢI DỪNG LẠI và báo cáo yêu cầu con người quyết định thay vì tự ý suy đoán (Hallucination).
- Đảm bảo các tính năng đặc thù của rạp chiếu phim hoạt động chính xác: cơ chế giữ ghế tạm thời (5 phút), ràng buộc lịch chiếu (không trùng phòng, cách nhau 10-15 phút dọn dẹp, khóa bán vé sau 15 phút), và việc tích hợp Gemini API thông qua các service trung gian.

## Outputs
- Mã nguồn trong các thư mục: `app/models/`, `app/routes/`, `app/services/`, `app/templates/`, `app/static/`.
- Tệp cấu hình và điểm khởi chạy: `app.py`, `requirements.txt`.

## Verification (Kiểm tra trước khi hoàn thành)
Trước khi báo cáo hoàn thành việc cài đặt một module, Agent phải kiểm tra:
- [ ] Code tuân thủ đúng kiến trúc phân tầng chưa?
- [ ] Đã bảo mật tuyệt đối các thông tin nhạy cảm (API Key, thông tin thanh toán) chưa?
- [ ] Các ràng buộc nghiệp vụ (giữ ghế, tính giá vé, phân quyền Admin/Nhân viên/Khách hàng) đã được hiện thực hóa chính xác chưa?