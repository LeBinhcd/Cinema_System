CREATE DATABASE IF NOT EXISTS cinema_system CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE cinema_system;

CREATE TABLE users (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  full_name VARCHAR(150) NOT NULL,
  phone VARCHAR(20) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  role ENUM('CUSTOMER','STAFF','ADMIN') NOT NULL DEFAULT 'CUSTOMER',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE movies (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  title VARCHAR(255) NOT NULL,
  duration_minutes SMALLINT UNSIGNED NOT NULL,
  age_rating VARCHAR(20) NULL,
  synopsis VARCHAR(500) NULL,
  keywords VARCHAR(500) NULL,
  metadata_json JSON NULL,
  status ENUM('SHOWING','COMING_SOON','ENDED') NOT NULL DEFAULT 'COMING_SOON',
  release_date DATE NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT chk_movie_duration CHECK (duration_minutes > 0),
  INDEX ix_movies_title (title),
  INDEX ix_movies_status_release (status, release_date)
) ENGINE=InnoDB;

CREATE TABLE genres (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100) NOT NULL UNIQUE
) ENGINE=InnoDB;

CREATE TABLE movie_genres (
  movie_id BIGINT UNSIGNED NOT NULL,
  genre_id BIGINT UNSIGNED NOT NULL,
  PRIMARY KEY (movie_id, genre_id),
  CONSTRAINT fk_movie_genres_movie FOREIGN KEY (movie_id) REFERENCES movies(id),
  CONSTRAINT fk_movie_genres_genre FOREIGN KEY (genre_id) REFERENCES genres(id),
  INDEX ix_movie_genres_genre (genre_id, movie_id)
) ENGINE=InnoDB;

CREATE TABLE screening_rooms (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100) NOT NULL UNIQUE,
  row_count SMALLINT UNSIGNED NOT NULL,
  column_count SMALLINT UNSIGNED NOT NULL,
  CONSTRAINT chk_room_dimensions CHECK (row_count > 0 AND column_count > 0)
) ENGINE=InnoDB;

CREATE TABLE seats (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  room_id BIGINT UNSIGNED NOT NULL,
  row_label VARCHAR(5) NOT NULL,
  seat_number SMALLINT UNSIGNED NOT NULL,
  seat_type ENUM('STANDARD','COUPLE','VIP') NOT NULL DEFAULT 'STANDARD',
  CONSTRAINT uq_room_seat UNIQUE (room_id, row_label, seat_number),
  CONSTRAINT fk_seats_room FOREIGN KEY (room_id) REFERENCES screening_rooms(id),
  CONSTRAINT chk_seat_number CHECK (seat_number > 0),
  INDEX ix_seats_room_type (room_id, seat_type)
) ENGINE=InnoDB;

CREATE TABLE screenings (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  movie_id BIGINT UNSIGNED NOT NULL,
  room_id BIGINT UNSIGNED NOT NULL,
  start_time DATETIME NOT NULL,
  end_time DATETIME NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_screenings_movie FOREIGN KEY (movie_id) REFERENCES movies(id),
  CONSTRAINT fk_screenings_room FOREIGN KEY (room_id) REFERENCES screening_rooms(id),
  CONSTRAINT chk_screening_time CHECK (end_time > start_time),
  INDEX ix_screenings_room_time (room_id, start_time, end_time),
  INDEX ix_screenings_start_movie (start_time, movie_id)
) ENGINE=InnoDB;

CREATE TABLE pricing_rules (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(120) NOT NULL,
  seat_type ENUM('STANDARD','COUPLE','VIP') NOT NULL,
  day_category ENUM('WEEKDAY','WEEKEND','HOLIDAY','ANY') NOT NULL DEFAULT 'ANY',
  start_hour TINYINT UNSIGNED NULL,
  end_hour TINYINT UNSIGNED NULL,
  base_price DECIMAL(10,2) NOT NULL,
  surcharge DECIMAL(10,2) NOT NULL DEFAULT 0.00,
  active BOOLEAN NOT NULL DEFAULT TRUE,
  CONSTRAINT chk_pricing_hours CHECK ((start_hour IS NULL AND end_hour IS NULL) OR (start_hour <= 23 AND end_hour <= 23)),
  CONSTRAINT chk_pricing_amounts CHECK (base_price >= 0 AND surcharge >= 0),
  INDEX ix_pricing_lookup (seat_type, day_category, active)
) ENGINE=InnoDB;

CREATE TABLE tickets (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  user_id BIGINT UNSIGNED NOT NULL,
  screening_id BIGINT UNSIGNED NOT NULL,
  seat_id BIGINT UNSIGNED NOT NULL,
  status ENUM('HELD','PAID','CANCELLED','CHECKED_IN') NOT NULL DEFAULT 'HELD',
  hold_expires_at DATETIME NULL,
  amount DECIMAL(10,2) NOT NULL,
  qr_code VARCHAR(255) NULL UNIQUE,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  cancelled_at DATETIME NULL,
  CONSTRAINT fk_tickets_user FOREIGN KEY (user_id) REFERENCES users(id),
  CONSTRAINT fk_tickets_screening FOREIGN KEY (screening_id) REFERENCES screenings(id),
  CONSTRAINT fk_tickets_seat FOREIGN KEY (seat_id) REFERENCES seats(id),
  CONSTRAINT chk_ticket_amount CHECK (amount >= 0),
  INDEX ix_tickets_seat_status (screening_id, seat_id, status, hold_expires_at),
  INDEX ix_tickets_user_created (user_id, created_at),
  INDEX ix_tickets_qr (qr_code)
) ENGINE=InnoDB;

CREATE TABLE payments (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  ticket_id BIGINT UNSIGNED NOT NULL,
  provider_name VARCHAR(100) NOT NULL,
  provider_reference VARCHAR(150) NOT NULL UNIQUE,
  status ENUM('PENDING','SUCCESS','FAILED','REFUNDED') NOT NULL DEFAULT 'PENDING',
  amount DECIMAL(10,2) NOT NULL,
  paid_at DATETIME NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_payments_ticket FOREIGN KEY (ticket_id) REFERENCES tickets(id),
  CONSTRAINT chk_payment_amount CHECK (amount >= 0),
  INDEX ix_payments_ticket_status (ticket_id, status),
  INDEX ix_payments_paid_at (paid_at)
) ENGINE=InnoDB;

CREATE TABLE ai_contents (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  movie_id BIGINT UNSIGNED NULL,
  content_type ENUM('MOVIE_DESCRIPTION','REVENUE_SUMMARY','MOVIE_RECOMMENDATION') NOT NULL,
  source_text TEXT NOT NULL,
  generated_text TEXT NOT NULL,
  status ENUM('DRAFT','EDITED','APPROVED','REJECTED') NOT NULL DEFAULT 'DRAFT',
  generated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  reviewed_by BIGINT UNSIGNED NULL,
  reviewed_at DATETIME NULL,
  CONSTRAINT fk_ai_movie FOREIGN KEY (movie_id) REFERENCES movies(id),
  CONSTRAINT fk_ai_reviewer FOREIGN KEY (reviewed_by) REFERENCES users(id),
  INDEX ix_ai_movie_type_status (movie_id, content_type, status)
) ENGINE=InnoDB;

CREATE TABLE revenue_summaries (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  period_type ENUM('DAY','WEEK','MONTH') NOT NULL,
  period_start DATE NOT NULL,
  period_end DATE NOT NULL,
  movie_id BIGINT UNSIGNED NULL,
  screening_id BIGINT UNSIGNED NULL,
  tickets_sold INT UNSIGNED NOT NULL DEFAULT 0,
  occupancy_rate DECIMAL(5,2) NOT NULL DEFAULT 0.00,
  revenue_amount DECIMAL(12,2) NOT NULL DEFAULT 0.00,
  ai_summary_id BIGINT UNSIGNED NULL,
  reviewed_by BIGINT UNSIGNED NULL,
  CONSTRAINT fk_summary_movie FOREIGN KEY (movie_id) REFERENCES movies(id),
  CONSTRAINT fk_summary_screening FOREIGN KEY (screening_id) REFERENCES screenings(id),
  CONSTRAINT fk_summary_ai FOREIGN KEY (ai_summary_id) REFERENCES ai_contents(id),
  CONSTRAINT fk_summary_reviewer FOREIGN KEY (reviewed_by) REFERENCES users(id),
  CONSTRAINT chk_summary_period CHECK (period_end >= period_start),
  CONSTRAINT chk_summary_occupancy CHECK (occupancy_rate >= 0 AND occupancy_rate <= 100),
  CONSTRAINT chk_summary_revenue CHECK (revenue_amount >= 0),
  INDEX ix_summary_period (period_type, period_start, period_end),
  INDEX ix_summary_movie (movie_id, period_start)
) ENGINE=InnoDB;