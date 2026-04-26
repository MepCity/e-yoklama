from flask import Blueprint, render_template, session, redirect, url_for, request, flash
from utils.decorators import role_required
from database import db
from models.course import Course
from models.schedule import Schedule
from models.attendance_record import AttendanceRecord
from models.attendance_session import AttendanceSession

teacher_bp = Blueprint('teacher', __name__)


@teacher_bp.route('/dashboard')
@role_required(1)
def dashboard():
    user_id = session['user']['id']
    my_courses = db.query(Course).filter(Course.teacher_id == user_id).all()
    return render_template('teacher/dashboard.html', courses=my_courses)


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
    return render_template('teacher/schedule.html', course=course, schedules=schedules)


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
