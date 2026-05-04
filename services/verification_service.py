import math


def validate_context(att_session, ip_address=None, latitude=None, longitude=None):
    ip_result = validate_ip(ip_address, att_session.allowed_ip_prefix)
    if not ip_result['ok']:
        return {
            'ok': False,
            'failed_layer': 'ip',
            'reason': ip_result['reason'],
            'ip_match': 0,
            'gps_match': None,
            'gps_distance_m': None,
        }

    gps_result = validate_gps(
        latitude=latitude,
        longitude=longitude,
        target_latitude=att_session.latitude,
        target_longitude=att_session.longitude,
        radius_m=att_session.radius_m,
    )
    if not gps_result['ok']:
        return {
            'ok': False,
            'failed_layer': 'gps',
            'reason': gps_result['reason'],
            'ip_match': 1,
            'gps_match': 0,
            'gps_distance_m': gps_result.get('distance_m'),
        }

    return {
        'ok': True,
        'failed_layer': None,
        'reason': None,
        'ip_match': 1 if att_session.allowed_ip_prefix else None,
        'gps_match': gps_result.get('gps_match'),
        'gps_distance_m': gps_result.get('distance_m'),
    }


def validate_ip(ip_address, allowed_prefix):
    if not allowed_prefix:
        return {'ok': True, 'reason': None}
    if not ip_address:
        return {'ok': False, 'reason': 'IP_MISSING'}
    if ip_address in ('127.0.0.1', '::1'):
        return {'ok': True, 'reason': 'LOCALHOST_BYPASS'}
    if ip_address.startswith(allowed_prefix):
        return {'ok': True, 'reason': None}
    return {'ok': False, 'reason': 'IP_NOT_ALLOWED'}


def validate_gps(latitude, longitude, target_latitude, target_longitude, radius_m):
    if target_latitude is None or target_longitude is None:
        return {'ok': True, 'reason': None, 'gps_match': None, 'distance_m': None}
    if latitude is None or longitude is None:
        return {'ok': False, 'reason': 'GPS_MISSING', 'distance_m': None}

    distance_m = haversine_m(latitude, longitude, target_latitude, target_longitude)
    if distance_m <= (radius_m or 100):
        return {'ok': True, 'reason': None, 'gps_match': 1, 'distance_m': distance_m}
    return {'ok': False, 'reason': 'GPS_OUT_OF_RANGE', 'distance_m': distance_m}


def haversine_m(lat1, lon1, lat2, lon2):
    radius = 6371000
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return radius * c
