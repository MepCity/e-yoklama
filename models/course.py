from sqlalchemy import Column, Integer, String, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from database.session import Base, utcnow_str


class Course(Base):
    __tablename__ = 'courses'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    code = Column(String(20), unique=True, nullable=True)
    description = Column(Text, nullable=True)
    teacher_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    department = Column(String(100), nullable=True)
    class_name = Column(String(50), nullable=True)
    semester = Column(String(30), nullable=True)
    is_active = Column(Integer, nullable=False, default=1)
    created_at = Column(Text, nullable=False, default=utcnow_str)

    # Relationship'ler
    teacher = relationship('User', back_populates='taught_courses')
    schedules = relationship('Schedule', back_populates='course', lazy='dynamic')
    students = relationship('CourseStudent', back_populates='course', lazy='dynamic')
    sessions = relationship('AttendanceSession', back_populates='course', lazy='dynamic')


class CourseStudent(Base):
    __tablename__ = 'course_students'

    id = Column(Integer, primary_key=True, autoincrement=True)
    course_id = Column(Integer, ForeignKey('courses.id', ondelete='CASCADE'), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    enrolled_at = Column(Text, nullable=False, default=utcnow_str)

    __table_args__ = (
        UniqueConstraint('course_id', 'student_id', name='uq_course_student'),
    )

    # Relationship'ler
    course = relationship('Course', back_populates='students')
    student = relationship('User')
