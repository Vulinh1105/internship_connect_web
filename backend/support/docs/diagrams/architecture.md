# Kiến trúc hệ thống

Một ứng dụng FastAPI duy nhất, chia module bên trong, dùng chung một database MySQL.

```mermaid
flowchart TB
    U["Người dùng: Sinh viên · Doanh nghiệp · Nhà trường · Quản trị"]
    FE["Frontend HTML/CSS/JS"]
    subgraph APP["FastAPI (một tiến trình, cổng 8000)"]
        direction TB
        CORE["core: config · database · security (JWT) · dependencies"]
        AUTH["M20 auth"]
        STU["M03 students"]
        INT["M13 internships"]
        IVW["interviews"]
        AI["ai: matching · rag · agent"]
        INT -- "gọi hàm" --> STU
        IVW -- "gọi hàm" --> INT
        AI -- "gọi hàm" --> STU
        AI -- "gọi hàm" --> INT
    end
    DB[("MySQL internship_connect")]
    QD[("Qdrant local")]
    U --> FE -- "HTTP + JSON + JWT" --> APP
    APP --> DB
    AI --> QD
```

**Luồng sinh viên ứng tuyển:** đăng nhập (M20 trả JWT) → gửi yêu cầu ứng tuyển → `get_current_user` xác định người dùng và vai trò → M13 gọi `students.service` lấy hồ sơ → kiểm tra tin còn mở, còn hạn, chưa ứng tuyển → lưu đơn `pending` → sinh viên xem trạng thái ở `/api/applications/me`.

**Quy tắc phụ thuộc:** module ưu tiên gọi hàm trong `service.py` của module khác (ví dụ `students.service.get_student_by_user_id`) thay vì tự truy vấn bảng của họ. Ngoại lệ hiện có: `interviews` và `ai` đọc trực tiếp model của M13 (`Application`, `Internship`) để join và lập chỉ mục, chỉ đọc, không ghi.
