from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models.users import Users

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        result = Users.login(username, password)
        if result:
            session['user'] = {'id': result['user'].id, 'username': result['user'].username, 'role': result['user'].role}
            session['token'] = result['token']
            flash('Giriş başarılı!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Geçersiz kullanıcı adı veya şifre.', 'error')
    return render_template('auth.html')

@auth_bp.route('/register', methods=['POST'])
def register():
    # Sadece öğrenci kaydına izin ver
    username = request.form['username']
    email = request.form['email']
    password = request.form['password']
    student_number = request.form.get('student_number', '')
    department = request.form.get('department', '')
    class_name = request.form.get('class_name', '')
    
    # Öğrenci olarak kaydet (role=2)
    Users.register(username, email, password, role=2, student_number=student_number, 
                   department=department, class_name=class_name)
    flash('Kayıt başarılı! Giriş yapın.', 'success')
    return redirect(url_for('auth.login_page'))

@auth_bp.route('/logout')
def logout():
    token = session.get('token')
    if token:
        Users.logout(token)
    session.clear()
    flash('Çıkış yapıldı.', 'info')
    return redirect(url_for('auth.login_page'))

@auth_bp.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        # Şifre sıfırlama mantığı (şimdilik basit)
        flash('Şifre sıfırlama bağlantısı gönderildi.', 'info')
    return render_template('auth.html')