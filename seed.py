"""
Veritabanı başlangıç verileri - Test kullanıcıları oluştur
"""
from databases.dbconnect import SessionLocal, Base, engine
from sqlalchemy import text
from controllers.hash import hash_password
import sqlite3
import os

# Session oluştur
db = SessionLocal()

# Veritabanı dosyasını kontrol et ve sil
db_path = "e_yoklama.db"
if os.path.exists(db_path):
    os.remove(db_path)
    print("Eski veritabanı silindi.")

# Tabloları oluştur
Base.metadata.create_all(bind=engine)
print("Veritabanı tabloları oluşturuldu.")

def create_test_users():
    """Test kullanıcıları oluştur"""
    
    # ==================== ADMINLER ====================
    admins = [
        {'username': 'admin1', 'email': 'admin1@test.com', 'password': 'admin123', 'role': 0, 'branch': 'Yönetim'},
        {'username': 'admin2', 'email': 'admin2@test.com', 'password': 'admin123', 'role': 0, 'branch': 'Yönetim'},
        {'username': 'admin3', 'email': 'admin3@test.com', 'password': 'admin123', 'role': 0, 'branch': 'Yönetim'},
    ]
    
    print("\n=== ADMIN HESAPLARI ===")
    for admin in admins:
        existing = db.execute(text(f"SELECT * FROM users WHERE username = '{admin['username']}'")).fetchone()
        if not existing:
            hashed = hash_password(admin['password'])
            db.execute(
                text("INSERT INTO users (username, email, hashed_password, role, branch) VALUES (:username, :email, :hashed, :role, :branch)"),
                {"username": admin['username'], "email": admin['email'], "hashed": hashed, "role": admin['role'], "branch": admin['branch']}
            )
        print(f"Username: {admin['username']} | Password: {admin['password']} | Role: Admin")
    
    # ==================== ÖĞRETMENLER ====================
    teachers = [
        {'username': 'teacher1', 'email': 'teacher1@test.com', 'password': 'teacher123', 'role': 1, 'branch': 'Matematik'},
        {'username': 'teacher2', 'email': 'teacher2@test.com', 'password': 'teacher123', 'role': 1, 'branch': 'Fizik'},
        {'username': 'teacher3', 'email': 'teacher3@test.com', 'password': 'teacher123', 'role': 1, 'branch': 'Kimya'},
        {'username': 'teacher4', 'email': 'teacher4@test.com', 'password': 'teacher123', 'role': 1, 'branch': 'Biyoloji'},
        {'username': 'teacher5', 'email': 'teacher5@test.com', 'password': 'teacher123', 'role': 1, 'branch': 'Türkçe'},
    ]
    
    print("\n=== ÖĞRETMEN HESAPLARI ===")
    for teacher in teachers:
        existing = db.execute(text(f"SELECT * FROM users WHERE username = '{teacher['username']}'")).fetchone()
        if not existing:
            hashed = hash_password(teacher['password'])
            db.execute(
                text("INSERT INTO users (username, email, hashed_password, role, branch) VALUES (:username, :email, :hashed, :role, :branch)"),
                {"username": teacher['username'], "email": teacher['email'], "hashed": hashed, "role": teacher['role'], "branch": teacher['branch']}
            )
        print(f"Username: {teacher['username']} | Password: {teacher['password']} | Branch: {teacher['branch']}")
    
    # ==================== ÖĞRENCİLER ====================
    departments = ['Bilgisayar Mühendisliği', 'Elektrik Mühendisliği', 'Makine Mühendisliği', 'İnşaat Mühendisliği', 'Endüstri Mühendisliği']
    classes = ['1. Sınıf', '2. Sınıf', '3. Sınıf', '4. Sınıf']
    
    print("\n=== ÖĞRENCİ HESAPLARI ===")
    student_count = 1
    for dept_idx, department in enumerate(departments):
        for i in range(5):  # Her bölümde 5 öğrenci
            username = f"student{student_count}"
            email = f"student{student_count}@test.com"
            password = "student123"
            student_number = f"2024{dept_idx+1:02d}{i+1:02d}"  # Öğrenci no: 20240101, 20240102, ...
            class_name = classes[i % 4]  # Döngüsel sınıf
            
            existing = db.execute(text(f"SELECT * FROM users WHERE username = '{username}'")).fetchone()
            if not existing:
                hashed = hash_password(password)
                db.execute(
                    text("INSERT INTO users (username, email, hashed_password, role, student_number, department, class_name) VALUES (:username, :email, :hashed, :role, :student_number, :department, :class_name)"),
                    {"username": username, "email": email, "hashed": hashed, "role": 2, "student_number": student_number, "department": department, "class_name": class_name}
                )
            
            if student_count == 1:  # İlk öğrenciyi göster
                print(f"Username: {username} | Password: {password} | Dept: {department} | No: {student_number}")
            
            student_count += 1
    
    db.commit()
    print(f"\nToplam {student_count-1} öğrenci oluşturuldu.")
    print("\n" + "="*50)
    print("TÜM GİRİŞ BİLGİLERİ")
    print("="*50)
    print("\n--- ADMIN ---")
    print("Username: admin1 | Password: admin123")
    print("\n--- TEACHER ---")
    print("Username: teacher1 | Password: teacher123")
    print("\n--- STUDENT ---")
    print("Username: student1 | Password: student123")
    print("="*50)

if __name__ == '__main__':
    create_test_users()