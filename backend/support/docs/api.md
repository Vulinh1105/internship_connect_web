# API đang dùng trong web

Swagger: http://localhost:8000/docs. Endpoint yêu cầu đăng nhập nhận `Authorization: Bearer <token>`.

| Nhóm | Chức năng |
| --- | --- |
| `/api/auth` | Register, login, me, verify; admin xem users và khóa/mở tài khoản |
| `/api/students` | Staff/admin xem danh sách phân trang; sinh viên quản lý me, skills, CV và download CV của mình |
| `/api/companies` | Danh sách/chi tiết công khai; doanh nghiệp tạo/cập nhật me |
| `/api/internships` | Danh sách/chi tiết công khai, tìm kiếm; doanh nghiệp tạo/cập nhật/đóng tin, xem ứng viên; staff/admin xem stats |
| `/api/applications` | Sinh viên xem/rút đơn; doanh nghiệp xét duyệt và tải CV theo quyền hiện có |
| `/api/interviews` | Mời, cập nhật, hủy, xem lịch cá nhân, phản hồi xác nhận/đổi lịch/từ chối |
| `/api/documents` | Staff/admin upload/list/detail/download/index/delete tài liệu kiến thức dùng chung |
| `/api/ai/status` | Người đăng nhập xem provider, tên model và cờ đã cấu hình; không trả key |
| `/api/ai/recommendations?top_k=5` | Sinh viên nhận matching theo hồ sơ |
| `/api/ai/chat` | POST `{ "question": "..." }`; trả answer/mode/sources, session lấy từ user |
| `/api/ai/agent` | POST message và tool: ask_knowledge hoặc recommend_internships |
| `/api/ai/reindex` | Staff/admin dựng lại index matching và index lại document đã đăng ký |

Upload tài liệu và lập chỉ mục là hai thao tác riêng. HTTP 201 upload chưa đồng nghĩa có thể tìm kiếm trong chatbot. Kết quả index trả status/chunk_count/error; metadata trạng thái được lưu trong DB.

Frontend không truy cập OpenAI trực tiếp. Một OPENAI_API_KEY nằm trong .env phía server phục vụ tất cả lời gọi AI. Khi thiếu key, API trả lỗi 503 dễ nhận biết; status chỉ trả configured=false.
