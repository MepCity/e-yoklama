#!/usr/bin/env python3
"""
Cihaz eşleşmelerini kontrol etme scripti
"""

from database import db
from models.device_pairing import DevicePairing

def check_pairings():
    """Veritabanındaki cihaz eşleşmelerini kontrol eder"""
    try:
        # Tüm eşleşmeleri say
        total_count = db.query(DevicePairing).count()
        
        # Aktif eşleşmeleri say
        active_count = db.query(DevicePairing).filter(DevicePairing.is_active == True).count()
        
        # Pasif eşleşmeleri say
        inactive_count = db.query(DevicePairing).filter(DevicePairing.is_active == False).count()
        
        print(f"📊 Cihaz Eşleşme Durumu:")
        print(f"   Toplam eşleşme: {total_count}")
        print(f"   Aktif eşleşmeler: {active_count}")
        print(f"   Pasif eşleşmeler: {inactive_count}")
        
        if total_count > 0:
            print(f"\n📋 Eşleşme Detayları:")
            pairings = db.query(DevicePairing).all()
            for p in pairings:
                status = "✅ Aktif" if p.is_active else "❌ Pasif"
                print(f"   User {p.user_id}: {status}")
        
        return total_count, active_count, inactive_count
        
    except Exception as e:
        print(f"❌ Hata: {e}")
        return 0, 0, 0

if __name__ == "__main__":
    check_pairings()
