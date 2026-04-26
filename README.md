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
