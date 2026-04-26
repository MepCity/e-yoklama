from flask import Blueprint, render_template, session, redirect, url_for, request, flash, current_app
from utils.decorators import role_required
from utils.rate_limit import limiter
from database import db
from models.course import Course, CourseStudent
from models.attendance_record import AttendanceRecord
from services import attendance_service, statistics_service

student_bp = Blueprint('student', __name__)


@student_bp.route('/dashboard')
@role_required(2)
def dashboard():
    user_id = session['user']['id']
    enrollments = db.query(CourseStudent).filter(CourseStudent.student_id == user_id).all()
    my_courses = []
    active_sessions = {}
    checked_in_sessions = set()
    for cs in enrollments:
        course = db.query(Course).filter_by(id=cs.course_id).first()
        if course:
            my_courses.append(course)
            active = attendance_service.get_active_session_for_student(course.id, user_id)
            if active:
                active_sessions[course.id] = active
                existing = db.query(AttendanceRecord).filter_by(
                    session_id=active.id,
                    student_id=user_id,
                ).first()
                if existing:
                    checked_in_sessions.add(active.id)
    return render_template(
        'student/dashboard.html',
        courses=my_courses,
        active_sessions=active_sessions,
        checked_in_sessions=checked_in_sessions,
    )


@student_bp.route('/session/<session_id>/check-in', methods=['POST'])
@role_required(2)
@limiter.limit(lambda: current_app.config.get('RATE_LIMIT_ATTEND', '10/minute'))
def check_in(session_id):
    user_id = session['user']['id']
    submitted_code = request.form.get('code', '')
    override = request.form.get('override') == '1'
    override_reason = request.form.get('override_reason', '').strip() or None
    latitude = request.form.get('latitude', type=float)
    longitude = request.form.get('longitude', type=float)

    record, error = attendance_service.check_in(
        session_id=session_id,
        student_id=user_id,
        submitted_code=submitted_code,
        ip_address=request.remote_addr,
        latitude=latitude,
        longitude=longitude,
        override=override,
        override_reason=override_reason,
    )
    if error:
        flash(error, 'error')
        return redirect(url_for('student.dashboard'))

    if record.status == 'suspicious':
        flash('Yoklama kaydınız şüpheli olarak öğretmen onayına gönderildi.', 'warning')
    else:
        flash('Yoklama kaydınız doğrulandı.', 'success')
    return redirect(url_for('student.statistics'))


@student_bp.route('/statistics')
@role_required(2)
def statistics():
    user_id = session['user']['id']
    stats = statistics_service.get_student_statistics(user_id)
    return render_template('student/statistics.html', **stats)
