from flask import Blueprint, render_template, session, redirect, url_for, request, flash, send_file, jsonify
from utils.decorators import role_required
from database import db
from models.user import User
from models.course import Course, CourseStudent
from models.schedule import Schedule
from models.popular_course import PopularCourse
from models.classroom import Building, Classroom
from models.device_pairing import DevicePairing
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


@admin_bp.route('/edit_student/<int:student_id>', methods=['POST'])
@role_required(0)
def edit_student(student_id):
    """Öğrenci bilgilerini güncelle"""
    try:
        student = db.query(User).filter_by(id=student_id, role=2).first()
        if not student:
            return jsonify({'success': False, 'message': 'Öğrenci bulunamadı'}), 404
        
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        student_number = request.form.get('student_number', '').strip()
        department = request.form.get('department', '').strip()
        class_name = request.form.get('class_name', '').strip()
        
        # Validasyonlar
        if not username or not email or not student_number:
            return jsonify({'success': False, 'message': 'Kullanıcı adı, e-posta ve öğrenci numarası zorunludur'}), 400
        
        # Kullanıcı adı benzersizliği kontrolü (kendisi hariç)
        existing_user = db.query(User).filter(
            User.username == username,
            User.id != student_id
        ).first()
        if existing_user:
            return jsonify({'success': False, 'message': 'Bu kullanıcı adı zaten kullanılıyor'}), 400
        
        # E-posta benzersizliği kontrolü (kendisi hariç)
        existing_email = db.query(User).filter(
            User.email == email,
            User.id != student_id
        ).first()
        if existing_email:
            return jsonify({'success': False, 'message': 'Bu e-posta adresi zaten kullanılıyor'}), 400
        
        # Öğrenci numarası benzersizliği kontrolü (kendisi hariç)
        existing_student_number = db.query(User).filter(
            User.student_number == student_number,
            User.id != student_id
        ).first()
        if existing_student_number:
            return jsonify({'success': False, 'message': 'Bu öğrenci numarası zaten kullanılıyor'}), 400
        
        # Öğrenci bilgilerini güncelle
        student.username = username
        student.email = email
        student.student_number = student_number
        student.department = department if department else None
        student.class_name = class_name if class_name else None
        
        db.commit()
        
        return jsonify({'success': True, 'message': 'Öğrenci bilgileri başarıyla güncellendi'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@admin_bp.route('/reset-student-device-pairing/<int:student_id>', methods=['POST'])
@role_required(0)
def reset_student_device_pairing(student_id):
    """Öğrencinin cihaz eşleşmesini sıfırla"""
    try:
        # Öğrenciyi kontrol et
        student = db.query(User).filter_by(id=student_id, role=2).first()
        if not student:
            return jsonify({'success': False, 'message': 'Öğrenci bulunamadı'}), 404
        
        # Öğrencinin cihaz eşleşmelerini bul ve sil
        pairings = db.query(DevicePairing).filter_by(user_id=student_id).all()
        
        if not pairings:
            return jsonify({'success': False, 'message': 'Bu öğrencinin cihaz eşleşmesi bulunmamaktadır'}), 404
        
        # Tüm eşleşmeleri sil
        for pairing in pairings:
            db.delete(pairing)
        
        db.commit()
        
        return jsonify({
            'success': True, 
            'message': f'{student.username} kullanıcısının {len(pairings)} adet cihaz eşleşmesi başarıyla sıfırlandı'
        })
        
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


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


@admin_bp.route('/edit_teacher/<int:teacher_id>', methods=['POST'])
@role_required(0)
def edit_teacher(teacher_id):
    try:
        teacher = db.query(User).filter(User.id == teacher_id, User.role == 1).first()
        if not teacher:
            return {'success': False, 'message': 'Öğretmen bulunamadı.'}
        
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        branch = request.form.get('branch', '').strip()
        
        if not username or not email:
            return {'success': False, 'message': 'Tüm zorunlu alanlar doldurulmalıdır.'}
        
        # Kullanıcı adı ve e-posta benzersizlik kontrolü
        existing_user = db.query(User).filter(
            User.username == username,
            User.id != teacher_id
        ).first()
        if existing_user:
            return {'success': False, 'message': 'Bu kullanıcı adı zaten kullanılıyor.'}
        
        existing_email = db.query(User).filter(
            User.email == email,
            User.id != teacher_id
        ).first()
        if existing_email:
            return {'success': False, 'message': 'Bu e-posta adresi zaten kullanılıyor.'}
        
        # Güncelleme
        teacher.username = username
        teacher.email = email
        teacher.branch = branch or None
        
        db.commit()
        
        return {'success': True, 'message': 'Öğretmen bilgileri güncellendi.'}
        
    except Exception as e:
        return {'success': False, 'message': f'Bir hata oluştu: {str(e)}'}


@admin_bp.route('/courses')
@role_required(0)
def courses():
    try:
        show_inactive = request.args.get('show_inactive', 'false') == 'true'
        
        # Kurs sorgusu
        course_query = db.query(Course)
        if not show_inactive:
            course_query = course_query.filter(Course.is_active == 1)
        course_list = course_query.all()
        
        # Sadece aktif öğretmenler
        teacher_list = db.query(User).filter(User.role == 1, User.is_active == 1).all()
        # Sadece aktif öğrenciler
        student_list = db.query(User).filter(User.role == 2, User.is_active == 1).all()
        
        # Bölümleri al
        departments = db.query(User.department).filter(
            User.role == 1, User.department.isnot(None)
        ).distinct().all()
        departments = [d[0] for d in departments if d[0]]
        
        # Fakülte-bölüm eşleştirmesi
        faculty_departments = {
            'Mühendislik Fakültesi': [
                'Bilgisayar Mühendisliği',
                'Yazılım Mühendisliği', 
                'Elektrik-Elektronik Mühendisliği',
                'Makine Mühendisliği',
                'İnşaat Mühendisliği',
                'Endüstri Mühendisliği',
                'Kimya Mühendisliği',
                'Çevre Mühendisliği',
                'Gıda Mühendisliği'
            ],
            'Tıp Fakültesi': [
                'Tıp',
                'Diş Hekimliği',
                'Eczacılık'
            ],
            'Sağlık Bilimleri Fakültesi': [
                'Hemşirelik',
                'Fizyoterapi ve Rehabilitasyon'
            ],
            'Eğitim Fakültesi': [
                'Psikolojik Danışmanlık ve Rehberlik'
            ],
            'Fen Edebiyat Fakültesi': [
                'Psikoloji',
                'Moleküler Biyoloji ve Genetik'
            ],
            'Hukuk Fakültesi': [
                'Hukuk'
            ],
            'İktisadi ve İdari Bilimler Fakültesi': [
                'İşletme',
                'İktisat',
                'Uluslararası Ticaret ve Finans'
            ]
        }
        
        # Mevcut dersleri al (kurs şablonları olarak)
        existing_courses = db.query(Course).filter(
            Course.is_active == 1
        ).all()
        
        return render_template('admin/courses.html', 
                         courses=course_list, 
                         teachers=teacher_list, 
                         students=student_list, 
                         departments=departments,
                         faculty_departments=faculty_departments,
                         existing_courses=existing_courses,
                         show_inactive=show_inactive)
    except Exception as e:
        flash(f'Dersler sayfasında hata: {str(e)}', 'error')
        return redirect(url_for('admin.dashboard'))


def generate_course_code(department, name):
    """Otomatik ders kodu üretir"""
    if not department or not name:
        return None
    
    # Departman kod harfleri
    dept_codes = {
        'Bilgisayar Mühendisliği': 'BM',
        'Yazılım Mühendisliği': 'YM',
        'Elektrik-Elektronik Mühendisliği': 'EE',
        'Makine Mühendisliği': 'MM',
        'İnşaat Mühendisliği': 'İM',
        'Endüstri Mühendisliği': 'EM',
        'Kimya Mühendisliği': 'KM',
        'Çevre Mühendisliği': 'ÇM',
        'Gıda Mühendisliği': 'GM',
        'Tıp': 'TP',
        'Diş Hekimliği': 'DH',
        'Eczacılık': 'EC',
        'Hemşirelik': 'HS',
        'Fizyoterapi ve Rehabilitasyon': 'FR',
        'Psikoloji': 'PS',
        'Hukuk': 'HK',
        'İşletme': 'İS',
        'İktisat': 'IK',
        'Uluslararası Ticaret ve Finans': 'UF',
        'Psikolojik Danışmanlık ve Rehberlik': 'PD',
        'Moleküler Biyoloji ve Genetik': 'BG'
    }
    
    dept_code = dept_codes.get(department, 'GN')  # Genel olarak 'GN'
    
    # Ders adından kelime al
    words = name.split()
    if len(words) >= 2:
        # İki kelimeden ilk harflerini al
        course_code_part = ''.join([word[0].upper() for word in words[:2]])
    else:
        # Tek kelime ise ilk üç harfi
        course_code_part = words[0][:3].upper() if len(words[0]) >= 3 else words[0].upper()
    
    # Mevcut ders kodlarını kontrol et
    base_code = f"{dept_code}{course_code_part}"
    existing_codes = db.query(Course.code).filter(
        Course.code.like(f"{base_code}%")
    ).all()
    existing_codes = [code[0] for code in existing_codes if code[0]]
    
    if not existing_codes:
        return base_code
    
    # Eğer aynı kod varsa sonuna sayı ekle
    counter = 1
    while f"{base_code}{counter:02d}" in existing_codes:
        counter += 1
    
    return f"{base_code}{counter:02d}"


@admin_bp.route('/create_course', methods=['POST'])
@role_required(0)
def create_course():
    try:
        # Ders bilgileri
        name = request.form.get('name', '').strip()
        code = request.form.get('code', '').strip()
        description = request.form.get('description', '').strip()
        teacher_id = request.form.get('teacher_id', type=int)
        department = request.form.get('department', '').strip()
        class_name = request.form.get('class_name', '').strip()
        building_code = request.form.get('building_code', '').strip()
        classroom_code = request.form.get('classroom_code', '').strip()
        day_of_week = request.form.get('day_of_week', type=int)
        start_time = request.form.get('start_time', '').strip()
        end_time = request.form.get('end_time', '').strip()

        if not name or not teacher_id:
            flash('Ders adı ve öğretmen seçimi zorunludur.', 'error')
            return redirect(url_for('admin.courses'))
        
        # Ders kodu belirtilmemişse otomatik oluştur
        if not code:
            code = generate_course_code(department, name)
            if code:
                flash(f'Otomatik ders kodu oluşturuldu: {code}', 'info')
        else:
            # Manuel kod girilmişse benzersizlik kontrolü
            existing_code = db.query(Course).filter(Course.code == code).first()
            if existing_code:
                flash(f'Bu ders kodu ({code}) zaten kullanılıyor. Başka bir kod deneyin veya boş bırakarak otomatik oluşturun.', 'error')
                return redirect(url_for('admin.courses'))

        # Ders çakışma kontrolleri
        if day_of_week and start_time and end_time:
            # 1. Aynı öğretmenin aynı gün ve saatte başka dersi var mı?
            conflict = db.query(Course).filter(
                Course.teacher_id == teacher_id,
                Course.day_of_week == day_of_week,
                Course.is_active == 1  # Sadece aktif dersler kontrol edilir
            ).filter(
                # Zaman çakışması kontrolü
                (Course.start_time <= start_time) & (Course.end_time > start_time) |
                (Course.start_time < end_time) & (Course.end_time >= end_time) |
                (Course.start_time >= start_time) & (Course.end_time <= end_time)
            ).first()
            
            if conflict:
                flash(f'Öğretmenin aynı gün ve saatte başka dersi var: {conflict.name} ({conflict.start_time}-{conflict.end_time})', 'error')
                return redirect(url_for('admin.courses'))

            # 2. Aynı derslikte aynı gün ve saatte başka ders var mı?
            if building_code and classroom_code:
                classroom_conflict = db.query(Course).filter(
                    Course.building_code == building_code,
                    Course.classroom_code == classroom_code,
                    Course.day_of_week == day_of_week,
                    Course.is_active == 1
                ).filter(
                    (Course.start_time <= start_time) & (Course.end_time > start_time) |
                    (Course.start_time < end_time) & (Course.end_time >= end_time) |
                    (Course.start_time >= start_time) & (Course.end_time <= end_time)
                ).first()
                
                if classroom_conflict:
                    flash(f'Dersliğin aynı gün ve saatte başka ders var: {classroom_conflict.name} ({classroom_conflict.start_time}-{classroom_conflict.end_time})', 'error')
                    return redirect(url_for('admin.courses'))

            # 3. Aynı sınıfta aynı gün ve saatte başka ders var mı? (class_name kontrolü)
            if class_name:
                class_conflict = db.query(Course).filter(
                    Course.class_name == class_name,
                    Course.day_of_week == day_of_week,
                    Course.is_active == 1
                ).filter(
                    (Course.start_time <= start_time) & (Course.end_time > start_time) |
                    (Course.start_time < end_time) & (Course.end_time >= end_time) |
                    (Course.start_time >= start_time) & (Course.end_time <= end_time)
                ).first()
                
                if class_conflict:
                    flash(f'Sınıfın aynı gün ve saatte başka ders var: {class_conflict.name} ({class_conflict.start_time}-{class_conflict.end_time})', 'error')
                    return redirect(url_for('admin.courses'))

        # Öğretmenin fakültesi ile ders fakültesini kontrol et
        teacher = db.query(User).filter(User.id == teacher_id).first()
        if teacher and teacher.branch and department:
            # Fakülte-bölüm eşleştirmesi
            faculty_departments = {
                'Mühendislik Fakültesi': [
                    'Bilgisayar Mühendisliği', 'Yazılım Mühendisliği', 'Elektrik-Elektronik Mühendisliği',
                    'Makine Mühendisliği', 'İnşaat Mühendisliği', 'Endüstri Mühendisliği',
                    'Kimya Mühendisliği', 'Çevre Mühendisliği', 'Gıda Mühendisliği'
                ],
                'Tıp Fakültesi': ['Tıp', 'Diş Hekimliği', 'Eczacılık'],
                'Sağlık Bilimleri Fakültesi': ['Hemşirelik', 'Fizyoterapi ve Rehabilitasyon'],
                'Eğitim Fakültesi': ['Psikolojik Danışmanlık ve Rehberlik'],
                'Fen Edebiyat Fakültesi': ['Psikoloji', 'Moleküler Biyoloji ve Genetik'],
                'Hukuk Fakültesi': ['Hukuk'],
                'İktisadi ve İdari Bilimler Fakültesi': ['İşletme', 'İktisat', 'Uluslararası Ticaret ve Finans']
            }
            
            # Öğretmenin ve dersin fakültelerini bul
            teacher_faculty = None
            course_faculty = None
            
            for faculty, departments in faculty_departments.items():
                if teacher.branch in departments:
                    teacher_faculty = faculty
                if department in departments:
                    course_faculty = faculty
            
            # Farklı fakültelerde ise izin verme
            if teacher_faculty and course_faculty and teacher_faculty != course_faculty:
                flash(f'Öğretmenin fakültesi ({teacher_faculty}) ile dersin fakültesi ({course_faculty}) uyuşmuyor. Öğretmen sadece kendi fakültesindeki dersleri verebilir.', 'error')
                return redirect(url_for('admin.courses'))

        # Yeni ders oluştur
        course = Course(
            name=name,
            code=code or None,
            description=description or None,
            teacher_id=teacher_id,
            department=department or None,
            class_name=class_name or None,
            building_code=building_code or None,
            classroom_code=classroom_code or None,
            day_of_week=day_of_week,
            start_time=start_time,
            end_time=end_time,
            is_active=1  # Aktif olarak oluştur
        )
        db.add(course)
        db.commit()
        flash('Ders oluşturuldu. Öğretmen onayı bekleniyor.', 'success')
        return redirect(url_for('admin.courses'))
    except Exception as e:
        return {'success': False, 'message': f'Bir hata oluştu: {str(e)}'}


@admin_bp.route('/edit_course/<int:course_id>', methods=['POST'])
@role_required(0)
def edit_course(course_id):
    try:
        course = db.query(Course).filter(Course.id == course_id).first()
        if not course:
            return {'success': False, 'message': 'Ders bulunamadı.'}
        
        name = request.form.get('name', '').strip()
        code = request.form.get('code', '').strip()
        description = request.form.get('description', '').strip()
        teacher_id = request.form.get('teacher_id', type=int)
        department = request.form.get('department', '').strip()
        class_name = request.form.get('class_name', '').strip()
        building_code = request.form.get('building_code', '').strip()
        classroom_code = request.form.get('classroom_code', '').strip()
        day_of_week = request.form.get('day_of_week', type=int)
        start_time = request.form.get('start_time', '').strip()
        end_time = request.form.get('end_time', '').strip()

        if not name or not teacher_id:
            return {'success': False, 'message': 'Ders adı ve öğretmen seçimi zorunludur.'}
        
        # Ders kodu belirtilmemişse otomatik oluştur
        if not code:
            code = generate_course_code(department, name)
        else:
            # Manuel kod girilmişse benzersizlik kontrolü (kendisi hariç)
            existing_code = db.query(Course).filter(Course.code == code, Course.id != course_id).first()
            if existing_code:
                return {'success': False, 'message': f'Bu ders kodu ({code}) zaten kullanılıyor.'}

        # Ders çakışma kontrolleri
        if day_of_week and start_time and end_time:
            # 1. Aynı öğretmenin aynı gün ve saatte başka dersi var mı? (kendisi hariç)
            conflict = db.query(Course).filter(
                Course.teacher_id == teacher_id,
                Course.day_of_week == day_of_week,
                Course.is_active == 1,
                Course.id != course_id
            ).filter(
                # Zaman çakışması kontrolü
                (Course.start_time <= start_time) & (Course.end_time > start_time) |
                (Course.start_time < end_time) & (Course.end_time >= end_time) |
                (Course.start_time >= start_time) & (Course.end_time <= end_time)
            ).first()
            
            if conflict:
                return {'success': False, 'message': f'Öğretmenin aynı gün ve saatte başka dersi var: {conflict.name} ({conflict.start_time}-{conflict.end_time})'}

            # 2. Aynı derslikte aynı gün ve saatte başka ders var mı? (kendisi hariç)
            if building_code and classroom_code:
                classroom_conflict = db.query(Course).filter(
                    Course.building_code == building_code,
                    Course.classroom_code == classroom_code,
                    Course.day_of_week == day_of_week,
                    Course.is_active == 1,
                    Course.id != course_id
                ).filter(
                    (Course.start_time <= start_time) & (Course.end_time > start_time) |
                    (Course.start_time < end_time) & (Course.end_time >= end_time) |
                    (Course.start_time >= start_time) & (Course.end_time <= end_time)
                ).first()
                
                if classroom_conflict:
                    return {'success': False, 'message': f'Dersliğin aynı gün ve saatte başka ders var: {classroom_conflict.name} ({classroom_conflict.start_time}-{classroom_conflict.end_time})'}

            # 3. Aynı sınıfta aynı gün ve saatte başka ders var mı? (kendisi hariç)
            if class_name:
                class_conflict = db.query(Course).filter(
                    Course.class_name == class_name,
                    Course.day_of_week == day_of_week,
                    Course.is_active == 1,
                    Course.id != course_id
                ).filter(
                    (Course.start_time <= start_time) & (Course.end_time > start_time) |
                    (Course.start_time < end_time) & (Course.end_time >= end_time) |
                    (Course.start_time >= start_time) & (Course.end_time <= end_time)
                ).first()
                
                if class_conflict:
                    return {'success': False, 'message': f'Sınıfın aynı gün ve saatte başka ders var: {class_conflict.name} ({class_conflict.start_time}-{class_conflict.end_time})'}

        # Öğretmenin fakültesi ile ders fakültesini kontrol et
        teacher = db.query(User).filter(User.id == teacher_id).first()
        if teacher and teacher.branch and department:
            # Fakülte-bölüm eşleştirmesi
            faculty_departments = {
                'Mühendislik Fakültesi': [
                    'Bilgisayar Mühendisliği', 'Yazılım Mühendisliği', 'Elektrik-Elektronik Mühendisliği',
                    'Makine Mühendisliği', 'İnşaat Mühendisliği', 'Endüstri Mühendisliği',
                    'Kimya Mühendisliği', 'Çevre Mühendisliği', 'Gıda Mühendisliği'
                ],
                'Tıp Fakültesi': ['Tıp', 'Diş Hekimliği', 'Eczacılık'],
                'Sağlık Bilimleri Fakültesi': ['Hemşirelik', 'Fizyoterapi ve Rehabilitasyon'],
                'Eğitim Fakültesi': ['Psikolojik Danışmanlık ve Rehberlik'],
                'Fen Edebiyat Fakültesi': ['Psikoloji', 'Moleküler Biyoloji ve Genetik'],
                'Hukuk Fakültesi': ['Hukuk'],
                'İktisadi ve İdari Bilimler Fakültesi': ['İşletme', 'İktisat', 'Uluslararası Ticaret ve Finans']
            }
            
            # Öğretmenin ve dersin fakültelerini bul
            teacher_faculty = None
            course_faculty = None
            
            for faculty, departments in faculty_departments.items():
                if teacher.branch in departments:
                    teacher_faculty = faculty
                if department in departments:
                    course_faculty = faculty
            
            # Farklı fakültelerde ise izin verme
            if teacher_faculty and course_faculty and teacher_faculty != course_faculty:
                return {'success': False, 'message': f'Öğretmenin fakültesi ({teacher_faculty}) ile dersin fakültesi ({course_faculty}) uyuşmuyor. Öğretmen sadece kendi fakültesindeki dersleri verebilir.'}

        # Güncelleme
        course.name = name
        course.code = code or None
        course.description = description or None
        course.teacher_id = teacher_id
        course.department = department or None
        course.class_name = class_name or None
        course.building_code = building_code or None
        course.classroom_code = classroom_code or None
        course.day_of_week = day_of_week
        course.start_time = start_time
        course.end_time = end_time
        
        db.commit()
        
        return {'success': True, 'message': 'Ders bilgileri güncellendi.'}
        
    except Exception as e:
        return {'success': False, 'message': f'Bir hata oluştu: {str(e)}'}


@admin_bp.route('/toggle_course/<int:course_id>', methods=['POST'])
@role_required(0)
def toggle_course(course_id):
    try:
        course = db.query(Course).filter(Course.id == course_id).first()
        if not course:
            flash('Ders bulunamadı.', 'error')
            return redirect(url_for('admin.courses'))
        
        course.is_active = 0 if course.is_active == 1 else 1
        db.commit()
        
        status = "pasif" if course.is_active == 0 else "aktif"
        flash(f'Ders {status} durumuna getirildi.', 'success')
        return redirect(url_for('admin.courses'))
    except Exception as e:
        flash(f'Ders durumu değiştirilirken hata: {str(e)}', 'error')
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
