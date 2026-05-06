from datetime import datetime, timedelta

from models.location_verification import LocationVerification


def create_gps_verification(user_id, latitude, longitude, accuracy, db):
    verification = LocationVerification(user_id, 'gps', latitude, longitude, accuracy)
    verification.verify_location(latitude, longitude, accuracy)
    db.add(verification)
    db.commit()
    return verification


def create_network_verification(user_id, remote_addr, allowed_prefix, db):
    verification = LocationVerification(user_id, 'network')
    verification.verify_network(remote_addr, allowed_prefix=allowed_prefix)
    db.add(verification)
    db.commit()
    return verification


def create_manual_verification(user_id, db):
    verification = LocationVerification(user_id, 'manual')
    verification.manual_verify()
    db.add(verification)
    db.commit()
    return verification


def get_latest_status(user_id, db):
    verification = LocationVerification.get_latest_verification(user_id, db)
    if not verification:
        return False, 'Henüz konum doğrulaması yapılmadı'

    verified_at = _parse_dt(verification.verified_at)
    if not verified_at or verified_at < datetime.now() - timedelta(hours=1):
        return False, 'Konum doğrulamasının süresi dolmuş'
    return True, 'Konum doğrulaması geçerli'


def _parse_dt(value):
    if isinstance(value, datetime):
        return value
    if not value:
        return None
    try:
        return datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
    except ValueError:
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return None
