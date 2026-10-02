# NHẬT KÝ PROMPT VÀ QUY TRÌNH TINH CHỈNH - BIỂU ĐỒ HOẠT ĐỘNG

> **Tính chất:** Kịch bản tương tác Người dùng – AI được mô phỏng để minh họa quá trình thiết kế; không phải bản ghi hội thoại lịch sử. Đối chiếu `docs/SRS.md` (bản nội dung GD3) mục UC06/UC08, `docs/requirement-analysis/requirement-analysis.md` và `.agents/activity-diagram/SKILL.md`.

## 📌 BƯỚC 1: PROMPT KHỞI TẠO SKILL

> **User Prompt:**
> "Hãy đóng vai System Architect. Viết `.agents/activity-diagram/SKILL.md` hướng dẫn AI sinh Activity Diagram bằng PlantUML cho UC01–UC13 từ tài liệu GD3. Bắt buộc có `@startuml`, `@enduml`, tiêu đề UC/FR, `start`, `stop`, nhánh `if ... then ... else ... endif` cho luồng chính và ngoại lệ; thêm `note bottom` trước `stop` để ghi rõ baseline và các quy tắc chưa xác nhận. Không suy diễn nghiệp vụ ngoài tài liệu."

---

## 📌 BƯỚC 2: PROMPT SINH TÀI LIỆU/SƠ ĐỒ (LẦN 1)

> **User Prompt:**
> "Sử dụng `.agents/activity-diagram/SKILL.md` và đối chiếu mục UC06 của GD3 (`docs/SRS.md`). Vẽ PlantUML Activity Diagram `UC06_Đặt giữ chỗ trực tuyến (AI gợi ý phim)` theo FR-06: AI gợi ý 2–3 phim có suất còn ghế, khách chọn ghế và giữ chỗ tối đa 5 phút trước khi chuyển sang UC08. Thể hiện cả ghế đã bị người khác giữ và trường hợp quá hạn; không phát hành vé chỉ nhờ giữ ghế."

**Đầu ra lần 1 (mô phỏng):** AI chỉ vẽ đường thành công `chọn ghế → HELD → chuyển sang thanh toán`, không diễn tả rõ khi đồng hồ giữ ghế hết hạn.

---

## 📌 BƯỚC 3: ĐÁNH GIÁ & PHÁT HIỆN LỖI (AI CHECK)

- ❌ **Điểm chưa ổn 1:** Thiếu nhánh `if ... else` riêng cho thời điểm **hết 5 phút** mà chưa có thanh toán xác thực; ghế bị giữ vô thời hạn thay vì trở về Trống.
- ❌ **Điểm chưa ổn 2:** Thiếu `note bottom` ghi baseline FR-06: HELD tối đa 5 phút, chưa phải vé; việc phát hành vé thuộc UC08 sau thanh toán thành công.
- ❌ **Điểm chưa ổn 3:** Chưa tách trường hợp ghế bận do đặt đồng thời và chưa nhấn mạnh gợi ý AI chỉ lấy phim/suất còn ghế từ dữ liệu thực tế (NFR-02, NFR-04).

---

## 📌 BƯỚC 4: PROMPT YÊU CẦU SỬA ĐỔI & BỔ SUNG

> **User Prompt:**
> "Hãy sửa UC06 dựa trên các lỗi ở Bước 3. Thêm `if ... else` kiểm tra ghế còn trống trước khi giữ và một `if ... else` sau khi bắt đầu đếm 5 phút: nếu chưa hết hạn thì chuyển sang UC08; nếu hết hạn mà chưa có kết quả thanh toán đã xác thực thì giải phóng HELD → Trống và báo khách chọn lại. Thêm `note bottom` trước `stop`, ghi rõ ràng buộc baseline và phần chưa xác nhận; AI chỉ gợi ý 2–3 phim từ suất còn ghế. Giữ cú pháp PlantUML hợp lệ, không thêm nghiệp vụ thanh toán tại quầy."

---

## 📌 BƯỚC 5: KẾT QUẢ CHỐT CUỐI CÙNG (FINAL OUTPUT)

**UC06 / FR-06 — Activity Diagram (PlantUML):**

```plantuml
@startuml
title UC06 - Hoạt động: Đặt giữ chỗ trực tuyến (AI gợi ý phim) [FR-06]

start
:Khách hàng xem phim và suất chiếu;
:Phân hệ AI gợi ý 2-3 phim từ dữ liệu phim/suất còn ghế;
:Khách hàng chọn suất và ghế;
:Hệ thống kiểm tra suất còn mở bán và trạng thái ghế;

if (Suất còn bán và ghế Trống?) then (Có)
  :Khóa ghế nguyên tử; tạo đơn giữ chỗ HELD;
  :Bắt đầu đếm 5 phút (300 giây);
  if (Còn trong thời hạn giữ ghế?) then (Có)
    :Chuyển sang UC08 để thanh toán online;
    :Chỉ xác nhận ghế sau khi UC08 xác thực thanh toán;
  else (Không)
    :Hủy giữ chỗ chưa thanh toán;
    :Trả ghế HELD về Trống;
    :Thông báo hết hạn và yêu cầu chọn lại;
  endif
else (Không)
  :Từ chối giữ ghế bận hoặc suất đã khóa bán;
  :Thông báo khách chọn suất/ghế khác;
endif

note bottom
Theo baseline UC06/FR-06: HELD tối đa 5 phút, chưa phải vé;
AI chỉ gợi ý phim/suất có dữ liệu ghế trống, khách tự quyết định.
UC08 chỉ cấp vé QR sau thanh toán thành công đã xác thực.
Chưa xác nhận: cách xử lý kết quả thanh toán đến trễ sau khi hết hạn;
phải đối soát, không suy đoán đã bán ghế.
Thanh toán tại quầy và in vé giấy nằm ngoài baseline đang áp dụng.
end note

stop
@enduml
```

**Điểm chốt:** Có nhánh hết hạn/ghế bận, `note bottom` ghi baseline và không biến giữ chỗ thành vé.
