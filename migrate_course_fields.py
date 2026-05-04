"""
Database migration script to update Course model fields
"""
import sqlite3
import os

def migrate_course_fields():
    db_path = os.path.join(os.path.dirname(__file__), 'e_yoklama.db')
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Add new columns if they don't exist
        cursor.execute("PRAGMA table_info(courses)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'building_code' not in columns:
            cursor.execute("ALTER TABLE courses ADD COLUMN building_code TEXT")
            print("Added building_code column")
        
        if 'classroom_code' not in columns:
            cursor.execute("ALTER TABLE courses ADD COLUMN classroom_code TEXT")
            print("Added classroom_code column")
        
        # Migrate data from old building_id/classroom_id to new fields
        cursor.execute("""
            UPDATE courses 
            SET building_code = (
                SELECT building_code FROM buildings WHERE buildings.id = courses.building_id
            )
            WHERE building_id IS NOT NULL AND building_code IS NULL
        """)
        
        cursor.execute("""
            UPDATE courses 
            SET classroom_code = (
                SELECT classroom_code FROM classrooms WHERE classrooms.id = courses.classroom_id
            )
            WHERE classroom_id IS NOT NULL AND classroom_code IS NULL
        """)
        
        conn.commit()
        print("Migration completed successfully")
        
    except Exception as e:
        print(f"Migration error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    migrate_course_fields()
