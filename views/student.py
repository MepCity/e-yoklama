from flask import Blueprint, render_template, session, redirect, url_for, request, flash, current_app, jsonify
import logging
from utils.decorators import role_required
from utils.rate_limit import limiter
from database import db
from models.course import Course, CourseStudent
from models.attendance_record import AttendanceRecord
from models.schedule import Schedule
from models.device_pairing import DevicePairing
from models.location_verification import LocationVerification
from models.user import User
from services import attendance_service, statistics_service
from services import device_pairing_service, location_verification_service
from datetime import datetime

student_bp = Blueprint('student', __name__)
logger = logging.getLogger(__name__)


def _get_valid_device_pairing(user_id):
    return device_pairing_service.get_valid_pairing(
        user_id=user_id,
        db=db,
        require_pairing=current_app.config.get('REQUIRE_DEVICE_PAIRING', True),
    )


def _device_pairing_required_message():
    return 'Yoklamaya katılmak için önce cihaz eşlemesi yapmalısınız.'


@student_bp.route('/dashboard')
@role_required(2)
def dashboard():
    user_id = session['user']['id']
    enrollments = db.query(CourseStudent).filter(CourseStudent.student_id == user_id).all()
    my_courses = []
    active_sessions = {}
    checked_in_sessions = set()
    for cs in enrollments:
        course = db.query(Course).filter_by(id=cs.course_id).first()
        if course:
            my_courses.append(course)
            active = attendance_service.get_active_session_for_student(course.id, user_id)
            if active:
                active_sessions[course.id] = active
                existing = db.query(AttendanceRecord).filter_by(
                    session_id=active.id,
                    student_id=user_id,
                ).first()
                if existing:
                    checked_in_sessions.add(active.id)
    return render_template(
        'student/dashboard.html',
        courses=my_courses,
        active_sessions=active_sessions,
        checked_in_sessions=checked_in_sessions,
    )


@student_bp.route('/session/<session_id>/check-in', methods=['POST'])
@role_required(2)
@limiter.limit(lambda: current_app.config.get('RATE_LIMIT_ATTEND', '10/minute'))
def check_in(session_id):
    user_id = session['user']['id']
    submitted_code = request.form.get('code', '')
    if not _get_valid_device_pairing(user_id):
        flash(_device_pairing_required_message(), 'error')
        return redirect(url_for('student.verifications'))

    override = request.form.get('override') == '1'
    override_reason = request.form.get('override_reason', '').strip() or None
    latitude = request.form.get('latitude', type=float)
    longitude = request.form.get('longitude', type=float)
    active_verification = LocationVerification.get_active_verification(user_id, db)
    if active_verification and active_verification.is_expired:
        active_verification = None
    if active_verification and latitude is None and longitude is None:
        latitude = active_verification.latitude
        longitude = active_verification.longitude
        if active_verification.is_suspicious and not override:
            override = True
            override_reason = 'Ön doğrulama şüpheli olarak tamamlandı.'
    force_suspicious = bool(active_verification and active_verification.is_suspicious)

    record, error = attendance_service.check_in(
        session_id=session_id,
        student_id=user_id,
        submitted_code=submitted_code,
        ip_address=request.remote_addr,
        latitude=latitude,
        longitude=longitude,
        override=override,
        override_reason=override_reason,
        force_suspicious=force_suspicious,
    )
    if error:
        flash(error, 'error')
        return redirect(url_for('student.dashboard'))

    if record.status == 'suspicious':
        flash('Yoklama kaydınız şüpheli olarak öğretmen onayına gönderildi.', 'warning')
    else:
        flash('Yoklama kaydınız doğrulandı.', 'success')
    return redirect(url_for('student.statistics'))


@student_bp.route('/schedule')
@role_required(2)
def schedule():
    user_id = session['user']['id']
    enrollments = db.query(CourseStudent).filter(CourseStudent.student_id == user_id).all()
    course_ids = [cs.course_id for cs in enrollments]
    schedules = db.query(Schedule).join(Course).filter(Course.id.in_(course_ids)).all()
    return render_template('student/schedule.html', schedules=schedules)


@student_bp.route('/statistics')
@role_required(2)
def statistics():
    user_id = session['user']['id']
    stats = statistics_service.get_student_statistics(user_id)
    return render_template('student/statistics.html', **stats)


@student_bp.route('/verifications')
@role_required(2)
def verifications():
    try:
        user_id = session['user']['id']
        
        # Cihaz eşleme bilgisini al
        device_pairing = _get_valid_device_pairing(user_id)
        
        # Konum doğrulama bilgisini al
        location_verification = LocationVerification.get_active_verification(user_id, db)
        
        # Mevcut kullanıcı bilgisini al
        current_user = db.query(User).filter_by(id=user_id).first()

        active_attendance = []
        enrollments = db.query(CourseStudent).filter(CourseStudent.student_id == user_id).all()
        for enrollment in enrollments:
            course = db.query(Course).filter_by(id=enrollment.course_id).first()
            active_session = attendance_service.get_active_session_for_student(enrollment.course_id, user_id)
            if not course or not active_session:
                continue
            existing_record = db.query(AttendanceRecord).filter_by(
                session_id=active_session.id,
                student_id=user_id,
            ).first()
            active_attendance.append({
                'course': course,
                'session': active_session,
                'checked_in': existing_record is not None,
                'record': existing_record,
            })
        
        return render_template('student/verifications.html', 
                             device_pairing=device_pairing,
                             location_verification=location_verification,
                             current_user=current_user,
                             active_attendance=active_attendance)
    
    except Exception:
        logger.exception('Student verifications page failed')
        flash('Doğrulamalar sayfası yüklenirken hata oluştu.', 'error')
        return redirect(url_for('student.dashboard'))


# API Route'ları
@student_bp.route('/api/get-mac-address')
@role_required(2)
def get_mac_address():
    """Tarayıcılar MAC adresini vermez; cihaz anahtarı client tarafında üretilir."""
    return 'Tarayıcı cihaz anahtarı gerekli', 400


@student_bp.route('/api/pair-device', methods=['POST'])
@role_required(2)
def pair_device():
    """Cihaz eşle"""
    try:
        user_id = session['user']['id']
        data = request.get_json(silent=True) or {}
        _, error = device_pairing_service.pair_device(
            user_id=user_id,
            raw_device_id=data.get('device_id'),
            user_agent=request.headers.get('User-Agent'),
            secret_key=current_app.config.get('DEVICE_PAIRING_SECRET'),
            db=db,
        )
        if error:
            return jsonify({'success': False, 'message': error}), 400
        return jsonify({'success': True, 'message': 'Cihaz başarıyla eşlendi'})
        
    except Exception:
        logger.exception('Device pairing failed')
        return jsonify({'success': False, 'message': 'Cihaz eşleme sırasında hata oluştu'}), 500


@student_bp.route('/api/verify-location', methods=['POST'])
@role_required(2)
def verify_location():
    """Konum doğrula"""
    try:
        user_id = session['user']['id']
        if not _get_valid_device_pairing(user_id):
            return jsonify({'success': False, 'message': _device_pairing_required_message()}), 400

        data = request.get_json()
        
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        accuracy = data.get('accuracy')
        
        verification = location_verification_service.create_gps_verification(user_id, latitude, longitude, accuracy, db)
        
        return jsonify({
            'success': True,
            'in_campus': verification.verified,
            'is_suspicious': verification.is_suspicious,
            'campus_name': verification.campus_name,
            'distance': verification.distance_from_campus
        })
        
    except Exception:
        logger.exception('Location verification failed')
        return jsonify({'success': False, 'message': 'Konum doğrulama sırasında hata oluştu'}), 500


@student_bp.route('/api/verify-network', methods=['GET', 'POST'])
@role_required(2)
def verify_network():
    """Ağ doğrula"""
    try:
        user_id = session['user']['id']
        if not _get_valid_device_pairing(user_id):
            return jsonify({'success': False, 'message': _device_pairing_required_message()}), 400

        remote_addr = request.headers.get('X-Forwarded-For', request.remote_addr or '').split(',')[0].strip()
        allowed_prefix = current_app.config.get('ALLOWED_IP_PREFIX')
        trusted_network = (
            remote_addr in ('127.0.0.1', '::1')
            or (allowed_prefix and remote_addr.startswith(allowed_prefix))
        )

        verification = location_verification_service.create_network_verification(user_id, remote_addr, allowed_prefix, db)
        
        # Ağ adını al
        data = request.get_json() if request.method == 'POST' else {}
        network_name = data.get('network_name', 'Unknown')
        
        return jsonify({
            'success': True,
            'is_eduroam': trusted_network,
            'is_trusted_network': trusted_network,
            'is_suspicious': verification.is_suspicious,
            'network_name': network_name,
            'network_info': remote_addr
        })
        
    except Exception:
        logger.exception('Network verification failed')
        return jsonify({'success': False, 'message': 'Ağ doğrulama sırasında hata oluştu'}), 500


@student_bp.route('/api/manual-verification', methods=['POST'])
@role_required(2)
def manual_verification():
    """Otomatik doğrulama başarısızsa şüpheli doğrulama oluştur."""
    try:
        user_id = session['user']['id']
        if not _get_valid_device_pairing(user_id):
            return jsonify({'success': False, 'message': _device_pairing_required_message()}), 400

        location_verification_service.create_manual_verification(user_id, db)
        return jsonify({'success': True, 'is_suspicious': True})
    except Exception:
        logger.exception('Manual verification failed')
        return jsonify({'success': False, 'message': 'Manuel doğrulama sırasında hata oluştu'}), 500


@student_bp.route('/api/start-verification', methods=['GET', 'POST'])
@role_required(2)
def start_verification():
    """Doğrulama kodu başlat"""
    try:
        user_id = session['user']['id']
        data = request.get_json(silent=True) or {}
        with_location = data.get('with_location', True)
        is_suspicious = data.get('is_suspicious', False)
        
        if not _get_valid_device_pairing(user_id):
            return jsonify({'success': False, 'message': _device_pairing_required_message()}), 400
        
        # Aktif konum doğrulamasını kontrol et
        active_verification = LocationVerification.get_active_verification(user_id, db)
        
        if not active_verification or active_verification.is_expired:
            # Yeni konum doğrulaması oluştur
            if with_location:
                return jsonify({'success': False, 'message': 'Önce konum doğrulaması yapın'}), 400
            else:
                # Konumsuz doğrulama - şüpheli olarak işaretle
                new_verification = LocationVerification(
                    user_id=user_id,
                    verification_type='manual',
                    latitude=0.0,
                    longitude=0.0,
                )
                new_verification.manual_verify()
                db.add(new_verification)
                db.commit()
                active_verification = new_verification
        
        # Şüpheli flag'ini güncelle
        if is_suspicious:
            active_verification.is_suspicious = True
            db.commit()
        
        session['verification_user_id'] = user_id
        session['verification_expires'] = (datetime.now().timestamp() + 60)  # 60 saniye
        
        return jsonify({
            'success': True,
            'is_suspicious': active_verification.is_suspicious,
            'expires_in': 60,
            'message': 'Doğrulama başlatıldı'
        })
        
    except Exception:
        logger.exception('Start verification failed')
        return jsonify({'success': False, 'message': 'Doğrulama başlatılırken hata oluştu'}), 500


@student_bp.route('/api/validate-device', methods=['POST'])
@role_required(2)
def validate_device():
    """Cihaz eşleşmesini doğrula - farklı cihazdan giriş kontrolü"""
    try:
        user_id = session['user']['id']
        data = request.get_json(silent=True) or {}
        device_id = data.get('device_id')
        
        if not device_id:
            return jsonify({'valid': False, 'message': 'Cihaz bilgisi alınamadı'}), 400
        
        # Aktif eşlemeyi kontrol et
        active_pairing = DevicePairing.get_active_pairing(user_id, db)
        
        if not active_pairing:
            return jsonify({'valid': False, 'message': 'Bu hesap için aktif cihaz eşleşmesi bulunamadı'})

        is_valid = device_pairing_service.verify_device_id(
            raw_device_id=device_id,
            user_agent=request.headers.get('User-Agent'),
            stored_hash=active_pairing.mac_address,
            secret_key=current_app.config.get('DEVICE_PAIRING_SECRET'),
        )

        if not is_valid:
            return jsonify({'valid': False, 'message': 'Bu hesap size ait değil. Eşleşen cihaz farklı.'})
        
        return jsonify({'valid': True, 'message': 'Cihaz doğrulaması başarılı'})
        
    except Exception:
        logger.exception('Device validation failed')
        return jsonify({'valid': False, 'message': 'Cihaz doğrulama sırasında hata oluştu'}), 500


@student_bp.route('/api/check-device-pairing')
@role_required(2)
def check_device_pairing():
    """Cihaz eşleme durumunu kontrol et"""
    try:
        user_id = session['user']['id']
        if not current_app.config.get('REQUIRE_DEVICE_PAIRING', True):
            return jsonify({'success': True, 'required': False, 'has_pairing': False})
        
        pairing = _get_valid_device_pairing(user_id)
        return jsonify({
            'success': True,
            'required': True,
            'has_pairing': pairing is not None
        })
    except Exception:
        logger.exception('Device pairing status check failed')
        return jsonify({'success': False, 'message': 'Cihaz eşleşme durumu alınamadı'}), 500


@student_bp.route('/api/check-location-verification')
@role_required(2)
def check_location_verification():
    """Konum doğrulama durumunu kontrol et"""
    try:
        user_id = session['user']['id']

        verified, message = location_verification_service.get_latest_status(user_id, db)
        return jsonify({
            'success': True,
            'verified': verified,
            'message': message
        })
        
    except Exception:
        logger.exception('Location verification status check failed')
        return jsonify({'success': False, 'message': 'Konum doğrulama durumu alınamadı'}), 500


@student_bp.route('/api/submit-verification', methods=['POST'])
@role_required(2)
def submit_verification():
    """Doğrulama sonrası aktif yoklamaya katıl."""
    try:
        user_id = session['user']['id']
        if not _get_valid_device_pairing(user_id):
            return jsonify({'success': False, 'message': _device_pairing_required_message()}), 400

        data = request.get_json(silent=True) or {}
        session_id = data.get('session_id')
        submitted_code = (data.get('code') or '').strip()
        
        stored_user_id = session.get('verification_user_id')
        expires_at = session.get('verification_expires', 0)
        
        if stored_user_id != user_id or datetime.now().timestamp() > expires_at:
            return jsonify({'success': False, 'message': 'Doğrulama süresi dolmuş veya geçersiz'}), 400
        
        # Aktif konum doğrulamasını al
        active_verification = LocationVerification.get_active_verification(user_id, db)
        
        if not active_verification:
            return jsonify({'success': False, 'message': 'Aktif konum doğrulaması bulunamadı'}), 400

        record, error = attendance_service.check_in(
            session_id=session_id,
            student_id=user_id,
            submitted_code=submitted_code,
            ip_address=request.remote_addr,
            latitude=active_verification.latitude,
            longitude=active_verification.longitude,
            override=active_verification.is_suspicious,
            override_reason='Doğrulamalar sayfasından manuel/şüpheli doğrulama' if active_verification.is_suspicious else None,
            force_suspicious=active_verification.is_suspicious,
        )
        if error:
            return jsonify({'success': False, 'message': error}), 400
        
        # Session'ı temizle
        session.pop('verification_user_id', None)
        session.pop('verification_expires', None)
        
        return jsonify({
            'success': True,
            'message': 'Yoklama kaydı oluşturuldu',
            'status': record.status,
            'suspicious': record.status == 'suspicious',
        })
        
    except Exception:
        logger.exception('Submit verification failed')
        return jsonify({'success': False, 'message': 'Yoklama kaydı oluşturulurken hata oluştu'}), 500
