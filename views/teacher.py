from flask import Blueprint, render_template, session, redirect, url_for, request, flash
from models.users import Users
from models.lessons import Courses, CourseStudents, Lessons, Attendance
from databases import db

teacher_bp = Blueprint('teacher', __name__)

@teacher_bp.route('/dashboard')
def dashboard():
    if 'user' not in session or session['user']['role'] != 1:
        return redirect(url_for('auth.login_page'))
    
    user_id = session['user']['id']
    my_courses = Courses.get_by_teacher(user_id)
    return render_template('teacher.html', courses=my_courses)

# Ders saatlerini ayarla
@teacher_bp.route('/course/<int:course_id>/schedule', methods=['GET', 'POST'])
def course_schedule(course_id):
    if 'user' not in session or session['user']['role'] != 1:
        return redirect(url_for('auth.login_page'))
    
    course = Courses.query.get(course_id)
    if not course or course.teacher_id != session['user']['id']:
        return redirect(url_for('teacher.dashboard'))
    
    if request.method == 'POST':
        day_of_week = int(request.form['day_of_week'])
        start_time = request.form['start_time']
        end_time = request.form['end_time']
        room = request.form.get('room', '')
        
        Lessons.create(course_id, day_of_week, start_time, end_time, room)
        flash('Ders saati eklendi!', 'success')
    
    schedule = Lessons.get_by_course(course_id)
    return render_template('teacher_schedule.html', course=course, schedule=schedule)

# Yoklama paylaşma
@teacher_bp.route('/course/<int:course_id>/attendance')
def share_attendance(course_id):
    if 'user' not in session or session['user']['role'] != 1:
        return redirect(url_for('auth.login_page'))
    
    course = Courses.query.get(course_id)
    if not course or course.teacher_id != session['user']['id']:
        return redirect(url_for('teacher.dashboard'))
    
    # QR kod için basit bir token oluştur
    import secrets
    qr_token = secrets.token_hex(16)
    
    attendances = Attendance.get_by_course(course_id)
    return render_template('teacher_attendance.html', course=course, attendances=attendances, qr_token=qr_token)

# İstatistikler
@teacher_bp.route('/statistics')
def statistics():
    if 'user' not in session or session['user']['role'] != 1:
        return redirect(url_for('auth.login_page'))
    
    user_id = session['user']['id']
    my_courses = Courses.get_by_teacher(user_id)
    
    course_stats = []
    for course in my_courses:
        attendances = Attendance.get_by_course(course.id)
        present = len([a for a in attendances if a.status == 1])
        absent = len([a for a in attendances if a.status == 0])
        total = len(attendances)
        rate = (present / total * 100) if total > 0 else 0
        course_stats.append({
            'course': course,
            'total': total,
            'present': present,
            'absent': absent,
            'rate': rate
        })
    
    return render_template('teacher_statistics.html', course_stats=course_stats)