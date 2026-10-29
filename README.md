# Internship Connect
Hệ thống kết nối sinh viên với doanh nghiệp thực tập.
- **Backend:** Python, FastAPI, SQLAlchemy, MySQL, JWT
- **Frontend:** HTML, CSS, JavaScript thuần (không cần build)
- **AI:** gợi ý vị trí phù hợp (matching) và chatbot hỏi đáp (RAG), vector lưu bằng Qdrant local (miễn phí)
Kiến trúc: **một ứng dụng FastAPI, một database MySQL chung**, chia module bên trong. Các module gọi nhau bằng hàm Python (ví dụ M13 gọi `students.service`), không gọi HTTP vòng quanh. API chỉ dành cho frontend, Postman và Swagger.

| Module | Thư mục | Phụ trách |
|---|---|---|
| M20 Tài khoản, JWT, phân quyền | `backend/app/modules/auth` | đăng ký, đăng nhập, vai trò |
| M03 Sinh viên | `backend/app/modules/students` | hồ sơ, kỹ năng, CV |
| M13 Doanh nghiệp và thực tập | `backend/app/modules/internships` | công ty, tin thực tập, ứng tuyển, xét duyệt |
| Phỏng vấn | `backend/app/modules/interviews` | mời, xác nhận, đổi lịch |
| AI | `backend/app/modules/ai` | matching, RAG, agent |

## Chạy thử nhanh
Yêu cầu: Python 3.10+, MySQL.
1. **Tạo database.** Bật MySQL trong XAMPP, mở `http://localhost/phpmyadmin` → tab **SQL**, dán nội dung `database/schema.sql` rồi `database/seed.sql` (chạy lần lượt, mỗi file một lần bấm Go).
2. **Cấu hình.** Sao chép `.env.example` thành `.env` ở thư mục gốc, sửa `DATABASE_URL` nếu root MySQL của bạn có mật khẩu, và đặt `JWT_SECRET` (cả nhóm dùng chung một giá trị).
3. **Cài thư viện.** Mở thư mục `backend/` trong terminal:
   ```
   python -m venv venv
   venv\Scripts\activate          (Mac/Linux: source venv/bin/activate)
   pip install -r requirements.txt
   ```
4. **Chạy server** (vẫn ở thư mục `backend/`):
   ```
   uvicorn app.main:app --reload
   ```
5. Mở trình duyệt:
   - Swagger (thử API): http://localhost:8000/docs
   - Giao diện web: http://localhost:8000/app/

**Tài khoản mẫu** (sau khi chạy `seed.sql`), mật khẩu chung `Test@123`:
`admin@example.com`, `staff@example.com`, `sv01@example.com` … `sv10@example.com`, `dn01@example.com` … `dn05@example.com`.

> Dùng PyCharm: mở thư mục gốc `internship-connect`, chuột phải thư mục `backend` → **Mark Directory as → Sources Root** để PyCharm hiểu `from app...`. Không chạy bằng nút Run trên `main.py`, hãy dùng lệnh `uvicorn` ở trên.

Nếu chưa muốn dùng MySQL, đặt trong `.env`: `DATABASE_URL=sqlite:///./dev.db` (app tự tạo bảng, nhưng không có dữ liệu mẫu).

## Kiểm thử

```
cd backend
pytest
```
Kiểm thử dùng SQLite trong bộ nhớ nên không đụng tới MySQL thật. Bộ Postman nằm ở `postman/internship_connect.json`: nhập vào Postman, chạy một request `Login as ...` trước, token tự lưu cho các request sau.

## Phần AI

- **Gợi ý (AI1):** so khớp ngành học, kỹ năng, phần giới thiệu của sinh viên với tin thực tập đang mở. Điểm = 0.6 × độ tương đồng vector + 0.4 × số kỹ năng trùng (tối đa tại 3 kỹ năng). Có giải thích kỹ năng trùng.
- **Chatbot (AI2):** tìm các đoạn liên quan trong `rag/knowledge/faq.md` và các tin thực tập, rồi trả lời. Mặc định trả lời bằng trích đoạn tài liệu (miễn phí). Điền `LLM_API_KEY` trong `.env` nếu muốn dùng LLM sinh câu trả lời (có tính phí theo nhà cung cấp).
- **Agent:** bộ điều phối theo từ khóa, chọn giữa gợi ý và hỏi đáp.
- **Vector:** Qdrant chạy local, lưu ở `backend/qdrant_data/`. Nếu chưa cài hoặc Qdrant lỗi, app tự dùng bộ nhớ trong. Embedding mặc định là hashing (nhẹ, offline, hiểu từ khóa); muốn hiểu ngữ nghĩa tốt hơn thì `pip install sentence-transformers` và đặt `EMBEDDING_BACKEND=sentence_transformers`.
- Lưu ý: Qdrant local chỉ cho một tiến trình mở thư mục tại một thời điểm, nên không chạy nhiều worker.

## Bảo mật đã áp dụng

- Mật khẩu băm PBKDF2-HMAC-SHA256 (muối ngẫu nhiên), không lưu bản rõ.
- Vai trò lấy từ DB theo tài khoản trong JWT, không tin client. Danh tính sinh viên khi ứng tuyển lấy từ JWT.
- Kiểm tra quyền sở hữu: sinh viên chỉ xem hồ sơ của mình, doanh nghiệp chỉ quản lý tin và đơn của mình.
- Ràng buộc UNIQUE ở DB chặn ứng tuyển trùng; CV chỉ nhận PDF/DOC/DOCX ≤ 5MB, lưu bằng tên do server đặt.
- Truy vấn tham số hóa (SQLAlchemy), tìm kiếm escape ký tự `%`/`_`. Frontend escape mọi dữ liệu trước khi hiển thị.
- Nội dung tin thực tập đưa vào chatbot được đánh dấu là dữ liệu, không phải chỉ dẫn (giảm rủi ro prompt injection).

**Trước khi triển khai thật:** đặt `JWT_SECRET` mạnh, đổi `CORS_ORIGINS` thành địa chỉ frontend cụ thể (đang để `*` cho tiện học), chạy qua HTTPS, và cân nhắc lưu token bằng cookie HttpOnly thay vì `localStorage`.

## Giới hạn hiện tại

- Chưa có đặt lại mật khẩu, xác minh email, thông báo tự động.
- Tài khoản `staff` và `admin` chỉ tạo qua seed hoặc trực tiếp trong DB.
- Giờ phỏng vấn lưu đúng giờ nhập vào (giờ địa phương), không quy đổi múi giờ.
- Danh sách ứng viên truy vấn hồ sơ sinh viên từng dòng, đủ cho quy mô đồ án.
