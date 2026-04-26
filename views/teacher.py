from flask import Blueprint, render_template, session, redirect, url_for, request, flash, current_app
from utils.decorators import role_required
from utils.qr_generator import generate_qr_base64
from database import db
from models.course import Course
from models.schedule import Schedule
from models.attendance_record import AttendanceRecord
from models.attendance_session import AttendanceSession
from services import attendance_service

teacher_bp = Blueprint('teacher', __name__)


@teacher_bp.route('/dashboard')
@role_required(1)
def dashboard():
    user_id = session['user']['id']
    my_courses = db.query(Course).filter(Course.teacher_id == user_id).all()

    active_sessions = {}
    for course in my_courses:
        active = attendance_service.get_active_session(course.id)
        if active:
            active_sessions[course.id] = active.id

    return render_template('teacher/dashboard.html', courses=my_courses, active_sessions=active_sessions)


@teacher_bp.route('/course/<int:course_id>/schedule', methods=['GET', 'POST'])
@role_required(1)
def course_schedule(course_id):
    user_id = session['user']['id']
    course = db.query(Course).filter_by(id=course_id, teacher_id=user_id).first()
    if not course:
        flash('Ders bulunamadi.', 'error')
        return redirect(url_for('teacher.dashboard'))

    if request.method == 'POST':
        day_of_week = request.form.get('day_of_week', type=int)
        start_time = request.form.get('start_time', '').strip()
        end_time = request.form.get('end_time', '').strip()
        room = request.form.get('room', '').strip()

        if day_of_week is not None and start_time and end_time:
            schedule = Schedule(
                course_id=course_id,
                day_of_week=day_of_week,
                start_time=start_time,
                end_time=end_time,
                room=room or None,
            )
            db.add(schedule)
            db.commit()
            flash('Ders saati eklendi.', 'success')
        else:
            flash('Tum alanlar doldurulmalidir.', 'error')

    schedules = db.query(Schedule).filter_by(course_id=course_id).order_by(Schedule.day_of_week).all()
    active_session = attendance_service.get_active_session(course_id)
    return render_template('teacher/schedule.html', course=course, schedules=schedules, active_session=active_session)


@teacher_bp.route('/course/<int:course_id>/start-session', methods=['POST'])
@role_required(1)
def start_session(course_id):
    user_id = session['user']['id']
    refresh_seconds = request.form.get('refresh_seconds', type=int) or current_app.config.get('QR_REFRESH_SECONDS', 10)
    allowed_ip = request.form.get('allowed_ip_prefix', '').strip() or current_app.config.get('ALLOWED_IP_PREFIX')
    latitude = request.form.get('latitude', type=float)
    longitude = request.form.get('longitude', type=float)
    radius_m = request.form.get('radius_m', type=int) or current_app.config.get('GEOFENCE_RADIUS_M', 100)

    schedule_id = request.form.get('schedule_id', type=int)

    att_session, error = attendance_service.start_session(
        course_id=course_id,
        teacher_id=user_id,
        schedule_id=schedule_id,
        refresh_seconds=refresh_seconds,
        allowed_ip_prefix=allowed_ip,
        latitude=latitude,
        longitude=longitude,
        radius_m=radius_m,
    )
    if error:
        flash(error, 'error')
        return redirect(url_for('teacher.course_schedule', course_id=course_id))

    flash('Yoklama oturumu baslatildi.', 'success')
    return redirect(url_for('teacher.active_session', session_id=att_session.id))


@teacher_bp.route('/session/<session_id>')
@role_required(1)
def active_session(session_id):
    user_id = session['user']['id']
    att_session = attendance_service.get_session_by_id(session_id)
    if not att_session or att_session.teacher_id != user_id:
        flash('Oturum bulunamadi.', 'error')
        return redirect(url_for('teacher.dashboard'))

    records = attendance_service.get_session_records(session_id)
    enrolled_count = attendance_service.get_enrolled_count(att_session.course_id)

    qr_data = att_session.current_code
    qr_base64 = generate_qr_base64(qr_data) if att_session.status == 'active' else None

    return render_template('teacher/active_session.html',
                           att_session=att_session,
                           records=records,
                           enrolled_count=enrolled_count,
                           qr_base64=qr_base64)


@teacher_bp.route('/session/<session_id>/end', methods=['POST'])
@role_required(1)
def end_session(session_id):
    user_id = session['user']['id']
    att_session, error = attendance_service.end_session(session_id, user_id)
    if error:
        flash(error, 'error')
        return redirect(url_for('teacher.dashboard'))

    flash('Yoklama oturumu sonlandirildi.', 'success')
    return redirect(url_for('teacher.active_session', session_id=session_id))


@teacher_bp.route('/statistics')
@role_required(1)
def statistics():
    user_id = session['user']['id']
    my_courses = db.query(Course).filter(Course.teacher_id == user_id).all()

    course_stats = []
    for course in my_courses:
        total = db.query(AttendanceRecord).filter(AttendanceRecord.course_id == course.id).count()
        present = db.query(AttendanceRecord).filter(
            AttendanceRecord.course_id == course.id,
            AttendanceRecord.status.in_(['verified', 'approved', 'manual'])
        ).count()
        rate = (present / total * 100) if total > 0 else 0
        course_stats.append({
            'course': course,
            'total': total,
            'present': present,
            'absent': total - present,
            'rate': round(rate, 1),
        })

    return render_template('teacher/statistics.html', course_stats=course_stats)
