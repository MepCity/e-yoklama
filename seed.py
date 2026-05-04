"""
Minimal seed data — test ve gelistirme icin baslangic verileri olusturur.
Kullanim: python3 seed.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from app import create_app
from database import db, init_db
from database.session import Base, engine as _engine
from models.user import User
from models.course import Course, CourseStudent
from models.schedule import Schedule
from utils.hashing import hash_password


def seed():
    app = create_app('development')

    with app.app_context():
        if _engine is None:
            init_db(app)
        from database.session import engine
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        print('Tablolar yeniden olusturuldu.')

        # ==================== ADMIN ====================
        admin = User(
            username='admin',
            email='admin@eyoklama.test',
            hashed_password=hash_password('admin123'),
            role=0,
            branch='Yonetim',
        )
        db.add(admin)

        # ==================== OGRETMENLER ====================
        t1 = User(
            username='ogretmen1',
            email='ogretmen1@eyoklama.test',
            hashed_password=hash_password('ogretmen123'),
            role=1,
            branch='Yazilim Muhendisligi',
        )
        t2 = User(
            username='ogretmen2',
            email='ogretmen2@eyoklama.test',
            hashed_password=hash_password('ogretmen123'),
            role=1,
            branch='Veri Tabani',
        )
        t3 = User(
            username='ferhat-kara-t',
            email='ferhat-kara-t@eyoklama.test',
            hashed_password=hash_password('123ferhat'),
            role=1,
            branch='Yazilim Muhendisligi',
        )
        db.add_all([t1, t2, t3])
        db.flush()

        # ==================== OGRENCILER ====================
        departments = ['Bilgisayar Muhendisligi', 'Elektrik Muhendisligi']
        classes = ['1. Sinif', '2. Sinif', '3. Sinif']
        students = []

        for dept_idx, dept in enumerate(departments):
            for i in range(5):
                s = User(
                    username=f'ogrenci{dept_idx * 5 + i + 1}',
                    email=f'ogrenci{dept_idx * 5 + i + 1}@eyoklama.test',
                    hashed_password=hash_password('ogrenci123'),
                    role=2,
                    student_number=f'2024{dept_idx + 1:02d}{i + 1:02d}',
                    department=dept,
                    class_name=classes[i % 3],
                )
                students.append(s)

        # Add the specific student user requested
        s_special = User(
            username='ferhat-kara-s',
            email='ferhat-kara-s@eyoklama.test',
            hashed_password=hash_password('123ferhat'),
            role=2,
            student_number='20241001',
            department='Bilgisayar Muhendisligi',
            class_name='1. Sinif',
        )
        students.append(s_special)
        
        # Add Nisanur Kara
        s_nisanur = User(
            username='nisanur-kara',
            email='nisanur.kara@eyoklama.test',
            hashed_password=hash_password('123456'),
            role=2,
            student_number='20241002',
            department='Bilgisayar Muhendisligi',
            class_name='2. Sinif',
        )
        students.append(s_nisanur)
        
        # Add Berfin
        s_berfin = User(
            username='berfin',
            email='berfin@eyoklama.test',
            hashed_password=hash_password('123456'),
            role=2,
            student_number='20241003',
            department='Bilgisayar Muhendisligi',
            class_name='2. Sinif',
        )
        students.append(s_berfin)
        
        db.add_all(students)
        db.flush()

        # ==================== DERSLER ====================
        c1 = Course(
            name='Yazilim Muhendisligi',
            code='YZM301',
            description='Yazilim gelistirme surecleri ve metodolojileri',
            teacher_id=t1.id,
            department='Bilgisayar Muhendisligi',
            class_name='3. Sinif',
            semester='2025-2026 Bahar',
        )
        c2 = Course(
            name='Veri Tabani Yonetim Sistemleri',
            code='VTY201',
            description='Iliskisel veritabani tasarimi ve SQL',
            teacher_id=t2.id,
            department='Bilgisayar Muhendisligi',
            class_name='2. Sinif',
            semester='2025-2026 Bahar',
        )
        c3 = Course(
            name='Algoritma Analizi',
            code='ALG401',
            description='Algoritma karmasikligi ve tasarim teknikleri',
            teacher_id=t1.id,
            department='Bilgisayar Muhendisligi',
            class_name='3. Sinif',
            semester='2025-2026 Bahar',
        )
        c4 = Course(
            name='Web Programlama',
            code='WEB202',
            description='Modern web teknolojileri ve frameworkler',
            teacher_id=t3.id,
            department='Bilgisayar Muhendisligi',
            class_name='2. Sinif',
            semester='2025-2026 Bahar',
        )
        db.add_all([c1, c2, c3, c4])
        db.flush()

        # ==================== DERS KAYITLARI ====================
        # Ilk 5 ogrenci (Bilgisayar Muh.) -> YZM301 ve ALG401
        # Ilk 3 ogrenci -> VTY201
        # Tum ogrenciler -> WEB202 (ferhat-kara-t'nin dersi)
        for s in students[:5]:
            db.add(CourseStudent(course_id=c1.id, student_id=s.id))
            db.add(CourseStudent(course_id=c3.id, student_id=s.id))
        for s in students[:3]:
            db.add(CourseStudent(course_id=c2.id, student_id=s.id))
        for s in students:
            db.add(CourseStudent(course_id=c4.id, student_id=s.id))

        # ==================== DERS PROGRAMI ====================
        db.add(Schedule(
            course_id=c1.id, day_of_week=0,
            start_time='09:00', end_time='11:50',
            room='D-301',
            latitude=40.9833, longitude=29.0500, radius_m=100,
        ))
        db.add(Schedule(
            course_id=c2.id, day_of_week=2,
            start_time='13:00', end_time='14:50',
            room='B-205',
        ))
        db.add(Schedule(
            course_id=c3.id, day_of_week=3,
            start_time='10:00', end_time='12:50',
            room='D-301',
        ))
        db.add(Schedule(
            course_id=c4.id, day_of_week=4,
            start_time='14:00', end_time='16:50',
            room='B-101',
        ))

        db.commit()

        # ==================== OZET ====================
        print('\n=== SEED DATA OLUSTURULDU ===\n')
        print('--- ADMIN ---')
        print('  admin / admin123\n')
        print('--- OGRETMENLER ---')
        print('  ogretmen1 / ogretmen123  (Yazilim Muhendisligi)')
        print('  ogretmen2 / ogretmen123  (Veri Tabani)')
        print('  ferhat-kara-t / 123ferhat  (Yazilim Muhendisligi)\n')
        print('--- OGRENCILER ---')
        print('  ogrenci1 ~ ogrenci10 / ogrenci123')
        print('  ferhat-kara-s / 123ferhat')
        print('  nisanur-kara / 123456')
        print('  berfin / 123456')
        print(f'  Bolumler: {", ".join(departments)}\n')
        print('--- DERSLER ---')
        print(f'  {c1.code} {c1.name} — {t1.username} — 5 ogrenci')
        print(f'  {c2.code} {c2.name} — {t2.username} — 3 ogrenci')
        print(f'  {c3.code} {c3.name} — {t1.username} — 5 ogrenci')
        print(f'  {c4.code} {c4.name} — {t3.username} — {len(students)} ogrenci\n')
        print('--- DERS PROGRAMI ---')
        print('  YZM301: Pazartesi 09:00-11:50 D-301')
        print('  VTY201: Carsamba 13:00-14:50 B-205')
        print('  ALG401: Persembe 10:00-12:50 D-301')
        print('  WEB202: Cuma 14:00-16:50 B-101')
        print('\n============================')


if __name__ == '__main__':
    seed()
