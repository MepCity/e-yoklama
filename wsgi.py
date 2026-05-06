import os

from app import create_app, socketio

config_name = os.environ.get('FLASK_CONFIG', 'development')
app = create_app(config_name)

if __name__ == '__main__':
    debug = app.config.get('DEBUG', False)
    socketio.run(app, host='0.0.0.0', port=5050, debug=debug, allow_unsafe_werkzeug=debug)
