from datetime import datetime, timezone

from flask import Flask, redirect, url_for, session, render_template, request, flash
from flask_socketio import SocketIO
from config import config

socketio = SocketIO(manage_session=False)


def create_app(config_name='development'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Rate limiting
    from utils.rate_limit import limiter
    limiter.init_app(app)

    # Veritabani
    from database import init_db
    init_db(app)

    # SocketIO
    socketio.init_app(app, cors_allowed_origins='*')
    from sockets.attendance_socket import register_socket_events
    register_socket_events(socketio)

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

    @app.before_request
    def enforce_session_timeout():
        if request.endpoint == 'static' or 'user' not in session:
            return None

        now = datetime.now(timezone.utc)
        last_activity = session.get('last_activity_at')
        timeout_seconds = app.config['PERMANENT_SESSION_LIFETIME'].total_seconds()

        if last_activity:
            try:
                last_seen = datetime.fromisoformat(last_activity)
            except ValueError:
                last_seen = None
            if last_seen and last_seen.tzinfo is None:
                last_seen = last_seen.replace(tzinfo=timezone.utc)
            if last_seen and (now - last_seen).total_seconds() > timeout_seconds:
                session.clear()
                flash('Oturum suresi doldu. Lutfen tekrar giris yapin.', 'warning')
                return redirect(url_for('auth.login_page'))

        session['last_activity_at'] = now.isoformat()
        session.permanent = True
        return None

    # Hata sayfalari
    @app.errorhandler(404)
    def not_found(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(403)
    def forbidden(error):
        return render_template('errors/403.html'), 403

    @app.errorhandler(429)
    def too_many_requests(error):
        return render_template('errors/429.html'), 429

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
