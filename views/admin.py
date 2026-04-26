from flask import Blueprint, render_template, session, redirect, url_for, request, flash, send_file
from utils.decorators import role_required
from database import db
from models.user import User
from models.course import Course, CourseStudent
from services import auth_service, statistics_service, export_service

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/dashboard')
@role_required(0)
def dashboard():
    return render_template('admin/dashboard.html')


@admin_bp.route('/students')
@role_required(0)
def students():
    sort_by = request.args.get('sort', 'student_number')
    department = request.args.get('department', '')

    query = db.query(User).filter(User.role == 2)

    if department:
        query = query.filter(User.department == department)

    if sort_by == 'department':
        query = query.order_by(User.department)
    elif sort_by == 'class_name':
        query = query.order_by(User.class_name)
    else:
        query = query.order_by(User.student_number)

    student_list = query.all()

    departments = db.query(User.department).filter(
        User.role == 2, User.department.isnot(None)
    ).distinct().all()
    departments = [d[0] for d in departments if d[0]]

    return render_template('admin/students.html', students=student_list, departments=departments)


@admin_bp.route('/teachers')
@role_required(0)
def teachers():
    teacher_list = db.query(User).filter(User.role == 1).all()
    return render_template('admin/teachers.html', teachers=teacher_list)


@admin_bp.route('/add_teacher', methods=['POST'])
@role_required(0)
def add_teacher():
    username = request.form.get('username', '').strip()
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '')
    branch = request.form.get('branch', '').strip()

    if not username or not email or not password:
        flash('Tüm zorunlu alanlar doldurulmalıdır.', 'error')
        return redirect(url_for('admin.teachers'))

    user, error = auth_service.register_teacher(username, email, password, branch=branch or None)
    if error:
        flash(error, 'error')
    else:
        flash('Öğretmen başarıyla eklendi.', 'success')
    return redirect(url_for('admin.teachers'))


@admin_bp.route('/courses')
@role_required(0)
def courses():
    course_list = db.query(Course).all()
    teacher_list = db.query(User).filter(User.role == 1).all()
    student_list = db.query(User).filter(User.role == 2).all()
    return render_template('admin/courses.html', courses=course_list, teachers=teacher_list, students=student_list)


@admin_bp.route('/create_course', methods=['POST'])
@role_required(0)
def create_course():
    name = request.form.get('name', '').strip()
    code = request.form.get('code', '').strip()
    description = request.form.get('description', '').strip()
    teacher_id = request.form.get('teacher_id', type=int)
    department = request.form.get('department', '').strip()
    class_name = request.form.get('class_name', '').strip()

    if not name or not teacher_id:
        flash('Ders adı ve öğretmen seçimi zorunludur.', 'error')
        return redirect(url_for('admin.courses'))

    course = Course(
        name=name,
        code=code or None,
        description=description or None,
        teacher_id=teacher_id,
        department=department or None,
        class_name=class_name or None,
    )
    db.add(course)
    db.commit()
    flash('Ders başarıyla oluşturuldu.', 'success')
    return redirect(url_for('admin.courses'))


@admin_bp.route('/add_student_to_course', methods=['POST'])
@role_required(0)
def add_student_to_course():
    course_id = request.form.get('course_id', type=int)
    student_id = request.form.get('student_id', type=int)

    if not course_id or not student_id:
        flash('Ders ve öğrenci seçimi zorunludur.', 'error')
        return redirect(url_for('admin.courses'))

    existing = db.query(CourseStudent).filter_by(course_id=course_id, student_id=student_id).first()
    if existing:
        flash('Bu öğrenci zaten bu derse kayıtlı.', 'error')
        return redirect(url_for('admin.courses'))

    cs = CourseStudent(course_id=course_id, student_id=student_id)
    db.add(cs)
    db.commit()
    flash('Öğrenci derse eklendi.', 'success')
    return redirect(url_for('admin.courses'))


@admin_bp.route('/statistics')
@role_required(0)
def statistics():
    stats = statistics_service.get_admin_statistics()
    return render_template('admin/statistics.html', **stats)


@admin_bp.route('/export/all')
@role_required(0)
def export_all():
    buf, filename = export_service.export_all_courses()
    return send_file(buf, download_name=filename, as_attachment=True,
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')


@admin_bp.route('/export/course/<int:course_id>')
@role_required(0)
def export_course(course_id):
    result, filename_or_error = export_service.export_course_attendance(course_id)
    if result is None:
        flash(filename_or_error, 'error')
        return redirect(url_for('admin.statistics'))
    return send_file(result, download_name=filename_or_error, as_attachment=True,
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
