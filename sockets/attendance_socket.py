from flask import session as flask_session
from flask_socketio import emit, join_room, leave_room

from services import attendance_service
from utils.qr_generator import generate_qr_base64

_registered = False


def _room_name(session_id):
    return f'attendance:{session_id}'


def _current_user():
    return flask_session.get('user') or {}


def _can_access_session(att_session):
    user = _current_user()
    if not user or not att_session:
        return False
    if user.get('role') == 1:
        return att_session.teacher_id == user.get('id')
    return False


def _code_payload(att_session):
    payload = attendance_service.get_code_payload(att_session)
    payload['qr_base64'] = generate_qr_base64(att_session.current_code)
    return payload


def register_socket_events(socketio):
    global _registered
    if _registered:
        return
    _registered = True

    @socketio.on('join_attendance_session')
    def join_attendance_session(data):
        session_id = (data or {}).get('session_id')
        att_session = attendance_service.get_session_by_id(session_id)
        if not _can_access_session(att_session):
            emit('attendance_error', {'message': 'Oturuma erisim yetkiniz yok.'})
            return

        join_room(_room_name(session_id))
        emit('code_rotated', _code_payload(att_session))

    @socketio.on('leave_attendance_session')
    def leave_attendance_session(data):
        session_id = (data or {}).get('session_id')
        if session_id:
            leave_room(_room_name(session_id))

    @socketio.on('refresh_attendance_code')
    def refresh_attendance_code(data):
        session_id = (data or {}).get('session_id')
        att_session = attendance_service.get_session_by_id(session_id)
        if not _can_access_session(att_session):
            emit('attendance_error', {'message': 'Oturuma erisim yetkiniz yok.'})
            return
        if att_session.status != 'active':
            emit('attendance_error', {'message': 'Oturum aktif degil.'})
            return

        att_session = attendance_service.refresh_code_if_expired(session_id)
        socketio.emit('code_rotated', _code_payload(att_session), room=_room_name(session_id))
