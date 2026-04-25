

from sqlalchemy import Column, Integer, String
from databases import Base
from controllers.hash import hash_password, verify_password
import secrets

# db'yi burada import etme, lazy loading kullan
def get_db():
    from databases import db
    return db

class Users(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(Integer, default=2)  # 0: admin, 1: teacher, 2: student
    
    # Öğrenci için ek alanlar
    student_number = Column(String, nullable=True)  # Öğrenci numarası
    department = Column(String, nullable=True)  # Bölüm
    class_name = Column(String, nullable=True)  # Sınıf
    phone = Column(String, nullable=True)  # Telefon
    
    # Öğretmen için ek alanlar
    branch = Column(String, nullable=True)  # Branş

    @staticmethod
    def register(username: str, email: str, password: str, role: int = 2, student_number: str = None, department: str = None, class_name: str = None, phone: str = None, branch: str = None):
        """Kullanıcı kaydı."""
        db = get_db()
        hashed_password = hash_password(password)
        new_user = Users(username=username, email=email, hashed_password=hashed_password, role=role,
                        student_number=student_number, department=department, class_name=class_name,
                        phone=phone, branch=branch)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user

    @staticmethod
    def login(username: str, password: str):
        """Giriş yapma."""
        db = get_db()
        user = db.query(Users).filter(Users.username == username).first()
        if user and verify_password(password, user.hashed_password):
            token = secrets.token_hex(32)
            # Auth tablosuna ekle (auth.py'den)
            from .auth import Auth
            auth_entry = Auth(user_id=user.id, token=token)
            db.add(auth_entry)
            db.commit()
            return {"token": token, "user": user}
        return None

    @staticmethod
    def logout(token: str):
        """Çıkış yapma."""
        db = get_db()
        from .auth import Auth
        auth_entry = db.query(Auth).filter(Auth.token == token).first()
        if auth_entry:
            db.delete(auth_entry)
            db.commit()
            return True
        return False