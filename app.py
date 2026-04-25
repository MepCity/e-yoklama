from flask import Flask, render_template, request, redirect, url_for, session, flash
from databases import engine, Base, init_db
from views.auth import auth_bp
from views.admin import admin_bp
from views.teacher import teacher_bp
from views.student import student_bp
import os
import webbrowser

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Güvenlik için değiştirin

# Blueprint'leri kaydet
app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(teacher_bp, url_prefix='/teacher')
app.register_blueprint(student_bp, url_prefix='/student')

# Veritabanı tablolarını oluştur (yoksa)
init_db()

@app.route('/')
def home():
    if 'user' in session:
        user = session['user']
        if user['role'] == 0:
            return redirect(url_for('admin.dashboard'))
        elif user['role'] == 1:
            return redirect(url_for('teacher.dashboard'))
        elif user['role'] == 2:
            return redirect(url_for('student.dashboard'))
    return redirect(url_for('auth.login_page'))

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404


# Microsoft Edge ile tarayıcıyı aç
url = 'http://127.0.0.1:5000'
    
# Edge'i başlat ve URL'i aç
os.system(f'start msedge "{url}"')
    
if __name__ == '__main__':
    
    # Flask uygulamasını çalıştır
    app.run(debug=True, host='0.0.0.0', port=5000)