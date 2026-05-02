from flask import Blueprint, render_template, session, redirect, url_for, request, flash, send_file
from utils.decorators import role_required
from database import db
from models.user import User
from models.course import Course, CourseStudent
from models.schedule import Schedule
from models.popular_course import PopularCourse
from models.classroom import Building, Classroom
from services import auth_service, statistics_service, export_service

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/dashboard')
@role_required(0)
def dashboard():
    return render_template('admin/dashboard.html')


@admin_bp.route('/students')
@role_required(0)
def students():
    show_inactive = request.args.get('show_inactive', 'false') == 'true'
    sort_by = request.args.get('sort', 'student_number')
    department = request.args.get('department', '')

    query = db.query(User).filter(User.role == 2)

    if not show_inactive:
        query = query.filter(User.is_active == 1)

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

    return render_template('admin/students.html', students=student_list, departments=departments, show_inactive=show_inactive)


@admin_bp.route('/teachers')
@role_required(0)
def teachers():
    try:
        show_inactive = request.args.get('show_inactive', 'false') == 'true'
        query = db.query(User).filter(User.role == 1)
        
        if not show_inactive:
            query = query.filter(User.is_active == 1)
            
        teacher_list = query.all()
        return render_template('admin/teachers.html', teachers=teacher_list, show_inactive=show_inactive)
    except Exception as e:
        flash(f'Öğretmenler sayfasında hata: {str(e)}', 'error')
        return redirect(url_for('admin.dashboard'))


@admin_bp.route('/add_student', methods=['POST'])
@role_required(0)
def add_student():
    username = request.form.get('username', '').strip()
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '')
    student_number = request.form.get('student_number', '').strip()
    department = request.form.get('department', '').strip()
    class_name = request.form.get('class_name', '').strip()

    if not username or not email or not password or not student_number:
        flash('Tüm zorunlu alanlar doldurulmalıdır.', 'error')
        return redirect(url_for('admin.students'))

    user, error = auth_service.register_student(username, email, password, student_number, department or None, class_name or None)
    if error:
        flash(error, 'error')
    else:
        flash('Öğrenci başarıyla eklendi.', 'success')
    return redirect(url_for('admin.students'))


@admin_bp.route('/toggle_student/<int:student_id>', methods=['POST'])
@role_required(0)
def toggle_student(student_id):
    student = db.query(User).filter(User.id == student_id, User.role == 2).first()
    if not student:
        flash('Öğrenci bulunamadı.', 'error')
        return redirect(url_for('admin.students'))
    
    student.is_active = 0 if student.is_active == 1 else 1
    db.commit()
    
    status = "pasif" if student.is_active == 0 else "aktif"
    flash(f'Öğrenci {status} durumuna getirildi.', 'success')
    return redirect(url_for('admin.students'))


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


@admin_bp.route('/toggle_teacher/<int:teacher_id>', methods=['POST'])
@role_required(0)
def toggle_teacher(teacher_id):
    teacher = db.query(User).filter(User.id == teacher_id, User.role == 1).first()
    if not teacher:
        flash('Öğretmen bulunamadı.', 'error')
        return redirect(url_for('admin.teachers'))
    
    teacher.is_active = 0 if teacher.is_active == 1 else 1
    db.commit()
    
    status = "pasif" if teacher.is_active == 0 else "aktif"
    flash(f'Öğretmen {status} durumuna getirildi.', 'success')
    return redirect(url_for('admin.teachers'))


@admin_bp.route('/courses')
@role_required(0)
def courses():
    try:
        show_inactive = request.args.get('show_inactive', 'false') == 'true'
        
        # Kurs sorgusu - bina ve sınıf bilgileriyle birlikte
        course_query = db.query(Course).outerjoin(Building, Course.building_id == Building.id).outerjoin(Classroom, Course.classroom_id == Classroom.id)
        if not show_inactive:
            course_query = course_query.filter(Course.is_active == 1)
        course_list = course_query.all()
        
        # Sadece aktif öğretmenler
        teacher_list = db.query(User).filter(User.role == 1, User.is_active == 1).all()
        # Sadece aktif öğrenciler
        student_list = db.query(User).filter(User.role == 2, User.is_active == 1).all()
        # Popüler dersler
        popular_courses = db.query(PopularCourse).filter(PopularCourse.is_active == 1).all()
        # Binalar
        buildings = db.query(Building).filter(Building.is_active == True).all()
        # Sınıflar
        classrooms = db.query(Classroom).filter(Classroom.is_active == True).all()
        
        return render_template('admin/courses.html', 
                         courses=course_list, 
                         teachers=teacher_list, 
                         students=student_list, 
                         popular_courses=popular_courses, 
                         buildings=buildings,
                         classrooms=classrooms,
                         show_inactive=show_inactive)
    except Exception as e:
        flash(f'Dersler sayfasında hata: {str(e)}', 'error')
        return redirect(url_for('admin.dashboard'))


@admin_bp.route('/create_course', methods=['POST'])
@role_required(0)
def create_course():
    try:
        # Popüler ders seçimi
        popular_course_id = request.form.get('popular_course_id', type=int)
        # Özel ders bilgileri
        name = request.form.get('name', '').strip()
        code = request.form.get('code', '').strip()
        description = request.form.get('description', '').strip()
        teacher_id = request.form.get('teacher_id', type=int)
        department = request.form.get('department', '').strip()
        class_name = request.form.get('class_name', '').strip()
        building_id = request.form.get('building_id', type=int)
        classroom_id = request.form.get('classroom_id', type=int)
        day_of_week = request.form.get('day_of_week', type=int)
        start_time = request.form.get('start_time', '').strip()
        end_time = request.form.get('end_time', '').strip()

        if popular_course_id:
            # Popüler ders seçildiyse bilgileri database'den al
            popular_course = db.query(PopularCourse).filter(PopularCourse.id == popular_course_id).first()
            if not popular_course:
                flash('Popüler ders bulunamadı.', 'error')
                return redirect(url_for('admin.courses'))
            
            name = popular_course.course_name
            code = popular_course.course_code
            description = popular_course.description
            department = popular_course.department

        if not name or not teacher_id:
            flash('Ders adı ve öğretmen seçimi zorunludur.', 'error')
            return redirect(url_for('admin.courses'))

        # Ders çakışma kontrolleri
        if day_of_week and start_time and end_time:
            # 1. Aynı öğretmenin aynı gün ve saatte başka dersi var mı?
            conflict = db.query(Course).filter(
                Course.teacher_id == teacher_id,
                Course.day_of_week == day_of_week,
                Course.status == 1,  # Sadece aktif dersler kontrol edilir
                Course.id != request.form.get('course_id', 0)  # Edit durumunda kendini kontrol etme
            ).filter(
                # Zaman çakışması kontrolü
                (Course.start_time <= start_time) & (Course.end_time > start_time) |
                (Course.start_time < end_time) & (Course.end_time >= end_time) |
                (Course.start_time >= start_time) & (Course.end_time <= end_time)
            ).first()
            
            if conflict:
                flash(f'Öğretmenin aynı gün ve saatte başka dersi var: {conflict.name} ({conflict.start_time}-{conflict.end_time})', 'error')
                return redirect(url_for('admin.courses'))

            # 2. Aynı sınıfta aynı gün ve saatte başka ders var mı?
            if classroom_id:
                classroom_conflict = db.query(Course).filter(
                    Course.classroom_id == classroom_id,
                    Course.day_of_week == day_of_week,
                    Course.status == 1,
                    Course.id != request.form.get('course_id', 0)
                ).filter(
                    (Course.start_time <= start_time) & (Course.end_time > start_time) |
                    (Course.start_time < end_time) & (Course.end_time >= end_time) |
                    (Course.start_time >= start_time) & (Course.end_time <= end_time)
                ).first()
                
                if classroom_conflict:
                    flash(f'Sınıfın aynı gün ve saatte başka ders var: {classroom_conflict.name} ({classroom_conflict.start_time}-{classroom_conflict.end_time})', 'error')
                    return redirect(url_for('admin.courses'))

            # 3. Aynı sınıfta aynı gün ve saatte başka ders var mı? (class_name kontrolü)
            if class_name:
                class_conflict = db.query(Course).filter(
                    Course.class_name == class_name,
                    Course.day_of_week == day_of_week,
                    Course.status == 1,
                    Course.id != request.form.get('course_id', 0)
                ).filter(
                    (Course.start_time <= start_time) & (Course.end_time > start_time) |
                    (Course.start_time < end_time) & (Course.end_time >= end_time) |
                    (Course.start_time >= start_time) & (Course.end_time <= end_time)
                ).first()
                
                if class_conflict:
                    flash(f'Sınıfın aynı gün ve saatte başka ders var: {class_conflict.name} ({class_conflict.start_time}-{class_conflict.end_time})', 'error')
                    return redirect(url_for('admin.courses'))

        # Öğretmenin bölümü ile ders bölümünü kontrol et (öğretmen branşı yoksa izin ver)
        teacher = db.query(User).filter(User.id == teacher_id).first()
        if teacher and teacher.branch and department and teacher.branch != department:
            flash(f'Öğretmenin bölümü ({teacher.branch}) ile dersin bölümü ({department}) uyuşmuyor.', 'error')
            return redirect(url_for('admin.courses'))

        # Yeni ders oluştur - öğretmen onayı bekliyor olarak
        course = Course(
            name=name,
            code=code or None,
            description=description or None,
            teacher_id=teacher_id,
            department=department or None,
            class_name=class_name or None,
            building_id=building_id,
            classroom_id=classroom_id,
            day_of_week=day_of_week,
            start_time=start_time,
            end_time=end_time,
            teacher_approval=0,  # Öğretmen onayı bekliyor
            status=0  # Onay bekliyor
        )
        db.add(course)
        db.commit()
        flash('Ders oluşturuldu. Öğretmen onayı bekleniyor.', 'success')
        return redirect(url_for('admin.courses'))
    except Exception as e:
        flash(f'Ders oluşturulurken hata: {str(e)}', 'error')
        return redirect(url_for('admin.courses'))


@admin_bp.route('/toggle_course/<int:course_id>', methods=['POST'])
@role_required(0)
def toggle_course(course_id):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        flash('Ders bulunamadı.', 'error')
        return redirect(url_for('admin.courses'))
    
    course.is_active = 0 if course.is_active == 1 else 1
    db.commit()
    
    status = "pasif" if course.is_active == 0 else "aktif"
    flash(f'Ders {status} durumuna getirildi.', 'success')
    return redirect(url_for('admin.courses'))


@admin_bp.route('/student_approvals')
@role_required(0)
def student_approvals():
    """Adminin öğrenci onayları"""
    # Admin onayı bekleyen öğrenciler
    pending_students = db.query(CourseStudent).filter(
        CourseStudent.admin_approval == 0
    ).all()
    
    # Admin onayı almış öğrenciler
    approved_students = db.query(CourseStudent).filter(
        CourseStudent.admin_approval == 1
    ).all()
    
    # Reddedilen öğrenciler
    rejected_students = db.query(CourseStudent).filter(
        CourseStudent.admin_approval == 2
    ).all()
    
    return render_template('admin/student_approvals.html',
                         pending_students=pending_students,
                         approved_students=approved_students,
                         rejected_students=rejected_students)


@admin_bp.route('/approve_student/<int:cs_id>', methods=['POST'])
@role_required(0)
def approve_student(cs_id):
    """Öğrenci ders kaydını onayla/reddet"""
    course_student = db.query(CourseStudent).filter(CourseStudent.id == cs_id).first()
    if not course_student:
        flash('Öğrenci kaydı bulunamadı.', 'error')
        return redirect(url_for('admin.student_approvals'))
    
    action = request.form.get('action')
    if action == 'approve':
        course_student.admin_approval = 1
        flash('Öğrenci ders kaydı onaylandı.', 'success')
    elif action == 'reject':
        course_student.admin_approval = 2
        flash('Öğrenci ders kaydı reddedildi.', 'warning')
    
    db.commit()
    return redirect(url_for('admin.student_approvals'))


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
    try:
        stats = statistics_service.get_admin_statistics()
        return render_template('admin/statistics.html', **stats)
    except Exception as e:
        flash(f'İstatistikler sayfasında hata: {str(e)}', 'error')
        return redirect(url_for('admin.dashboard'))


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


@admin_bp.route('/schedule')
@role_required(0)
def schedule():
    schedules = db.query(Schedule).join(Course).join(User).all()
    courses = db.query(Course).all()
    return render_template('admin/schedule.html', schedules=schedules, courses=courses)


@admin_bp.route('/add_schedule', methods=['POST'])
@role_required(0)
def add_schedule():
    course_id = request.form.get('course_id', type=int)
    day_of_week = request.form.get('day_of_week', type=int)
    start_time = request.form.get('start_time', '').strip()
    end_time = request.form.get('end_time', '').strip()
    room = request.form.get('room', '').strip()

    if not all([course_id, day_of_week is not None, start_time, end_time]):
        flash('Tüm zorunlu alanlar doldurulmalıdır.', 'error')
        return redirect(url_for('admin.schedule'))

    # Çakışma kontrolü
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        flash('Ders bulunamadı.', 'error')
        return redirect(url_for('admin.schedule'))

    # Aynı sınıfta aynı saatte başka ders var mı?
    room_conflict = db.query(Schedule).join(Course).filter(
        Schedule.day_of_week == day_of_week,
        Schedule.room == room,
        Schedule.start_time < end_time,
        Schedule.end_time > start_time
    ).first()

    if room_conflict:
        flash(f'Bu sınıfta ({room}) aynı saatte {room_conflict.course.name} dersi bulunmaktadır.', 'error')
        return redirect(url_for('admin.schedule'))

    # Öğretmenin aynı saatte başka dersi var mı?
    teacher_conflict = db.query(Schedule).join(Course).filter(
        Schedule.day_of_week == day_of_week,
        Course.teacher_id == course.teacher_id,
        Schedule.start_time < end_time,
        Schedule.end_time > start_time
    ).first()

    if teacher_conflict:
        flash(f'Öğretmenin aynı saatte {teacher_conflict.course.name} dersi bulunmaktadır.', 'error')
        return redirect(url_for('admin.schedule'))

    schedule = Schedule(
        course_id=course_id,
        day_of_week=day_of_week,
        start_time=start_time,
        end_time=end_time,
        room=room or None
    )
    db.add(schedule)
    db.commit()
    flash('Ders programı başarıyla eklendi.', 'success')
    return redirect(url_for('admin.schedule'))
