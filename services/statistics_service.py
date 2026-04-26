from collections import Counter

from database import db
from models.attendance_record import AttendanceRecord
from models.attendance_session import AttendanceSession
from models.course import Course, CourseStudent
from models.user import User


PRESENT_STATUSES = ('verified', 'approved', 'manual')
def _rate(part, total):
    return round((part / total * 100), 1) if total else 0


def _status_counts(records):
    counts = Counter(record.status for record in records)
    return {
        'verified': counts.get('verified', 0),
        'approved': counts.get('approved', 0),
        'manual': counts.get('manual', 0),
        'suspicious': counts.get('suspicious', 0),
        'rejected': counts.get('rejected', 0),
    }


def _course_expected_count(course_id):
    session_count = db.query(AttendanceSession).filter_by(course_id=course_id).count()
    enrolled_count = db.query(CourseStudent).filter_by(course_id=course_id).count()
    return session_count * enrolled_count, session_count, enrolled_count


def _course_summary(course):
    records = db.query(AttendanceRecord).filter_by(course_id=course.id).all()
    expected, session_count, enrolled_count = _course_expected_count(course.id)
    submitted = len(records)
    present = len([r for r in records if r.status in PRESENT_STATUSES])
    suspicious = len([r for r in records if r.status == 'suspicious'])
    rejected = len([r for r in records if r.status == 'rejected'])
    missed = max(expected - submitted, 0)
    absent = rejected + missed

    return {
        'course': course,
        'total': expected,
        'submitted': submitted,
        'present': present,
        'suspicious': suspicious,
        'rejected': rejected,
        'missed': missed,
        'absent': absent,
        'rate': _rate(present, expected),
        'session_count': session_count,
        'enrolled_count': enrolled_count,
    }


def get_admin_statistics():
    total_students = db.query(User).filter(User.role == 2).count()
    total_teachers = db.query(User).filter(User.role == 1).count()
    total_courses = db.query(Course).count()
    total_sessions = db.query(AttendanceSession).count()

    courses = db.query(Course).order_by(Course.name).all()
    course_stats = [_course_summary(course) for course in courses]

    total_expected = sum(item['total'] for item in course_stats)
    total_records = sum(item['submitted'] for item in course_stats)
    verified_count = sum(item['present'] for item in course_stats)
    suspicious_count = sum(item['suspicious'] for item in course_stats)
    rejected_count = sum(item['rejected'] for item in course_stats)
    missed_count = sum(item['missed'] for item in course_stats)
    absent_count = rejected_count + missed_count

    dept_stats = db.query(User.department).filter(
        User.role == 2,
        User.department.isnot(None),
    ).all()
    dept_counts = Counter(dept for (dept,) in dept_stats if dept)

    return {
        'total_students': total_students,
        'total_teachers': total_teachers,
        'total_courses': total_courses,
        'total_sessions': total_sessions,
        'total_records': total_records,
        'total_expected': total_expected,
        'verified_count': verified_count,
        'suspicious_count': suspicious_count,
        'rejected_count': rejected_count,
        'missed_count': missed_count,
        'absent_count': absent_count,
        'attendance_rate': _rate(verified_count, total_expected),
        'dept_stats': sorted(dept_counts.items()),
        'course_stats': course_stats,
        'status_chart': {
            'labels': ['Katılım', 'Şüpheli', 'Reddedilen', 'Girilmemiş'],
            'data': [verified_count, suspicious_count, rejected_count, missed_count],
            'colors': ['#27ae60', '#f39c12', '#e74c3c', '#95a5a6'],
        },
        'course_rate_chart': {
            'labels': [item['course'].name for item in course_stats],
            'data': [item['rate'] for item in course_stats],
        },
    }


def get_teacher_statistics(teacher_id):
    courses = db.query(Course).filter_by(teacher_id=teacher_id).order_by(Course.name).all()
    course_stats = [_course_summary(course) for course in courses]

    return {
        'course_stats': course_stats,
        'chart_data': {
            'labels': [item['course'].name for item in course_stats],
            'present': [item['present'] for item in course_stats],
            'absent': [item['absent'] for item in course_stats],
            'suspicious': [item['suspicious'] for item in course_stats],
        },
    }


def get_student_statistics(student_id):
    enrollments = db.query(CourseStudent).filter_by(student_id=student_id).all()
    course_stats = {}
    total_expected = 0
    total_present = 0
    total_suspicious = 0
    total_rejected = 0
    total_missed = 0

    for enrollment in enrollments:
        course = db.query(Course).filter_by(id=enrollment.course_id).first()
        if not course:
            continue

        sessions = db.query(AttendanceSession).filter_by(course_id=course.id).all()
        session_ids = [att_session.id for att_session in sessions]
        records = []
        if session_ids:
            records = db.query(AttendanceRecord).filter(
                AttendanceRecord.student_id == student_id,
                AttendanceRecord.session_id.in_(session_ids),
            ).all()

        expected = len(sessions)
        submitted = len(records)
        present = len([r for r in records if r.status in PRESENT_STATUSES])
        suspicious = len([r for r in records if r.status == 'suspicious'])
        rejected = len([r for r in records if r.status == 'rejected'])
        missed = max(expected - submitted, 0)
        absent = rejected + missed

        course_stats[course.id] = {
            'name': course.name,
            'code': course.code,
            'total': expected,
            'submitted': submitted,
            'present': present,
            'suspicious': suspicious,
            'rejected': rejected,
            'missed': missed,
            'absent': absent,
            'rate': _rate(present, expected),
        }

        total_expected += expected
        total_present += present
        total_suspicious += suspicious
        total_rejected += rejected
        total_missed += missed

    total_absent = total_rejected + total_missed

    return {
        'total': total_expected,
        'present': total_present,
        'suspicious': total_suspicious,
        'rejected': total_rejected,
        'missed': total_missed,
        'absent': total_absent,
        'rate': _rate(total_present, total_expected),
        'course_stats': course_stats,
        'chart_data': {
            'labels': ['Katılım', 'Şüpheli', 'Reddedilen', 'Girilmemiş'],
            'data': [total_present, total_suspicious, total_rejected, total_missed],
            'colors': ['#27ae60', '#f39c12', '#e74c3c', '#95a5a6'],
        },
        'course_rate_chart': {
            'labels': [item['name'] for item in course_stats.values()],
            'data': [item['rate'] for item in course_stats.values()],
        },
    }
