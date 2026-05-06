import hashlib
import hmac

from models.device_pairing import DevicePairing
from models.user import User


def encrypt_device_id(raw_device_id, user_agent, secret_key):
    raw = (raw_device_id or '').strip()
    if not raw or len(raw) > 128:
        return None
    payload = f'{raw}|{user_agent or ""}'.encode('utf-8')
    return hmac.new(secret_key.encode('utf-8'), payload, hashlib.sha256).hexdigest()


def verify_device_id(raw_device_id, user_agent, stored_hash, secret_key):
    current_hash = encrypt_device_id(raw_device_id, user_agent, secret_key)
    if not current_hash or not stored_hash:
        return False
    return hmac.compare_digest(current_hash.lower(), stored_hash.lower())


def get_valid_pairing(user_id, db, require_pairing=True):
    if not require_pairing:
        return True
    pairing = DevicePairing.get_active_pairing(user_id, db)
    if not pairing or pairing.is_expired:
        return None
    return pairing


def pair_device(user_id, raw_device_id, user_agent, secret_key, db):
    user = db.query(User).filter_by(id=user_id).first()
    if not user or not user.student_number:
        return None, 'Öğrenci numarası bulunamadı'

    encrypted_device_key = encrypt_device_id(raw_device_id, user_agent, secret_key)
    if not encrypted_device_key:
        return None, 'Geçerli cihaz anahtarı alınamadı'

    existing_mac_pairing = DevicePairing.get_by_mac_address(encrypted_device_key, db)
    if existing_mac_pairing and existing_mac_pairing.user_id != user_id:
        other_user = db.query(User).filter_by(id=existing_mac_pairing.user_id).first()
        owner = other_user.username if other_user else 'başka bir kullanıcı'
        return None, f'Bu cihaz zaten {owner} kullanıcısı tarafından eşlenmiş. Her cihaz sadece bir kullanıcı hesabında kullanılabilir.'

    existing_pairing = DevicePairing.get_active_pairing(user_id, db)
    if existing_pairing and not existing_pairing.can_renew:
        return None, 'Henüz yeniden eşleme yapamazsınız'

    if existing_pairing:
        existing_pairing.is_active = False

    new_pairing = DevicePairing(user_id, encrypted_device_key, user.student_number)
    db.add(new_pairing)
    db.commit()
    return new_pairing, None


def cleanup_expired_pairings(db):
    count = DevicePairing.cleanup_expired(db)
    db.commit()
    return count
