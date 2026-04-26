from datetime import datetime, timezone

from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app
from services import auth_service
from utils.rate_limit import limiter

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET'])
def login_page():
    if 'user' in session:
        return redirect(url_for('home'))
    return render_template('auth/login.html')


@auth_bp.route('/login', methods=['POST'])
@limiter.limit(lambda: current_app.config.get('RATE_LIMIT_LOGIN', '5/minute'))
def login():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')

    if not username or not password:
        flash('Kullanıcı adı ve şifre gereklidir.', 'error')
        return redirect(url_for('auth.login_page'))

    user, error = auth_service.login(username, password)
    if error:
        flash(error, 'error')
        return redirect(url_for('auth.login_page'))

    session.permanent = True
    session['user'] = user.to_dict()
    session['last_activity_at'] = datetime.now(timezone.utc).isoformat()

    if user.role == 0:
        return redirect(url_for('admin.dashboard'))
    elif user.role == 1:
        return redirect(url_for('teacher.dashboard'))
    else:
        return redirect(url_for('student.dashboard'))


@auth_bp.route('/register', methods=['POST'])
@limiter.limit(lambda: current_app.config.get('RATE_LIMIT_REGISTER', '5/minute'))
def register():
    username = request.form.get('username', '').strip()
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '')
    student_number = request.form.get('student_number', '').strip()
    department = request.form.get('department', '').strip()
    class_name = request.form.get('class_name', '').strip()
    phone = request.form.get('phone', '').strip()

    if not username or not email or not password or not student_number:
        flash('Tüm zorunlu alanlar doldurulmalıdır.', 'error')
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

    flash('Kayıt başarılı! Giriş yapabilirsiniz.', 'success')
    return redirect(url_for('auth.login_page'))


@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('Başarıyla çıkış yapıldı.', 'success')
    return redirect(url_for('auth.login_page'))
