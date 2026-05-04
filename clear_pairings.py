#!/usr/bin/env python3
"""
Cihaz eşleşmelerini temizleme scripti
"""

from database import db
from models.device_pairing import DevicePairing

def clear_all_pairings():
    """Veritabanındaki tüm cihaz eşleşmelerini siler"""
    try:
        # Tüm eşleşmeleri sil
        deleted_count = db.query(DevicePairing).count()
        db.query(DevicePairing).delete()
        db.commit()
        
        print(f"✅ {deleted_count} cihaz eşleşmesi başarıyla silindi.")
        return True
    except Exception as e:
        print(f"❌ Hata: {e}")
        db.rollback()
        return False

if __name__ == "__main__":
    clear_all_pairings()
