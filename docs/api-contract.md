# API Sözleşmesi (Taslak)

> Bu doküman 1. hafta ortak görevi kapsamında hazırlanan bir **taslaktır**. Ekip
> toplantısında gözden geçirilip onaylandıktan sonra nihai hale gelecektir. İlgili
> veri modelleri için bkz. [db-schema.md](./db-schema.md).

## Genel Kurallar

- Base URL: `/api`
- Kimlik doğrulama gereken endpoint'ler `Authorization: Bearer <token>` header'ı bekler.
- Başarılı yanıt formatı: `{ "data": ..., "meta": { ... } }`
- Hata formatı: `{ "error": { "code": "...", "message": "..." } }`
- Liste endpoint'leri sayfalama kullanır: `?page=1&limit=20`, yanıtta `meta.total`, `meta.page`, `meta.limit` döner.

## Kişi 1 — Etkinlik Verisi ve Keşif

| Method | Endpoint | Açıklama |
|--------|----------|----------|
| GET | `/events` | Etkinlikleri listeler. Query: `category`, `city`, `date_from`, `date_to`, `price_min`, `price_max`, `venue_id`, `page`, `limit` |
| GET | `/events/:id` | Etkinlik detayı |
| GET | `/categories` | Kategori listesi |
| GET | `/venues` | Mekân listesi |
| GET | `/venues/:id` | Mekân detayı |

## Kişi 2 — Kullanıcı ve Kişiselleştirme

| Method | Endpoint | Açıklama |
|--------|----------|----------|
| POST | `/auth/register` | Kayıt. Body: `email`, `password`, `name` |
| POST | `/auth/login` | Giriş. Body: `email`, `password` → `token` döner |
| POST | `/auth/logout` | Çıkış |
| GET | `/users/me` | Profil bilgisi |
| PUT | `/users/me` | Profil güncelleme |
| GET | `/users/me/interests` | İlgi alanlarını getirir |
| PUT | `/users/me/interests` | İlgi alanlarını günceller. Body: `category_ids: []` |
| GET | `/users/me/favorites` | Favori etkinlikler |
| POST | `/users/me/favorites/:eventId` | Favoriye ekle |
| DELETE | `/users/me/favorites/:eventId` | Favoriden çıkar |
| POST | `/events/:id/rating` | Etkinliği puanla. Body: `rating: 1-5` |
| GET | `/recommendations` | "Senin için önerilenler" listesi |

## Kişi 3 — Akıllı Arama ve Etkileşim

| Method | Endpoint | Açıklama |
|--------|----------|----------|
| GET | `/search` | Doğal dil arama. Query: `q` (örn. "bu hafta sonu ucuz bir konser") → sonuçta filtrelenmiş `events` listesi + `meta.parsed_filters` (yorumlanan filtreler, şeffaflık için) |
| GET | `/events/:id/similar` | Benzer etkinlikler ("bunu sevenler şunu da sevdi") |
| GET | `/notifications` | Kullanıcının bildirimleri |
| POST | `/notifications/subscribe` | Belirli bir etkinlik/kategori için hatırlatma talebi. Body: `event_id` veya `category_id`, `remind_before` |
| PUT | `/notifications/:id/read` | Bildirimi okundu işaretle |

## Açık Sorular

- `search` endpoint'i `events` listelemesiyle aynı response şemasını mı kullanacak, yoksa ek alanlar (`relevance_score` vb.) içerecek mi?
- Harita görünümü için `/events` yanıtında `venue.lat`/`venue.lng` her zaman dolu gelecek mi, yoksa ayrı bir `/events/map` endpoint'i mi gerekir?
- Token tipi: JWT mi, session mı? (Kişi 2 ile netleştirilecek)
