from app import create_app
from database import db
from models.classroom import Building, Classroom

def seed_classrooms():
    """Bina ve sınıf verilerini database'e ekle"""
    
    app = create_app('development')
    with app.app_context():
        
        # Mevcut verileri temizle
        db.query(Classroom).delete()
        db.query(Building).delete()
        db.commit()
        
        # Tabloları yeniden oluştur (constraint'ları sıfırlamak için)
        from database import Base
        Base.metadata.drop_all(bind=db.bind, tables=[Building.__table__, Classroom.__table__])
        Base.metadata.create_all(bind=db.bind, tables=[Building.__table__, Classroom.__table__])
        print("Tablolar yeniden oluşturuldu")
        
        # Binalar
        buildings_data = [
            (1, 'T1', 'Teknik Bilimler Fakültesi'),
            (2, 'T2', 'Mühendislik Fakültesi'),
            (3, 'T3', 'Fen Edebiyat Fakültesi'),
            (4, 'T4', 'İktisadi ve İdari Bilimler Fakültesi'),
            (5, 'T5', 'Sağlık Bilimleri Fakültesi'),
        ]
        
        for building_id, code, name in buildings_data:
            building = Building(
                building_code=code,
                building_name=name,
                is_active=True
            )
            db.add(building)
        
        db.commit()
        print("Binalar eklendi")
        
        # Sınıflar - Her binada Z01-Z09 ve 101-109
        classrooms_data = []
        
        for building_id in range(1, 6):  # T1-T5
            # Z01-Z09 (Laboratuvarlar)
            for i in range(1, 10):
                classroom_code = f"Z{i:02d}"
                classroom_name = f"{classroom_code} Laboratuvar"
                classrooms_data.append((building_id, classroom_code, classroom_name, 30))
            
            # 101-109 (Derslikler)
            for i in range(1, 10):
                classroom_code = f"{i:03d}"
                classroom_name = f"{classroom_code} Derslik"
                classrooms_data.append((building_id, classroom_code, classroom_name, 40))
        
        for building_id, code, name, capacity in classrooms_data:
            classroom = Classroom(
                building_id=building_id,
                classroom_code=code,
                classroom_name=name,
                capacity=capacity,
                is_active=True
            )
            db.add(classroom)
        
        db.commit()
        print(f"{len(classrooms_data)} sınıf eklendi")
        print("Bina ve sınıf seed data başarıyla tamamlandı!")

if __name__ == "__main__":
    seed_classrooms()
