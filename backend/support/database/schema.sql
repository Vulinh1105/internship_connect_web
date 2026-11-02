-- Internship Connect: lược đồ cơ sở dữ liệu MySQL dùng chung cho cả nhóm.
-- Chạy file này trước, rồi chạy seed.sql để có dữ liệu mẫu.
-- Thứ tự tạo bảng: users -> students... -> companies... -> interviews (bảng có khóa ngoại tạo sau).

CREATE DATABASE IF NOT EXISTS internship_connect
    CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE internship_connect;

-- ===================== M20: Tài khoản =====================
CREATE TABLE IF NOT EXISTS users (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    email         VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role          VARCHAR(20)  NOT NULL,            -- student | company | staff | admin
    is_active     BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ===================== M03: Sinh viên =====================
CREATE TABLE IF NOT EXISTS students (
    id                INT AUTO_INCREMENT PRIMARY KEY,
    user_id           INT NOT NULL UNIQUE,
    student_code      VARCHAR(20) UNIQUE,
    full_name         VARCHAR(255) NOT NULL,
    major             VARCHAR(255),
    gpa               DECIMAL(4,2),
    phone             VARCHAR(20),
    profile_summary   TEXT,
    internship_status VARCHAR(20) NOT NULL DEFAULT 'not_started', -- not_started | searching | interning | completed
    FOREIGN KEY (user_id) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS student_skills (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    skill_name VARCHAR(100) NOT NULL,
    UNIQUE (student_id, skill_name),
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS student_cvs (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    student_id  INT NOT NULL,
    file_name   VARCHAR(255) NOT NULL,
    file_path   VARCHAR(500) NOT NULL,
    is_primary  BOOLEAN  NOT NULL DEFAULT FALSE,
    uploaded_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ===================== M13: Doanh nghiệp và thực tập =====================
CREATE TABLE IF NOT EXISTS companies (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    user_id      INT NOT NULL UNIQUE,
    company_name VARCHAR(255) NOT NULL,
    description  TEXT,
    address      VARCHAR(255),
    website      VARCHAR(255),
    FOREIGN KEY (user_id) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS internships (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    company_id   INT NOT NULL,
    title        VARCHAR(255) NOT NULL,
    description  TEXT,
    requirements TEXT,
    location     VARCHAR(255),
    deadline     DATE,
    status       VARCHAR(20) NOT NULL DEFAULT 'open',  -- open | closed
    created_at   DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_internships_status_deadline (status, deadline),
    FOREIGN KEY (company_id) REFERENCES companies(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS applications (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    internship_id INT NOT NULL,
    student_id    INT NOT NULL,
    cv_id         INT NULL,
    cover_letter  TEXT,
    status        VARCHAR(20) NOT NULL DEFAULT 'pending', -- pending | reviewing | accepted | rejected | withdrawn
    applied_at    DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (internship_id, student_id),                   -- mỗi sinh viên chỉ ứng tuyển 1 lần/vị trí
    INDEX idx_applications_student (student_id),
    FOREIGN KEY (internship_id) REFERENCES internships(id),
    FOREIGN KEY (student_id)    REFERENCES students(id),
    FOREIGN KEY (cv_id)         REFERENCES student_cvs(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ===================== Lịch phỏng vấn =====================
CREATE TABLE IF NOT EXISTS interviews (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    application_id  INT NOT NULL,
    scheduled_at    DATETIME     NOT NULL,
    location        VARCHAR(255) NOT NULL,
    note            TEXT,
    status          VARCHAR(20)  NOT NULL DEFAULT 'invited', -- invited | confirmed | declined | reschedule_requested | cancelled
    student_message TEXT,
    created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (application_id) REFERENCES applications(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
