from flask import Flask, redirect, url_for, session, render_template
from flask_socketio import SocketIO
from config import config

socketio = SocketIO()


def create_app(config_name='development'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Veritabani
    from database import init_db
    init_db(app)

    # SocketIO
    socketio.init_app(app, cors_allowed_origins='*')

    # Blueprint'ler
    from views.auth import auth_bp
    from views.admin import admin_bp
    from views.teacher import teacher_bp
    from views.student import student_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(teacher_bp, url_prefix='/teacher')
    app.register_blueprint(student_bp, url_prefix='/student')

    # Ana sayfa
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

    # Hata sayfalari
    @app.errorhandler(404)
    def not_found(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(403)
    def forbidden(error):
        return render_template('errors/403.html'), 403

    # Template context - tum template'lerde kullanilabilir helper'lar
    from utils.helpers import day_name, format_datetime, format_date, STATUS_LABELS, STATUS_COLORS
    app.jinja_env.globals.update(
        day_name=day_name,
        format_datetime=format_datetime,
        format_date=format_date,
        STATUS_LABELS=STATUS_LABELS,
        STATUS_COLORS=STATUS_COLORS,
    )

    return app
