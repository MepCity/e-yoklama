from sqlalchemy import Column, Integer, String, Text, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from database.session import Base, utcnow_str
from datetime import datetime, timedelta


class DevicePairing(Base):
    __tablename__ = 'device_pairings'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    mac_address = Column(String(17), nullable=False, unique=True)  # Geriye uyumlu alan: tarayıcı cihaz anahtarı
    student_number = Column(String(20), nullable=False, index=True)
    
    # Eşleme zamanları
    created_at = Column(Text, nullable=False, default=utcnow_str)
    last_paired_at = Column(Text, nullable=False, default=utcnow_str)
    expires_at = Column(Text, nullable=False)  # 1 ay sonrası
    
    # Durum
    is_active = Column(Boolean, nullable=False, default=True)
    is_verified = Column(Boolean, nullable=False, default=False)  # Öğretmen tarafından doğrulanmış mı?
    
    # Relationship
    user = relationship('User', back_populates='device_pairings')
    
    def __init__(self, user_id, mac_address, student_number):
        self.user_id = user_id
        self.mac_address = mac_address.upper()
        self.student_number = student_number
        self.created_at = utcnow_str()
        self.last_paired_at = utcnow_str()
        # 1 ay sonrası expire tarihi
        expire_date = datetime.now() + timedelta(days=30)
        self.expires_at = expire_date.strftime('%Y-%m-%d %H:%M:%S')
    
    @property
    def days_until_renewal(self):
        """Yeniden eşleme için kalan gün sayısı"""
        try:
            if not self.expires_at:
                return 0
            
            expire_date = datetime.strptime(self.expires_at, '%Y-%m-%d %H:%M:%S')
            remaining = expire_date - datetime.now()
            return max(0, remaining.days)
        except:
            return 0
    
    @property
    def is_expired(self):
        """Eşlemenin süresi dolmuş mu?"""
        return self.days_until_renewal <= 0
    
    @property
    def can_renew(self):
        """Yeniden eşleme yapılabilir mi?"""
        return self.is_expired
    
    def renew_pairing(self):
        """Eşlemeyi yenile"""
        self.last_paired_at = utcnow_str()
        expire_date = datetime.now() + timedelta(days=30)
        self.expires_at = expire_date.strftime('%Y-%m-%d %H:%M:%S')
        self.is_active = True
    
    @classmethod
    def get_active_pairing(cls, user_id, db_session):
        """Kullanıcının aktif eşlemesini getir"""
        return db_session.query(cls).filter(
            cls.user_id == user_id,
            cls.is_active == True
        ).first()
    
    @classmethod
    def get_by_mac_address(cls, mac_address, db_session):
        """Cihaz anahtarına göre eşleme getir"""
        return db_session.query(cls).filter(
            cls.mac_address == mac_address.upper(),
            cls.is_active == True
        ).first()
    
    @classmethod
    def cleanup_expired(cls, db_session):
        """Süresi dolmuş eşlemeleri temizle"""
        expired_pairings = db_session.query(cls).filter(
            cls.is_active == True,
            cls.expires_at < datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ).all()
        
        for pairing in expired_pairings:
            pairing.is_active = False
        
        db_session.commit()
        return len(expired_pairings)
