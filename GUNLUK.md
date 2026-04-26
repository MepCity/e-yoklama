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

**Sonraki hedef:** Faz 1 — Yoklama oturum yaşam döngüsü (start/end), attendance_service.py

---

*Sonraki adımlar bu dosyaya eklenecektir.*
