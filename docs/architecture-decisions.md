# Architectural Decision Records

## ADR-001: Chọn Layered Architecture

- **Trạng thái:** Đề xuất chờ Human Gate 2
- **Quyết định:** Tổ chức hệ thống theo các lớp Routes, Services và Data Access/Models.
- **Rationale:** Phù hợp quy mô và phạm vi hệ thống rạp; tách trách nhiệm, dễ kiểm thử và bảo trì; đáp ứng NFR-05 mà không đưa thêm hạ tầng phân tán.
- **Hệ quả:** Service phải giữ quy tắc nghiệp vụ; Routes không truy cập trực tiếp dữ liệu hoặc hệ thống ngoài.

## ADR-002: Sử dụng Flask làm lớp ứng dụng HTTP

- **Trạng thái:** Đề xuất chờ Human Gate 2
- **Quyết định:** Dùng Flask theo technology constraint của dự án để cung cấp Routes và giao diện hệ thống.
- **Rationale:** Flask đủ cho các luồng UC01–UC13 và hỗ trợ tổ chức theo factory/layer mà không cần framework dư thừa.
- **Hệ quả:** Cần duy trì ranh giới rõ giữa route và service để tránh logic nghiệp vụ nằm trong controller.

## ADR-003: MySQL là hệ thống lưu trữ nghiệp vụ

- **Trạng thái:** Đề xuất chờ Human Gate 2
- **Quyết định:** Dùng MySQL cho dữ liệu phim, phòng, ghế, suất, vé, người dùng, giao dịch và số liệu báo cáo.
- **Rationale:** Phù hợp yêu cầu dữ liệu nhất quán, chống bán trùng ghế và truy vấn báo cáo; phù hợp technology constraint.
- **Hệ quả:** Các thao tác giữ ghế/thanh toán phải được điều phối qua transaction và kiểm soát đồng thời.

## ADR-004: Tách AI Gateway và quy trình kiểm duyệt

- **Trạng thái:** Đề xuất chờ Human Gate 2
- **Quyết định:** Mọi gọi Google Gemini đi qua AI Gateway; kết quả mô tả/gợi ý/tóm tắt không được tự động trở thành dữ liệu nghiệp vụ.
- **Rationale:** Đáp ứng NFR-04, bảo vệ API key, giới hạn dữ liệu gửi ra ngoài và bảo đảm Admin kiểm duyệt theo FR-12.
- **Hệ quả:** Các luồng AI phải hỗ trợ trạng thái chờ duyệt và xử lý trường hợp Gemini không trả kết quả hợp lệ.

## ADR-005: Cổng thanh toán qua adapter riêng

- **Trạng thái:** Đề xuất chờ Human Gate 2
- **Quyết định:** Payment & Ticket Service giao tiếp với Cổng thanh toán qua một ranh giới adapter, chỉ nhận kết quả giao dịch cần thiết.
- **Rationale:** Giảm phụ thuộc trực tiếp vào nhà cung cấp, giữ dữ liệu thanh toán ngoài phạm vi lưu trữ không cần thiết và hỗ trợ FR-08/NFR-03.
- **Hệ quả:** QR chỉ được phát hành sau khi xác nhận thanh toán thành công; thông tin thẻ không thuộc dữ liệu hệ thống.

## ADR-006: Giữ ghế và thanh toán là luồng nhất quán

- **Trạng thái:** Đề xuất chờ Human Gate 2
- **Quyết định:** Booking/Payment/đọc trạng thái ghế dùng kiểm soát giao dịch để đảm bảo thời hạn giữ 5 phút và không bán trùng.
- **Rationale:** Trực tiếp đáp ứng FR-06, FR-08 và NFR-02 trong môi trường có nhiều khách cùng chọn ghế.
- **Hệ quả:** Cần xử lý rõ hết hạn, thanh toán thất bại và giải phóng ghế; chi tiết triển khai sẽ thuộc giai đoạn sau và không nằm trong tài liệu kiến trúc này.