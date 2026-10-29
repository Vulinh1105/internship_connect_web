# Thiết kế cơ sở dữ liệu

Một database MySQL `internship_connect`, charset `utf8mb4`. Script tạo bảng: `database/schema.sql`. Dữ liệu mẫu: `database/seed.sql`.

## Quy ước

- Tên bảng và cột `snake_case`; bảng số nhiều. Khóa chính `id INT AUTO_INCREMENT`.
- Khóa ngoại đặt tên `<bảng số ít>_id`.
- Thời điểm tạo lưu giờ UTC. Giờ phỏng vấn (`interviews.scheduled_at`) lưu đúng giờ người dùng nhập.
- Giá trị trạng thái là chữ thường tiếng Anh, lưu `VARCHAR(20)`; việc kiểm tra giá trị hợp lệ do tầng ứng dụng đảm nhiệm.

## Các bảng

| Bảng | Module | Cột chính | Ràng buộc |
|---|---|---|---|
| `users` | M20 | `email`, `password_hash`, `role`, `is_active`, `created_at` | `email` UNIQUE |
| `students` | M03 | `user_id`, `student_code`, `full_name`, `major`, `gpa DECIMAL(4,2)`, `phone`, `profile_summary`, `internship_status` | `user_id` UNIQUE, FK `users`; `student_code` UNIQUE |
| `student_skills` | M03 | `student_id`, `skill_name` | UNIQUE (`student_id`, `skill_name`), FK `students` |
| `student_cvs` | M03 | `student_id`, `file_name`, `file_path`, `is_primary`, `uploaded_at` | FK `students` |
| `companies` | M13 | `user_id`, `company_name`, `description`, `address`, `website` | `user_id` UNIQUE, FK `users` |
| `internships` | M13 | `company_id`, `title`, `description`, `requirements`, `location`, `deadline`, `status`, `created_at` | FK `companies`; chỉ mục (`status`, `deadline`) |
| `applications` | M13 | `internship_id`, `student_id`, `cv_id`, `cover_letter`, `status`, `applied_at` | UNIQUE (`internship_id`, `student_id`); FK `internships`, `students`, `student_cvs` |
| `interviews` | Phỏng vấn | `application_id`, `scheduled_at`, `location`, `note`, `status`, `student_message`, `created_at` | FK `applications` |

`GPA` dùng `DECIMAL(4,2)` (tối đa 99.99) để chứa được cả thang 4 lẫn thang 10.

## Thứ tự tạo và nạp dữ liệu

`users` → `students`, `student_skills`, `student_cvs` → `companies`, `internships` → `applications` → `interviews`.

## Quy ước ID của dữ liệu mẫu

| `users.id` | Vai trò |
|---|---|
| 1 | admin |
| 2 | staff |
| 3 – 12 | student (`students.id` 1 – 10) |
| 13 – 17 | company (`companies.id` 1 – 5) |

Sơ đồ quan hệ: xem `diagrams/erd.md`.
