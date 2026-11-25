# Yapay Zekâ Destekli Etkinlik Keşif ve Öneri Platformu (Ankara)

## Amaç ve Kapsam

Bu proje, Ankara'da düzenlenen etkinlikleri (konser, tiyatro, sergi, festival vb.) farklı
kaynaklardan (Biletix, Passo, belediye siteleri vb.) toplayan, bunları yapay zekâ ile
kategorize eden ve kullanıcıya kişiselleştirilmiş öneriler sunan bir web platformudur.

Kullanıcılar:
- Ankara'daki etkinlikleri arayabilir, filtreleyebilir ve harita/takvim üzerinde görebilir,
- Doğal dil ile arama yapabilir (örn. "bu hafta sonu ucuz bir konser"),
- İlgi alanlarına göre kişiselleştirilmiş etkinlik önerileri alabilir,
- Favori etkinliklerini kaydedebilir ve puanlayabilir.

## Takım ve Görev Dağılımı

| Kişi | Alan | Sorumluluklar |
|------|------|----------------|
| Elifnaz | Etkinlik Verisi ve Keşif | Scraper, etkinlik/mekân verisi, listeleme & filtreleme API'leri, otomatik kategorizasyon, ana sayfa/liste/detay sayfaları |
| Seray | Kullanıcı ve Kişiselleştirme | Auth, profil, favoriler, öneri motoru (içerik tabanlı + iş birlikçi filtreleme), cold start, "Senin için önerilenler" |
| İrem | Akıllı Arama ve Etkileşim | Doğal dille arama, benzer etkinlik önerisi, arama/bildirim servisleri, harita & takvim görünümü, responsive tasarım, CI/deploy |

Ortak işler: API sözleşmesi & DB şeması (1. hafta, üçü birlikte), UI tasarım sistemi (Elifnaz),
test yazımı (herkes kendi özelliği için), rapor/README (herkes kendi bölümü, Seray birleştirir),
sunum ve demo (İrem hazırlar).

## Proje Yapısı

```
.
├── backend/   # API, veritabanı, servisler
├── frontend/  # Web arayüzü
├── ai/        # Kategorizasyon, öneri motoru, doğal dil arama modelleri
├── data/      # Scraper'lar ve veri temizleme script'leri
└── docs/      # API sözleşmesi, DB şeması ve diğer teknik dökümanlar
```

Her klasörün kendi README'si, o alandaki kurulum ve kullanım bilgilerini içerir.

## Kurulum ve Kullanım

> Teknoloji seçimleri ve kurulum adımları ilerleyen haftalarda bu bölüme eklenecektir.

## Geliştirme Süreci

Geliştirme süreci GitHub Issues ve commit geçmişi üzerinden takip edilir. Her haftalık görev
bir Issue olarak açılır ve ilgili commit'ler açıklayıcı mesajlarla bu Issue'lara referans verir.

## Takım Üyeleri

- Elifnaz: Etkinlik Verisi ve Keşif
- Seray: Kullanıcı ve Kişiselleştirme
- İrem: Akıllı Arama ve Etkileşim
