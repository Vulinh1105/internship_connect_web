-- Dữ liệu mẫu (hư cấu). Mật khẩu của MỌI tài khoản mẫu: Test@123
-- ID users: 1 admin | 2 staff | 3-12 sinh viên | 13-17 doanh nghiệp
-- Chạy sau schema.sql. Dùng INSERT IGNORE nên chạy lại không bị lỗi trùng khóa.

USE internship_connect;
SET NAMES utf8mb4;

INSERT IGNORE INTO users (id, email, password_hash, role, is_active) VALUES
  (1, 'admin@example.com', 'pbkdf2_sha256$200000$b2014d7cd70c7f5d3ddddd288f4033f1$1500bd1f94333f25506812f3c5365670cc5868dfa5839ab95d252c1cc053abec', 'admin', 1),
  (2, 'staff@example.com', 'pbkdf2_sha256$200000$00142b25beb4a27b23cd0c37380575d6$bfd031ba4e30647624ecce36c917d52116cc636b4da9ea451af49cec7e9a0912', 'staff', 1),
  (3, 'sv01@example.com', 'pbkdf2_sha256$200000$479a0675d2f7d0dcaeb29ee523519fa3$6b99e67a5fb039503b88caed0bfc100738a350ffc4e989a5cd1abfc1fbe16081', 'student', 1),
  (4, 'sv02@example.com', 'pbkdf2_sha256$200000$933d2a86d352b494d4be02f8147cf406$c8aca5cf20af653dff7ea050fa1b001dd72e7300f327d527f28d919ac72b000d', 'student', 1),
  (5, 'sv03@example.com', 'pbkdf2_sha256$200000$605c0e7060469c4df6f2c18694356be4$91dcf2642c794b70c720ece8d2df6f19b98934e89e7500cea3f1c7f012d6e4eb', 'student', 1),
  (6, 'sv04@example.com', 'pbkdf2_sha256$200000$0a403934fae497aa40238ee864da15e2$c19df2204b9bbbb184e13d37109ca1110cf1b6a859c718fde6ba7d31d43fb383', 'student', 1),
  (7, 'sv05@example.com', 'pbkdf2_sha256$200000$1041e7a8ec2a1092020e481bbc5e1967$0e6be3900c0166bff99a820612ccdb2e7a14544ca5a897ca87dd7f0e25bb0acb', 'student', 1),
  (8, 'sv06@example.com', 'pbkdf2_sha256$200000$4a11bfb65176d224d4558aa89ea7464b$91b286efd93766abc9a62dbf2178c38d1b87037726463a2e457b27f1b2eadba9', 'student', 1),
  (9, 'sv07@example.com', 'pbkdf2_sha256$200000$398c93596f30ee89023146ec5f5b3f06$5348c8a5658f580b6fcb15fdde974b5bd52af3f8ced9da92da443d829c7b4984', 'student', 1),
  (10, 'sv08@example.com', 'pbkdf2_sha256$200000$e49a87efa0c6f8440802adba778b78e0$28885e06663c5b077d06a2b1ec8b801209c674d9cb2cea65882188baceb090f0', 'student', 1),
  (11, 'sv09@example.com', 'pbkdf2_sha256$200000$b99237ddac7acd28af591092d2b0d984$884d694f0904bbc09ee7f800c4b160aea9cab9ca7df0163b9b43fa7fb36c9aa1', 'student', 1),
  (12, 'sv10@example.com', 'pbkdf2_sha256$200000$70e6c0a2c4b346427b5abd55bab7cff0$b9c898a76b67dcb2c3b2aaafc0ee6b170735926062d4fca2e94a699db0e92b89', 'student', 1),
  (13, 'dn01@example.com', 'pbkdf2_sha256$200000$52ee48e332643a8f81941542854a0bb6$41838cb2b84b82c5203df583b629b27e21d7e3e3b1f08cf58f2b54495b2913e8', 'company', 1),
  (14, 'dn02@example.com', 'pbkdf2_sha256$200000$546bd82b7ab9203af676c3939a1c78b9$4399b0ecfd8edf7c1173c113b9b35104857583a9de8c1639cfb88ef7e5b84821', 'company', 1),
  (15, 'dn03@example.com', 'pbkdf2_sha256$200000$3279ab75ab471367d43fcd5d156483c4$e76359f1101835c3ade5e504583a5c596347b0f488cf4234332dc516a26d6bc2', 'company', 1),
  (16, 'dn04@example.com', 'pbkdf2_sha256$200000$0b8e360dcc1e5c4f4127efe31147b486$171dbe1db12e18877c80bced615ff44913a3233f09d39754d67b31bd368b29e5', 'company', 1),
  (17, 'dn05@example.com', 'pbkdf2_sha256$200000$9fc950686daa68c0c808cd6e6ab19d74$8cd2a57495f72254630464a9eabe051e130b5da1a9e5075d09b67740a6e3fa63', 'company', 1);

INSERT IGNORE INTO students (id, user_id, student_code, full_name, major, gpa, phone, profile_summary, internship_status) VALUES
  (1, 3, 'SV001', 'Nguyễn Văn An', 'Công nghệ thông tin', 3.2, '0901000001', 'Sinh viên năm 3, yêu thích lập trình backend và xây dựng API.', 'searching'),
  (2, 4, 'SV002', 'Trần Thị Bình', 'Kỹ thuật phần mềm', 3.45, '0901000002', 'Quan tâm phát triển web, đã làm đồ án website bán hàng.', 'searching'),
  (3, 5, 'SV003', 'Lê Minh Châu', 'Khoa học dữ liệu', 3.6, '0901000003', 'Thích phân tích dữ liệu và học máy, từng tham gia cuộc thi dữ liệu của trường.', 'searching'),
  (4, 6, 'SV004', 'Phạm Quốc Dũng', 'Hệ thống thông tin', 2.9, '0901000004', 'Có kinh nghiệm làm báo cáo và truy vấn cơ sở dữ liệu.', 'not_started'),
  (5, 7, 'SV005', 'Hoàng Thu Hà', 'Thiết kế đồ họa', 3.3, '0901000005', 'Thiết kế giao diện và nhận diện thương hiệu, có portfolio cá nhân.', 'searching'),
  (6, 8, 'SV006', 'Đỗ Gia Huy', 'An toàn thông tin', 3.1, '0901000006', 'Quan tâm bảo mật hệ thống và mạng, thường tham gia CTF.', 'not_started'),
  (7, 9, 'SV007', 'Vũ Ngọc Lan', 'Marketing', 3.5, '0901000007', 'Viết nội dung mạng xã hội và chạy quảng cáo cho dự án nhỏ.', 'searching'),
  (8, 10, 'SV008', 'Bùi Đức Minh', 'Công nghệ thông tin', 3.0, '0901000008', 'Học lập trình web front-end, muốn thực hành trong môi trường doanh nghiệp.', 'not_started'),
  (9, 11, 'SV009', 'Đặng Khánh Linh', 'Kỹ thuật phần mềm', 3.7, '0901000009', 'Thành thạo Python và làm việc nhóm với Git, thích viết kiểm thử.', 'interning'),
  (10, 12, 'SV010', 'Ngô Thanh Sơn', 'Quản trị kinh doanh', 3.2, '0901000010', 'Quan tâm vận hành và phân tích số liệu kinh doanh.', 'not_started');

INSERT IGNORE INTO student_skills (id, student_id, skill_name) VALUES
  (1, 1, 'Python'),
  (2, 1, 'FastAPI'),
  (3, 1, 'SQL'),
  (4, 1, 'Git'),
  (5, 2, 'JavaScript'),
  (6, 2, 'React'),
  (7, 2, 'HTML'),
  (8, 2, 'CSS'),
  (9, 2, 'Git'),
  (10, 3, 'Python'),
  (11, 3, 'Pandas'),
  (12, 3, 'Machine Learning'),
  (13, 3, 'SQL'),
  (14, 4, 'SQL'),
  (15, 4, 'Excel'),
  (16, 4, 'Power BI'),
  (17, 5, 'Figma'),
  (18, 5, 'Photoshop'),
  (19, 5, 'UI/UX'),
  (20, 6, 'Linux'),
  (21, 6, 'Networking'),
  (22, 6, 'Security'),
  (23, 7, 'Content'),
  (24, 7, 'SEO'),
  (25, 7, 'Facebook Ads'),
  (26, 8, 'HTML'),
  (27, 8, 'CSS'),
  (28, 8, 'JavaScript'),
  (29, 9, 'Python'),
  (30, 9, 'Testing'),
  (31, 9, 'Postman'),
  (32, 9, 'Git'),
  (33, 10, 'Excel'),
  (34, 10, 'Analytics');

INSERT IGNORE INTO companies (id, user_id, company_name, description, address, website) VALUES
  (1, 13, 'Công ty TNHH Phần mềm Sao Mai', 'Công ty phát triển phần mềm quản lý cho doanh nghiệp vừa và nhỏ (dữ liệu mẫu hư cấu).', 'Cầu Giấy, Hà Nội', 'https://saomai.example.com'),
  (2, 14, 'Công ty Cổ phần Giải pháp Dữ liệu Việt Data', 'Tư vấn và xây dựng hệ thống phân tích dữ liệu (dữ liệu mẫu hư cấu).', 'Quận 1, TP. Hồ Chí Minh', 'https://vietdata.example.com'),
  (3, 15, 'Công ty TNHH Thiết kế Sáng Tạo Xanh', 'Studio thiết kế giao diện và nhận diện thương hiệu (dữ liệu mẫu hư cấu).', 'Hải Châu, Đà Nẵng', 'https://sangtaoxanh.example.com'),
  (4, 16, 'Công ty Cổ phần Truyền thông Hướng Dương', 'Agency truyền thông và quảng cáo số (dữ liệu mẫu hư cấu).', 'Đống Đa, Hà Nội', 'https://huongduong.example.com'),
  (5, 17, 'Công ty An ninh mạng Bảo Thành', 'Dịch vụ đánh giá và giám sát an toàn thông tin (dữ liệu mẫu hư cấu).', 'Thanh Xuân, Hà Nội', 'https://baothanh.example.com');

INSERT IGNORE INTO internships (id, company_id, title, description, requirements, location, deadline, status) VALUES
  (1, 1, 'Thực tập sinh Python Backend', 'Tham gia xây dựng và bảo trì các API cho sản phẩm quản lý, được mentor hướng dẫn trực tiếp.', 'Python, FastAPI, SQL, Git. Biết REST API là lợi thế.', 'Hà Nội', '2026-12-31', 'open'),
  (2, 1, 'Thực tập sinh Frontend ReactJS', 'Xây dựng giao diện web cho hệ thống nội bộ bằng React.', 'JavaScript, React, HTML, CSS. Biết Git.', 'Hà Nội', '2026-12-20', 'open'),
  (3, 1, 'Thực tập sinh Kiểm thử phần mềm', 'Viết ca kiểm thử, kiểm thử API và ghi nhận lỗi.', 'Testing, Postman, SQL cơ bản. Cẩn thận, tỉ mỉ.', 'Hà Nội', '2027-01-15', 'open'),
  (4, 2, 'Thực tập sinh Data Analyst', 'Làm sạch dữ liệu, xây dựng báo cáo và dashboard cho khách hàng.', 'Python, SQL, Excel, Power BI.', 'TP. Hồ Chí Minh', '2026-12-31', 'open'),
  (5, 2, 'Thực tập sinh Machine Learning', 'Hỗ trợ huấn luyện và đánh giá mô hình dự báo trên dữ liệu thực tế.', 'Python, Machine Learning, Pandas. Có nền tảng thống kê.', 'TP. Hồ Chí Minh', '2027-01-10', 'open'),
  (6, 3, 'Thực tập sinh UI/UX Design', 'Thiết kế wireframe và prototype cho ứng dụng di động.', 'Figma, Photoshop, UI/UX. Có portfolio.', 'Đà Nẵng', '2026-12-25', 'open'),
  (7, 4, 'Thực tập sinh Content Marketing', 'Viết bài cho website và mạng xã hội, hỗ trợ tối ưu SEO.', 'Content, SEO, Facebook Ads. Văn phong tốt.', 'Hà Nội', '2026-12-15', 'open'),
  (8, 4, 'Thực tập sinh Digital Marketing', 'Hỗ trợ chạy quảng cáo và báo cáo hiệu quả chiến dịch.', 'Marketing, Google Ads, Analytics.', 'Hà Nội', '2026-09-30', 'open'),
  (9, 5, 'Thực tập sinh An toàn thông tin', 'Hỗ trợ giám sát hệ thống và rà soát lỗ hổng cơ bản.', 'Linux, Networking, Security.', 'Hà Nội', '2027-01-31', 'open'),
  (10, 5, 'Thực tập sinh Pentest', 'Tham gia các đợt kiểm thử xâm nhập có kiểm soát.', 'Linux, Networking, Security, Python.', 'Hà Nội', '2026-11-30', 'closed');

INSERT IGNORE INTO applications (id, internship_id, student_id, cv_id, cover_letter, status, applied_at) VALUES
  (1, 1, 1, NULL, 'Em mong muốn được thực tập backend và học hỏi từ đội ngũ của công ty.', 'pending', '2026-10-20 09:15:00'),
  (2, 1, 2, NULL, 'Em đã làm đồ án API bán hàng và muốn áp dụng vào thực tế.', 'reviewing', '2026-10-21 14:30:00'),
  (3, 1, 9, NULL, 'Em có kinh nghiệm Python và viết kiểm thử, mong được đóng góp.', 'accepted', '2026-10-18 10:00:00'),
  (4, 4, 3, NULL, 'Em muốn thực hành phân tích dữ liệu trên bài toán thật.', 'pending', '2026-10-22 08:45:00'),
  (5, 6, 5, NULL, 'Portfolio của em đính kèm trong hồ sơ.', 'rejected', '2026-10-19 16:20:00'),
  (6, 7, 7, NULL, 'Em có kinh nghiệm viết nội dung cho các dự án nhỏ.', 'reviewing', '2026-10-23 11:10:00'),
  (7, 2, 2, NULL, 'Em quan tâm đến mảng frontend.', 'withdrawn', '2026-10-17 13:00:00');

INSERT IGNORE INTO interviews (id, application_id, scheduled_at, location, note, status, student_message) VALUES
  (1, 2, '2026-11-10 09:00:00', 'Văn phòng công ty, Cầu Giấy, Hà Nội', 'Mang theo CV bản in.', 'invited', NULL),
  (2, 6, '2026-11-12 14:00:00', 'Họp trực tuyến (link gửi qua email)', 'Phỏng vấn 30 phút.', 'confirmed', 'Em xác nhận tham gia ạ.');
