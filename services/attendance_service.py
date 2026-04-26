import uuid
import string
import secrets
from datetime import datetime, timedelta

from database import db
from models.attendance_session import AttendanceSession
from models.attendance_record import AttendanceRecord
from models.course import Course, CourseStudent
from models.schedule import Schedule
from models.verification_log import VerificationLog
from services import verification_service


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
        return None, 'Bu ders için zaten aktif bir yoklama oturumu var.'

    course = db.query(Course).filter_by(id=course_id, teacher_id=teacher_id).first()
    if not course:
        return None, 'Ders bulunamadı veya yetkiniz yok.'

    if schedule_id:
        schedule = db.query(Schedule).filter_by(id=schedule_id, course_id=course_id).first()
        if not schedule:
            return None, 'Ders saati bulunamadı.'
        if latitude is None:
            latitude = schedule.latitude
        if longitude is None:
            longitude = schedule.longitude
        if radius_m is None:
            radius_m = schedule.radius_m

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
        return None, 'Oturum bulunamadı veya yetkiniz yok.'
    if session.status == 'ended':
        return None, 'Bu oturum zaten sonlandırılmış.'

    session.status = 'ended'
    session.ended_at = _now_iso()
    db.commit()
    return session, None


def get_active_session(course_id):
    return db.query(AttendanceSession).filter_by(
        course_id=course_id, status='active'
    ).first()


def get_active_session_for_student(course_id, student_id):
    enrollment = db.query(CourseStudent).filter_by(
        course_id=course_id,
        student_id=student_id,
    ).first()
    if not enrollment:
        return None
    return get_active_session(course_id)


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


def get_suspicious_records(session_id):
    return db.query(AttendanceRecord).filter_by(
        session_id=session_id,
        status='suspicious',
    ).order_by(AttendanceRecord.submitted_at.asc()).all()


def get_enrolled_count(course_id):
    return db.query(CourseStudent).filter_by(course_id=course_id).count()


def resolve_suspicious(record_id, teacher_id, decision, note=None):
    record = db.query(AttendanceRecord).filter_by(id=record_id).first()
    if not record:
        return None, 'Kayıt bulunamadı.'

    att_session = db.query(AttendanceSession).filter_by(id=record.session_id).first()
    if not att_session or att_session.teacher_id != teacher_id:
        return None, 'Bu kaydı inceleme yetkiniz yok.'

    if record.status != 'suspicious':
        return None, 'Bu kayıt şüpheli durumda değil.'

    if decision == 'approve':
        record.status = 'approved'
        result_detail = 'SUSPICIOUS_APPROVED'
    elif decision == 'reject':
        record.status = 'rejected'
        result_detail = 'SUSPICIOUS_REJECTED'
    else:
        return None, 'Geçersiz karar.'

    record.reviewed_by = teacher_id
    record.reviewed_at = _now_iso()
    record.review_note = note
    db.commit()
    db.refresh(record)

    _log_verification(record.id, record.student_id, record.session_id, 'review', decision, result_detail)
    return record, None


def check_in(session_id, student_id, submitted_code, ip_address=None,
             latitude=None, longitude=None, override=False, override_reason=None):
    att_session = db.query(AttendanceSession).filter_by(
        id=session_id,
        status='active',
    ).first()
    if not att_session:
        return None, 'Aktif yoklama oturumu bulunamadı.'

    enrollment = db.query(CourseStudent).filter_by(
        course_id=att_session.course_id,
        student_id=student_id,
    ).first()
    if not enrollment:
        return None, 'Bu derse kayıtlı değilsiniz.'

    existing = db.query(AttendanceRecord).filter_by(
        session_id=session_id,
        student_id=student_id,
    ).first()
    if existing:
        _log_verification(existing.id, student_id, session_id, 'duplicate', 'fail', 'DUPLICATE_CHECK_IN')
        return None, 'Bu yoklama oturumuna zaten katıldınız.'

    normalized_code = (submitted_code or '').strip().upper()
    expected_code = (att_session.current_code or '').strip().upper()

    if is_code_expired(att_session):
        _log_verification(None, student_id, session_id, 'code', 'fail', 'CODE_EXPIRED')
        return None, 'Kodun süresi doldu. Yeni kodu bekleyin.'

    if not normalized_code or normalized_code != expected_code:
        _log_verification(None, student_id, session_id, 'code', 'fail', 'CODE_MISMATCH')
        return None, 'Kod hatalı.'

    verification = verification_service.validate_context(
        att_session=att_session,
        ip_address=ip_address,
        latitude=latitude,
        longitude=longitude,
    )
    if not verification['ok'] and not override:
        _log_verification(None, student_id, session_id, verification['failed_layer'], 'fail', verification['reason'])
        return None, _verification_message(verification)

    record = AttendanceRecord(
        session_id=session_id,
        student_id=student_id,
        course_id=att_session.course_id,
        status='verified' if verification['ok'] else 'suspicious',
        submitted_code=normalized_code,
        ip_address=ip_address,
        ip_match=verification.get('ip_match'),
        gps_match=verification.get('gps_match'),
        gps_distance_m=verification.get('gps_distance_m'),
        override_used=1 if override and not verification['ok'] else 0,
        override_reason=override_reason if override and not verification['ok'] else None,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    _log_verification(record.id, student_id, session_id, 'code', 'pass', 'CODE_MATCH')
    if verification.get('ip_match') is not None:
        _log_verification(record.id, student_id, session_id, 'ip', 'pass' if verification['ip_match'] else 'fail', verification.get('reason'))
    if verification.get('gps_match') is not None:
        _log_verification(record.id, student_id, session_id, 'gps', 'pass' if verification['gps_match'] else 'fail', verification.get('reason'))
    if record.status == 'suspicious':
        _log_verification(record.id, student_id, session_id, verification['failed_layer'], 'override', verification['reason'])
    return record, None


def _log_verification(record_id, student_id, session_id, check_type, check_result, detail=None):
    log = VerificationLog(
        record_id=record_id,
        student_id=student_id,
        session_id=session_id,
        check_type=check_type,
        check_result=check_result,
        detail=detail,
    )
    db.add(log)
    db.commit()
    return log


def _verification_message(verification):
    if verification['failed_layer'] == 'ip':
        return 'IP doğrulaması başarısız. Yine de devam etmek için onay verin.'
    if verification['failed_layer'] == 'gps':
        return 'GPS doğrulaması başarısız. Yine de devam etmek için onay verin.'
    return 'Doğrulama başarısız.'
