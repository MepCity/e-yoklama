# E-Yoklama

Flask tabanlı, dinamik QR kodlu ve çok katmanlı doğrulama mekanizmalı elektronik yoklama sistemi.

---

## Proje Tanımı

E-Yoklama, üniversite ortamında kâğıtsız ve güvenilir yoklama almayı sağlayan bir web uygulamasıdır. Öğretmenler her ders için 10 saniyede bir yenilenen dinamik QR/alfanümerik kod üretir; öğrenciler bu kodu tarayarak yoklamalarını iletir. Sistem, kodu doğrulamanın yanı sıra **IP ağ kontrolü** ve **GPS konum doğrulaması** uygulayarak varlık sahtekârlığını önler. Şüpheli kayıtlar öğretmen onayına sunulur; tüm yoklama verisi Excel olarak dışa aktarılabilir.

---

## Özellikler

- **Dinamik QR & alfanümerik kod** — 10 saniyelik otomatik yenileme, WebSocket (Socket.IO) ile anlık dağıtım
- **IP prefix doğrulaması** — Kurumun yerel ağı dışındaki bağlantılar şüpheli olarak işaretlenir
- **GPS geofence doğrulaması** — Haversine formülüyle mesafe hesabı, yapılandırılabilir yarıçap (varsayılan 100 m)
- **Şüpheli yoklama yönetimi** — IP/GPS doğrulaması başarısız olan kayıtlar öğretmen onayına düşer; öğrenci "Yine de Devam Et" seçeneğiyle override sebebi girebilir
- **Rol tabanlı erişim kontrolü** — Admin / Öğretmen / Öğrenci rolleri, dekoratör tabanlı yetkilendirme
- **Excel (.xlsx) dışa aktarma** — Öğretmen kendi dersini, admin tüm sistemi export eder
- **İstatistik & grafikler** — Chart.js ile devam oranı, şüpheli oran, ders bazlı karşılaştırma
- **Rate limiting** — Login 5/dak, yoklama gönderimi 10/dak, genel 30/dak
- **Oturum güvenliği** — 30 dakika pasiflik sonrası otomatik oturum sonlandırma
- **Çevrimdışı destek** — Service Worker + IndexedDB ile bağlantısız ortamda yoklama kuyruğu, sonradan senkronizasyon
- **QR kamera tarayıcı** — BarcodeDetector API entegrasyonu, kamera ile otomatik kod okuma

---

## Kullanılan Teknolojiler

### Backend

| Teknoloji | Sürüm | Amaç |
|---|---|---|
| Python | 3.11+ | Uygulama dili |
| Flask | 3.1.1 | Web framework |
| Flask-SocketIO | 5.5.1 | Gerçek zamanlı WebSocket iletişimi |
| Flask-Limiter | 3.11.0 | Rate limiting |
| SQLAlchemy | 2.0.40 | ORM & veritabanı soyutlaması |
| openpyxl | 3.1.5 | Excel dışa aktarma |
| qrcode + Pillow | 8.0 | QR kod üretimi |
| geopy | 2.4.1 | Coğrafi hesaplamalar |

### Frontend

| Teknoloji | Amaç |
|---|---|
| Jinja2 | Sunucu taraflı HTML şablonlama |
| Chart.js (CDN) | İstatistik grafikleri |
| Socket.IO (CDN) | Gerçek zamanlı kod güncellemesi |
| Service Worker | Çevrimdışı destek |
| BarcodeDetector API | Kamera ile QR okuma |

### Veritabanı

| Teknoloji | Amaç |
|---|---|
| SQLite | Geliştirme ortamı |
| SQLAlchemy scoped_session | Thread-safe oturum yönetimi |

---

## Kurulum Adımları

### Gereksinimler

- Python 3.11+
- pip

### 1. Depoyu klonla

```bash
git clone https://github.com/MepCity/e-yoklama.git
cd e-yoklama
```

### 2. Sanal ortam oluştur ve bağımlılıkları yükle

```bash
python3 -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Veritabanını oluştur ve örnek veriyle doldur

```bash
python3 seed.py
```

### 4. Uygulamayı başlat

```bash
python3 wsgi.py
```

Uygulama `http://127.0.0.1:5050` adresinde çalışır.

---

## Kullanım

### Test Kullanıcıları

Seed sonrası aşağıdaki hesaplar kullanıma hazırdır:

| Rol | Kullanıcı Adı | Şifre |
|---|---|---|
| Admin | `admin` | `admin123` |
| Öğretmen | `ogretmen1` | `ogretmen123` |
| Öğretmen | `ogretmen2` | `ogretmen123` |
| Öğrenci | `ogrenci1` … `ogrenci10` | `ogrenci123` |

### Yoklama Akışı

1. **Öğretmen** → Ders Programı → Yoklama Başlat (opsiyonel: IP prefix ve GPS yarıçapı belirle)
2. **Öğrenciler** → Anlık QR kodu tara veya alfanümerik kodu gir
3. **Sistem** → IP + GPS doğrulaması yap; başarısız ise şüpheli olarak işaretle
4. **Öğretmen** → Şüpheli kayıtları incele, onayla veya reddet
5. **Öğretmen / Admin** → Excel olarak dışa aktar

### Entegrasyon Testi

```bash
python3 tests/integration_check.py
```

Login, yoklama gönderimi, şüpheli onay, Excel export, süresi dolmuş kod ve çevrimdışı asset akışlarını doğrular.

---

## Mimari

Proje, 4 katmanlı modüler monolit yapısını benimser:

```
views/       →  HTTP istekleri & yönlendirme (Flask Blueprint'leri)
services/    →  Tüm iş mantığı (attendance, auth, export, statistics, verification)
models/      →  SQLAlchemy şema tanımları
database/    →  Engine & scoped_session yönetimi
```

View katmanı hiçbir zaman doğrudan modele veya veritabanına erişmez; her işlem ilgili servis üzerinden gerçekleşir.

---

## Lisans

Bu proje [MIT Lisansı](LICENSE) kapsamında lisanslanmıştır.
