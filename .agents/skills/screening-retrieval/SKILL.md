---
name: screening-retrieval
description: Convert structured intent into safe, parameterized SQL queries to retrieve movies, showtimes, and real-time seat availability.
---

# Screening Retrieval Skill

## Objective
Chuyển đổi Structured Intent JSON thành câu truy vấn SQL an toàn để lấy danh sách phim, suất chiếu và số ghế trống thực tế từ CSDL.

## Input:
Structured intent JSON

## Process:
1. Xây dựng parameterized SQL query (tuyệt đối không nối chuỗi).
2. Lọc theo phim/thể loại (movie_title, genre).
3. Lọc theo ngày và khung giờ (date, min_time, max_time).
4. Tính toán số ghế trống theo từng loại: STANDARD, VIP, COUPLE (loại trừ vé BOOKED/USED và seat_holds còn hạn).
5. Sắp xếp theo giờ chiếu tăng dần.
6. Giới hạn số lượng kết quả (limit = 5).

## Rules:
- Không sử dụng SQL string concatenation (chống SQL Injection).
- Phải sử dụng parameterized query.
- Không truy xuất toàn bộ database.
- Không gửi toàn bộ database cho Gemini.
- Nếu không có kết quả phù hợp -> trả về danh sách rỗng (empty result).

---