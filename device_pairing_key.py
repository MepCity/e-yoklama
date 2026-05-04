#!/usr/bin/env python3
"""
E-Yoklama Cihaz Eşleşmesi Anahtar Dosyası
Bu dosya cihaz eşleşmesi için güvenli anahtar içerir.
"""

# Sabit gizli anahtar - BU ANAHTAR GÜVENLİ TUTULMALIDIR!
DEVICE_PAIRING_SECRET_KEY = "EY2024_SECURE_DEVICE_PAIRING_KEY_V1!@#$%"

# Anahtar bilgileri
KEY_INFO = {
    "version": "1.0",
    "created_date": "2024-05-04",
    "description": "E-Yoklama Cihaz Eşleşmesi Güvenlik Anahtarı",
    "algorithm": "HMAC-SHA256"
}

def get_pairing_key():
    """Cihaz eşleşmesi anahtarını döndür"""
    return DEVICE_PAIRING_SECRET_KEY

def get_key_info():
    """Anahtar bilgilerini döndür"""
    return KEY_INFO
