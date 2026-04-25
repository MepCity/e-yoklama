from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from database.session import Base


class AttendanceRecord(Base):
    __tablename__ = 'attendance_records'

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(36), ForeignKey('attendance_sessions.id'), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    course_id = Column(Integer, ForeignKey('courses.id'), nullable=False, index=True)

    # Durum: 'verified' | 'suspicious' | 'approved' | 'rejected' | 'manual'
    status = Column(String(20), nullable=False, default='verified', index=True)

    # Ogrencinin gonderdigi kod
    submitted_code = Column(String(20), nullable=True)

    # Dogrulama verileri (FR-06)
    ip_address = Column(String(45), nullable=True)
    ip_match = Column(Integer, nullable=True)      # 1=eslesti, 0=eslesemedi
    gps_match = Column(Integer, nullable=True)      # 1=alanda, 0=disarda
    gps_distance_m = Column(Float, nullable=True)

    # "Yine de Devam Et" (FR-07)
    override_used = Column(Integer, nullable=False, default=0)
    override_reason = Column(String(200), nullable=True)

    # Ogretmen incelemesi (FR-09)
    reviewed_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    reviewed_at = Column(Text, nullable=True)
    review_note = Column(String(500), nullable=True)

    # Zaman
    submitted_at = Column(Text, nullable=False, server_default='(datetime("now"))')

    # FR-15: Ayni ogrenci ayni oturuma iki kez katılamaz
    __table_args__ = (
        UniqueConstraint('session_id', 'student_id', name='uq_session_student'),
    )

    # Relationship'ler
    session = relationship('AttendanceSession', back_populates='records')
    student = relationship('User', foreign_keys=[student_id], back_populates='attendance_records')
    reviewer = relationship('User', foreign_keys=[reviewed_by], back_populates='reviewed_records')
