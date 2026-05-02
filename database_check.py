#!/usr/bin/env python3
"""
Database Veri Kontrol ve Düzeltme Scripti
Tüm tabloları kontrol eder ve uyumsuz verileri düzeltir
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Flask uygulamasını yükle
from app import create_app
from database import db
from models.user import User
from models.course import Course, CourseStudent
from models.schedule import Schedule
from models.attendance_session import AttendanceSession
from models.attendance_record import AttendanceRecord
from models.classroom import Classroom

def check_users():
    """Kullanıcı tablosunu kontrol et"""
    print("=== KULLANICILAR TABLOSU KONTROLÜ ===")
    users = db.query(User).all()
    print(f"Toplam kullanıcı: {len(users)}")
    
    issues = []
    for user in users:
        # Rol kontrolü
        if user.role not in [0, 1, 2]:  # 0: admin, 1: teacher, 2: student
            issues.append(f"Kullanıcı {user.id} geçersiz role: {user.role}")
        
        # Email kontrolü
        if not user.email or '@' not in user.email:
            issues.append(f"Kullanıcı {user.id} geçersiz email: {user.email}")
        
        # Boş username kontrolü
        if not user.username:
            issues.append(f"Kullanıcı {user.id} boş username")
    
    if issues:
        print("Hatalar:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("✅ Kullanıcı tablosu temiz")
    
    return len(issues) == 0

def check_courses():
    """Ders tablosunu kontrol et"""
    print("\n=== DERSLER TABLOSU KONTROLÜ ===")
    courses = db.query(Course).all()
    print(f"Toplam ders: {len(courses)}")
    
    issues = []
    for course in courses:
        # Ders adı kontrolü
        if not course.name:
            issues.append(f"Ders {course.id} boş name")
        
        # Öğretmen ID kontrolü
        if not course.teacher_id:
            issues.append(f"Ders {course.id} boş teacher_id")
        else:
            teacher = db.query(User).filter_by(id=course.teacher_id).first()
            if not teacher:
                issues.append(f"Ders {course.id} var olmayan öğretmen: {course.teacher_id}")
            elif teacher.role != 1:
                issues.append(f"Ders {course.id} öğretmen rolünde değil: {course.teacher_id} (role: {teacher.role})")
        
        # Onay durumu kontrolü
        if course.teacher_approval not in [0, 1, 2]:
            issues.append(f"Ders {course.id} geçersiz teacher_approval: {course.teacher_approval}")
        
        # Aktiflik kontrolü
        if course.is_active not in [0, 1]:
            issues.append(f"Ders {course.id} geçersiz is_active: {course.is_active}")
    
    if issues:
        print("Hatalar:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("✅ Ders tablosu temiz")
    
    return len(issues) == 0

def check_schedules():
    """Ders programı tablosunu kontrol et"""
    print("\n=== DERS PROGRAMI TABLOSU KONTROLÜ ===")
    schedules = db.query(Schedule).all()
    print(f"Toplam program: {len(schedules)}")
    
    issues = []
    for schedule in schedules:
        # Ders ID kontrolü
        if not schedule.course_id:
            issues.append(f"Program {schedule.id} boş course_id")
        else:
            course = db.query(Course).filter_by(id=schedule.course_id).first()
            if not course:
                issues.append(f"Program {schedule.id} var olmayan ders: {schedule.course_id}")
        
        # Gün kontrolü
        if schedule.day_of_week not in range(7):  # 0-6 arası
            issues.append(f"Program {schedule.id} geçersiz day_of_week: {schedule.day_of_week}")
        
        # Saat formatı kontrolü
        if not schedule.start_time or ':' not in schedule.start_time:
            issues.append(f"Program {schedule.id} geçersiz start_time: {schedule.start_time}")
        else:
            try:
                hour, minute = map(int, schedule.start_time.split(':'))
                if not (0 <= hour <= 23 and 0 <= minute <= 59):
                    issues.append(f"Program {schedule.id} geçersiz start_time aralığı: {schedule.start_time}")
            except:
                issues.append(f"Program {schedule.id} start_time parse hatası: {schedule.start_time}")
        
        if not schedule.end_time or ':' not in schedule.end_time:
            issues.append(f"Program {schedule.id} geçersiz end_time: {schedule.end_time}")
        else:
            try:
                hour, minute = map(int, schedule.end_time.split(':'))
                if not (0 <= hour <= 23 and 0 <= minute <= 59):
                    issues.append(f"Program {schedule.id} geçersiz end_time aralığı: {schedule.end_time}")
            except:
                issues.append(f"Program {schedule.id} end_time parse hatası: {schedule.end_time}")
        
        # Saat mantığı kontrolü
        if schedule.start_time and schedule.end_time:
            try:
                start_minutes = int(schedule.start_time[:2]) * 60 + int(schedule.start_time[3:5])
                end_minutes = int(schedule.end_time[:2]) * 60 + int(schedule.end_time[3:5])
                if start_minutes >= end_minutes:
                    issues.append(f"Program {schedule.id} başlangıç bitişten büyük: {schedule.start_time} >= {schedule.end_time}")
            except:
                pass
    
    if issues:
        print("Hatalar:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("✅ Ders programı tablosu temiz")
    
    return len(issues) == 0

def check_attendance_sessions():
    """Yoklama oturumları tablosunu kontrol et"""
    print("\n=== YOKLAMA OTURUMLARI TABLOSU KONTROLÜ ===")
    sessions = db.query(AttendanceSession).all()
    print(f"Toplam oturum: {len(sessions)}")
    
    issues = []
    for session in sessions:
        # Ders ID kontrolü
        if not session.course_id:
            issues.append(f"Oturum {session.id} boş course_id")
        else:
            course = db.query(Course).filter_by(id=session.course_id).first()
            if not course:
                issues.append(f"Oturum {session.id} var olmayan ders: {session.course_id}")
        
        # Öğretmen ID kontrolü
        if not session.teacher_id:
            issues.append(f"Oturum {session.id} boş teacher_id")
        else:
            teacher = db.query(User).filter_by(id=session.teacher_id).first()
            if not teacher:
                issues.append(f"Oturum {session.id} var olmayan öğretmen: {session.teacher_id}")
        
        # Durum kontrolü
        if session.status not in ['active', 'ended']:
            issues.append(f"Oturum {session.id} geçersiz status: {session.status}")
        
        # Kod yenileme süresi kontrolü
        if not session.code_refresh_seconds or session.code_refresh_seconds < 1:
            issues.append(f"Oturum {session.id} geçersiz code_refresh_seconds: {session.code_refresh_seconds}")
    
    if issues:
        print("Hatalar:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("✅ Yoklama oturumları tablosu temiz")
    
    return len(issues) == 0

def check_course_students():
    """Ders-öğrenci ilişkileri tablosunu kontrol et"""
    print("\n=== DERS-ÖĞRENCİ İLİŞKİLERİ TABLOSU KONTROLÜ ===")
    course_students = db.query(CourseStudent).all()
    print(f"Toplam ders-öğrenci ilişkisi: {len(course_students)}")
    
    issues = []
    for cs in course_students:
        # Ders ID kontrolü
        if not cs.course_id:
            issues.append(f"İlişki {cs.id} boş course_id")
        else:
            course = db.query(Course).filter_by(id=cs.course_id).first()
            if not course:
                issues.append(f"İlişki {cs.id} var olmayan ders: {cs.course_id}")
        
        # Öğrenci ID kontrolü
        if not cs.student_id:
            issues.append(f"İlişki {cs.id} boş student_id")
        else:
            student = db.query(User).filter_by(id=cs.student_id).first()
            if not student:
                issues.append(f"İlişki {cs.id} var olmayan öğrenci: {cs.student_id}")
            elif student.role != 2:
                issues.append(f"İlişki {cs.id} öğrenci rolünde değil: {cs.student_id} (role: {student.role})")
    
    if issues:
        print("Hatalar:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("✅ Ders-öğrenci ilişkileri tablosu temiz")
    
    return len(issues) == 0

def fix_data():
    """Uyumsuz verileri düzelt"""
    print("\n=== VERİ DÜZELTMELERİ ===")
    
    # Ders onay durumlarını düzelt (0 olanları 1 yap)
    courses = db.query(Course).filter_by(teacher_approval=0).all()
    if courses:
        print(f"{len(courses)} dersin onay durumu 0'dan 1'e düzeltiliyor...")
        for course in courses:
            course.teacher_approval = 1
        db.commit()
        print("✅ Ders onayları düzeltildi")
    
    # Geçersiz rol ID'lerini düzelt
    users = db.query(User).all()
    fixed_users = []
    for user in users:
        if user.role not in [0, 1, 2]:
            # Varsayılan olarak öğrenci yap
            user.role = 2
            fixed_users.append(user.id)
    
    if fixed_users:
        print(f"{len(fixed_users)} kullanıcının rolü öğrenci olarak düzeltildi: {fixed_users}")
        db.commit()
        print("✅ Kullanıcı rolleri düzeltildi")
    
    # Aktif olmayan dersleri aktif yap
    inactive_courses = db.query(Course).filter_by(is_active=0).all()
    if inactive_courses:
        print(f"{len(inactive_courses)} pasif ders aktif yapılıyor...")
        for course in inactive_courses:
            course.is_active = 1
        db.commit()
        print("✅ Pasif dersler aktif yapıldı")

def main():
    """Ana kontrol fonksiyonu"""
    app = create_app()
    with app.app_context():
        print("DATABASE VERİ KONTROL BAŞLATILIYOR...")
        print("=" * 50)
        
        # Tüm kontrolleri çalıştır
        results = []
        results.append(check_users())
        results.append(check_courses())
        results.append(check_schedules())
        results.append(check_attendance_sessions())
        results.append(check_course_students())
        
        print(f"\n=== ÖZET ===")
        total_checks = len(results)
        passed_checks = sum(results)
        
        print(f"Toplam kontrol: {total_checks}")
        print(f"Başarılı: {passed_checks}")
        print(f"Hatalı: {total_checks - passed_checks}")
        
        if passed_checks < total_checks:
            print("\nVeri düzeltme işlemi başlatılıyor...")
            fix_data()
            print("\nDüzeltme sonrası tekrar kontrol ediliyor...")
            # Düzeltme sonrası tekrar kontrol et
            results = []
            results.append(check_users())
            results.append(check_courses())
            results.append(check_schedules())
            results.append(check_attendance_sessions())
            results.append(check_course_students())
            
            passed_after = sum(results)
            if passed_after == total_checks:
                print("✅ Tüm veriler başarıyla düzeltildi!")
            else:
                print(f"⚠️  Düzeltme sonrası hala {total_checks - passed_after} hata var")
        else:
            print("✅ Tüm veriler temiz!")

if __name__ == "__main__":
    main()
