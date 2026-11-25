# Seray (Kullanıcı ve Kişiselleştirme) – 1. Hafta Özeti

## Yapılanlar

**API sözleşmesi (`api-contract.md`, Seray bölümü)**
- Token tipi JWT olarak netleştirildi: `access_token` (30 dk) + `refresh_token` (7 gün), bcrypt ile şifre hash'leme.
- `/auth/refresh` endpoint'i eklendi; register/login yanıtları ve hata kodları (`EMAIL_TAKEN`, `INVALID_CREDENTIALS`, `INVALID_TOKEN`) tanımlandı.
- `/users/me/interests` cold start ekranı için netleştirildi: ilgi alanı seçilince `onboarding_done = true`.
- Öneri motoruna veri sağlamak için `POST /interactions` (view, click, dismiss, ticket_click) eklendi.
- `/recommendations` yanıt formatı `{ event, score, reason }` olarak belirlendi; cold start davranışı (popüler + yakın tarihli etkinlikler) yazıldı.

**DB şeması (`db-schema.md`)**
- `users` tablosuna `district`, `onboarding_done`, `updated_at` eklendi.
- `interests` tablosuna `weight` alanı eklendi (etkileşimlerle güncellenecek).
- Yeni tablolar: `interactions` (örtük geri bildirim) ve opsiyonel `recommendations_cache`.

## Elifnaz ve İrem'den beklenenler
- **Elifnaz:** `events` id tipi (UUID mi INT mi) ve favori/öneri listelerinde kullanılacak event özet formatı.
- **İrem:** Bildirim ve arama endpoint'lerinde aynı JWT doğrulamasının kullanılması.

## 2. Hafta Planı
- Ekip toplantısında sözleşmeyi ve şemayı onaylamak
- Backend'de `users` modeli, kayıt ve giriş endpoint'lerinin ilk hali
