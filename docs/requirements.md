# Yêu cầu hệ thống

## Đối tượng sử dụng

| Vai trò | Mô tả | Quyền chính |
|---|---|---|
| `student` | Sinh viên | Quản lý hồ sơ, kỹ năng, CV; tìm và ứng tuyển; theo dõi, rút đơn; phản hồi lịch phỏng vấn; xem gợi ý; hỏi chatbot |
| `company` | Đại diện doanh nghiệp | Quản lý hồ sơ công ty; đăng, sửa, đóng tin; xem ứng viên và CV; cập nhật trạng thái; mời phỏng vấn |
| `staff` | Cán bộ nhà trường | Xem hồ sơ sinh viên, ứng viên theo tin, thống kê |
| `admin` | Quản trị viên | Toàn bộ quyền của staff, quản lý tài khoản |

## Yêu cầu chức năng

1. Đăng ký, đăng nhập, xác thực JWT, phân quyền theo vai trò (M20).
2. Quản lý hồ sơ sinh viên, kỹ năng, CV, tình trạng thực tập (M03).
3. Quản lý hồ sơ doanh nghiệp (M13).
4. Đăng tin, sửa, đóng tin thực tập; tìm kiếm theo từ khóa và địa điểm, có phân trang (M13).
5. Sinh viên ứng tuyển kèm thư giới thiệu và CV; mỗi vị trí chỉ ứng tuyển một lần; không ứng tuyển được tin đã đóng hoặc quá hạn (M13).
6. Doanh nghiệp xem ứng viên, tải CV, chuyển trạng thái `reviewing`, `accepted`, `rejected`; sinh viên theo dõi và có thể rút hồ sơ (M13).
7. Doanh nghiệp mời phỏng vấn, đổi hoặc hủy lịch; sinh viên xác nhận, từ chối hoặc đề nghị đổi lịch.
8. Gợi ý vị trí thực tập phù hợp dựa trên hồ sơ sinh viên (AI1).
9. Chatbot hỏi đáp về quy trình thực tập và các tin đang mở, trích nguồn (AI2).
10. Thống kê tổng quan cho staff và admin.

## Yêu cầu phi chức năng

- **Bảo mật:** băm mật khẩu, JWT có hạn, kiểm tra quyền sở hữu dữ liệu, kiểm tra đầu vào, giới hạn kích thước và loại file.
- **Toàn vẹn dữ liệu:** khóa ngoại thật, ràng buộc UNIQUE cho ứng tuyển, tài khoản và hồ sơ.
- **Dễ bảo trì:** mỗi module có `models`, `schemas`, `service`, `router` riêng; module khác chỉ dùng hàm `service`.
- **Chi phí:** vector lưu bằng Qdrant local, chatbot chạy được không cần LLM trả phí.
- **Kiểm thử:** có kiểm thử tự động (`pytest`) và bộ Postman.
