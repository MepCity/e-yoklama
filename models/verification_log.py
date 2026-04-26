from sqlalchemy import Column, Integer, String, Text, ForeignKey
from database.session import Base, utcnow_str


class VerificationLog(Base):
    __tablename__ = 'verification_logs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    record_id = Column(Integer, ForeignKey('attendance_records.id'), nullable=True)
    student_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    session_id = Column(String(36), ForeignKey('attendance_sessions.id'), nullable=False, index=True)
    check_type = Column(String(20), nullable=False)   # 'ip' | 'gps' | 'code' | 'duplicate'
    check_result = Column(String(20), nullable=False)  # 'pass' | 'fail' | 'override'
    detail = Column(Text, nullable=True)
    created_at = Column(Text, nullable=False, default=utcnow_str)
