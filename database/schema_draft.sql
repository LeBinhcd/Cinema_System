-- Sơ đồ CSDL sơ bộ cho Hệ thống quản lý rạp chiếu phim có tích hợp AI.
CREATE DATABASE IF NOT EXISTS cinema_system CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE cinema_system;

CREATE TABLE users (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  full_name VARCHAR(150) NOT NULL,
  phone VARCHAR(20) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  role ENUM('CUSTOMER','STAFF','ADMIN') NOT NULL DEFAULT 'CUSTOMER',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE movies (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  title VARCHAR(255) NOT NULL,
  genre VARCHAR(100) NOT NULL,
  duration_minutes SMALLINT UNSIGNED NOT NULL,
  age_rating VARCHAR(20),
  description TEXT,
  status ENUM('SHOWING','COMING_SOON','ENDED') NOT NULL DEFAULT 'COMING_SOON',
  ai_description_status ENUM('DRAFT','APPROVED') NOT NULL DEFAULT 'DRAFT',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE screening_rooms (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100) NOT NULL UNIQUE,
  row_count SMALLINT UNSIGNED NOT NULL,
  column_count SMALLINT UNSIGNED NOT NULL
);

CREATE TABLE seats (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  room_id BIGINT UNSIGNED NOT NULL,
  row_label VARCHAR(5) NOT NULL,
  seat_number SMALLINT UNSIGNED NOT NULL,
  seat_type ENUM('STANDARD','COUPLE','VIP') NOT NULL DEFAULT 'STANDARD',
  UNIQUE KEY uq_room_seat (room_id, row_label, seat_number),
  FOREIGN KEY (room_id) REFERENCES screening_rooms(id)
);

CREATE TABLE screenings (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  movie_id BIGINT UNSIGNED NOT NULL,
  room_id BIGINT UNSIGNED NOT NULL,
  start_time DATETIME NOT NULL,
  end_time DATETIME NOT NULL,
  FOREIGN KEY (movie_id) REFERENCES movies(id),
  FOREIGN KEY (room_id) REFERENCES screening_rooms(id),
  INDEX ix_screening_time (room_id, start_time, end_time)
);

CREATE TABLE tickets (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  user_id BIGINT UNSIGNED NOT NULL,
  screening_id BIGINT UNSIGNED NOT NULL,
  seat_id BIGINT UNSIGNED NOT NULL,
  status ENUM('HELD','PAID','CANCELLED','CHECKED_IN') NOT NULL DEFAULT 'HELD',
  hold_expires_at DATETIME NULL,
  payment_reference VARCHAR(150) NULL,
  qr_code VARCHAR(255) NULL UNIQUE,
  amount DECIMAL(10,2) NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id),
  FOREIGN KEY (screening_id) REFERENCES screenings(id),
  FOREIGN KEY (seat_id) REFERENCES seats(id),
  INDEX ix_screening_seat_status (screening_id, seat_id, status)
);

-- Khi giữ ghế, khóa bản ghi seats tương ứng bằng SELECT ... FOR UPDATE trong
-- transaction và chỉ tạo vé nếu không tồn tại vé HELD chưa hết hạn, PAID hoặc
-- CHECKED_IN cho cùng (screening_id, seat_id). Vé CANCELLED được giữ làm lịch sử.
