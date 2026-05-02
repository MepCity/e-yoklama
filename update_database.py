from app import create_app
from database import db
from sqlalchemy import text

def update_database():
    """Database'i yeni alanlarla güncelle"""
    
    app = create_app('development')
    with app.app_context():
        
        try:
            # Course tablosuna yeni alanları ekle
            db.execute(text("""
                ALTER TABLE courses 
                ADD COLUMN teacher_approval INTEGER DEFAULT 0
            """))
            print("teacher_approval alanı eklendi")
        except Exception as e:
            print(f"teacher_approval alanı zaten var: {e}")
        
        try:
            db.execute(text("""
                ALTER TABLE courses 
                ADD COLUMN status INTEGER DEFAULT 0
            """))
            print("status alanı eklendi")
        except Exception as e:
            print(f"status alanı zaten var: {e}")
        
        try:
            # CourseStudent tablosuna admin_approval alanını ekle
            db.execute(text("""
                ALTER TABLE course_students 
                ADD COLUMN admin_approval INTEGER DEFAULT 0
            """))
            print("admin_approval alanı eklendi")
        except Exception as e:
            print(f"admin_approval alanı zaten var: {e}")
        
        try:
            # Course tablosuna bina ve sınıf alanları ekle
            db.execute(text("""
                ALTER TABLE courses 
                ADD COLUMN building_id INTEGER
            """))
            print("building_id alanı eklendi")
        except Exception as e:
            print(f"building_id alanı zaten var: {e}")
        
        try:
            db.execute(text("""
                ALTER TABLE courses 
                ADD COLUMN classroom_id INTEGER
            """))
            print("classroom_id alanı eklendi")
        except Exception as e:
            print(f"classroom_id alanı zaten var: {e}")
        
        try:
            db.execute(text("""
                ALTER TABLE courses 
                ADD COLUMN day_of_week INTEGER
            """))
            print("day_of_week alanı eklendi")
        except Exception as e:
            print(f"day_of_week alanı zaten var: {e}")
        
        try:
            db.execute(text("""
                ALTER TABLE courses 
                ADD COLUMN start_time VARCHAR(5)
            """))
            print("start_time alanı eklendi")
        except Exception as e:
            print(f"start_time alanı zaten var: {e}")
        
        try:
            db.execute(text("""
                ALTER TABLE courses 
                ADD COLUMN end_time VARCHAR(5)
            """))
            print("end_time alanı eklendi")
        except Exception as e:
            print(f"end_time alanı zaten var: {e}")
        
        try:
            # Eski unique constraint'ı kaldır ve yeni constraint'ı oluştur
            db.execute(text("DROP INDEX IF EXISTS sqlite_autoindex_classrooms_1"))
            print("Eski unique constraint kaldırıldı")
        except Exception as e:
            print(f"Constraint kaldırma hatası: {e}")
        
        db.commit()
        print("Database başarıyla güncellendi!")

if __name__ == "__main__":
    update_database()
