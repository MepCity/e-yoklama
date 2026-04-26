from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from services import auth_service

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET'])
def login_page():
    if 'user' in session:
        return redirect(url_for('home'))
    return render_template('auth/login.html')


@auth_bp.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')

    if not username or not password:
        flash('Kullanici adi ve sifre gereklidir.', 'error')
        return redirect(url_for('auth.login_page'))

    user, error = auth_service.login(username, password)
    if error:
        flash(error, 'error')
        return redirect(url_for('auth.login_page'))

    session['user'] = user.to_dict()

    if user.role == 0:
        return redirect(url_for('admin.dashboard'))
    elif user.role == 1:
        return redirect(url_for('teacher.dashboard'))
    else:
        return redirect(url_for('student.dashboard'))


@auth_bp.route('/register', methods=['POST'])
def register():
    username = request.form.get('username', '').strip()
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '')
    student_number = request.form.get('student_number', '').strip()
    department = request.form.get('department', '').strip()
    class_name = request.form.get('class_name', '').strip()
    phone = request.form.get('phone', '').strip()

    if not username or not email or not password or not student_number:
        flash('Tum zorunlu alanlar doldurulmalidir.', 'error')
        return redirect(url_for('auth.login_page'))

    user, error = auth_service.register_student(
        username=username,
        email=email,
        password=password,
        student_number=student_number,
        department=department or None,
        class_name=class_name or None,
        phone=phone or None,
    )
    if error:
        flash(error, 'error')
        return redirect(url_for('auth.login_page'))

    flash('Kayit basarili! Giris yapabilirsiniz.', 'success')
    return redirect(url_for('auth.login_page'))


@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('Basariyla cikis yapildi.', 'success')
    return redirect(url_for('auth.login_page'))
