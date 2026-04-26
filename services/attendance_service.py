import uuid
import string
import secrets
from datetime import datetime, timedelta

from database import db
from models.attendance_session import AttendanceSession
from models.attendance_record import AttendanceRecord
from models.course import Course, CourseStudent


def _generate_code(length=6):
    alphabet = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def _now_iso():
    return datetime.utcnow().isoformat()


def _parse_iso(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def start_session(course_id, teacher_id, schedule_id=None,
                  refresh_seconds=10, allowed_ip_prefix=None,
                  latitude=None, longitude=None, radius_m=100):
    active = db.query(AttendanceSession).filter_by(
        course_id=course_id, status='active'
    ).first()
    if active:
        return None, 'Bu ders icin zaten aktif bir yoklama oturumu var.'

    course = db.query(Course).filter_by(id=course_id, teacher_id=teacher_id).first()
    if not course:
        return None, 'Ders bulunamadi veya yetkiniz yok.'

    now = datetime.utcnow()
    code = _generate_code()
    expires_at = now + timedelta(seconds=refresh_seconds)

    session = AttendanceSession(
        id=str(uuid.uuid4()),
        course_id=course_id,
        schedule_id=schedule_id,
        teacher_id=teacher_id,
        current_code=code,
        code_expires_at=expires_at.isoformat(),
        code_refresh_seconds=refresh_seconds,
        allowed_ip_prefix=allowed_ip_prefix,
        latitude=latitude,
        longitude=longitude,
        radius_m=radius_m,
    )
    db.add(session)
    db.commit()
    return session, None


def end_session(session_id, teacher_id):
    session = db.query(AttendanceSession).filter_by(
        id=session_id, teacher_id=teacher_id
    ).first()
    if not session:
        return None, 'Oturum bulunamadi veya yetkiniz yok.'
    if session.status == 'ended':
        return None, 'Bu oturum zaten sonlandirilmis.'

    session.status = 'ended'
    session.ended_at = _now_iso()
    db.commit()
    return session, None


def get_active_session(course_id):
    return db.query(AttendanceSession).filter_by(
        course_id=course_id, status='active'
    ).first()


def get_session_by_id(session_id):
    return db.query(AttendanceSession).filter_by(id=session_id).first()


def refresh_code(session_id):
    session = db.query(AttendanceSession).filter_by(
        id=session_id, status='active'
    ).first()
    if not session:
        return None

    now = datetime.utcnow()
    session.current_code = _generate_code()
    session.code_expires_at = (now + timedelta(seconds=session.code_refresh_seconds)).isoformat()
    db.commit()
    return session


def is_code_expired(session):
    expires_at = _parse_iso(session.code_expires_at)
    return expires_at is None or datetime.utcnow() >= expires_at


def refresh_code_if_expired(session_id):
    session = db.query(AttendanceSession).filter_by(
        id=session_id, status='active'
    ).first()
    if not session:
        return None
    if is_code_expired(session):
        return refresh_code(session_id)
    return session


def get_code_payload(session):
    return {
        'session_id': session.id,
        'code': session.current_code,
        'expires_at': session.code_expires_at,
        'refresh_seconds': session.code_refresh_seconds,
    }


def get_session_records(session_id):
    return db.query(AttendanceRecord).filter_by(
        session_id=session_id
    ).order_by(AttendanceRecord.submitted_at.desc()).all()


def get_enrolled_count(course_id):
    return db.query(CourseStudent).filter_by(course_id=course_id).count()
