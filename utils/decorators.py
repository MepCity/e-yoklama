from functools import wraps
from flask import session, redirect, url_for, flash, abort


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user' not in session:
            flash('Bu sayfaya erişmek için giriş yapmalısınız.', 'error')
            return redirect(url_for('auth.login_page'))
        return f(*args, **kwargs)
    return decorated


def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if 'user' not in session:
                flash('Bu sayfaya erişmek için giriş yapmalısınız.', 'error')
                return redirect(url_for('auth.login_page'))
            if session['user']['role'] not in roles:
                abort(403)
            return f(*args, **kwargs)
        return decorated
    return decorator
