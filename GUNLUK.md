# E-Yoklama Sistemi — Proje Günlüğü

> Bu dosya, projenin geçirdiği tüm süreçleri, alınan kararları ve yapılan değişiklikleri kronolojik olarak kayıt altına alır.

---

## 2026-04-26 — Gün 1: Mevcut Durum Analizi ve Mimari Planlama

### 1. Mevcut Durum Analizi

**Saat:** ~İlk oturum

Projenin mevcut kodu ve dokümanları (SRS v1.3, SDD v1.0) detaylıca incelendi.

**Mevcut yapı:**
- Flask + SQLAlchemy + SQLite
- Server-side template rendering (Jinja2)
- 3 rol: Admin (0), Öğretmen (1), Öğrenci (2)
- Basit MVC benzeri klasör yapısı: `views/`, `models/`, `controllers/`, `templates/`, `static/`

**Çalışan özellikler:**
- Kullanıcı giriş/kayıt/çıkış (session tabanlı)
- Admin: Öğrenci, öğretmen, ders yönetimi (CRUD)
- Öğretmen: Ders programı oluşturma, basit yoklama paylaşımı (statik token)
- Öğrenci: QR okuma arayüzü, temel istatistik görüntüleme
- Şifre hashleme (PBKDF2-SHA256)
- Seed data ile test verileri oluşturma

**Tespit edilen eksiklikler (SRS YAPILMALIDIR gereksinimleri):**

| FR Kodu | Gereksinim | Durum |
|---------|-----------|-------|
| FR-04 | Periyodik yenilenen dinamik QR/alfanümerik kod (10sn) | Yok |
| FR-06 | Çok katmanlı doğrulama (İnternet + IP + GPS) | Stub (return True) |
| FR-07 | "Yine de Devam Et" + loglama | Yok |
| FR-08 | Şüpheli yoklamalar ekranı | Yok |
| FR-09 | Öğretmen şüpheli onay/ret mekanizması | Yok |
| FR-11 | Excel (.xlsx) dışa aktarma | Yok |
| FR-12 | Yoklama oturumunu sonlandırma | Yok |
| FR-13 | UUID tabanlı benzersiz oturum kimliği | Yok |
| FR-14 | Tablo + grafik istatistikler | Kısmen (grafik yok) |
| FR-15 | Aynı oturuma çift katılım engeli (duplicate check) | Yok |
| FR-23 | Offline veri saklama + senkronizasyon | Yok |

**Tespit edilen teknik sorunlar:**
- `app.py:43` — `os.system('start msedge ...')` macOS'ta çalışmaz
- `models/lessons.py:5` — `from databases import db` hatalı import
- `controllers/security_functuons.py` — Dosya adında typo, fonksiyonlar boş stub
- `app.secret_key = 'your_secret_key'` — Güvenlik açığı

**SDD ile kod arasındaki mimari farklar:**
- SDD: SPA + REST API + WebSocket → Kod: Server-side rendering
- SDD: PostgreSQL + Redis → Kod: SQLite
- SDD: JWT auth → Kod: Flask session/cookie
- SDD: Docker + CI/CD → Kod: Yok
- SDD: Rate limiting, TLS 1.3 → Kod: Yok

### 2. Mimari Karar: Pragmatik Yaklaşım

**Karar:** SDD'deki ideal mimariye (SPA + PostgreSQL + Redis + Docker) geçiş bu aşamada yapılmayacak. Bunun yerine mevcut Flask + SQLite yapısı korunarak SRS'teki tüm YAPILMALIDIR gereksinimleri eksiksiz implemente edilecek.

**Gerekçe:**
- Proje bir ders ödevi olup 4 kişilik ekip ve tek dönem kısıtı var
- Mevcut iskelet çalışıyor, sıfırdan yazmak zaman kaybı olur
- Flask ile tüm gereksinimler karşılanabilir (WebSocket için Flask-SocketIO, Excel için openpyxl)
- SDD'deki ileri düzey bileşenler (Redis, Docker, CI/CD) v2.0 için planlanabilir

### 3. Mimari Karar Analizi — Detaylı İnceleme

> Bu bölüm, proje için en uygun yazılım mimarisinin belirlenmesi sürecini detaylıca belgeler.
> Analiz sonuçları ve nihai karar aşağıda yer almaktadır.

**Analiz tarihi:** 2026-04-26  
**Analiz sonucu:** Modüler Monolit + Katmanlı Mimari (Layered Architecture) seçildi.  
**Detaylar:** Aşağıda — Bölüm 3.1 ~ 3.6

#### 3.1. Değerlendirilen Mimari Alternatifler

| # | Mimari | Sonuç | Gerekçe |
|---|--------|-------|---------|
| 1 | **Mikroservis** | REDDEDILDI | Operasyonel karmaşıklık (service discovery, API gateway, message broker, distributed tracing), dağıtık veri tutarlılığı problemi (Saga Pattern gerekir), network overhead (NFR-07 "2sn" hedefini tehlikeye atar), 4 kişilik ekip için aşırı mühendislik |
| 2 | **Saf Monolit (mevcut)** | YETERSİZ | Katmanlar arası sınır yok, model'lerde iş mantığı, view'larda sorgu, test edilemez yapı — 5000+ satırda bakım yapılamaz hale gelir |
| 3 | **Klasik MVC** | TEK BAŞINA YETERSİZ | İş mantığı için ayrı katman yok; ya fat-controller ya fat-model problemi oluşur |
| 4 | **SOA** | REDDEDILDI | Enterprise ölçek, SOAP/XML tabanlı, bu proje için gereksiz karmaşıklık |
| 5 | **Modüler Monolit + Katmanlı** | SEÇİLDİ | Tek deploy, net katman sınırları, test edilebilir, ekip paralel çalışabilir, gelecekte mikroservise geçiş kolay |

#### 3.2. Seçilen Mimari: Modüler Monolit + 4 Katmanlı Mimari

**Tanım:** Tek bir Flask uygulaması olarak deploy edilir (monolit) ama iç yapısı 4 net katmana ayrılmıştır (modüler).

**4 Katman:**

1. **Sunum Katmanı (Presentation)** — `views/`, `templates/`, `static/`, `sockets/`
   - HTTP request/response, template rendering, WebSocket event handling
   - İş mantığı YOKTUR, sadece service katmanını çağırır

2. **İş Mantığı Katmanı (Service/Business)** — `services/`
   - Tüm iş kuralları burada: yoklama başlatma, doğrulama, istatistik hesaplama, Excel üretimi
   - Veritabanı sorgularını burada yapar (model nesneleri üzerinden)
   - Service'ler birbirini çağırabilir (döngüsel bağımlılık hariç)

3. **Veri Erişim Katmanı (Data Access / Model)** — `models/`
   - Sadece SQLAlchemy şema tanımı + relationship'ler
   - İş mantığı, veritabanı sorgusu, statik metot YOKTUR

4. **Veritabanı Katmanı (Persistence)** — `database/`
   - SQLAlchemy engine, scoped_session, bağlantı yönetimi

**Yatay Kesişen Katman (Cross-Cutting):** `utils/`, `config.py`
   - Decorator'lar, hashing, QR üretimi, yardımcı fonksiyonlar

#### 3.3. Katmanlar Arası Kurallar (Dependency Rules)

1. Bağımlılık her zaman yukarıdan aşağıya akar: Sunum → Servis → Model → Veritabanı
2. Katman atlama YASAK: View doğrudan Model'e erişemez, her zaman Service üzerinden
3. Model'ler saf şema: İş mantığı, sorgu, statik metot olmaz
4. Service'ler birbirini çağırabilir ama döngüsel bağımlılık yasak
5. View'lar sadece HTTP işi yapar: request parse, service çağır, response dön

#### 3.4. Klasör Yapısı (Yeni)

```
e-yoklama/
├── app.py                      # Application factory + SocketIO init
├── config.py                   # Dev/Prod yapılandırma sınıfları
├── wsgi.py                     # Giriş noktası: socketio.run(app)
├── requirements.txt            # Tüm pip bağımlılıkları
├── seed.py                     # ORM tabanlı test verisi
├── GUNLUK.md                   # Bu dosya
│
├── database/                   # KATMAN 4: Veritabanı bağlantısı
│   ├── __init__.py             # db, Base, init_db() export
│   └── session.py              # engine, scoped_session, teardown
│
├── models/                     # KATMAN 3: Saf şema tanımları
│   ├── __init__.py             # Tüm model import'ları
│   ├── user.py                 # User modeli
│   ├── course.py               # Course + CourseStudent
│   ├── schedule.py             # Schedule (ders saatleri)
│   ├── attendance_session.py   # AttendanceSession (UUID pk)
│   ├── attendance_record.py    # AttendanceRecord (yoklama kaydı)
│   └── verification_log.py     # VerificationLog (audit trail)
│
├── services/                   # KATMAN 2: İş mantığı
│   ├── __init__.py
│   ├── auth_service.py         # Giriş/çıkış/kayıt
│   ├── attendance_service.py   # Oturum yaşam döngüsü, kod üretimi
│   ├── verification_service.py # IP/GPS/kod doğrulama zinciri
│   ├── statistics_service.py   # İstatistik hesaplama
│   └── export_service.py       # Excel (.xlsx) üretimi
│
├── views/                      # KATMAN 1: HTTP route'ları
│   ├── __init__.py
│   ├── auth.py                 # /login, /register, /logout
│   ├── admin.py                # /admin/*
│   ├── teacher.py              # /teacher/*
│   ├── student.py              # /student/*
│   └── api.py                  # /api/* (JSON endpoint'ler)
│
├── sockets/                    # KATMAN 1: WebSocket event'leri
│   ├── __init__.py
│   └── attendance_socket.py    # Canlı QR yenileme, anlık liste
│
├── utils/                      # Yatay kesişen: yardımcı araçlar
│   ├── __init__.py
│   ├── hashing.py              # Şifre hash/verify
│   ├── decorators.py           # @login_required, @role_required
│   ├── qr_generator.py         # QR kod üretimi (base64)
│   └── helpers.py              # Türkçe gün adları, tarih format
│
├── templates/                  # Jinja2 şablonları
│   ├── base.html               # Ana layout (nav, footer, CDN)
│   ├── components/             # Yeniden kullanılabilir parçalar
│   │   ├── _nav.html
│   │   ├── _flash.html
│   │   └── _stats_chart.html
│   ├── auth/login.html
│   ├── admin/dashboard.html, students.html, teachers.html, courses.html, statistics.html
│   ├── teacher/dashboard.html, schedule.html, attendance_session.html, suspicious.html, statistics.html, export.html
│   ├── student/dashboard.html, attend.html, statistics.html
│   └── errors/404.html
│
├── static/
│   ├── css/style.css           # Responsive CSS (mobile-first)
│   └── js/
│       ├── app.js              # Genel JS (flash, nav toggle)
│       ├── attendance_session.js # SocketIO client (öğretmen)
│       ├── student_attend.js   # 3 adımlı yoklama akışı
│       ├── charts.js           # Chart.js helper'ları
│       └── offline.js          # Service Worker + IndexedDB
│
└── sw.js                       # Service Worker (offline destek)
```

#### 3.5. Veritabanı Şeması (Yeni)

**Tablolar:**
- `users` — Kullanıcılar (admin/öğretmen/öğrenci tek tabloda, role ile ayrışır)
- `courses` — Dersler (code alanı eklendi, semester eklendi)
- `course_students` — Ders-öğrenci ilişkisi (UNIQUE constraint)
- `schedules` — Ders saatleri (latitude/longitude/radius_m eklendi — geofence için)
- `attendance_sessions` — Yoklama oturumları (UUID pk, current_code, code_expires_at, status, geofence/IP bilgileri)
- `attendance_records` — Yoklama kayıtları (session_id + student_id UNIQUE — FR-15, tüm doğrulama detayları, şüpheli yönetim alanları)
- `verification_logs` — Doğrulama audit trail (her kontrol adımı loglanır)

**Silinen tablolar:**
- `auth` — Flask session yeterli, ayrı token tablosu gereksiz
- `statistics` — attendance_records üzerinden sorguyla hesaplanır
- `attendance` (eski) — attendance_records ile değiştirildi

**Tablo ilişkileri:**
```
users (1) ──< (N) courses             [teacher_id]
users (N) >──< (N) courses            [course_students ara tablosu]
courses (1) ──< (N) schedules         [course_id]
courses (1) ──< (N) attendance_sessions [course_id]
attendance_sessions (1) ──< (N) attendance_records [session_id]
users (1) ──< (N) attendance_records   [student_id]
attendance_records (1) ──< (N) verification_logs [record_id]
```

#### 3.6. Uygulama Fazları

| Faz | İçerik | Bağımlılık |
|-----|--------|------------|
| **Faz 0** | Altyapı: app factory, config, database session, base template, decorators, requirements.txt | Yok — ilk yapılacak |
| **Faz 1** | Yeni modeller + Yoklama oturum yaşam döngüsü (start/end) | Faz 0 |
| **Faz 2** | Dinamik QR kod + WebSocket canlı yenileme | Faz 1 |
| **Faz 3** | Öğrenci yoklama akışı + 3 katmanlı doğrulama (IP/GPS/kod) | Faz 2 |
| **Faz 4** | Şüpheli yoklama yönetimi (öğretmen onay/ret) | Faz 3 |
| **Faz 5** | İstatistikler + Chart.js grafikleri | Faz 3 |
| **Faz 6** | Excel (.xlsx) dışa aktarma | Faz 3 |
| **Faz 7** | Offline destek (Service Worker + IndexedDB) | Faz 3 |
| **Faz 8** | Güvenlik: rate limiting, expired code rejection, session timeout | Faz 0-3 |
| **Faz 9** | Responsive UI + Türkçe lokalizasyon cilaması | Faz 5 |
| **Faz 10** | Seed data + entegrasyon testi | Tümü |

**Paralel çalışabilecek fazlar:** 4, 5, 6 birbirinden bağımsız — Faz 3 bittikten sonra paralel geliştirilebilir.

---

### 4. Adım 1 — Git + Temel Dosyalar (Tamamlandı)

**Tarih:** 2026-04-26

**Oluşturulan dosyalar:**
- `.gitignore` — Python, IDE, OS, veritabanı dosyaları için ignore kuralları
- `requirements.txt` — 10 bağımlılık: Flask 3.1.1, SQLAlchemy 2.0.40, Flask-SocketIO 5.5.1, flask-limiter 3.11.0, openpyxl 3.1.5, qrcode 8.0, geopy 2.4.1, Pillow 11.2.1, python-socketio 5.13.0, python-engineio 4.12.1
- `config.py` — Config/DevelopmentConfig/ProductionConfig/TestConfig sınıfları. QR yenileme, geofence, IP, rate limit, devamsızlık eşiği ayarları

**Test:** `pip install` başarılı, config import doğrulandı.

### 5. Adım 2 — Veritabanı Katmanı (Tamamlandı)

**Tarih:** 2026-04-26

**Oluşturulan dosyalar:**
- `database/__init__.py` — `init_db(app)`, `get_db()` export. `app.teardown_appcontext` ile her request sonunda session temizleme
- `database/session.py` — `engine`, `scoped_session` (thread-safe), `Base`, `shutdown_session`

**Eski `databases/` ile farkı:**
- Eski: `db = SessionLocal()` ile global tek session kullanıyordu; bu yapı request/thread bazlı session yönetimi sağlamıyordu
- Yeni: `scoped_session` ile her thread kendi session'ına sahip, `teardown_appcontext` ile otomatik temizleme

**Test:** Engine oluşturma, session alma, shutdown başarılı.

### 6. Adım 3 — Yardımcı Araçlar (Tamamlandı)

**Tarih:** 2026-04-26

**Oluşturulan dosyalar:**
- `utils/__init__.py`
- `utils/hashing.py` — `hash_password()`, `verify_password()` (eski `controllers/hash.py`'den taşındı, aynı PBKDF2-SHA256 mantığı)
- `utils/decorators.py` — `@login_required`, `@role_required(*roles)` (tüm view'larda tekrar eden session kontrolünü merkezileştirdik)
- `utils/helpers.py` — Türkçe gün adları, durum etiketleri/renkleri, tarih formatlama fonksiyonları
- `utils/qr_generator.py` — `generate_qr_base64(data)` QR kod üretip base64 string döner

**Test:** Hash/verify çalışıyor, helper fonksiyonlar doğru, QR base64 üretimi başarılı.

### 7. Adım 4 — Yeni Modeller (Tamamlandı)

**Tarih:** 2026-04-26

**Oluşturulan/değiştirilen dosyalar:**
- `models/__init__.py` — Yeniden yazıldı, yeni model import'ları
- `models/user.py` — `User` modeli (eski `Users` → tekil isimlendirme). `to_dict()` metodu eklendi. İş mantığı (login, register, logout) çıkarıldı → service'e taşınacak
- `models/course.py` — `Course` + `CourseStudent` modelleri. `code` ve `semester` alanları eklendi. UNIQUE constraint course_student çiftine
- `models/schedule.py` — `Schedule` modeli (eski `Lessons` adı karışıklık yaratıyordu). `latitude`/`longitude`/`radius_m` alanları eklendi (geofence — NFR-05/06)
- `models/attendance_session.py` — **YENİ** tablo. UUID primary key (FR-13), `current_code` + `code_expires_at` (FR-04), `status` active/ended (FR-12), geofence ve IP bilgileri
- `models/attendance_record.py` — **YENİ** tablo. Eski `Attendance` + `Statistics` birleştirildi. `session_id + student_id` UNIQUE constraint (FR-15). Doğrulama alanları: `ip_match`, `gps_match`, `gps_distance_m`. Override alanları: `override_used`, `override_reason` (FR-07). İnceleme alanları: `reviewed_by`, `reviewed_at`, `review_note` (FR-09)
- `models/verification_log.py` — **YENİ** tablo. Audit trail: her doğrulama adımı loglanır

**Silinen kavramlar (henüz dosyalar silinmedi, Adım 12'de silinecek):**
- `Auth` modeli → Flask session yeterli
- `Statistics` modeli → Sorguyla hesaplanacak
- `Attendance` modeli → `AttendanceRecord` ile değiştirildi
- Model'lerdeki statik metotlar (login, register, create, mark_attendance vs.) → Service katmanına taşınacak

**Test:** 7 tablo sorunsuz oluştu: `users`, `courses`, `course_students`, `schedules`, `attendance_sessions`, `attendance_records`, `verification_logs`. Nesne oluşturma, relationship erişimi ve duplicate constraint kontrolü başarılı.

### 8. Adım 5 — App Factory + Base Template + View'lar (Tamamlandı)

**Tarih:** 2026-04-26

**Oluşturulan/değiştirilen dosyalar:**

- `app.py` — **Yeniden yazıldı.** Application Factory pattern (`create_app(config_name)`). Blueprint register, init_db, SocketIO init, error handler'lar, jinja globals (day_name, format_datetime, STATUS_LABELS, STATUS_COLORS). Eski monolitik `if __name__` bloğu kaldırıldı.
- `wsgi.py` — **YENİ.** Giriş noktası: `from app import create_app, socketio; app = create_app(); socketio.run(app)`
- `templates/base.html` — **YENİ.** Ana layout: viewport meta, CSS link, Chart.js CDN, Socket.IO CDN, nav include, flash include, content/scripts blokları
- `templates/components/_nav.html` — **YENİ.** Rol bazlı navigasyon (admin/öğretmen/öğrenci linkleri), mobil hamburger menü toggle
- `templates/components/_flash.html` — **YENİ.** Flash mesajları: success/error/info/warning tipleri, kapatma butonu
- `templates/errors/404.html` — **YENİ.** 404/403 hata sayfası
- `static/js/app.js` — **Yeniden yazıldı.** `toggleNav()` mobil menü, flash mesajları 5sn sonra otomatik kapanma

**View'lar (Sunum Katmanı):**

- `views/admin.py` — **Yeniden yazıldı.** `@role_required(0)` decorator ile korunan admin route'ları: dashboard, students (filtreleme/sıralama), teachers, add_teacher, courses, create_course, add_student_to_course, statistics
- `views/teacher.py` — **Yeniden yazıldı.** `@role_required(1)` ile: dashboard (öğretmenin dersleri), course_schedule (GET/POST — ders saati ekleme), statistics (ders bazlı katılım istatistikleri)
- `views/student.py` — **Yeniden yazıldı.** `@role_required(2)` ile: dashboard (kayıtlı dersler), statistics (genel + ders bazlı katılım oranı)

**Admin Template'leri:**
- `templates/admin/dashboard.html` — Hızlı erişim linkleri (Öğrenciler, Öğretmenler, Dersler, İstatistikler)
- `templates/admin/students.html` — Öğrenci listesi: bölüm filtresi, sıralama (öğrenci no/bölüm/sınıf)
- `templates/admin/teachers.html` — Öğretmen listesi + yeni öğretmen ekleme formu
- `templates/admin/courses.html` — Ders listesi + yeni ders oluşturma + derse öğrenci ekleme
- `templates/admin/statistics.html` — İstatistik kartları (toplam öğrenci/öğretmen/ders/kayıt) + bölüm bazlı dağılım tablosu

**Test:** Tüm route'lar Flask route map'de doğrulandı.

### 9. Adım 6 — Auth Sistemi + Kalan Template'ler + CSS (Tamamlandı)

**Tarih:** 2026-04-26

**Auth Sistemi:**

- `services/auth_service.py` — **YENİ.** İş mantığı katmanı:
  - `login(username, password)` → user veya hata mesajı döner
  - `register_student(username, email, password, student_number, ...)` → user veya hata
  - `register_teacher(username, email, password, branch)` → user veya hata
  - `get_user_by_id(user_id)` → user nesnesi
- `views/auth.py` — **Yeniden yazıldı.** GET/POST `/login`, POST `/register`, GET `/logout`. Doğrudan model erişimi yerine auth_service kullanır
- `templates/auth/login.html` — **YENİ.** Tab arayüzü: Giriş / Kayıt Ol sekmeleri. Giriş: kullanıcı adı + şifre. Kayıt: ad, e-posta, şifre, öğrenci no, bölüm, sınıf

**Kalan Template'ler:**

- `templates/teacher/dashboard.html` — Öğretmenin dersleri (kart grid) + ders programı linki
- `templates/teacher/schedule.html` — **YENİ.** Ders saati ekleme formu (gün, başlangıç, bitiş, derslik) + mevcut program tablosu
- `templates/teacher/statistics.html` — **YENİ.** Ders bazlı katılım oranı kartları + detaylı tablo + Chart.js bar grafik
- `templates/student/dashboard.html` — **YENİ.** Öğrencinin kayıtlı dersleri (kart grid)
- `templates/student/statistics.html` — **YENİ.** Genel istatistik kartları (toplam/katılım/devamsız/oran) + ders bazlı tablo + Chart.js doughnut grafik

**CSS:**

- `static/css/style.css` — **Tamamen yeniden yazıldı.** Responsive tasarım:
  - Modern reset + system font stack
  - Navigasyon: flex layout, mobil hamburger menü (768px altı)
  - Flash mesajlar: sol border renk kodlu (success/error/info/warning)
  - Butonlar: btn, btn-primary, btn-danger, btn-small
  - Kart sistemi: card, card-grid (auto-fill grid), card-actions
  - İstatistik kartları: stats-grid, stat-card, stat-number
  - Form sistemi: form-group, form-row (grid), form-inline (flex)
  - Tablo: table-responsive (overflow scroll), hover efekti
  - Tab sistemi: tablink, tabcontent
  - Durum renkleri: status-verified, status-suspicious, status-absent vb.
  - QR bölümü: qr-section, qr-code
  - 3 breakpoint: 768px, 480px

**Test:** `python3 -c "from app import create_app; app = create_app()"` başarılı. 18 route doğrulandı:
- `/`, `/login`, `/register`, `/logout`
- `/admin/dashboard`, `/admin/students`, `/admin/teachers`, `/admin/add_teacher`, `/admin/courses`, `/admin/create_course`, `/admin/add_student_to_course`, `/admin/statistics`
- `/teacher/dashboard`, `/teacher/course/<int:course_id>/schedule`, `/teacher/statistics`
- `/student/dashboard`, `/student/statistics`
- `/static/<path:filename>`

---

### Faz 0 Durumu

Adım 1-6 tamamlandı. Faz 0 (Altyapı) büyük ölçüde tamamlanmış durumda:

- [x] config.py — Merkezi yapılandırma
- [x] requirements.txt — Bağımlılıklar
- [x] database/ — Scoped session, init_db, teardown
- [x] models/ — 7 model (User, Course, CourseStudent, Schedule, AttendanceSession, AttendanceRecord, VerificationLog)
- [x] utils/ — Hashing, decorators, helpers, QR generator
- [x] app.py — Application factory + SocketIO
- [x] wsgi.py — Giriş noktası
- [x] templates/ — Base layout + admin (5) + teacher (3) + student (2) + auth (1) + error (1) + components (2)
- [x] CSS — Responsive tasarım
- [x] Auth sistemi — Service + view + template

**Sonraki hedef:** ~~Faz 1 — Yoklama oturum yaşam döngüsü~~ → Tamamlandı (aşağıya bakınız)

---

### 10. Faz 1 — Yoklama Oturum Yaşam Döngüsü + Minimal Seed (Tamamlandı)

**Tarih:** 2026-04-26

**Kapsam:** FR-12 (oturum sonlandırma), FR-13 (UUID tabanlı oturum kimliği), minimal seed data

#### 10.1. attendance_service.py — Yoklama Oturum Servisi

**Dosya:** `services/attendance_service.py` — **YENİ**

**Fonksiyonlar:**
- `_generate_code(length=6)` — `secrets.choice()` ile kriptografik güvenli 6 haneli alfanümerik kod üretir (A-Z + 0-9)
- `start_session(course_id, teacher_id, ...)` — Yeni yoklama oturumu başlatır:
  - Aynı ders için aktif oturum varsa engeller
  - Dersin o öğretmene ait olduğunu doğrular
  - UUID primary key oluşturur (FR-13)
  - İlk kodu üretir, expire süresini ayarlar
  - Geofence ve IP ayarlarını kaydeder
  - `(session, None)` veya `(None, error_message)` döner
- `end_session(session_id, teacher_id)` — Oturumu sonlandırır (FR-12):
  - Sahiplik kontrolü yapar
  - `status='ended'`, `ended_at` kaydeder
  - Tekrar sonlandırmayı engeller
- `get_active_session(course_id)` — Bir dersin aktif oturumunu döner
- `get_session_by_id(session_id)` — UUID ile oturum sorgular
- `refresh_code(session_id)` — Yeni kod üretir + expire günceller (Faz 2'de WebSocket ile kullanılacak)
- `get_session_records(session_id)` — Oturuma ait katılım kayıtlarını döner
- `get_enrolled_count(course_id)` — Derse kayıtlı öğrenci sayısı

#### 10.2. Teacher View Güncellemeleri

**Dosya:** `views/teacher.py` — **Güncellendi**

**Yeni route'lar:**
- `POST /teacher/course/<id>/start-session` — Yoklama başlatma formu işler. Config'den veya formdan: refresh_seconds, allowed_ip_prefix, latitude/longitude, radius_m. Başarılı olursa aktif oturum sayfasına yönlendirir.
- `GET /teacher/session/<session_id>` — Aktif oturum sayfası: QR kodu + alfanümerik kod + katılım listesi + istatistikler. QR base64 olarak generate edilir.
- `POST /teacher/session/<session_id>/end` — Oturumu sonlandırır, aynı sayfaya yönlendirir (artık "sonlandırılmış" olarak gösterilir).

**Güncellenen route'lar:**
- `GET /teacher/dashboard` — Artık aktif oturumları da gönderir → template'te "Aktif Yoklama" butonu
- `GET /teacher/course/<id>/schedule` — Aktif oturum varsa "Aktif Oturuma Git" linki, yoksa "Yoklama Başlat" formu gösterir

#### 10.3. Template Güncellemeleri

- `templates/teacher/active_session.html` — **YENİ.** Aktif yoklama oturum sayfası:
  - Üstte 3 stat kartı: oturum durumu, katılım/kayıtlı sayısı, kod yenileme süresi
  - Ortada QR bölümü: QR görsel (base64 PNG) + alfanümerik kod + bilgi mesajı
  - "Oturumu Sonlandır" butonu (confirm dialog ile)
  - Sonlandırılmış oturumlar için bilgi mesajı
  - Altta katılım tablosu: öğrenci no, ad, durum (renkli), saat, IP, IP/GPS eşleşme bilgisi
- `templates/teacher/schedule.html` — **Güncellendi.** "Yoklama Oturumu" bölümü eklendi: aktif oturum varsa link, yoksa başlatma formu (ders saati seçimi, kod yenileme süresi, IP filtresi)
- `templates/teacher/dashboard.html` — **Güncellendi.** Aktif yoklama olan derslerde "Aktif Yoklama" butonu

#### 10.4. Minimal Seed Data

**Dosya:** `seed.py` — **Tamamen yeniden yazıldı**

Eski seed eski modül yapısını kullanıyordu (`databases.dbconnect`, `controllers.hash`). Yeni mimariyle uyumlu ORM tabanlı seed:

**Oluşturulan veriler:**
- 1 admin: `admin / admin123`
- 2 öğretmen: `ogretmen1 / ogretmen123` (Yazılım Müh.), `ogretmen2 / ogretmen123` (Veri Tabanı)
- 10 öğrenci: `ogrenci1~10 / ogrenci123` (2 bölüm × 5 öğrenci)
- 3 ders: YZM301 (öğretmen1, 5 öğrenci), VTY201 (öğretmen2, 3 öğrenci), ALG401 (öğretmen1, 5 öğrenci)
- 3 ders programı: Pazartesi, Çarşamba, Perşembe
- 1 ders programında geofence: YZM301 D-301 (40.9833, 29.0500, 100m)

**Kullanım:** `python3 seed.py` — DB'yi sıfırlar ve yeniden oluşturur.

#### 10.5. Diğer Düzeltmeler

- `wsgi.py` — Port 5050'ye değiştirildi (macOS AirPlay 5000'i kullanıyor). `allow_unsafe_werkzeug=True` eklendi (geliştirme modu).

#### 10.6. Testler

**Birim testleri (10/10 başarılı):**
1. Kod üretimi (6 karakter, alfanümerik)
2. Oturum başlatma (UUID pk, initial code, status=active)
3. Aynı derse çift oturum engeli
4. Aktif oturum sorgulama
5. UUID ile oturum getirme
6. Kod yenileme (eski ≠ yeni)
7. Kayıtlı öğrenci sayısı
8. Boş kayıt listesi
9. Oturum sonlandırma (status=ended, ended_at set)
10. Tekrar sonlandırma engeli

**HTTP entegrasyon testleri (tam döngü):**
1. `POST /login` → 302 (giriş başarılı)
2. `GET /teacher/dashboard` → 200, "Ders Programı" linkleri mevcut
3. `GET /teacher/course/1/schedule` → 200, "Yoklamayı Başlat" butonu mevcut
4. `POST /teacher/course/1/start-session` → 302 → aktif oturum sayfasına yönlendirme
5. `GET /teacher/session/<uuid>` → 200, QR kodu + "Katılım / 5 kayıtlı" + QR görseli
6. `GET /teacher/dashboard` → "Aktif Yoklama" butonu görünür
7. `POST /teacher/session/<uuid>/end` → 302 → oturum sayfası "sonlandırılmıştır"
8. `GET /teacher/course/1/schedule` → "Yoklamayı Başlat" tekrar görünür

**Toplam route sayısı:** 22 (önceki 18 + 4 yeni)

---

### Revize Faz Sıralaması

Faz 1 tamamlandıktan sonra diğer AI'ın önerisiyle sıralama revize edildi:

| Faz | İçerik | Durum |
|-----|--------|-------|
| **Faz 1** | Yoklama oturum başlat/bitir + minimal seed | **TAMAMLANDI** |
| **Faz 2** | Dinamik QR kod + süreli kod doğrulama | **TAMAMLANDI** |
| **Faz 3** | Öğrenci yoklama akışı + duplicate check (FR-15) | **TAMAMLANDI** |
| **Faz 4** | IP/GPS doğrulama + "Yine de Devam Et" (FR-06, FR-07) | **TAMAMLANDI** |
| **Faz 5** | Şüpheli yoklama yönetimi — öğretmen onay/ret (FR-08, FR-09) | **TAMAMLANDI** |
| **Faz 6** | İstatistikleri gerçek veriye dayandır + Chart.js (FR-14) | **TAMAMLANDI** |
| **Faz 7** | Excel export (FR-11) | **TAMAMLANDI** |
| **Faz 8** | Güvenlik: rate limit, session timeout, expired code | **TAMAMLANDI** |
| **Faz 9** | Responsive UI cilası + Türkçe lokalizasyon | Bekliyor |
| **Faz 10** | Offline destek (FR-23) | Bekliyor |
| **Faz 11** | Entegrasyon testi + final cleanup | Bekliyor |

---

### 11. Faz 2 — Dinamik QR Kod + WebSocket Canlı Yenileme (Tamamlandı)

**Tarih:** 2026-04-26

**Kapsam:** FR-04 — Yoklama oturumu boyunca periyodik yenilenen QR/alfanümerik kod.

#### 11.1. Socket.IO Event Katmanı

**Dosya:** `sockets/attendance_socket.py` — **YENİ**

**Event'ler:**
- `join_attendance_session` — Öğretmen aktif oturum odasına katılır. Sunucuda rol ve oturum sahipliği kontrol edilir.
- `refresh_attendance_code` — Kod süresi dolduysa yeni kod üretilir ve `code_rotated` event'i aynı oturum odasına yayınlanır.
- `leave_attendance_session` — Sayfadan çıkarken Socket.IO odasından ayrılır.

Yetkisiz erişimde `attendance_error` event'i gönderilir. Öğretmen sadece kendi oturumuna erişebilir.

#### 11.2. Attendance Service Güncellemeleri

**Dosya:** `services/attendance_service.py`

Eklenen fonksiyonlar:
- `is_code_expired(session)` — `code_expires_at` alanını kontrol eder.
- `refresh_code_if_expired(session_id)` — Kod süresi dolduysa yeniler, dolmadıysa mevcut kodu korur.
- `get_code_payload(session)` — WebSocket payload'u için code/expires/refresh bilgilerini döner.

`refresh_code(session_id)` Faz 1'deki gibi her çağrıda yeni kod üretir; WebSocket akışı ise çoklu istemcide gereksiz çift yenilemeyi önlemek için `refresh_code_if_expired()` kullanır.

#### 11.3. App + Template Güncellemeleri

**Dosyalar:**
- `app.py` — Socket.IO `manage_session=False` ile Flask session uyumlu hale getirildi. `register_socket_events(socketio)` çağrısı eklendi.
- `views/teacher.py` — Aktif oturum sayfası açılırken kod süresi dolmuşsa ilk render öncesi yenilenir.
- `templates/teacher/active_session.html` — QR görseli, alfanümerik kod, geçerlilik zamanı ve kalan süre canlı güncellenir.

Sayfa Socket.IO ile oturuma bağlanır, her saniye kalan süreyi gösterir ve süre dolduğunda sunucudan yenileme ister.

#### 11.4. Testler

**Geçen testler:**
- `py_compile` başarılı.
- Aktif oturum sayfası 200 döndü.
- Template içinde `codeCountdown`, `join_attendance_session`, `qrImage` render edildi.
- Socket.IO test client bağlandı.
- `join_attendance_session` → `code_rotated` döndü.
- Süresi geçmiş kod için `refresh_attendance_code` → yeni kod üretildi.
- Yetkisiz öğretmen başka öğretmenin oturumuna katılınca `attendance_error` aldı.
- Dev server smoke testi yapıldı. 5050 portu dolu olduğu için uygulama geçici olarak 5051 portunda başlatıldı; `HEAD /login` isteği 200 OK döndü.

---

### 12. Faz 3 — Öğrenci Yoklama Akışı + Duplicate Check (Tamamlandı)

**Tarih:** 2026-04-26

**Kapsam:** FR-15 — Aynı öğrencinin aynı yoklama oturumuna birden fazla katılmasını engelleme. Faz 2'deki süreli kodun öğrenci check-in sırasında doğrulanması.

#### 12.1. Attendance Service Güncellemeleri

**Dosya:** `services/attendance_service.py`

Eklenen fonksiyonlar:
- `get_active_session_for_student(course_id, student_id)` — Öğrencinin derse kayıtlı olduğunu doğrulayıp aktif oturumu döner.
- `check_in(session_id, student_id, submitted_code, ip_address=None)` — Öğrenci yoklama geçişini işler:
  - Oturum aktif mi kontrol eder.
  - Öğrenci derse kayıtlı mı kontrol eder.
  - Duplicate kayıt var mı kontrol eder.
  - Kod süresi geçmiş mi kontrol eder.
  - Gönderilen kod mevcut kodla eşleşiyor mu kontrol eder.
  - Başarılıysa `AttendanceRecord(status='verified')` oluşturur.
  - Kod/duplicate kontrollerini `VerificationLog` tablosuna yazar.

#### 12.2. Student View + Template Güncellemeleri

**Dosyalar:**
- `views/student.py` — Öğrenci dashboard artık kayıtlı derslerdeki aktif oturumları gönderir. `POST /student/session/<session_id>/check-in` route'u eklendi.
- `templates/student/dashboard.html` — Aktif oturum olan derslerde kod giriş formu ve "Yoklama Ver" butonu gösterilir. Öğrenci zaten katıldıysa form yerine katılım bilgisi gösterilir.

#### 12.3. Testler

**Geçen testler:**
- `py_compile` başarılı.
- Doğru kodla check-in başarılı, `AttendanceRecord(status='verified')` oluştu.
- Kod büyük/küçük harf duyarsız doğrulandı.
- Aynı öğrenci aynı oturuma ikinci kez katılamadı.
- Derse kayıtlı olmayan öğrenci check-in yapamadı.
- Süresi geçmiş kod reddedildi.
- HTTP akışı: öğrenci dashboard aktif oturum formunu gösterdi, check-in sonrası istatistik sayfasına yönlendirdi.

---

### 13. Legacy Temizlik (Tamamlandı)

**Tarih:** 2026-04-26

Yeni modüler monolit yapısına geçildikten sonra kullanılmayan eski dosyalar kaldırıldı:

- `controllers/` — eski controller/stub dosyaları
- `databases/` — eski global session veritabanı katmanı
- `models/auth.py`, `models/lessons.py`, `models/users.py` — eski model dosyaları
- Eski root template dosyaları (`templates/admin.html`, `templates/student.html`, `templates/teacher.html`, vb.)
- `static/js/script.js` — eski login tab script'i
- Uygulama tarafından kullanılmayan büyük teslim dokümanları (`.docx`, `.pdf`) repo dışına alındı
- `__pycache__` klasörleri ve lokal `e_yoklama.db`

**Doğrulama:**
- Eski `databases`, `controllers`, `models.users`, `models.lessons`, `models.auth` import referansı kalmadı.
- `database/` aktif veritabanı katmanı olarak kaldı; eski `databases/` tamamen kaldırıldı.
- `py_compile` başarılı.
- `create_app('testing')` başarılı.
- `/login` 200, 404 sayfası 404 döndü.
- Öğrenci check-in smoke testi başarılı.

---

### 14. Faz 4 — IP/GPS Doğrulama + Yine de Devam Et (Tamamlandı)

**Tarih:** 2026-04-26

**Kapsam:** FR-06, FR-07 — Öğrenci yoklama geçişinde IP/GPS doğrulama ve doğrulama başarısızsa öğrencinin "Yine de Devam Et" ile şüpheli kayıt oluşturabilmesi.

#### 14.1. Verification Service

**Dosya:** `services/verification_service.py` — **YENİ**

Eklenen kontroller:
- `validate_ip(ip_address, allowed_prefix)` — IP prefix doğrulaması.
- `validate_gps(latitude, longitude, target_latitude, target_longitude, radius_m)` — kampüs/sınıf yarıçapı kontrolü.
- `haversine_m(...)` — iki GPS noktası arasındaki mesafeyi metre cinsinden hesaplar.
- `validate_context(...)` — IP + GPS sonuçlarını tek structured sonuçta toplar.

Not: Lokal geliştirme/test için `127.0.0.1` ve `::1` IP adresleri bypass edilir.

#### 14.2. Attendance Service Güncellemeleri

**Dosya:** `services/attendance_service.py`

- `check_in()` artık IP/GPS doğrulama sonucunu kullanır.
- Doğrulama başarılıysa kayıt `status='verified'` olur.
- Doğrulama başarısız ve override yoksa işlem reddedilir.
- Doğrulama başarısız ve override varsa kayıt `status='suspicious'`, `override_used=1` olur.
- IP/GPS eşleşme bilgileri `AttendanceRecord` alanlarına yazılır.
- Kod/IP/GPS/override sonuçları `VerificationLog` tablosuna yazılır.
- Öğretmen ders programı seçerse `Schedule.latitude/longitude/radius_m` değerleri oturuma kopyalanır.

#### 14.3. Student View + Template Güncellemeleri

**Dosyalar:**
- `views/student.py` — check-in formundan `latitude`, `longitude`, `override`, `override_reason` alınır.
- `templates/student/dashboard.html` — GPS hidden input'ları, konum alma JavaScript'i, "Yine de Devam Et" seçeneği ve opsiyonel açıklama alanı eklendi.

#### 14.4. Testler

**Geçen testler:**
- `py_compile` başarılı.
- Doğru IP + doğru GPS → `verified`.
- Hatalı IP + override yok → işlem reddedildi.
- Hatalı IP + override var → `suspicious`.
- Hatalı GPS + override var → `suspicious`.
- Duplicate check hâlâ çalışıyor.
- HTTP öğrenci dashboard GPS alanlarını render ediyor.
- HTTP override check-in sonrası `AttendanceRecord(status='suspicious')` oluştu.

#### 14.5. Bug Fix — gps_distance_m None Kontrolü

**Dosya:** `templates/teacher/active_session.html:72`

**Sorun:** GPS koordinatları gönderilmediğinde `gps_match=0` ama `gps_distance_m=None` oluyordu. Template'teki `{{ r.gps_distance_m|round(0) }}` ifadesi None üzerinde `round()` çağırınca `TypeError: type NoneType doesn't define __round__ method` hatası veriyordu. Bu hata öğretmenin aktif oturum sayfasını tamamen kırıyordu (500 hatası).

**Düzeltme:** `{% if r.gps_distance_m is not none %}` kontrolü eklendi. Mesafe bilgisi yoksa sadece "Hayir" yazılır, varsa "Hayir (Xm)" gösterilir.

---

### 15. Faz 5 — Şüpheli Yoklama Yönetimi (Tamamlandı)

**Tarih:** 2026-04-26

**Kapsam:** FR-08, FR-09 — Öğretmenin şüpheli yoklamaları görmesi, incelemesi ve onay/ret kararı vermesi.

#### 15.1. Attendance Service Güncellemeleri

**Dosya:** `services/attendance_service.py`

Eklenen fonksiyonlar:
- `get_suspicious_records(session_id)` — Bir yoklama oturumundaki `status='suspicious'` kayıtları listeler.
- `resolve_suspicious(record_id, teacher_id, decision, note=None)` — Öğretmen sahiplik kontrolü yaparak şüpheli kaydı onaylar veya reddeder.

Karar sonucu:
- `approve` → kayıt `status='approved'` olur.
- `reject` → kayıt `status='rejected'` olur.
- `reviewed_by`, `reviewed_at`, `review_note` alanları doldurulur.
- Karar `VerificationLog` tablosuna `review` adımı olarak yazılır.

#### 15.2. Teacher View + Template Güncellemeleri

**Dosyalar:**
- `views/teacher.py` — Aktif oturum sayfasına şüpheli kayıt listesi gönderildi. `POST /teacher/records/<record_id>/resolve` route'u eklendi.
- `templates/teacher/active_session.html` — "Şüpheli Yoklamalar" tablosu eklendi. Öğretmen her kayıt için not girip "Onayla" veya "Reddet" kararı verebilir.

#### 15.3. Testler

**Geçen testler:**
- `py_compile` başarılı.
- Servis testi: şüpheli kayıt listelendi, onay kararıyla `approved`, ret kararıyla `rejected` durumuna geçti.
- Sahip olmayan öğretmenin inceleme yapması engellendi.
- Aynı kayıt ikinci kez incelenemedi.
- HTTP testi: öğretmen aktif oturum sayfasında şüpheli tabloyu gördü, POST ile onay kararı kayda işlendi.

---

### 16. Faz 6 — İstatistikler + Chart.js Grafikleri (Tamamlandı)

**Tarih:** 2026-04-26

**Kapsam:** FR-14 — Admin, öğretmen ve öğrenci istatistiklerinin gerçek yoklama verisine dayandırılması ve grafiklerle gösterilmesi.

#### 16.1. Statistics Service

**Dosya:** `services/statistics_service.py` — **YENİ**

Eklenen hesaplamalar:
- Beklenen yoklama sayısı: `yoklama oturumu x kayıtlı öğrenci`.
- Katılım: `verified`, `approved`, `manual`.
- Şüpheli: `suspicious`.
- Reddedilen: `rejected`.
- Girilmemiş/devamsız: Beklenen yoklama olup hiç kayıt oluşmayan durumlar.
- Katılım oranı: Katılım / beklenen yoklama.

Bu değişiklikle sadece oluşmuş kayıtları sayan eski yaklaşım bırakıldı; hiç yoklama vermeyen öğrenciler de devamsızlık hesabına dahil edildi.

#### 16.2. Route Güncellemeleri

**Dosyalar:**
- `views/admin.py` — Sistem istatistikleri `statistics_service.get_admin_statistics()` üzerinden alınır.
- `views/teacher.py` — Öğretmen ders istatistikleri `statistics_service.get_teacher_statistics()` üzerinden alınır.
- `views/student.py` — Öğrenci kişisel istatistikleri `statistics_service.get_student_statistics()` üzerinden alınır.

#### 16.3. Template + Grafik Güncellemeleri

**Dosyalar:**
- `templates/admin/statistics.html` — Durum dağılımı doughnut grafik, ders bazlı katılım oranı bar grafik, ders bazlı özet tablo.
- `templates/teacher/statistics.html` — Katılım/devamsız/şüpheli durumlarını gösteren bar grafik ve detaylı tablo.
- `templates/student/statistics.html` — Kişisel durum dağılımı doughnut grafik, ders bazlı katılım oranı bar grafik ve detaylı tablo.
- `static/css/style.css` — Grafik panelleri için responsive `chart-grid` ve `chart-panel` stilleri.

#### 16.4. Testler

**Geçen testler:**
- `py_compile` başarılı.
- Servis testi: 2 oturum x 2 öğrenci senaryosunda beklenen yoklama, katılım, şüpheli, reddedilen ve girilmemiş değerleri doğru hesaplandı.
- HTTP testi: admin/öğretmen/öğrenci istatistik sayfaları 200 döndü ve Chart.js canvas/script verileri render edildi.

---

### 17. Faz 7 — Excel Export (Tamamlandı)

**Tarih:** 2026-04-26

**Kapsam:** FR-11 — Yoklama verilerinin `.xlsx` formatında dışa aktarılması.

#### 17.1. Export Service

**Dosya:** `services/export_service.py` — **YENİ**

Eklenen fonksiyonlar:
- `export_course_attendance(course_id)` — Tek ders için Excel üretir.
- `export_all_courses()` — Admin için tüm dersleri içeren Excel üretir.

Excel içeriği:
- Yoklama kayıtları sayfası: Öğrenci no, ad, oturum tarihi, durum, kod, IP, GPS mesafe, gönderim zamanı.
- Öğrenci özet sayfası: Toplam oturum, katılım, şüpheli, devamsız, oran.
- Tüm ders export'unda genel özet ve ders bazlı ayrı sayfalar.

#### 17.2. Route + UI Güncellemeleri

**Dosyalar:**
- `views/admin.py` — `GET /admin/export/all`, `GET /admin/export/course/<course_id>` route'ları eklendi.
- `views/teacher.py` — `GET /teacher/export/course/<course_id>` route'u eklendi. Öğretmen sadece kendi dersini indirebilir.
- `templates/admin/statistics.html` — Tüm dersleri ve tek dersi Excel indirme linkleri eklendi.
- `templates/teacher/statistics.html` — Ders bazlı Excel indirme linki eklendi.

#### 17.3. Stabilite Düzeltmeleri

- Excel sheet adları güvenli hale getirildi: `/`, `:`, `?`, `*`, `[`, `]` gibi Excel'in kabul etmediği karakterler temizlenir.
- Aynı sheet adına düşen dersler için otomatik sıra eklenir.
- İndirme dosya adı güvenli karakterlere indirgenir.
- Tarih alanları hem string hem `datetime` nesnesi olarak düzgün formatlanır.
- Model timestamp default'ları Python tarafındaki `utcnow_str()` ile üretilir; eski SQLite literal default sorunu temizlendi.

#### 17.4. Testler

**Geçen testler:**
- `py_compile` başarılı.
- Öğretmen kendi dersini `.xlsx` olarak indirebildi.
- Başka öğretmenin dersi indirmesi engellendi.
- Admin tüm dersleri ve tek dersi indirebildi.
- Üretilen `.xlsx` dosyaları `openpyxl` ile açıldı.
- Girilmemiş yoklama satırları export'a yazıldı.
- `ALG/401`, `ALG:401` gibi yasak karakterli/çakışan ders kodlarıyla export 500 vermeden çalıştı.

---

### 18. Faz 8 — Güvenlik: Rate Limit + Session Timeout + Expired Code (Tamamlandı)

**Tarih:** 2026-04-26

**Kapsam:** NFR güvenlik gereksinimleri — yoğun istekleri sınırlama, oturum zaman aşımı ve süresi dolmuş yoklama kodlarının reddedilmesi.

#### 18.1. Rate Limiting

**Dosyalar:**
- `utils/rate_limit.py` — Flask-Limiter instance'ı eklendi.
- `app.py` — Limiter uygulamaya bağlandı, 429 hata sayfası tanımlandı.
- `views/auth.py` — Login ve kayıt route'larına rate limit eklendi.
- `views/student.py` — Yoklama verme route'una rate limit eklendi.
- `templates/errors/429.html` — Çok fazla istek hata sayfası eklendi.

Config değerleri:
- `RATE_LIMIT_DEFAULT = '30/minute'`
- `RATE_LIMIT_LOGIN = '5/minute'`
- `RATE_LIMIT_REGISTER = '5/minute'`
- `RATE_LIMIT_ATTEND = '10/minute'`

#### 18.2. Session Timeout

**Dosyalar:**
- `config.py` — `SESSION_TIMEOUT_MINUTES`, `PERMANENT_SESSION_LIFETIME`, `SESSION_REFRESH_EACH_REQUEST` eklendi.
- `app.py` — `before_request` ile son aktivite zamanı kontrol edildi.
- `views/auth.py` — Girişte session permanent yapıldı ve `last_activity_at` set edildi.

Davranış:
- Kullanıcı 30 dakika pasif kalırsa session temizlenir.
- Kullanıcı login sayfasına yönlendirilir.
- Her geçerli request son aktivite zamanını günceller.

#### 18.3. Expired Code + QR Süre Sınırı

Mevcut `attendance_service.check_in()` içindeki süresi dolmuş kod reddi korundu ve test edildi.

**Dosya:** `views/teacher.py`
- Öğretmenin girdiği QR yenileme süresi config min/max aralığına çekildi.
- `QR_REFRESH_MIN = 5`, `QR_REFRESH_MAX = 30` sınırları uygulanır.

#### 18.4. Testler

**Geçen testler:**
- `py_compile` başarılı.
- Uygulama `create_app('testing')` ile açıldı.
- Login rate limit: aynı IP'den limit aşılınca 429 döndü.
- Session timeout: eski `last_activity_at` ile korumalı sayfa login'e yönlendirdi.
- Expired code rejection: süresi dolmuş kodla yoklama reddedildi.
- QR refresh clamp: 999 saniye isteyen oturum 30 saniyeye sınırlandı.

---

*Sonraki adımlar bu dosyaya eklenecektir.*
