from .dbconnect import engine, SessionLocal, Base, get_db, init_db

# Veritabanı tablolarını kontrol et ve oluştur (yoksa)
# init_db() çağrısı app.py'de yapılacak

# Veritabanı objesi burada kullanılabilir
db = SessionLocal()