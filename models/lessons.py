

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from databases import Base
from databases import db
from datetime import datetime

class Courses(Base):
    """Ders modeli (öğretmen tarafından oluşturulan)"""
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)  # Ders adı
    description = Column(String)  # Ders açıklaması
    teacher_id = Column(Integer, ForeignKey("users.id"))  # Öğretmen ID
    department = Column(String)  # Bölüm
    class_name = Column(String)  # Sınıf
    created_at = Column(DateTime, default=datetime.utcnow)
    
    @staticmethod
    def create(name: str, description: str, teacher_id: int, department: str, class_name: str):
        """Ders oluştur"""
        course = Courses(name=name, description=description, teacher_id=teacher_id, 
                        department=department, class_name=class_name)
        db.add(course)
        db.commit()
        db.refresh(course)
        return course
    
    @staticmethod
    def get_all():
        """Tüm dersleri getir"""
        return db.query(Courses).all()
    
    @staticmethod
    def get_by_teacher(teacher_id: int):
        """Öğretmenin derslerini getir"""
        return db.query(Courses).filter(Courses.teacher_id == teacher_id).all()
    
    @staticmethod
    def add_student(course_id: int, student_id: int):
        """Derse öğrenci ekle"""
        from .lessons import CourseStudents
        cs = CourseStudents(course_id=course_id, student_id=student_id)
        db.add(cs)
        db.commit()
        return cs
    
    @staticmethod
    def get_students(course_id: int):
        """Dersin öğrencilerini getir"""
        from .lessons import CourseStudents
        return db.query(CourseStudents).filter(CourseStudents.course_id == course_id).all()


class CourseStudents(Base):
    """Ders-Öğrenci ilişkisi"""
    __tablename__ = "course_students"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"))
    student_id = Column(Integer, ForeignKey("users.id"))


class Lessons(Base):
    """Ders saatleri (yoklama için)"""
    __tablename__ = "lessons"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"))
    day_of_week = Column(Integer)  # 0: Pazartesi - 6: Pazar
    start_time = Column(String)  # HH:MM format
    end_time = Column(String)  # HH:MM format
    room = Column(String)  # Salon
    
    @staticmethod
    def create(course_id: int, day_of_week: int, start_time: str, end_time: str, room: str):
        """Ders saati oluştur"""
        lesson = Lessons(course_id=course_id, day_of_week=day_of_week, 
                        start_time=start_time, end_time=end_time, room=room)
        db.add(lesson)
        db.commit()
        db.refresh(lesson)
        return lesson
    
    @staticmethod
    def get_by_course(course_id: int):
        """Dersin saatlerini getir"""
        return db.query(Lessons).filter(Lessons.course_id == course_id).all()


class Attendance(Base):
    """Yoklama kaydı"""
    __tablename__ = "attendance"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"))
    student_id = Column(Integer, ForeignKey("users.id"))
    date = Column(DateTime, default=datetime.utcnow)
    status = Column(Integer, default=0)  # 0: Yok, 1: Var, 2: İzinli, 3: Geç
    qr_code = Column(String, nullable=True)  # QR kod
    
    @staticmethod
    def mark_attendance(course_id: int, student_id: int, status: int = 1):
        """Yoklama işaretle"""
        attendance = Attendance(course_id=course_id, student_id=student_id, status=status)
        db.add(attendance)
        db.commit()
        return attendance
    
    @staticmethod
    def get_by_student(student_id: int):
        """Öğrencinin yoklama kayıtlarını getir"""
        return db.query(Attendance).filter(Attendance.student_id == student_id).all()
    
    @staticmethod
    def get_by_course(course_id: int):
        """Dersin yoklama kayıtlarını getir"""
        return db.query(Attendance).filter(Attendance.course_id == course_id).all()


class Statistics(Base):
    """Öğrenci istatistikleri - ders bazlı yoklama kayıtları"""
    __tablename__ = "statistics"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"))  # Öğrenci ID
    course_id = Column(Integer, ForeignKey("courses.id"))  # Ders ID
    lesson_number = Column(Integer)  # Ders numarası (1, 2, 3, ... son ders)
    status = Column(Integer, default=0)  # 0: Yok, 1: Var
    date = Column(DateTime, default=datetime.utcnow)  # Tarih
    
    @staticmethod
    def record_attendance(student_id: int, course_id: int, lesson_number: int, status: int = 1):
        """Yoklama kaydı oluştur"""
        stat = Statistics(student_id=student_id, course_id=course_id, 
                          lesson_number=lesson_number, status=status)
        db.add(stat)
        db.commit()
        db.refresh(stat)
        return stat
    
    @staticmethod
    def get_by_student_course(student_id: int, course_id: int):
        """Öğrencinin belirli dersteki tüm yoklama kayıtlarını getir"""
        return db.query(Statistics).filter(
            Statistics.student_id == student_id,
            Statistics.course_id == course_id
        ).order_by(Statistics.lesson_number).all()
    
    @staticmethod
    def get_statistics(student_id: int, course_id: int):
        """Öğrencinin belirli dersteki istatistiklerini hesapla"""
        records = Statistics.get_by_student_course(student_id, course_id)
        total = len(records)
        present = len([r for r in records if r.status == 1])
        absent = len([r for r in records if r.status == 0])
        rate = (present / total * 100) if total > 0 else 0
        return {'total': total, 'present': present, 'absent': absent, 'rate': rate}
    
    @staticmethod
    def get_all_by_course(course_id: int):
        """Dersin tüm öğrenci istatistiklerini getir"""
        return db.query(Statistics).filter(Statistics.course_id == course_id).all()
    
    @staticmethod
    def get_next_lesson_number(course_id: int, student_id: int):
        """Sonraki ders numarasını getir"""
        last = db.query(Statistics).filter(
            Statistics.course_id == course_id,
            Statistics.student_id == student_id
        ).order_by(Statistics.lesson_number.desc()).first()
        
        if last:
            return last.lesson_number + 1
        return 1