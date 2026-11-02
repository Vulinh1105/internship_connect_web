# Phát triển

Thực hiện từ thư mục gốc dự án:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
Copy-Item .env.example .env
.\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --reload
```

Mở `/app/` trên cổng 8000; Swagger ở `/docs`. Mặc định `.env.example` chọn SQLite để chạy local. MySQL dùng schema và seed trong database, cấu hình DATABASE_URL tương ứng. Không chạy seed MySQL trên SQLite. Sinh viên và doanh nghiệp đăng ký qua giao diện. Staff/admin tạo qua seed MySQL hoặc quy trình quản trị database hiện có.

RAG: cấu hình OPENAI_API_KEY, QDRANT_URL, QDRANT_COLLECTION trong `.env`. Chạy `docker compose up -d qdrant` nếu dùng Qdrant local. Lần đầu dùng chatbot, CrossEncoder có thể cần tải model. Không thay model embedding trên collection đã index; dùng collection mới rồi nạp lại.

Đăng nhập staff/admin, mở Tài liệu kiến thức, upload PDF/DOCX/TXT và bấm Lập chỉ mục. Tài liệu upload thành công chưa đồng nghĩa đã index; lỗi được trả trong trạng thái xử lý. Chỉ upload kiến thức được chia sẻ cho mọi người dùng đăng nhập.

CLI nạp tài liệu qua cùng service:

```powershell
.\.venv\Scripts\python.exe backend/support/scripts/ingest_knowledge.py backend/data/knowledge/faq/guide.txt --owner-id 1
.\.venv\Scripts\python.exe backend/support/scripts/reindex_knowledge.py
.\.venv\Scripts\python.exe -m pytest backend/tests -q
```

Owner ID phải là staff/admin thật có trong database. `ingest_knowledge.py` sao chép file vào runtime storage rồi chạy pipeline hiện có. Reindex xử lý các document đã đăng ký trong DB, không tự quét mọi file trên đĩa.

`backend/data/runtime/uploads/`: tài liệu upload và CV; `backend/data/runtime/rag-index/`: bản sao chunks và status phục vụ debug. Các đường dẫn này không commit. Không chạy nhiều worker nếu dùng status JSON local; không chạy đồng thời reindex với upload/xóa tài liệu.
