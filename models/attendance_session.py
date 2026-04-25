import uuid
from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey
from sqlalchemy.orm import relationship
from database.session import Base


class AttendanceSession(Base):
    __tablename__ = 'attendance_sessions'

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    course_id = Column(Integer, ForeignKey('courses.id'), nullable=False, index=True)
    schedule_id = Column(Integer, ForeignKey('schedules.id'), nullable=True)
    teacher_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)

    # Oturum durumu
    status = Column(String(10), nullable=False, default='active', index=True)  # 'active' | 'ended'

    # Dinamik kod (FR-04)
    current_code = Column(String(20), nullable=False)
    code_expires_at = Column(Text, nullable=False)
    code_refresh_seconds = Column(Integer, nullable=False, default=10)

    # Geofence (oturuma ozel — schedule'dan kopyalanir veya override edilir)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    radius_m = Column(Integer, default=100)

    # IP dogrulama (NFR-05)
    allowed_ip_prefix = Column(String(50), nullable=True)

    # Zaman
    started_at = Column(Text, nullable=False, server_default='(datetime("now"))')
    ended_at = Column(Text, nullable=True)

    # Relationship'ler
    course = relationship('Course', back_populates='sessions')
    teacher = relationship('User')
    schedule = relationship('Schedule')
    records = relationship('AttendanceRecord', back_populates='session', lazy='dynamic')
