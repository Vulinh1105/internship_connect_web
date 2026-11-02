"""Local rule-based screening. Human approval is always required."""
import re
import unicodedata

def screen(internship):
    text = " ".join(str(getattr(internship, f, "") or "") for f in ("title", "description", "requirements", "location"))
    normalized = "".join(c for c in unicodedata.normalize("NFD", text.lower().replace("đ", "d")) if unicodedata.category(c) != "Mn")
    rules = [
        (r"\b(dat coc|dong phi|phi tuyen dung|phi giu cho|chuyen tien truoc)\b", "Yêu cầu đặt cọc/đóng phí: cần xác minh"),
        (r"\b(ca cuoc|danh bac|cai bong|lua dao)\b", "Nội dung liên quan cờ bạc/lừa đảo: cần xem xét"),
        (r"<\s*script\b|javascript:", "Nội dung có mã script đáng ngờ"),
    ]
    flags = [message for pattern, message in rules if re.search(pattern, normalized)]
    if not (internship.title or "").strip(): flags.append("Thiếu tiêu đề hợp lệ")
    if not (internship.description or "").strip(): flags.append("Thiếu mô tả công việc")
    if not (internship.requirements or "").strip(): flags.append("Thiếu yêu cầu ứng tuyển")
    return "\n".join(flags) or None

def submit_for_review(internship):
    internship.moderation_status = "pending"
    internship.auto_flags = screen(internship)
    internship.rejection_reason = None
    internship.reviewed_by = None
    internship.reviewed_at = None
