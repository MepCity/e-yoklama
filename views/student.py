from flask import Blueprint, render_template, session, redirect, url_for
from utils.decorators import role_required
from database import db
from models.course import Course, CourseStudent
from models.attendance_record import AttendanceRecord

student_bp = Blueprint('student', __name__)


@student_bp.route('/dashboard')
@role_required(2)
def dashboard():
    user_id = session['user']['id']
    enrollments = db.query(CourseStudent).filter(CourseStudent.student_id == user_id).all()
    my_courses = []
    for cs in enrollments:
        course = db.query(Course).filter_by(id=cs.course_id).first()
        if course:
            my_courses.append(course)
    return render_template('student/dashboard.html', courses=my_courses)


@student_bp.route('/statistics')
@role_required(2)
def statistics():
    user_id = session['user']['id']
    records = db.query(AttendanceRecord).filter(AttendanceRecord.student_id == user_id).all()

    total = len(records)
    present = len([r for r in records if r.status in ('verified', 'approved', 'manual')])
    absent = total - present
    rate = (present / total * 100) if total > 0 else 0

    course_stats = {}
    for r in records:
        cid = r.course_id
        if cid not in course_stats:
            course = db.query(Course).filter_by(id=cid).first()
            course_stats[cid] = {'name': course.name if course else '?', 'present': 0, 'absent': 0, 'total': 0}
        course_stats[cid]['total'] += 1
        if r.status in ('verified', 'approved', 'manual'):
            course_stats[cid]['present'] += 1
        else:
            course_stats[cid]['absent'] += 1

    return render_template('student/statistics.html',
                           total=total, present=present, absent=absent,
                           rate=round(rate, 1), course_stats=course_stats)
