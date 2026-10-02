# Cấu hình Groq cho chatbot

Chatbot sử dụng Groq Chat Completions API. Tên module `gemini_service.py`, class
`GeminiService`, alias `generate` và hàm `generate_response(prompt)` được giữ
nguyên để tương thích với luồng RAG/API/UI hiện tại; implementation không còn
gọi Google Gemini.

## Cài đặt và cấu hình

Từ thư mục gốc repository, chạy `python -m pip install -r requirements.txt`.
Thêm vào file `.env` phía server (không commit hoặc gửi khóa lên trình duyệt):

```dotenv
GROQ_API_KEY=your-groq-api-key
GROQ_MODEL=llama-3.1-8b-instant
```

`GROQ_MODEL` là tùy chọn; mặc định là `llama-3.1-8b-instant`. Có thể
thay bằng model khác mà tài khoản Groq của bạn có quyền sử dụng. Khởi động
lại Flask sau khi đổi `.env`.
App factory đã gọi `load_dotenv()`; script độc lập phải gọi `load_dotenv()`
trước khi tạo service hoặc cung cấp biến môi trường trực tiếp.

## Giới hạn và fallback

- SDK timeout: 15 giây; timeout nhỏ hơn vẫn được hỗ trợ.
- `max_retries=0`: không retry tự động gây tăng quota/độ trễ.
- `max_tokens=800`: giới hạn output theo hợp đồng gọi Groq.
- Thiếu key/model trả thông báo cấu hình an toàn; lỗi mạng, timeout, quota,
  authentication hoặc output rỗng trả fallback tiếng Việt chung.
- Log chẩn đoán chỉ ghi loại lỗi và chi tiết đã che key/prompt.
- SDK timeout là timeout HTTP (connect/read/write/pool), không phải bộ đếm
  wall-clock toàn bộ luồng RAG. Không khẳng định toàn bộ endpoint kết thúc đúng
  15 giây trong mọi trường hợp.

`google-generativeai` và các biến `GEMINI_*` không còn là dependency/cấu hình
thực thi. Cả chatbot và chức năng tạo mô tả phim quản trị đều đi qua gateway
Groq này.

Unit tests mock SDK, không gọi API thật và không tiêu thụ quota. Cần kiểm tra
credit/quyền truy cập model trong Groq Console trước khi dùng thực tế.