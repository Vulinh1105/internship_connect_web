from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.utils.timeutil import utcnow

# invited -> confirmed | declined | reschedule_requested ; company có thể cancelled hoặc đổi lịch (về invited)
INTERVIEW_STATUSES = ("invited", "confirmed", "declined", "reschedule_requested", "cancelled")


class Interview(Base):
    __tablename__ = "interviews"

    id = Column(Integer, primary_key=True)
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=False)
    # Giờ phỏng vấn lưu đúng như người dùng nhập (giờ địa phương), không đổi múi giờ
    scheduled_at = Column(DateTime, nullable=False)
    location = Column(String(255), nullable=False)
    note = Column(Text)
    status = Column(String(20), nullable=False, default="invited")
    student_message = Column(Text)
    created_at = Column(DateTime, nullable=False, default=utcnow)

    application = relationship("Application")
