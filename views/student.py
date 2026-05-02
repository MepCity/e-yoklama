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
import uuid
import random
import string
from datetime import datetime

student_bp = Blueprint('student', __name__)


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
    override = request.form.get('override') == '1'
    override_reason = request.form.get('override_reason', '').strip() or None
    latitude = request.form.get('latitude', type=float)
    longitude = request.form.get('longitude', type=float)

    record, error = attendance_service.check_in(
        session_id=session_id,
        student_id=user_id,
        submitted_code=submitted_code,
        ip_address=request.remote_addr,
        latitude=latitude,
        longitude=longitude,
        override=override,
        override_reason=override_reason,
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
        device_pairing = DevicePairing.get_active_pairing(user_id, db)
        
        # Konum doğrulama bilgisini al
        location_verification = LocationVerification.get_active_verification(user_id, db)
        
        # Mevcut kullanıcı bilgisini al
        current_user = db.query(User).filter_by(id=user_id).first()
        
        return render_template('student/verifications.html', 
                             device_pairing=device_pairing,
                             location_verification=location_verification,
                             current_user=current_user)
    
    except Exception as e:
        flash(f'Doğrulamalar sayfası yüklenirken hata: {str(e)}', 'error')
        return redirect(url_for('student.dashboard'))


# API Route'ları
@student_bp.route('/api/get-mac-address')
@role_required(2)
def get_mac_address():
    """MAC adresini al (basit implementasyon)"""
    try:
        # Gerçek uygulamada client-side JavaScript ile alınır
        # Şimdiliğine rastgele bir MAC adresi döndürelim
        import random
        mac = ':'.join(['{:02x}'.format(random.randint(0, 255)) for _ in range(6)])
        return mac
    except Exception as e:
        return 'Bilinmiyor', 500


@student_bp.route('/api/pair-device', methods=['POST'])
@role_required(2)
def pair_device():
    """Cihaz eşle"""
    try:
        user_id = session['user']['id']
        user = db.query(User).filter_by(id=user_id).first()
        
        if not user or not user.student_number:
            return jsonify({'success': False, 'message': 'Öğrenci numarası bulunamadı'}), 400
        
        # MAC adresi al (şimdilik rastgele)
        import random
        mac_address = ':'.join(['{:02x}'.format(random.randint(0, 255)) for _ in range(6)])
        
        # MAC adresinin başka bir kullanıcı tarafından kullanılıp kullanılmadığını kontrol et
        existing_mac_pairing = DevicePairing.get_by_mac_address(mac_address, db)
        if existing_mac_pairing and existing_mac_pairing.user_id != user_id:
            # MAC adresi başka bir kullanıcı tarafından kullanılıyor
            other_user = db.query(User).filter_by(id=existing_mac_pairing.user_id).first()
            return jsonify({
                'success': False, 
                'message': f'Bu MAC adresi zaten {other_user.username} kullanıcısı tarafından eşlenmiş. Her cihaz sadece bir kullanıcı hesabında kullanılabilir.'
            }), 400
        
        # Mevcut eşlemeyi kontrol et
        existing_pairing = DevicePairing.get_active_pairing(user_id, db)
        if existing_pairing and not existing_pairing.can_renew:
            return jsonify({'success': False, 'message': 'Henüz yeniden eşleme yapamazsınız'}), 400
        
        # Eski eşlemeyi pasif yap
        if existing_pairing:
            existing_pairing.is_active = False
        
        # Yeni eşleme oluştur
        new_pairing = DevicePairing(user_id, mac_address, user.student_number)
        db.add(new_pairing)
        db.commit()
        
        return jsonify({'success': True, 'message': 'Cihaz başarıyla eşlendi'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@student_bp.route('/api/verify-location', methods=['POST'])
@role_required(2)
def verify_location():
    """Konum doğrula"""
    try:
        user_id = session['user']['id']
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
            'campus_name': verification.campus_name,
            'distance': verification.distance_from_campus
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@student_bp.route('/api/verify-network')
@role_required(2)
def verify_network():
    """Ağ doğrula"""
    try:
        user_id = session['user']['id']
        
        # Gerçek ağ bilgisini al
        data = request.get_json() if request.is_json else {}
        network_info = data.get('network_info', request.headers.get('User-Agent', ''))
        
        # Eduroam kontrolü - daha gerçekçi kontrol
        is_eduroam = False
        
        # Client'dan gelen SSID bilgisi
        if 'ssid' in data:
            is_eduroam = 'eduroam' in data['ssid'].lower()
        else:
            # Header'dan kontrol (daha zayıf yöntem)
            is_eduroam = 'eduroam' in network_info.lower()
        
        # Yeni konum doğrulaması oluştur
        verification = LocationVerification(user_id, 'network')
        verification.verify_network(network_info)
        
        # Manuel olarak doğrulama durumunu ayarla
        verification.verified = is_eduroam
        verification.is_suspicious = not is_eduroam
        
        db.add(verification)
        db.commit()
        
        return jsonify({
            'success': True,
            'is_eduroam': is_eduroam,
            'network_info': network_info
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@student_bp.route('/api/start-verification')
@role_required(2)
def start_verification():
    """Doğrulama kodu başlat"""
    try:
        user_id = session['user']['id']
        
        # Aktif konum doğrulamasını kontrol et
        active_verification = LocationVerification.get_active_verification(user_id, db)
        
        if not active_verification or active_verification.is_expired:
            return jsonify({'success': False, 'message': 'Önce konum doğrulaması yapın'}), 400
        
        # Rastgele 6 haneli kod oluştur
        code = ''.join(random.choices(string.digits, k=6))
        
        # Session'a kodu kaydet
        session['verification_code'] = code
        session['verification_user_id'] = user_id
        session['verification_expires'] = (datetime.now().timestamp() + 60)  # 60 saniye
        
        return jsonify({'success': True, 'code': code})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@student_bp.route('/api/check-device-pairing')
@role_required(2)
def check_device_pairing():
    """Cihaz eşleme durumunu kontrol et"""
    try:
        user_id = session['user']['id']
        device_pairing = DevicePairing.get_active_pairing(user_id, db)
        
        return jsonify({
            'success': True,
            'has_pairing': device_pairing is not None,
            'can_renew': device_pairing.can_renew if device_pairing else False,
            'days_until_renewal': device_pairing.days_until_renewal if device_pairing else 0
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@student_bp.route('/api/submit-verification', methods=['POST'])
@role_required(2)
def submit_verification():
    """Doğrulama kodunu gönder"""
    try:
        user_id = session['user']['id']
        data = request.get_json()
        submitted_code = data.get('code')
        
        # Session'dan kodu kontrol et
        stored_code = session.get('verification_code')
        stored_user_id = session.get('verification_user_id')
        expires_at = session.get('verification_expires', 0)
        
        if not stored_code or stored_user_id != user_id or datetime.now().timestamp() > expires_at:
            return jsonify({'success': False, 'message': 'Doğrulama süresi dolmuş veya geçersiz'}), 400
        
        if submitted_code != stored_code:
            return jsonify({'success': False, 'message': 'Yanlış kod'}), 400
        
        # Aktif konum doğrulamasını al
        active_verification = LocationVerification.get_active_verification(user_id, db)
        
        if not active_verification:
            return jsonify({'success': False, 'message': 'Aktif konum doğrulaması bulunamadı'}), 400
        
        # Şüpheli ise öğretmen listesine ekle ( AttendanceRecord ile )
        if active_verification.is_suspicious:
            # Şüpheli işaretleme burada yapılacak
            pass
        
        # Session'ı temizle
        session.pop('verification_code', None)
        session.pop('verification_user_id', None)
        session.pop('verification_expires', None)
        
        return jsonify({'success': True, 'message': 'Doğrulama başarılı'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
