# Internship_connect

Code chính chỉ nằm ở hai nơi:

```text
Internship_connect/
├── frontend/
│   ├── index.html         # Trang chủ
│   └── src/
│       ├── pages/        # Các trang giao diện HTML
│       ├── features/     # Xử lý từng chức năng trên giao diện
│       ├── api/          # Gọi backend
│       ├── lib/          # Đăng nhập và hàm dùng chung
│       ├── app/          # Khởi động giao diện
│       └── styles/       # CSS
├── backend/
│   ├── app/
│   │   ├── main.py       # Điểm khởi động backend
│   │   ├── core/         # Cấu hình, database, bảo mật
│   │   ├── modules/      # Toàn bộ chức năng nghiệp vụ và AI
│   │   └── utils/        # Hàm tiện ích
│   ├── tests/            # Kiểm thử
│   ├── data/             # File upload và dữ liệu chạy, không phải code
│   ├── support/          # Tài liệu, SQL, Postman, script hỗ trợ
│   └── requirements.txt
├── .env                  # Cấu hình và OpenAI key phía server
├── .env.example
├── start.ps1             # Chạy web
└── docker-compose.yml    # Qdrant local nếu cần
```

## Bắt đầu đọc code

- **Frontend:** mở `frontend/index.html`; chọn trang trong `frontend/src/pages`, xử lý tương ứng trong `frontend/src/features`.
- **Backend:** mở `backend/app/main.py`; mỗi tính năng nằm trong `backend/app/modules` với router/service/models/schemas.
- **AI:** `backend/app/modules/ai`; matching trong `matching`, hỏi đáp trong `rag`.
- **Cấu hình AI:** `backend/app/modules/ai/providers`; dùng `gpt-4o-mini`, `text-embedding-3-small`, một `OPENAI_API_KEY` trong `.env`.

## Chạy web

```powershell
.\start.ps1
```

Mở http://localhost:8000/app/. Trong PyCharm chọn File → Reload All from Disk. Tên dự án là Internship_connect; backend đã được đánh dấu Sources Root. `.venv`, dữ liệu và tài liệu hỗ trợ được đánh dấu Excluded để tập trung vào source.

## Kiểm thử

```powershell
.\.venv\Scripts\python.exe -m pytest backend/tests -q
```

Hướng dẫn chi tiết: [phát triển](backend/support/docs/development.md), [API](backend/support/docs/api.md), [kết quả kiểm tra](backend/support/docs/validation.md).

Backup cũ được giữ ngoài project tại `D:\Internship_connect_backups`. Không xóa `.venv`, `.git`, `.idea` hoặc `.env`: chúng phục vụ chạy app, lịch sử Git và cấu hình PyCharm.
