---
name: question-analysis
description: Analyze natural-language user questions about movies, showtimes, seats, and policies, and extract structured intent JSON.
---

# Question Analysis Skill

## Objective
Phân tích câu hỏi bằng ngôn ngữ tự nhiên của khách hàng về rạp chiếu phim thành dữ liệu có cấu trúc (Structured Intent JSON) để phục vụ việc truy xuất cơ sở dữ liệu.

## Input:
Natural language question

## Output:
Structured intent (JSON)

## Required fields:
- intent
- movie_title
- genre
- date
- min_time
- max_time
- time_of_day
- seat_type
- price_inquiry
- policy_inquiry
- keywords

## Rules:
- Không tự tạo tên phim hoặc thể loại không xuất hiện trong câu hỏi.
- Không tự suy đoán ngày hoặc khung giờ nếu người dùng không đưa ra.
- Chuẩn hóa ngày ("hôm nay", "tối nay", "ngày mai") về định dạng YYYY-MM-DD theo giờ Asia/Ho_Chi_Minh.
- "tối nay" → date = <hôm nay>, time_of_day = "EVENING" (sau 18:00).
- "sau 19h" → min_time = "19:00".
- "buổi sáng" → time_of_day = "MORNING" (08:00 - 11:59).
- "buổi chiều" → time_of_day = "AFTERNOON" (12:00 - 17:59).
- "ghế VIP", "ghế đôi", "ghế thường" → seat_type = "VIP" | "COUPLE" | "STANDARD".
- Nếu người dùng hỏi giá vé, bật cờ price_inquiry = true.
- Nếu người dùng hỏi hủy vé/hoàn tiền, bật cờ policy_inquiry = true.
- Nếu câu hỏi không đủ thông tin hoặc nằm ngoài phạm vi rạp, trả về intent = "UNKNOWN" hoặc "AMBIGUOUS".

---