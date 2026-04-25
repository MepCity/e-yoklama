from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker, declarative_base

# Veritabanı URL'si (örnek olarak SQLite kullanıyoruz, değiştirilebilir)
DATABASE_URL = "sqlite:///./e_yoklama.db"

# Engine oluştur
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Session oluştur
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base sınıfı
Base = declarative_base()

# Veritabanı objesi (session factory)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Veritabanı tablolarını oluştur (yoksa)."""
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    
    # Tabloları oluştur (sadece yoksa)
    if not existing_tables:
        Base.metadata.create_all(bind=engine)
        print("Veritabanı tabloları oluşturuldu.")
    else:
        print(f"Mevcut tablolar: {existing_tables}")
    
    return engine