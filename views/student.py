from flask import Blueprint, render_template, session, redirect, url_for, request, flash
from models.users import Users
from models.lessons import Courses, CourseStudents, Lessons, Attendance
from databases import db

student_bp = Blueprint('student', __name__)

@student_bp.route('/dashboard')
def dashboard():
    if 'user' not in session or session['user']['role'] != 2:
        return redirect(url_for('auth.login_page'))
    
    user_id = session['user']['id']
    
    # Öğrencinin kayıtlı olduğu dersleri bul
    course_students = db.query(CourseStudents).filter(CourseStudents.student_id == user_id).all()
    my_courses = []
    for cs in course_students:
        course = Courses.query.get(cs.course_id)
        if course:
            my_courses.append(course)
    
    return render_template('student.html', courses=my_courses)

# Güvenlik kontrolü - tik alma
@student_bp.route('/security_check', methods=['GET', 'POST'])
def security_check():
    if 'user' not in session or session['user']['role'] != 2:
        return redirect(url_for('auth.login_page'))
    
    if request.method == 'POST':
        # Tüm tiklerin alındığını kontrol et
        terms = request.form.getlist('terms')
        if len(terms) >= 3:  # 3 güvenlik kontrolü
            session['security_verified'] = True
            flash('Güvenlik kontrolü başarılı!', 'success')
            return redirect(url_for('student.scan_qr'))
        else:
            flash('Lütfen tüm güvenlik kontrollerini onaylayın!', 'error')
    
    return render_template('student_security.html')

# QR kod okutma
@student_bp.route('/scan_qr')
def scan_qr():
    if 'user' not in session or session['user']['role'] != 2:
        return redirect(url_for('auth.login_page'))
    
    if not session.get('security_verified'):
        return redirect(url_for('student.security_check'))
    
    return render_template('student_scan_qr.html')

# QR kod işleme
@student_bp.route('/process_qr', methods=['POST'])
def process_qr():
    if 'user' not in session or session['user']['role'] != 2:
        return redirect(url_for('auth.login_page'))
    
    qr_data = request.form.get('qr_data', '')
    course_id = int(request.form.get('course_id', 0))
    
    # Yoklama işaretle
    user_id = session['user']['id']
    Attendance.mark_attendance(course_id, user_id, status=1)
    flash('Yoklama başarıyla işaretlendi!', 'success')
    
    return redirect(url_for('student.dashboard'))

# İstatistikler
@student_bp.route('/statistics')
def statistics():
    if 'user' not in session or session['user']['role'] != 2:
        return redirect(url_for('auth.login_page'))
    
    user_id = session['user']['id']
    attendances = Attendance.get_by_student(user_id)
    
    # İstatistik hesapla
    total = len(attendances)
    present = len([a for a in attendances if a.status == 1])
    absent = len([a for a in attendances if a.status == 0])
    excused = len([a for a in attendances if a.status == 2])
    late = len([a for a in attendances if a.status == 3])
    
    attendance_rate = (present / total * 100) if total > 0 else 0
    
    # Ders bazlı istatistik
    course_stats = {}
    for a in attendances:
        course = Courses.query.get(a.course_id)
        if course:
            if course.id not in course_stats:
                course_stats[course.id] = {'name': course.name, 'present': 0, 'absent': 0, 'total': 0}
            course_stats[course.id]['total'] += 1
            if a.status == 1:
                course_stats[course.id]['present'] += 1
            elif a.status == 0:
                course_stats[course.id]['absent'] += 1
    
    return render_template('student_statistics.html',
                         total=total, present=present, absent=absent,
                         excused=excused, late=late, attendance_rate=attendance_rate,
                         course_stats=course_stats)