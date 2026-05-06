from models.course import Course


DEPARTMENT_CODES = {
    'Bilgisayar Mühendisliği': 'BM',
    'Yazılım Mühendisliği': 'YM',
    'Elektrik-Elektronik Mühendisliği': 'EE',
    'Makine Mühendisliği': 'MM',
    'İnşaat Mühendisliği': 'İM',
    'Endüstri Mühendisliği': 'EM',
    'Kimya Mühendisliği': 'KM',
    'Çevre Mühendisliği': 'ÇM',
    'Gıda Mühendisliği': 'GM',
    'Tıp': 'TP',
    'Diş Hekimliği': 'DH',
    'Eczacılık': 'EC',
    'Hemşirelik': 'HS',
    'Fizyoterapi ve Rehabilitasyon': 'FR',
    'Psikoloji': 'PS',
    'Hukuk': 'HK',
    'İşletme': 'İS',
    'İktisat': 'IK',
    'Uluslararası Ticaret ve Finans': 'UF',
    'Psikolojik Danışmanlık ve Rehberlik': 'PD',
    'Moleküler Biyoloji ve Genetik': 'BG',
}


def generate_course_code(db, department, name):
    if not department or not name:
        return None

    dept_code = DEPARTMENT_CODES.get(department, 'GN')
    words = name.split()
    if len(words) >= 2:
        course_code_part = ''.join(word[0].upper() for word in words[:2])
    else:
        course_code_part = words[0][:3].upper() if len(words[0]) >= 3 else words[0].upper()

    base_code = f'{dept_code}{course_code_part}'
    existing_codes = db.query(Course.code).filter(Course.code.like(f'{base_code}%')).all()
    existing_codes = [code for (code,) in existing_codes if code]
    if not existing_codes:
        return base_code

    counter = 1
    while f'{base_code}{counter:02d}' in existing_codes:
        counter += 1
    return f'{base_code}{counter:02d}'
