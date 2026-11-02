# Kết quả xác minh ngày 02/11/2026

## Bản chạy thực tế

- Mã nguồn đã ghi đè vào `D:/Internship_connect`, được đối chiếu SHA-256 với workspace.
- Backup gốc: `D:/Internship_connect_backups/20261102-113753`.
- Backend khởi động thành công tại `http://localhost:8000`, dùng cấu hình MySQL đang có.
- Database đã có 17 tài khoản; không reset hoặc seed lại database thật.
- Bảng documents được đăng ký qua metadata chung để phục vụ module tài liệu.

## Kiểm thử tự động

Chạy ngay tại `D:/Internship_connect`:

```powershell
.\.venv\Scripts\python.exe -m pytest backend/tests -q --tb=short
```

Kết quả: **58 passed in 29.52s**, Python 3.13.5.

Test dùng SQLite tạm, không thay đổi database MySQL. Bao gồm nghiệp vụ auth/students/internships/applications/interviews, matching, adapter RAG, upload/index tài liệu, phân quyền, dashboard, preview CV, cùng một OpenAI key/model cho client và các đường dẫn tĩnh HTML/JS/CSS.

`node --check` vượt qua cho mọi file JS trong frontend/src. `compileall` vượt qua cho backend/app và scripts.

Đối chiếu AST: 71 hàm/lớp thuật toán gốc khớp sau khi chuẩn hóa import và cấu hình OpenAI client được phép đổi. Factory chọn embedder được bổ sung nhánh OpenAI theo yêu cầu. Công thức ranking và các prompt/guardrail không được thay bằng thuật toán mới.

## Kiểm tra trình duyệt trên database hiện có

- Trang chủ hiển thị tin đang mở từ database, không dùng danh sách giả lập trên frontend.
- Đăng nhập admin: thống kê 10 tin, 8 tin mở, 7 đơn và 1 đơn accepted; trang doanh nghiệp/tài khoản phân trang được tải.
- Trang tài liệu kiến thức mở thành công, trạng thái kho trống khớp database.
- Đăng nhập sinh viên mẫu: hồ sơ, ngành học, GPA, kỹ năng và đơn ứng tuyển được tải đúng.
- Đăng nhập doanh nghiệp mẫu: hồ sơ, ba tin tuyển dụng và lịch phỏng vấn được tải; nút sửa điền đúng nội dung vào form. Không lưu thay đổi thử nghiệm lên database thật.
- Trang chi tiết tin hiển thị mô tả, yêu cầu, deadline, thông tin công ty và đường dẫn đăng nhập/ứng tuyển.
- Không ghi nhận lỗi console tại các màn hình đã kiểm tra.

## Phần chưa thể xác minh bằng dịch vụ thật

`.env` gốc chưa có OPENAI_API_KEY. Các test OpenAI dùng dependency giả lập hoặc chỉ khởi tạo client; chưa gửi yêu cầu trả phí. Chatbot và matching OpenAI cần điền key hợp lệ rồi khởi động lại backend. RAG còn cần collection Qdrant đã index và model reranker. Không tạo câu trả lời giả để che cấu hình còn thiếu.

Model thống nhất: `gpt-4o-mini` cho generation/query expansion/evidence judge, `text-embedding-3-small` cho embedding RAG/matching. Matching index vẫn riêng và dùng công thức điểm gốc.
