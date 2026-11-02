# Tái cấu trúc và phạm vi giữ nguyên logic

Bản chỉnh sửa được chuẩn bị trong workspace Codex và được đồng bộ ghi đè vào `D:/Internship_connect` theo yêu cầu mới. Các file bị ghi đè có bản sao lưu trong `.codex-backups`; thông tin hash nằm trong sync-manifest.json. Không sao chép `.env`, `.git`, `.venv`, `.idea` từ nguồn.

## Các thay đổi

- RAG: `document_processing` chuyển thành `ingestion`; `retrieval.py` thành `retrieval/semantic.py`; hybrid vào `retrieval/hybrid.py`; indexing vào `retrieval`; prompt, query expansion, evidence vào `generation`.
- Hàm lưu/xóa/index Qdrant được chuyển từ chunking sang `retrieval/qdrant_store.py`. Giữ alias tại chunking để caller cũ tiếp tục dùng được.
- Giữ `rag_pipeline.py`, `graph.py`, `state.py`: đây là điều phối thực tế đã có, không tạo pipeline thay thế.
- Bổ sung `rag/service.py` chuyển kết quả pipeline sang contract frontend: answer/mode/sources. Session tách theo user ID.
- Tập trung factory OpenAI embedding dùng cho cả ingestion và semantic retrieval. Không thay model hoặc chiều vector.
- Matching giữ các implementation hashing/sentence-transformers, thêm adapter OpenAI tái sử dụng provider RAG, giữ nội dung profile, công thức 0.6 semantic + 0.4 skill, saturation 3 và thứ tự ranking. Bổ sung adapter lưu vector trong RAM vì module `ai/vector_store.py` được import nhưng không có trong nguồn.
- Theo yêu cầu tiếp theo, matching dùng lại factory OpenAI embedding của RAG; hashing vẫn giữ làm backend offline. Việc đổi provider có thể làm thay đổi giá trị semantic score, còn công thức tính điểm và thuật toán ranking không đổi. Reranker RAG không được ép vào matching vì nguồn không có logic gọi bước đó.
- Router AI dùng schema có sẵn tại `ai/schemas.py`, bỏ định nghĩa trùng.
- `agents/registry.py` và tools nối service. `/agent` nhận tool tường minh, mặc định `ask_knowledge`. Nguồn không có implementation agent; không tự thêm thuật toán suy luận hoặc phân loại từ khóa.
- Thêm documents model/repository/storage/service/router và giao diện quản lý tài liệu kiến thức. Chỉ staff/admin quản lý; tài liệu ở đây là kiến thức công khai cho mọi người dùng đăng nhập. CV tiếp tục thuộc students, không tự đưa vào RAG.
- Chuyển ingestion từ AsyncSession chưa được nối sang Session đồng bộ giống phần backend còn lại. Background wrapper mở Session riêng.
- Tách một số truy vấn đọc thuần sang repository của auth/students/internships; các service nghiệp vụ còn lại được giữ nguyên.
- Giữ companies/applications trong internships theo cấu trúc nghiệp vụ hiện có, tránh tạo module trùng trách nhiệm.
- Frontend vẫn HTML/JS thuần; HTTP client vào src/api, auth/helpers vào src/lib, bootstrap vào src/app và các handler từng trang vào src/features. Bổ sung dashboard, chatbot chung, trang chi tiết tin, sửa tin doanh nghiệp và preview CV bằng các API có sẵn hoặc API quản lý còn thiếu. Không chuyển React/TypeScript vì nguồn chưa có component React và việc viết lại nằm ngoài refactor giữ logic.
- Sửa link `student.html` trỏ nhầm tên `students.html`, đường dẫn điều hướng, nhận API origin khi app phục vụ cùng backend ở cổng khác 8000.
- `.env` được đọc từ gốc dự án; upload và RAG debug output chuyển về `data/runtime`.

## Kiểm chứng

`python backend/support/scripts/verify_preserved_logic.py D:/Internship_connect` đối chiếu AST, xác nhận 71 hàm/lớp thuật toán gốc khớp sau khi chuẩn hóa import và constructor provider. Factory get_embedder được loại khỏi đối chiếu vì được bổ sung nhánh OpenAI theo yêu cầu. Không tuyên bố output vector giữ nguyên khi đổi backend embedding.

Bộ test ban đầu tham chiếu chatbot FAQ và keyword agent không tồn tại trong nguồn. Các test đó được cập nhật thành kiểm tra adapter pipeline và dispatch tool tường minh. Không thay kỳ vọng scoring matching và quy tắc nghiệp vụ cũ.

Bộ kiểm thử đã được mở rộng từ 50 test; xem kết quả kiểm thử cuối cùng trong docs/validation.md. 50 test ban đầu đã vượt qua trên SQLite tạm với Python 3.13.5 và môi trường thư viện hiện có ở `.venv` của bản nguồn. Kiểm tra cú pháp JavaScript bằng `node --check` cũng vượt qua.

Test RAG API dùng pipeline giả lập tại ranh giới dịch vụ để xác minh mapping dữ liệu, session và lỗi provider; ingestion test dùng parser TXT thật. Chưa xác minh end-to-end bằng OpenAI, Qdrant và model reranker thật. Không gọi dịch vụ có phí trong quá trình kiểm thử.

## Giới hạn cần biết

- Matching index trong RAM, được dựng lại từ database khi cần; không tuyên bố có persistent matching Qdrant.
- RAG cần OpenAI key, Qdrant collection đúng model embedding và model CrossEncoder đã tải. Evidence judge, generator và query expansion nay dùng chung factory `gpt-4o-mini`; các prompt, schema và quyết định trong graph được giữ. Output token, timeout, retry được giới hạn ở provider.
- RAG retrieval gốc chưa lọc quyền theo tài liệu. Kho mới chỉ nhận kiến thức dùng chung; không dùng collection đó chứa CV hoặc tài liệu riêng tư.
- Thêm bảng documents qua AUTO_CREATE_TABLES khi chạy local. Chưa bổ sung hệ migration Alembic hoàn chỉnh hoặc migrate database production.
- `docker-compose.yml` chỉ chạy Qdrant; backend/frontend chạy chung qua FastAPI theo hướng dẫn README.
- Đã kiểm tra browser tương tác trên MySQL hiện có (xem validation.md). Chưa cài lại toàn bộ dependency trong môi trường sạch; requirements là danh sách dependency, không phải lockfile đã xác minh.
