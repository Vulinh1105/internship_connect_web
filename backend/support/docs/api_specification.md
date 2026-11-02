# Đặc tả API

Tài liệu này liệt kê endpoint của backend. Xem thêm và thử trực tiếp tại `http://localhost:8000/docs` (Swagger UI).

## Quy ước chung

- Tiền tố `/api`, dữ liệu JSON, tên trường `snake_case`.
- Xác thực: header `Authorization: Bearer <access_token>` (token lấy từ `/api/auth/login`).
- Vai trò lấy từ cơ sở dữ liệu theo tài khoản trong token, không tin dữ liệu client gửi lên. Danh tính sinh viên khi ứng tuyển cũng lấy từ token.
- Danh sách phân trang: `?page=1&page_size=20` (tối đa 100), trả về `{"items": [], "total": 0, "page": 1, "page_size": 20}`.
- Lỗi: `{"detail": "thông báo"}`.

| Mã | Ý nghĩa |
|---|---|
| 200 / 201 / 204 | Thành công / đã tạo / thành công không có nội dung |
| 400 | Dữ liệu hợp lệ về cú pháp nhưng sai nghiệp vụ (ví dụ vị trí đã đóng) |
| 401 | Chưa đăng nhập, token sai hoặc hết hạn |
| 403 | Không đủ quyền hoặc không phải chủ dữ liệu |
| 404 | Không tìm thấy |
| 409 | Xung đột (email trùng, đã ứng tuyển, chuyển trạng thái không hợp lệ) |
| 413 | File quá lớn |
| 422 | Dữ liệu đầu vào không qua kiểm tra |

## Trạng thái

- Đơn ứng tuyển: `pending` → `reviewing` → `accepted` / `rejected`; `pending` có thể sang thẳng `accepted` / `rejected`; sinh viên rút → `withdrawn` (chỉ khi `pending` hoặc `reviewing`). `accepted`, `rejected`, `withdrawn` là trạng thái cuối.
- Tin thực tập: `open`, `closed`. Danh sách công khai chỉ hiện tin `open` và chưa quá hạn.
- Lịch phỏng vấn: `invited` → `confirmed` / `declined` / `reschedule_requested`; doanh nghiệp có thể `cancelled` hoặc đổi lịch (về lại `invited`).
- Tình trạng thực tập của sinh viên: `not_started`, `searching`, `interning`, `completed`.


## Hệ thống

| Method | Endpoint | Quyền | Chức năng |
|---|---|---|---|
| GET | `/health` | công khai | Kiểm tra server |

## M20 - Auth

| Method | Endpoint | Quyền | Chức năng |
|---|---|---|---|
| POST | `/api/auth/register` | công khai | Đăng ký (role: student hoặc company) |
| POST | `/api/auth/login` | công khai | Đăng nhập, nhận JWT |
| GET | `/api/auth/me` | đã đăng nhập | Thông tin tài khoản hiện tại |
| POST | `/api/auth/verify` | công khai | Kiểm tra token còn hiệu lực (nội bộ) |
| GET | `/api/auth/users` | admin | Danh sách tài khoản (phân trang) |
| PATCH | `/api/auth/users/3/active` | admin | Khóa/mở tài khoản |

## M03 - Sinh viên

| Method | Endpoint | Quyền | Chức năng |
|---|---|---|---|
| GET | `/api/students/me` | student | Lấy hồ sơ của mình |
| PUT | `/api/students/me` | student | Tạo hoặc cập nhật hồ sơ (lần đầu cần full_name) |
| POST | `/api/students/me/skills` | student | Thêm kỹ năng |
| DELETE | `/api/students/me/skills/1` | student | Xóa kỹ năng |
| GET | `/api/students/me/cvs` | student | Danh sách CV |
| POST | `/api/students/me/cvs` | student | Tải CV lên (multipart, field `file`, PDF/DOC/DOCX ≤ 5MB) |
| PUT | `/api/students/me/cvs/1/primary` | student | Đặt CV chính |
| GET | `/api/students/1` | chủ hồ sơ, staff, admin | Xem hồ sơ theo id |
| GET | `/api/students/1/skills` | chủ hồ sơ, staff, admin | Kỹ năng của sinh viên |

## M13 - Doanh nghiệp

| Method | Endpoint | Quyền | Chức năng |
|---|---|---|---|
| POST | `/api/companies` | company | Tạo hồ sơ doanh nghiệp (mỗi tài khoản một hồ sơ) |
| GET | `/api/companies` | công khai | Danh sách doanh nghiệp (phân trang) |
| GET | `/api/companies/me` | company | Hồ sơ doanh nghiệp của mình |
| PUT | `/api/companies/me` | company | Cập nhật hồ sơ doanh nghiệp |
| GET | `/api/companies/1` | công khai | Chi tiết doanh nghiệp |

## M13 - Thực tập

| Method | Endpoint | Quyền | Chức năng |
|---|---|---|---|
| POST | `/api/internships` | company | Đăng tin thực tập |
| GET | `/api/internships` | công khai | Tìm kiếm vị trí đang mở và còn hạn |
| GET | `/api/internships/mine` | company | Tin của doanh nghiệp mình (kể cả đã đóng) |
| GET | `/api/internships/stats` | staff, admin | Thống kê tin và đơn ứng tuyển |
| GET | `/api/internships/1` | công khai | Chi tiết vị trí |
| PUT | `/api/internships/1` | company (chủ tin) | Sửa tin |
| POST | `/api/internships/1/close` | company (chủ tin) | Đóng tin |

## M13 - Ứng tuyển

| Method | Endpoint | Quyền | Chức năng |
|---|---|---|---|
| POST | `/api/internships/1/applications` | student | Ứng tuyển (danh tính lấy từ JWT) |
| GET | `/api/internships/1/applications` | company (chủ tin), staff, admin | Danh sách ứng viên của một vị trí |
| GET | `/api/applications/me` | student | Đơn ứng tuyển của mình |
| GET | `/api/applications/1` | student (chủ đơn), company (chủ tin), staff, admin | Chi tiết đơn |
| PATCH | `/api/applications/1/status` | company (chủ tin) | Cập nhật trạng thái: reviewing, accepted, rejected |
| POST | `/api/applications/1/withdraw` | student (chủ đơn) | Rút hồ sơ (khi pending hoặc reviewing) |
| GET | `/api/applications/1/cv` | student (chủ đơn), company (chủ tin), staff, admin | Tải CV đính kèm đơn |

## Phỏng vấn

| Method | Endpoint | Quyền | Chức năng |
|---|---|---|---|
| POST | `/api/interviews` | company | Mời phỏng vấn |
| GET | `/api/interviews/me` | student, company, staff, admin | Lịch phỏng vấn của mình |
| PATCH | `/api/interviews/1` | company | Đổi lịch (sinh viên phải xác nhận lại) |
| POST | `/api/interviews/1/cancel` | company | Hủy lịch |
| POST | `/api/interviews/1/respond` | student | Phản hồi: confirm, decline, reschedule |

## AI

| Method | Endpoint | Quyền | Chức năng |
|---|---|---|---|
| GET | `/api/ai/recommendations` | student | Gợi ý vị trí phù hợp (AI1) |
| POST | `/api/ai/chat` | đã đăng nhập | Chatbot hỏi đáp (AI2, RAG) |
| POST | `/api/ai/agent` | đã đăng nhập | Agent chọn tool gợi ý hoặc hỏi đáp |
| POST | `/api/ai/reindex` | staff, admin | Dựng lại chỉ mục vector |

## Ví dụ: ứng tuyển

```http
POST /api/internships/15/applications
Authorization: Bearer <access_token>
Content-Type: application/json

{"cover_letter": "Em mong muốn ứng tuyển vị trí Python Backend Intern.", "cv_id": null}
```

Phản hồi `201 Created`:

```json
{
  "id": 101,
  "internship_id": 15,
  "student_id": 12,
  "cv_id": null,
  "cover_letter": "Em mong muốn ứng tuyển vị trí Python Backend Intern.",
  "status": "pending",
  "applied_at": "2026-10-29T08:00:00"
}
```
