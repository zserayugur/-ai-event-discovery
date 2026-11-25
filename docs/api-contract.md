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

## Elifnaz — Etkinlik Verisi ve Keşif

| Method | Endpoint | Açıklama |
|--------|----------|----------|
| GET | `/events` | Etkinlikleri listeler. Query: `category`, `city`, `date_from`, `date_to`, `price_min`, `price_max`, `venue_id`, `page`, `limit` |
| GET | `/events/:id` | Etkinlik detayı |
| GET | `/categories` | Kategori listesi |
| GET | `/venues` | Mekân listesi |
| GET | `/venues/:id` | Mekân detayı |

## Seray — Kullanıcı ve Kişiselleştirme

Kimlik doğrulama JWT ile yapılır: `access_token` (30 dk) ve `refresh_token` (7 gün).
Şifreler bcrypt ile hash'lenir, en az 8 karakter olmalıdır.

| Method | Endpoint | Açıklama |
|--------|----------|----------|
| POST | `/auth/register` | Kayıt. Body: `email`, `password`, `name` → `201`, `{ user, access_token, refresh_token }`. Hata: `409 EMAIL_TAKEN` |
| POST | `/auth/login` | Giriş. Body: `email`, `password` → `{ user, access_token, refresh_token }`. Hata: `401 INVALID_CREDENTIALS` |
| POST | `/auth/refresh` | Body: `refresh_token` → yeni `access_token`. Hata: `401 INVALID_TOKEN` |
| POST | `/auth/logout` | Çıkış → `204` |
| GET | `/users/me` | Profil bilgisi (`onboarding_done` dahil) |
| PUT | `/users/me` | Profil güncelleme. Body: `name`, `district` |
| GET | `/users/me/interests` | İlgi alanlarını getirir: `{ categories: [{ id, name, weight }] }` |
| PUT | `/users/me/interests` | İlgi alanlarını günceller (cold start ekranı). Body: `category_ids: []` → `onboarding_done = true` olur |
| GET | `/users/me/favorites` | Favori etkinlikler (Elifnaz'ın event özet formatıyla, sayfalı) |
| POST | `/users/me/favorites/:eventId` | Favoriye ekle → `201` |
| DELETE | `/users/me/favorites/:eventId` | Favoriden çıkar → `204` |
| POST | `/events/:id/rating` | Etkinliği puanla. Body: `rating: 1-5` |
| POST | `/interactions` | Örtük geri bildirim. Body: `event_id`, `type` (`view`, `click`, `dismiss`, `ticket_click`) → `202` |
| GET | `/recommendations` | "Senin için önerilenler". Query: `limit`. Her öğe: `{ event, score, reason }`. Giriş yapılmamışsa veya ilgi alanı seçilmemişse popüler ve yakın tarihli etkinlikler döner (cold start) |

## İrem — Akıllı Arama ve Etkileşim

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
- ~~Token tipi: JWT mi, session mı?~~ → JWT (access + refresh token), bkz. Seray bölümü.
