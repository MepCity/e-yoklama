from datetime import datetime

TURKISH_DAYS = {
    0: 'Pazartesi',
    1: 'Salı',
    2: 'Çarşamba',
    3: 'Perşembe',
    4: 'Cuma',
    5: 'Cumartesi',
    6: 'Pazar',
}

STATUS_LABELS = {
    'verified': 'Doğrulanmış',
    'suspicious': 'Şüpheli',
    'approved': 'Onaylandı',
    'rejected': 'Reddedildi',
    'manual': 'Manuel Eklendi',
    'absent': 'Devamsız',
}

STATUS_COLORS = {
    'verified': '#27ae60',
    'suspicious': '#f39c12',
    'approved': '#2ecc71',
    'rejected': '#e74c3c',
    'manual': '#3498db',
    'absent': '#e74c3c',
}


def day_name(day_number):
    return TURKISH_DAYS.get(day_number, '')


def format_datetime(dt_string):
    if not dt_string:
        return ''
    try:
        dt = datetime.fromisoformat(dt_string)
        return dt.strftime('%d.%m.%Y %H:%M')
    except (ValueError, TypeError):
        return str(dt_string)


def format_date(dt_string):
    if not dt_string:
        return ''
    try:
        dt = datetime.fromisoformat(dt_string)
        return dt.strftime('%d.%m.%Y')
    except (ValueError, TypeError):
        return str(dt_string)


def format_percentage(value):
    if value is None:
        return '%0'
    return f'%{value:.1f}'
