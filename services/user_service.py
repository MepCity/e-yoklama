from models.user import User
from models.device_pairing import DevicePairing


def list_students(db, show_inactive=False, sort_by='student_number', department=None):
    query = db.query(User).filter(User.role == 2)
    if not show_inactive:
        query = query.filter(User.is_active == 1)
    if department:
        query = query.filter(User.department == department)
    if sort_by == 'department':
        query = query.order_by(User.department)
    elif sort_by == 'class_name':
        query = query.order_by(User.class_name)
    else:
        query = query.order_by(User.student_number)
    return query.all()


def list_teachers(db, show_inactive=False):
    query = db.query(User).filter(User.role == 1)
    if not show_inactive:
        query = query.filter(User.is_active == 1)
    return query.all()


def list_departments_for_role(db, role):
    departments = db.query(User.department).filter(
        User.role == role,
        User.department.isnot(None),
    ).distinct().all()
    return [department for (department,) in departments if department]


def toggle_user_active(db, user_id, role):
    user = db.query(User).filter(User.id == user_id, User.role == role).first()
    if not user:
        return None
    user.is_active = 0 if user.is_active == 1 else 1
    db.commit()
    return user


def reset_student_device_pairings(db, student_id):
    student = db.query(User).filter_by(id=student_id, role=2).first()
    if not student:
        return None, 0
    pairings = db.query(DevicePairing).filter_by(user_id=student_id).all()
    for pairing in pairings:
        db.delete(pairing)
    db.commit()
    return student, len(pairings)
