from sqlalchemy import Column, Integer, String, Text, Float, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from database.session import Base, utcnow_str
from datetime import datetime, timedelta


class LocationVerification(Base):
    __tablename__ = 'location_verifications'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    
    # Konum bilgileri
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    accuracy = Column(Float, nullable=True)  # GPS doğruluğu (metre)
    
    # Doğrulama türü
    verification_type = Column(String(20), nullable=False, default='manual')  # 'gps', 'network', 'manual'
    network_info = Column(Text, nullable=True)  # Sunucunun gördüğü istemci IP bilgisi
    
    # Zaman bilgileri
    verified_at = Column(Text, nullable=False, default=utcnow_str)
    expires_at = Column(Text, nullable=False)  # 1 dakika sonrası
    
    # Durum
    verified = Column(Boolean, nullable=False, default=False)
    is_suspicious = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=True)
    
    # Kampüs bilgileri
    campus_name = Column(String(100), nullable=True)  # Hangi kampüste olduğu
    distance_from_campus = Column(Float, nullable=True)  # Kampüse uzaklık
    
    # Relationship
    user = relationship('User', back_populates='location_verifications')
    
    def __init__(self, user_id, verification_type='manual', latitude=None, longitude=None, accuracy=None):
        self.user_id = user_id
        self.verification_type = verification_type
        self.latitude = latitude
        self.longitude = longitude
        self.accuracy = accuracy
        self.verified_at = utcnow_str()
        # 1 dakika sonrası expire tarihi
        expire_date = datetime.now() + timedelta(minutes=1)
        self.expires_at = expire_date.strftime('%Y-%m-%d %H:%M:%S')
    
    @property
    def is_expired(self):
        """Doğrulama süresi dolmuş mu?"""
        try:
            if not self.expires_at:
                return True
            
            expire_date = datetime.strptime(self.expires_at, '%Y-%m-%d %H:%M:%S')
            return datetime.now() > expire_date
        except:
            return True
    
    @property
    def seconds_remaining(self):
        """Kalan saniye sayısı"""
        try:
            if not self.expires_at:
                return 0
            
            expire_date = datetime.strptime(self.expires_at, '%Y-%m-%d %H:%M:%S')
            remaining = expire_date - datetime.now()
            return max(0, int(remaining.total_seconds()))
        except:
            return 0
    
    def verify_location(self, latitude, longitude, accuracy=None):
        """GPS konumunu doğrula"""
        self.latitude = latitude
        self.longitude = longitude
        self.accuracy = accuracy
        self.verification_type = 'gps'
        
        # GPS doğruluğu kontrolü
        if accuracy and accuracy > 100:  # 100 metreden daha az hassas ise şüpheli
            self.verified = False
            self.is_suspicious = True
            self.campus_name = None
            self.distance_from_campus = None
            return
        
        # Marmara Üniversitesi kampüs koordinatları (daha hassas)
        campuses = {
            'Göztepe Kampüsü': {'lat': 40.9925, 'lng': 29.0625, 'radius': 300},  # 500m -> 300m
            'Acıbadem Kampüsü': {'lat': 40.9917, 'lng': 29.0500, 'radius': 200},  # 300m -> 200m
            'Anadolu Hisarı Kampüsü': {'lat': 41.0833, 'lng': 29.0667, 'radius': 300},  # 400m -> 300m
            'Kartal Kampüsü': {'lat': 40.8750, 'lng': 29.1833, 'radius': 200},  # 300m -> 200m
            'Pendik Kampüsü': {'lat': 40.8667, 'lng': 29.2500, 'radius': 200}   # 300m -> 200m
        }
        
        # En yakın kampüsü bul
        min_distance = float('inf')
        closest_campus = None
        
        for campus_name, coords in campuses.items():
            distance = self.calculate_distance(
                latitude, longitude, 
                coords['lat'], coords['lng']
            )
            
            if distance < min_distance:
                min_distance = distance
                closest_campus = campus_name
        
        # Kampüs içinde mi? (daha katı kontrol)
        if closest_campus and min_distance <= campuses[closest_campus]['radius']:
            # Ekstra kontrol: GPS koordinatlarının geçerli olup olmadığını kontrol et
            if self._is_valid_gps_coordinate(latitude, longitude):
                self.verified = True
                self.is_suspicious = False
                self.campus_name = closest_campus
                self.distance_from_campus = min_distance
            else:
                self.verified = False
                self.is_suspicious = True
                self.campus_name = closest_campus
                self.distance_from_campus = min_distance
        else:
            self.verified = False
            self.is_suspicious = True
            self.campus_name = closest_campus
            self.distance_from_campus = min_distance
    
    def _is_valid_gps_coordinate(self, latitude, longitude):
        """GPS koordinatlarının geçerli olup olmadığını kontrol et"""
        try:
            # Koordinat aralığı kontrolü
            if not (-90 <= latitude <= 90) or not (-180 <= longitude <= 180):
                return False
            
            # Türkiye sınırları içinde mi kontrolü (yaklaşık)
            if not (36 <= latitude <= 42) or not (26 <= longitude <= 45):
                return False
            
            # Aşırı yuvarlatılmış koordinatları kontrol et
            lat_str = str(latitude)
            lng_str = str(longitude)
            
            # Eğer koordinatlar çok yuvarlatılmışsa şüpheli
            if (lat_str.endswith('.0') or lat_str.endswith('.00')) and (lng_str.endswith('.0') or lng_str.endswith('.00')):
                return False
            
            return True
        except:
            return False
    
    def verify_network(self, network_info, allowed_prefix=None):
        """Sunucunun gördüğü istemci IP bilgisine göre ağ doğrulaması yap."""
        self.verification_type = 'network'
        self.network_info = network_info
        
        trusted_network = (
            network_info in ('127.0.0.1', '::1')
            or bool(allowed_prefix and network_info and network_info.startswith(allowed_prefix))
        )
        if trusted_network:
            self.verified = True
            self.is_suspicious = False
        else:
            self.verified = False
            self.is_suspicious = True
    
    def manual_verify(self):
        """Manuel doğrulama (şüpheli)"""
        self.verification_type = 'manual'
        self.verified = True
        self.is_suspicious = True
    
    @staticmethod
    def calculate_distance(lat1, lon1, lat2, lon2):
        """İki nokta arasındaki mesafeyi hesapla (Haversine formülü)"""
        from math import radians, sin, cos, sqrt, atan2
        
        R = 6371000  # Dünya yarıçapı (metre)
        
        lat1_rad = radians(lat1)
        lon1_rad = radians(lon1)
        lat2_rad = radians(lat2)
        lon2_rad = radians(lon2)
        
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        a = sin(dlat/2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        
        return R * c
    
    @classmethod
    def get_active_verification(cls, user_id, db_session):
        """Kullanıcının aktif doğrulamasını getir"""
        return db_session.query(cls).filter(
            cls.user_id == user_id,
            cls.is_active == True,
            cls.verified == True,
            cls.expires_at >= datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        ).order_by(cls.id.desc()).first()
    
    @classmethod
    def cleanup_expired(cls, db_session):
        """Süresi dolmuş doğrulamaları temizle"""
        expired_verifications = db_session.query(cls).filter(
            cls.is_active == True,
            cls.expires_at < datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ).all()
        
        for verification in expired_verifications:
            verification.is_active = False
        
        db_session.commit()
        return len(expired_verifications)
