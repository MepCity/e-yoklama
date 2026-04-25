import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-gizli-anahtar-uretimde-degistir')
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(BASE_DIR, 'e_yoklama.db')}"

    # QR Kod Ayarları (FR-04, NFR-01)
    QR_REFRESH_SECONDS = 10
    QR_REFRESH_MIN = 5
    QR_REFRESH_MAX = 30

    # Geofence Ayarları (NFR-06)
    GEOFENCE_RADIUS_M = 100

    # IP Doğrulama (NFR-05)
    ALLOWED_IP_PREFIX = '192.168.'

    # Rate Limiting (NFR-04)
    RATE_LIMIT_DEFAULT = '30/minute'
    RATE_LIMIT_LOGIN = '5/minute'
    RATE_LIMIT_ATTEND = '10/minute'

    # Devamsızlık Uyarı Eşiği (FR-17)
    ABSENCE_WARNING_THRESHOLD = 0.80


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False
    SECRET_KEY = os.environ.get('SECRET_KEY')


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestConfig,
    'default': DevelopmentConfig,
}
