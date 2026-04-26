from database import db
from models.user import User
from utils.hashing import hash_password, verify_password


def login(username, password):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return None, 'Kullanıcı bulunamadı.'
    if not user.is_active:
        return None, 'Hesabınız devre dışı.'
    if not verify_password(password, user.hashed_password):
        return None, 'Şifre hatalı.'
    return user, None


def register_student(username, email, password, student_number, department=None, class_name=None, phone=None):
    if db.query(User).filter(User.username == username).first():
        return None, 'Bu kullanıcı adı zaten kayıtlı.'
    if db.query(User).filter(User.email == email).first():
        return None, 'Bu e-posta zaten kayıtlı.'
    if student_number and db.query(User).filter(User.student_number == student_number).first():
        return None, 'Bu öğrenci numarası zaten kayıtlı.'

    user = User(
        username=username,
        email=email,
        hashed_password=hash_password(password),
        role=2,
        student_number=student_number,
        department=department,
        class_name=class_name,
        phone=phone,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user, None


def register_teacher(username, email, password, branch=None):
    if db.query(User).filter(User.username == username).first():
        return None, 'Bu kullanıcı adı zaten kayıtlı.'
    if db.query(User).filter(User.email == email).first():
        return None, 'Bu e-posta zaten kayıtlı.'

    user = User(
        username=username,
        email=email,
        hashed_password=hash_password(password),
        role=1,
        branch=branch,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user, None


def get_user_by_id(user_id):
    return db.query(User).filter(User.id == user_id).first()
