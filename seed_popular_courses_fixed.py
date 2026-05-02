from app import create_app
from database import db
from models.popular_course import PopularCourse


def seed_popular_courses():
    """Popüler dersleri database'e ekle"""
    
    app = create_app('development')
    with app.app_context():
        
        popular_courses_data = [
            # Bilgisayar Mühendisliği
            ("Bilgisayar Mühendisliği", "Algoritma ve Programlama", "BMP101", "Programlama temelleri ve algoritma tasarımı"),
            ("Bilgisayar Mühendisliği", "Veri Yapıları", "BMP201", "Temel veri yapıları ve algoritmalar"),
            ("Bilgisayar Mühendisliği", "Veritabanı Sistemleri", "BMP301", "Veritabanı tasarımı ve SQL"),
            ("Bilgisayar Mühendisliği", "İşletim Sistemleri", "BMP302", "Modern işletim sistemleri"),
            ("Bilgisayar Mühendisliği", "Bilgisayar Ağları", "BMP303", "Ağ protokolleri ve iletişim"),
            ("Bilgisayar Mühendisliği", "Yapay Zeka", "BMP401", "Makine öğrenmesi ve derin öğrenme"),
            ("Bilgisayar Mühendisliği", "Yazılım Mühendisliği", "BMP402", "Yazılım geliştirme metodolojileri"),
            ("Bilgisayar Mühendisliği", "Bilgisayar Mimarisi", "BMP203", "Donanım ve mimari konseptler"),
            
            # Yazılım Mühendisliği
            ("Yazılım Mühendisliği", "Yazılım Tasarımı ve Analizi", "YZM101", "Yazılım analiz ve tasarım prensipleri"),
            ("Yazılım Mühendisliği", "Girişimcilik", "YZM201", "Teknoloji girişimciliği"),
            ("Yazılım Mühendisliği", "Mobil Uygulama Geliştirme", "YZM301", "iOS ve Android uygulama geliştirme"),
            ("Yazılım Mühendisliği", "Web Programlama", "YZM202", "Modern web teknolojileri"),
            ("Yazılım Mühendisliği", "Bulut Bilişim", "YZM302", "Bulut servisleri ve mimariler"),
            ("Yazılım Mühendisliği", "DevOps", "YZM401", "Sürekli entegrasyon ve dağıtım"),
            ("Yazılım Mühendisliği", "Proje Yönetimi", "YZM303", "Yazılım proje yönetimi"),
            
            # Elektrik-Elektronik Mühendisliği
            ("Elektrik-Elektronik Mühendisliği", "Devre Analizi", "ELM101", "Temel elektrik devreleri"),
            ("Elektrik-Elektronik Mühendisliği", "Elektronik", "ELM201", "Elektronik devreler ve bileşenler"),
            ("Elektrik-Elektronik Mühendisliği", "Sinyal İşleme", "ELM301", "Dijital sinyal işleme"),
            ("Elektrik-Elektronik Mühendisliği", "Kontrol Sistemleri", "ELM302", "Otomatik kontrol teorisi"),
            ("Elektrik-Elektronik Mühendisliği", "Güç Sistemleri", "ELM303", "Elektrik enerji sistemleri"),
            ("Elektrik-Elektronik Mühendisliği", "Mikroişlemciler", "ELM202", "Mikroişlemci mimarisi"),
            ("Elektrik-Elektronik Mühendisliği", "Telekomünikasyon", "ELM401", "İletişim sistemleri"),
            
            # Makine Mühendisliği
            ("Makine Mühendisliği", "Mühendislik Çizimi", "MAK101", "Teknik resim ve CAD"),
            ("Makine Mühendisliği", "Termodinamik", "MAK201", "Termodinamik prensipleri"),
            ("Makine Mühendisliği", "Akışkanlar Mekaniği", "MAK202", "Akışkan dinamiği"),
            ("Makine Mühendisliği", "Malzeme Bilimi", "MAK203", "Mühendislik malzemeleri"),
            ("Makine Mühendisliği", "Makine Elemanları", "MAK301", "Mekanik tasarım"),
            ("Makine Mühendisliği", "Isı Transferi", "MAK302", "Isı iletimi ve konveksiyon"),
            ("Makine Mühendisliği", "Üretim Mühendisliği", "MAK303", "Modern üretim teknikleri"),
            ("Makine Mühendisliği", "Robotik", "MAK401", "Endüstriyel robotik ve otomasyon"),
            
            # İnşaat Mühendisliği
            ("İnşaat Mühendisliği", "Statik", "INS101", "Yapı statiği"),
            ("İnşaat Mühendisliği", "Mukavemet", "INS201", "Malzeme mukavemeti"),
            ("İnşaat Mühendisliği", "Geoteknik", "INS202", "Zemin mekaniği"),
            ("İnşaat Mühendisliği", "Ulaştırma", "INS203", "Ulaşım sistemleri"),
            ("İnşaat Mühendisliği", "Hidrolik", "INS301", "Hidrolik prensipler"),
            ("İnşaat Mühendisliği", "Yapı Mühendisliği", "INS302", "Yapı tasarımı"),
            ("İnşaat Mühendisliği", "Çevre Mühendisliği", "INS303", "Çevre sistemleri"),
            ("İnşaat Mühendisliği", "Deprem Mühendisliği", "INS401", "Depreme dayanıklı tasarım"),
            
            # Tıp
            ("Tıp", "Anatomi", "TIP101", "İnsan anatomisi"),
            ("Tıp", "Fizyoloji", "TIP102", "İnsan fizyolojisi"),
            ("Tıp", "Biyokimya", "TIP103", "Tıbbi biyokimya"),
            ("Tıp", "Patoloji", "TIP201", "Hastalık patolojisi"),
            ("Tıp", "İç Hastalıkları", "TIP301", "Dahiliye"),
            ("Tıp", "Cerrahi", "TIP302", "Genel cerrahi"),
            ("Tıp", "Pediatri", "TIP303", "Çocuk sağlığı"),
            ("Tıp", "Kardiyoloji", "TIP401", "Kalp ve damar hastalıkları"),
            
            # Diş Hekimliği
            ("Diş Hekimliği", "Ağız ve Diş Anatomisi", "DIS101", "Diş anatomisi"),
            ("Diş Hekimliği", "Restoratif Diş Tedavisi", "DIS201", "Dolgu ve restorasyon"),
            ("Diş Hekimliği", "Endodonti", "DIS202", "Kanal tedavisi"),
            ("Diş Hekimliği", "Periodontoloji", "DIS203", "Diş eti hastalıkları"),
            ("Diş Hekimliği", "Protetik Diş Tedavisi", "DIS301", "Protez uygulamaları"),
            ("Diş Hekimliği", "Ortodonti", "DIS302", "Diş düzeltme"),
            
            # Eczacılık
            ("Eczacılık", "Farmakoloji", "ECZ101", "İlaç etkileşimleri"),
            ("Eczacılık", "Farmasötik Kimya", "ECZ201", "İlaç kimyası"),
            ("Eczacılık", "Farmakognozi", "ECZ202", "Bitkisel ilaçlar"),
            ("Eczacılık", "Farmasötik Teknoloji", "ECZ301", "İlaç üretimi"),
            ("Eczacılık", "Klinik Eczacılık", "ECZ302", "Hastane eczacılığı"),
            ("Eczacılık", "Toksikoloji", "ECZ303", "Zehir bilimi"),
            
            # Hemşirelik
            ("Hemşirelik", "Temel Hemşirelik İlkeleri", "HEM101", "Hemşirelik temelleri"),
            ("Hemşirelik", "İç Hastalıkları Hemşireliği", "HEM201", "Dahiliye hemşireliği"),
            ("Hemşirelik", "Cerrahi Hemşirelik", "HEM202", "Cerrahi hemşireliği"),
            ("Hemşirelik", "Çocuk Sağlığı Hemşireliği", "HEM203", "Pediatri hemşireliği"),
            ("Hemşirelik", "Kadın Sağlığı Hemşireliği", "HEM204", "Jinekoloji hemşireliği"),
            ("Hemşirelik", "Psikiyatri Hemşireliği", "HEM205", "Ruh sağlığı hemşireliği"),
            ("Hemşirelik", "Yoğun Bakım Hemşireliği", "HEM301", "Reanimasyon hemşireliği"),
            
            # Psikoloji
            ("Psikoloji", "Genel Psikoloji", "PSI101", "Psikolojiye giriş"),
            ("Psikoloji", "Gelişim Psikolojisi", "PSI201", "İnsan gelişimi"),
            ("Psikoloji", "Sosyal Psikoloji", "PSI202", "Sosyal davranış"),
            ("Psikoloji", "Klinik Psikoloji", "PSI301", "Psikopatoloji"),
            ("Psikoloji", "Nöropsikoloji", "PSI302", "Beyin ve davranış"),
            ("Psikoloji", "Endüstriyel Psikoloji", "PSI303", "İş psikolojisi"),
            
            # Hukuk
            ("Hukuk", "Anayasa Hukuku", "HUK101", "Anayasa ve temel haklar"),
            ("Hukuk", "Medeni Hukuk", "HUK201", "Kişiler hukuku"),
            ("Hukuk", "Borçlar Hukuku", "HUK202", "Sözleşmeler ve borçlar"),
            ("Hukuk", "Ceza Hukuku", "HUK203", "Suç ve ceza"),
            ("Hukuk", "Ticaret Hukuku", "HUK301", "Ticari işlemler"),
            ("Hukuk", "İdare Hukuku", "HUK302", "İdari işlemler"),
            
            # İşletme
            ("İşletme", "İşletme Yöneticiliği", "ISL101", "Yönetim prensipleri"),
            ("İşletme", "Muhasebe", "ISL201", "Finansal muhasebe"),
            ("İşletme", "Finansal Yönetim", "ISL202", "Kurumsal finans"),
            ("İşletme", "Pazarlama", "ISL203", "Pazarlama stratejileri"),
            ("İşletme", "İnsan Kaynakları", "ISL301", "İK yönetimi"),
            ("İşletme", "Stratejik Yönetim", "ISL302", "Strateji geliştirme"),
            ("İşletme", "Uluslararası İşletme", "ISL303", "Küresel işletmeler"),
            
            # İktisat
            ("İktisat", "Mikroekonomi", "IKT101", "Mikroekonomik teori"),
            ("İktisat", "Makroekonomi", "IKT102", "Makroekonomik analiz"),
            ("İktisat", "Ekonomi Politikası", "IKT201", "Ekonomik politikalar"),
            ("İktisat", "Uluslararası Ekonomi", "IKT202", "Uluslararası ticaret"),
            ("İktisat", "Para ve Bankacılık", "IKT203", "Finans sistemleri"),
            ("İktisat", "Ekonomik Gelişme", "IKT301", "Kalkınma ekonomisi"),
        ]
        
        # Mevcut kayıtları temizle
        db.query(PopularCourse).delete()
        
        # Yeni kayıtları ekle
        for department, course_name, course_code, description in popular_courses_data:
            course = PopularCourse(
                department=department,
                course_name=course_name,
                course_code=course_code,
                description=description
            )
            db.add(course)
        
        db.commit()
        print(f"{len(popular_courses_data)} popüler ders başarıyla eklendi.")


if __name__ == "__main__":
    seed_popular_courses()
