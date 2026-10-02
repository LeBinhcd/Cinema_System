---
name: database-design
description: Design normalized MySQL database schemas from approved requirements and architecture while ensuring proper constraints, foreign keys, indexes, and chatbot retrieval support.
---
# Database Design Skill
## Objective
Transform approved requirements and architecture into an optimized, normalized relational database schema.
## Inputs
Read:
- docs/requirements.md
- docs/architecture.md
Only use approved requirements.
## Process
1. Identify entities (Phim, Thể loại, Phòng chiếu, Ghế, Suất chiếu, Khách hàng, Vé, Thanh toán, User quản trị).
2. Define relationships (1-1, 1-N, N-N).
3. Apply normalization (Ít nhất dạng chuẩn 3NF).
4. Define Primary Keys (PK) and Foreign Keys (FK).
5. Define constraints (NOT NULL, UNIQUE, CHECK).
6. Define strategic indexes for fast searching (e.g., searching movies by title/genre, filtering showtimes by date, checking seat availability).
7. Ensure data types support chatbot retrieval requirements (storing movie synopses and metadata for RAG queries).
8. Generate SQL schema script.
## Rules
- Do not implement Flask source code.
- Do not modify approved requirements or architecture.
- Use proper SQL syntax for MySQL.
- Avoid cascading deletes where it can cause accidental data loss for financial/ticketing records.
## Outputs
Create:
- docs/database-design.md
- database/schema.sql
## Verification & Human Gate 3
Verify that all entities mapped from Use Cases (UC01 to UC13) are fully supported by the database schema.
Sau khi tạo xong các tệp, bắt buộc phải DỪNG LẠI và in ra biểu mẫu Human Gate 3 để chờ phê duyệt.