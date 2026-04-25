from flask import Blueprint, render_template, session, redirect, url_for, request, flash
from models.users import Users
from models.lessons import Courses, CourseStudents, Lessons, Attendance
from databases import db
from sqlalchemy import func

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/dashboard')
def dashboard():
    if 'user' not in session or session['user']['role'] != 0:
        return redirect(url_for('auth.login_page'))
    return render_template('admin.html')

# Öğrenci yönetimi
@admin_bp.route('/students')
def students():
    if 'user' not in session or session['user']['role'] != 0:
        return redirect(url_for('auth.login_page'))
    
    # Filtreleme ve sıralama
    sort_by = request.args.get('sort', 'student_number')
    department = request.args.get('department', '')
    
    students = db.query(Users).filter(Users.role == 2)
    
    if department:
        students = students.filter(Users.department == department)
    
    if sort_by == 'student_number':
        students = students.order_by(Users.student_number)
    elif sort_by == 'department':
        students = students.order_by(Users.department)
    elif sort_by == 'class_name':
        students = students.order_by(Users.class_name)
    
    students = students.all()
    
    # Bölümleri al
    departments = db.query(Users.department).filter(Users.role == 2, Users.department != None).distinct().all()
    departments = [d[0] for d in departments if d[0]]
    
    return render_template('admin_students.html', students=students, departments=departments)

# Öğretmen yönetimi
@admin_bp.route('/teachers')
def teachers():
    if 'user' not in session or session['user']['role'] != 0:
        return redirect(url_for('auth.login_page'))
    
    teachers = Users.query.filter(Users.role == 1).all()
    return render_template('admin_teachers.html', teachers=teachers)

# Öğretmen ekle
@admin_bp.route('/add_teacher', methods=['POST'])
def add_teacher():
    if 'user' not in session or session['user']['role'] != 0:
        return redirect(url_for('auth.login_page'))
    
    username = request.form['username']
    email = request.form['email']
    password = request.form['password']
    branch = request.form.get('branch', '')
    
    Users.register(username, email, password, role=1, branch=branch)
    flash('Öğretmen başarıyla eklendi!', 'success')
    return redirect(url_for('admin.teachers'))

# Ders yönetimi
@admin_bp.route('/courses')
def courses():
    if 'user' not in session or session['user']['role'] != 0:
        return redirect(url_for('auth.login_page'))
    
    all_courses = Courses.get_all()
    teachers = Users.query.filter(Users.role == 1).all()
    return render_template('admin_courses.html', courses=all_courses, teachers=teachers)

# Ders oluştur
@admin_bp.route('/create_course', methods=['POST'])
def create_course():
    if 'user' not in session or session['user']['role'] != 0:
        return redirect(url_for('auth.login_page'))
    
    name = request.form['name']
    description = request.form.get('description', '')
    teacher_id = int(request.form['teacher_id'])
    department = request.form.get('department', '')
    class_name = request.form.get('class_name', '')
    
    Courses.create(name, description, teacher_id, department, class_name)
    flash('Ders başarıyla oluşturuldu!', 'success')
    return redirect(url_for('admin.courses'))

# Derse öğrenci ekle
@admin_bp.route('/add_student_to_course', methods=['POST'])
def add_student_to_course():
    if 'user' not in session or session['user']['role'] != 0:
        return redirect(url_for('auth.login_page'))
    
    course_id = int(request.form['course_id'])
    student_id = int(request.form['student_id'])
    
    Courses.add_student(course_id, student_id)
    flash('Öğrenci derse eklendi!', 'success')
    return redirect(url_for('admin.courses'))

# İstatistikler
@admin_bp.route('/statistics')
def statistics():
    if 'user' not in session or session['user']['role'] != 0:
        return redirect(url_for('auth.login_page'))
    
    # Öğrenci istatistikleri
    total_students = Users.query.filter(Users.role == 2).count()
    total_teachers = Users.query.filter(Users.role == 1).count()
    total_courses = Courses.query.count()
    
    # Yoklama istatistikleri
    total_attendances = Attendance.query.count()
    present_count = Attendance.query.filter(Attendance.status == 1).count()
    absent_count = Attendance.query.filter(Attendance.status == 0).count()
    
    # Bölüm bazlı öğrenci sayıları
    dept_stats = db.query(Users.department, func.count(Users.id)).filter(
        Users.role == 2, Users.department != None
    ).group_by(Users.department).all()
    
    return render_template('admin_statistics.html', 
                         total_students=total_students,
                         total_teachers=total_teachers,
                         total_courses=total_courses,
                         total_attendances=total_attendances,
                         present_count=present_count,
                         absent_count=absent_count,
                         dept_stats=dept_stats)