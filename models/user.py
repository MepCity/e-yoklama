from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import relationship
from database.session import Base, utcnow_str


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(256), nullable=False)
    role = Column(Integer, nullable=False, default=2)  # 0=admin, 1=teacher, 2=student

    # Ogrenci alanlari
    student_number = Column(String(20), unique=True, nullable=True, index=True)
    department = Column(String(100), nullable=True)
    class_name = Column(String(50), nullable=True)
    phone = Column(String(20), nullable=True)

    # Ogretmen alanlari
    branch = Column(String(100), nullable=True)

    # Meta
    is_active = Column(Integer, nullable=False, default=1)
    created_at = Column(Text, nullable=False, default=utcnow_str)

    # Relationship'ler
    taught_courses = relationship('Course', back_populates='teacher', lazy='dynamic')
    attendance_records = relationship(
        'AttendanceRecord',
        foreign_keys='AttendanceRecord.student_id',
        back_populates='student',
        lazy='dynamic',
    )
    reviewed_records = relationship(
        'AttendanceRecord',
        foreign_keys='AttendanceRecord.reviewed_by',
        back_populates='reviewer',
        lazy='dynamic',
    )

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'student_number': self.student_number,
            'department': self.department,
            'class_name': self.class_name,
            'phone': self.phone,
            'branch': self.branch,
        }
