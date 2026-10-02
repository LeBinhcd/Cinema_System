# Vấn đề, điểm mơ hồ và quyết định cần theo dõi – Chatbot RAG

**Nguồn:** `docs/chatbot-requirements.md`, tài liệu requirements hiện có và `requirements-analysis` skill  
**Trạng thái:** Phân tích Bước 2; các điểm dưới đây không được tự suy diễn thành business rule

## 1. Quyết định đã chốt

| ID | Nội dung | Trạng thái / tác động |
|---|---|---|
| DEC-01 | Chatbot chỉ tư vấn và dẫn đường, không giữ ghế, thanh toán, hủy/hoàn tiền, phát hành QR hoặc sửa dữ liệu. | Đã chốt; phản ánh trong CB-FR-08, CB-FR-10 và CB-AC-17. |
| DEC-02 | Nguồn sự thật cho phim/suất/ghế gồm `movies`, `screenings`, `seats`, `tickets`, `seat_holds` và bảng liên quan cần thiết. | Đã chốt; phải backend đối chiếu, không giao cho Gemini. |
| DEC-03 | Link nút đặt vé là `/booking/<screening_id>`. | Đã chốt theo Human Gate; `screening_id` phải là ID thật từ `screenings`. |
| DEC-04 | Khóa Gemini dùng `GEMINI_API_KEY` phía server từ môi trường/`.env`, không lộ client. | Đã chốt; phản ánh trong CB-FR-13 và CB-AC-19. |
| DEC-05 | Khi thiếu căn cứ hoặc nguồn lỗi, chatbot từ chối hoặc thông báo chưa thể xác nhận, không bịa. | Đã chốt; là nhóm Anti-hallucination AC bắt buộc. |

## 2. Vấn đề cần giải quyết trước thiết kế/triển khai

| ID | Vấn đề | Rủi ro nếu không chốt | Đề xuất xử lý / chủ sở hữu |
|---|---|---|---|
| ISS-01 | Chưa có nguồn cấu hình cụ thể cho giá vé và chính sách hủy/hoàn tiền. | Chatbot có thể trả giá/chính sách không có căn cứ hoặc phải từ chối quá thường xuyên. | Product/Business xác định nguồn chính thức, trường dữ liệu và hiệu lực. Không dùng Gemini làm nguồn thay thế. |
| ISS-02 | Chưa chốt múi giờ vận hành khi hiểu “hôm nay”, “tối nay”, “ngày mai”. | Lọc sai ngày, nhất là gần nửa đêm hoặc khi server khác múi giờ. | Product/Backend chốt timezone rạp và truyền thời điểm tham chiếu cho truy vấn. |
| ISS-03 | Chưa định nghĩa khoảng giờ chính xác của “buổi sáng” và “tối nay”. | Kết quả khác nhau giữa người dùng và hệ thống. | Product duyệt các khoảng giờ hoặc yêu cầu chatbot hỏi lại. |
| ISS-04 | Trạng thái ticket nào được coi là đang chiếm ghế cho mục đích tra cứu chưa được chuẩn hóa thành contract chatbot. | Có thể báo thừa/thiếu ghế trống khi trạng thái `HELD`, `PAID`, `BOOKED`, `USED`, `CHECKED_IN` thay đổi. | Booking/Backend lập bảng trạng thái chính thức, đồng bộ với rule lõi và test transaction. |
| ISS-05 | Cách xử lý hold hết hạn trong schema hiện có cần bảo đảm nhất quán với việc tính ghế. | Hold hết hạn vẫn làm ghế bị báo bận hoặc gây bán trùng. | Booking/Backend xác định điều kiện thời gian và transaction; không để model tự tính. |
| ISS-06 | Chưa có giới hạn số Screening Cards, phân trang hoặc thứ tự ưu tiên. | Câu trả lời dài, khó dùng hoặc bỏ sót suất phù hợp. | Product/UX chốt giới hạn và sort; nếu chưa chốt, không ghi thành AC cứng. |
| ISS-07 | Chưa chốt hành vi khi câu hỏi chứa nhiều ý, ví dụ vừa hỏi giá vừa hỏi ghế. | Một phần câu hỏi có thể bị bỏ qua hoặc trả lời không nhất quán. | Product/UX quyết định trả nhiều phần hay hỏi người dùng chọn một nhu cầu. |
| ISS-08 | Chưa xác định kênh chuyển tiếp khi chatbot không trả lời được hoặc người dùng cần nhân viên. | Người dùng không biết nơi tiếp tục hỗ trợ. | Business xác định hotline/quầy/kênh hỗ trợ; hiện chỉ yêu cầu thông báo giới hạn. |
| ISS-09 | Chưa chốt yêu cầu đăng nhập khi bấm `/booking/<screening_id>`. | Trải nghiệm redirect và thông báo có thể không thống nhất. | Giữ nguyên quy tắc hệ thống lõi; UX cần xác nhận thông điệp, không cho chatbot vượt quyền. |
| ISS-10 | Chưa chốt cơ chế kiểm chứng output giữa backend và model. | Model có thể thay đổi số liệu/ID dù context đúng. | Thiết kế sau Bước 2 phải ưu tiên output có cấu trúc và validator backend; không coi prompt là kiểm soát đủ. |
| ISS-11 | Chưa chốt logging/audit tối thiểu cho câu hỏi và nguồn dữ liệu. | Khó điều tra hallucination hoặc vi phạm riêng tư. | Security/Privacy quy định log đã khử dữ liệu, retention và quyền truy cập trước triển khai. |
| ISS-12 | Chưa chốt ngưỡng timeout, retry, quota và fallback khi Gemini lỗi. | Trải nghiệm không ổn định hoặc retry gây tải/chi phí không kiểm soát. | Platform/Backend định nghĩa NFR vận hành sau khi chọn model/provider. |

## 3. Các điều không được coi là giả định đã duyệt

- Không suy ra chính sách hoàn tiền từ yêu cầu “hủy trước 60 phút”; tài liệu nền chỉ xác định thời điểm hủy, chưa xác định hoàn tiền/phí.
- Không suy ra giá cụ thể từ loại ghế hoặc khung giờ nếu chưa có nguồn giá chính thức.
- Không coi câu trả lời của Gemini là dữ liệu rạp, kể cả khi model trả lời tự tin.
- Không tự thêm tính năng bán bắp nước, đặt nhóm, thông báo SMS/email hoặc lịch sử hội thoại ngoài phạm vi đã duyệt.
- Không thay đổi route đặt vé hiện có; mapping chính thức cho card là `/booking/<screening_id>`.

## 4. Checklist Human Gate cho đầu ra Bước 2

- [ ] CB-FR bao phủ việc Chatbot được làm và không được làm.
- [ ] CB-NFR/constraint bảo vệ khóa Gemini, dữ liệu riêng tư, SQL và giao dịch lõi.
- [ ] Nguồn dữ liệu gồm `movies`, `screenings`, `seats`, `tickets`, `seat_holds` và quy tắc đối chiếu.
- [ ] Điều kiện từ chối gồm ngoài phạm vi, thiếu dữ liệu, nguồn lỗi, yêu cầu giao dịch và yêu cầu bí mật.
- [ ] Anti-hallucination AC kiểm tra cả text, số ghế, giá, chính sách, `screening_id` và link đặt vé.
- [ ] Các điểm chưa rõ được tách thành issue, không bị biến thành quy tắc nghiệp vụ ngầm.
- [ ] Không có source code, schema mới hoặc thiết kế architecture trong các tài liệu Bước 2.

**Điểm dừng:** Sau khi Human Gate duyệt bộ tài liệu requirements này, mới nhận lệnh chuyển sang bước thiết kế tiếp theo.