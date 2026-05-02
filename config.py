import os
from datetime import timedelta

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
    RATE_LIMIT_REGISTER = '5/minute'
    RATE_LIMIT_ATTEND = '10/minute'
    RATELIMIT_DEFAULT = RATE_LIMIT_DEFAULT
    RATELIMIT_STORAGE_URI = os.environ.get('RATELIMIT_STORAGE_URI', 'memory://')

    # Session Guvenligi
    SESSION_TIMEOUT_MINUTES = 30
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=SESSION_TIMEOUT_MINUTES)
    SESSION_REFRESH_EACH_REQUEST = True

    # Devamsızlık Uyarı Eşiği (FR-17)
    ABSENCE_WARNING_THRESHOLD = 0.80

    # Cihaz eşleşmesi zorunluluğu
    REQUIRE_DEVICE_PAIRING = os.environ.get('REQUIRE_DEVICE_PAIRING', 'true').lower() == 'true'


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False
    SECRET_KEY = os.environ.get('SECRET_KEY')


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    RATELIMIT_ENABLED = False
    REQUIRE_DEVICE_PAIRING = True


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestConfig,
    'default': DevelopmentConfig,
}
