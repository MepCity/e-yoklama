import hashlib
import hmac
from flask import Blueprint, render_template, session, redirect, url_for, request, flash, current_app, jsonify
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
from datetime import datetime

student_bp = Blueprint('student', __name__)


def _get_valid_device_pairing(user_id):
    if not current_app.config.get('REQUIRE_DEVICE_PAIRING', True):
        return True
    pairing = DevicePairing.get_active_pairing(user_id, db)
    if not pairing or pairing.is_expired:
        return None
    return pairing


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
    
    except Exception as e:
        flash(f'Doğrulamalar sayfası yüklenirken hata: {str(e)}', 'error')
        return redirect(url_for('student.dashboard'))


# API Route'ları
@student_bp.route('/api/get-mac-address')
@role_required(2)
def get_mac_address():
    """Tarayıcılar MAC adresini vermez; cihaz anahtarı client tarafında üretilir."""
    return 'Tarayıcı cihaz anahtarı gerekli', 400


def _derive_device_key(raw_device_id, user_agent):
    raw = (raw_device_id or '').strip()
    if not raw:
        return None
    
    # Kısa device ID'ler için de çalışacak şekilde güncellendi
    # Minimum uzunluk kontrolünü kaldır, sadece maksimum uzunluk kontrolü yap
    if len(raw) > 128:
        return None
    
    # Gizli anahtar ile HMAC kullanarak güvenli device key oluştur
    secret_key = current_app.config.get('DEVICE_PAIRING_SECRET', 'e-yoklama-device-pairing-dev')
    hmac_obj = hmac.new(secret_key.encode('utf-8'), f'{raw}|{user_agent or ""}'.encode('utf-8'), hashlib.sha256)
    digest = hmac_obj.hexdigest()
    return f'DV:{digest[:14]}'


def _encrypt_device_id(raw_device_id, user_agent):
    """Cihaz ID'sini gizli anahtar ile şifrele"""
    raw = (raw_device_id or '').strip()
    if not raw:
        return None
    
    # Gizli anahtar ile HMAC kullanarak şifrele
    secret_key = current_app.config.get('DEVICE_PAIRING_SECRET', 'e-yoklama-device-pairing-dev')
    hmac_obj = hmac.new(secret_key.encode('utf-8'), f'{raw}|{user_agent or ""}'.encode('utf-8'), hashlib.sha256)
    return hmac_obj.hexdigest()


def _verify_device_id(raw_device_id, user_agent, stored_hash):
    """Cihaz ID'sini saklı hash ile karşılaştır"""
    current_hash = _encrypt_device_id(raw_device_id, user_agent)
    if not current_hash or not stored_hash:
        return False
    
    # Case-insensitive karşılaştırma yap - her iki hash'i de küçük harfe çevir
    current_lower = current_hash.lower()
    stored_lower = stored_hash.lower()
    
    # Sadece ilk 14 karakteri karşılaştır (veritabanında kısa saklıyor olabilir)
    return hmac.compare_digest(current_lower[:14], stored_lower[:14])


@student_bp.route('/api/pair-device', methods=['POST'])
@role_required(2)
def pair_device():
    """Cihaz eşle"""
    try:
        user_id = session['user']['id']
        user = db.query(User).filter_by(id=user_id).first()
        data = request.get_json(silent=True) or {}
        
        print(f"DEBUG PAIR: User ID: {user_id}")
        print(f"DEBUG PAIR: Device ID from client: {data.get('device_id')}")
        print(f"DEBUG PAIR: User-Agent: {request.headers.get('User-Agent')}")
        
        if not user or not user.student_number:
            return jsonify({'success': False, 'message': 'Öğrenci numarası bulunamadı'}), 400
        
        # Cihaz ID'sini gizli anahtar ile şifrele
        encrypted_device_key = _encrypt_device_id(data.get('device_id'), request.headers.get('User-Agent'))
        print(f"DEBUG PAIR: Encrypted device key: {encrypted_device_key}")
        
        if not encrypted_device_key:
            return jsonify({'success': False, 'message': 'Geçerli cihaz anahtarı alınamadı'}), 400
        
        existing_mac_pairing = DevicePairing.get_by_mac_address(encrypted_device_key, db)
        if existing_mac_pairing and existing_mac_pairing.user_id != user_id:
            other_user = db.query(User).filter_by(id=existing_mac_pairing.user_id).first()
            return jsonify({
                'success': False, 
                'message': f'Bu cihaz zaten {other_user.username} kullanıcısı tarafından eşlenmiş. Her cihaz sadece bir kullanıcı hesabında kullanılabilir.'
            }), 400
        
        # Mevcut eşlemeyi kontrol et
        existing_pairing = DevicePairing.get_active_pairing(user_id, db)
        if existing_pairing and not existing_pairing.can_renew:
            return jsonify({'success': False, 'message': 'Henüz yeniden eşleme yapamazsınız'}), 400
        
        # Eski eşlemeyi pasif yap
        if existing_pairing:
            existing_pairing.is_active = False
        
        # Yeni eşleme oluştur (şifrelenmiş anahtar ile)
        new_pairing = DevicePairing(user_id, encrypted_device_key, user.student_number)
        db.add(new_pairing)
        db.commit()
        
        print(f"DEBUG PAIR: New pairing created with encrypted MAC: {encrypted_device_key}")
        
        return jsonify({'success': True, 'message': 'Cihaz başarıyla eşlendi'})
        
    except Exception as e:
        print(f"DEBUG PAIR: Exception: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


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
        
        # Yeni konum doğrulaması oluştur
        verification = LocationVerification(user_id, 'gps', latitude, longitude, accuracy)
        verification.verify_location(latitude, longitude, accuracy)
        
        db.add(verification)
        db.commit()
        
        return jsonify({
            'success': True,
            'in_campus': verification.verified,
            'is_suspicious': verification.is_suspicious,
            'campus_name': verification.campus_name,
            'distance': verification.distance_from_campus
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


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

        verification = LocationVerification(user_id, 'network')
        verification.verify_network(remote_addr, allowed_prefix=allowed_prefix)
        
        db.add(verification)
        db.commit()
        
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
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@student_bp.route('/api/manual-verification', methods=['POST'])
@role_required(2)
def manual_verification():
    """Otomatik doğrulama başarısızsa şüpheli doğrulama oluştur."""
    try:
        user_id = session['user']['id']
        if not _get_valid_device_pairing(user_id):
            return jsonify({'success': False, 'message': _device_pairing_required_message()}), 400

        verification = LocationVerification(user_id, 'manual')
        verification.manual_verify()
        db.add(verification)
        db.commit()
        return jsonify({'success': True, 'is_suspicious': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@student_bp.route('/api/start-verification', methods=['POST'])
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
                    latitude=0.0,
                    longitude=0.0,
                    network_name='Unknown',
                    is_suspicious=True,
                    is_trusted_network=False,
                    in_campus=False,
                    created_at=datetime.now()
                )
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
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@student_bp.route('/api/validate-device', methods=['POST'])
@role_required(2)
def validate_device():
    """Cihaz eşleşmesini doğrula - farklı cihazdan giriş kontrolü"""
    try:
        user_id = session['user']['id']
        data = request.get_json(silent=True) or {}
        device_id = data.get('device_id')
        
        print(f"DEBUG: User ID: {user_id}")
        print(f"DEBUG: Device ID from client: {device_id}")
        print(f"DEBUG: User-Agent: {request.headers.get('User-Agent')}")
        
        if not device_id:
            return jsonify({'valid': False, 'message': 'Cihaz bilgisi alınamadı'}), 400
        
        # Aktif eşlemeyi kontrol et
        active_pairing = DevicePairing.get_active_pairing(user_id, db)
        
        if not active_pairing:
            print("DEBUG: No active pairing found")
            return jsonify({'valid': False, 'message': 'Bu hesap için aktif cihaz eşleşmesi bulunamadı'})
        
        print(f"DEBUG: Active pairing MAC: {active_pairing.mac_address}")
        
        # Mevcut cihazın şifrelenmiş anahtarını oluştur ve karşılaştır
        current_device_hash = _encrypt_device_id(device_id, request.headers.get('User-Agent'))
        print(f"DEBUG: Current device hash: {current_device_hash}")
        print(f"DEBUG: Stored hash: {active_pairing.mac_address}")
        
        # Güvenli hash karşılaştırması yap
        is_valid = _verify_device_id(device_id, request.headers.get('User-Agent'), active_pairing.mac_address)
        print(f"DEBUG: Hash verification result: {is_valid}")
        
        if not is_valid:
            return jsonify({'valid': False, 'message': 'Bu hesap size ait değil. Eşleşen cihaz farklı.'})
        
        return jsonify({'valid': True, 'message': 'Cihaz doğrulaması başarılı'})
        
    except Exception as e:
        print(f"DEBUG: Exception in validate_device: {e}")
        return jsonify({'valid': False, 'message': str(e)}), 500


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
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@student_bp.route('/api/check-location-verification')
@role_required(2)
def check_location_verification():
    """Konum doğrulama durumunu kontrol et"""
    try:
        print(f"DEBUG: check-location-verification API çağrıldı")
        user_id = session['user']['id']
        print(f"DEBUG: User ID: {user_id}")
        
        # Son konum doğrulamasını kontrol et
        print(f"DEBUG: get_latest_verification çağrılıyor...")
        verification = LocationVerification.get_latest_verification(user_id, db)
        print(f"DEBUG: Verification sonucu: {verification}")
        
        if not verification:
            print(f"DEBUG: Hiç doğrulama bulunamadı")
            return jsonify({
                'success': True,
                'verified': False,
                'message': 'Henüz konum doğrulaması yapılmadı'
            })
        
        # Doğrulamanın geçerliliğini kontrol et (1 saat içinde geçerli)
        from datetime import datetime, timedelta
        print(f"DEBUG: Verification verified_at: {verification.verified_at}")
        
        # verified_at string ise datetime'a çevir
        if isinstance(verification.verified_at, str):
            try:
                created_dt = datetime.strptime(verification.verified_at, '%Y-%m-%d %H:%M:%S')
            except:
                created_dt = datetime.now()
        else:
            created_dt = verification.verified_at
            
        if created_dt < datetime.now() - timedelta(hours=1):
            print(f"DEBUG: Doğrulama süresi dolmuş")
            return jsonify({
                'success': True,
                'verified': False,
                'message': 'Konum doğrulamasının süresi dolmuş'
            })
        
        print(f"DEBUG: Doğrulama geçerli")
        return jsonify({
            'success': True,
            'verified': True,
            'message': 'Konum doğrulaması geçerli'
        })
        
    except Exception as e:
        print(f"DEBUG: check-location-verification hatası: {e}")
        import traceback
        print(f"DEBUG: Traceback: {traceback.format_exc()}")
        return jsonify({'success': False, 'message': str(e)}), 500
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


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
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
