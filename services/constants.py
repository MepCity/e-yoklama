PRESENT_STATUSES = ('verified', 'approved', 'manual')

STATUS_TR = {
    'verified': 'Doğrulandı',
    'approved': 'Var Sayıldı',
    'manual': 'Manuel',
    'suspicious': 'Şüpheli',
    'rejected': 'Yok Sayıldı',
}

FACULTY_DEPARTMENTS = {
    'Mühendislik Fakültesi': [
        'Bilgisayar Mühendisliği',
        'Yazılım Mühendisliği',
        'Elektrik-Elektronik Mühendisliği',
        'Makine Mühendisliği',
        'İnşaat Mühendisliği',
        'Endüstri Mühendisliği',
        'Kimya Mühendisliği',
        'Çevre Mühendisliği',
        'Gıda Mühendisliği',
    ],
    'Tıp Fakültesi': ['Tıp', 'Diş Hekimliği', 'Eczacılık'],
    'Sağlık Bilimleri Fakültesi': ['Hemşirelik', 'Fizyoterapi ve Rehabilitasyon'],
    'Eğitim Fakültesi': ['Psikolojik Danışmanlık ve Rehberlik'],
    'Fen Edebiyat Fakültesi': ['Psikoloji', 'Moleküler Biyoloji ve Genetik'],
    'Hukuk Fakültesi': ['Hukuk'],
    'İktisadi ve İdari Bilimler Fakültesi': ['İşletme', 'İktisat', 'Uluslararası Ticaret ve Finans'],
}


def rate(part, total):
    return round((part / total * 100), 1) if total else 0


def faculty_for_department(department):
    for faculty, departments in FACULTY_DEPARTMENTS.items():
        if department in departments:
            return faculty
    return None
