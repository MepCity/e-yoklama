# E-Yoklama

Flask tabanlı, dinamik QR kodlu ve IP/GPS doğrulamalı elektronik yoklama sistemi.

## Kurulum

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 seed.py
python3 wsgi.py
```

Uygulama varsayılan olarak `http://127.0.0.1:5050` adresinde çalışır.

## Test Kullanıcıları

Seed sonrası:

- Admin: `admin / admin123`
- Öğretmen: `ogretmen1 / ogretmen123`
- Öğrenci: `ogrenci1 / ogrenci123`

## Kontrol

```bash
python3 tests/integration_check.py
```

Bu kontrol login, admin/öğretmen/öğrenci akışları, yoklama, şüpheli onay, Excel export, expired code ve offline asset entegrasyonlarını doğrular.

## Son Eklenen Özellikler (FR-20 - FR-23)

### FR-20: Admin Paneli Öğrenci Düzenleme Butonları
- ✅ **Admin panelindeki öğrenci düzenleme butonları (kalem simgeleri) düzeltildi**
- Jinja2 template syntax hatası giderildi
- JavaScript debug ve error handling eklendi

### FR-21: Konum Doğrulama Sistemi
- ✅ **Konum doğrulama sistemndeki session erişim hatası düzeltildi**
- `session['user']['id']` → `session['user']['id']`
- API endpoint'leri çalışır hale getirildi

### FR-22: Öğretmen Paneli Şüpheli Yoklama Yönetimi
- ✅ **Öğretmen paneline şüpheli yoklama yönetimi eklendi**
- Şüpheli yoklamaları onaylama/red etme butonları eklendi
- Backend API endpoint'leri oluşturuldu:
  - `/approve_suspicious_attendance/<record_id>`
  - `/reject_suspicious_attendance/<record_id>`
- Frontend JavaScript fonksiyonları eklendi
- Güvenlik kontrolleri ve yetkilendirme eklendi

### FR-23: Offline Veri Saklama ve Senkronizasyon
- ✅ **Program dokümantasyonu güncellendi**
- GÜNLÜK.md dosyasına tüm değişiklikler kaydedildi
- README.md dosyasına son özellikler eklendi
