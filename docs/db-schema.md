# Veritabanı Şeması (Taslak)

> Bu doküman 1. hafta ortak görevi kapsamında hazırlanan bir **taslaktır**. Ekip
> toplantısında gözden geçirilip onaylandıktan sonra nihai hale gelecektir.

## Tablolar

### `users` (Kişi 2)
| Alan | Tip | Açıklama |
|------|-----|----------|
| id | UUID / INT PK | |
| email | string, unique | |
| password_hash | string | |
| name | string | |
| created_at | datetime | |

### `interests` (Kişi 2)
Kullanıcının ilgi alanı seçtiği kategoriler.
| Alan | Tip | Açıklama |
|------|-----|----------|
| user_id | FK → users.id | |
| category_id | FK → categories.id | |

### `categories` (Kişi 1)
| Alan | Tip | Açıklama |
|------|-----|----------|
| id | INT PK | |
| name | string | konser, tiyatro, sergi, festival, spor, atölye vb. |

### `tags` (Kişi 1 — AI tarafından üretilir)
| Alan | Tip | Açıklama |
|------|-----|----------|
| id | INT PK | |
| name | string | açıklamadan çıkarılan etiketler |

### `event_tags`
| Alan | Tip | Açıklama |
|------|-----|----------|
| event_id | FK → events.id | |
| tag_id | FK → tags.id | |

### `venues` (Kişi 1)
| Alan | Tip | Açıklama |
|------|-----|----------|
| id | INT PK | |
| name | string | |
| address | string | |
| city | string | varsayılan: Ankara |
| lat | float | harita görünümü için (Kişi 3) |
| lng | float | harita görünümü için (Kişi 3) |

### `events` (Kişi 1)
| Alan | Tip | Açıklama |
|------|-----|----------|
| id | UUID / INT PK | |
| title | string | |
| description | text | |
| category_id | FK → categories.id | |
| venue_id | FK → venues.id | |
| start_date | datetime | |
| end_date | datetime, nullable | |
| price | decimal, nullable | null = ücretsiz |
| source | string | biletix, passo, belediye vb. |
| source_url | string | |
| image_url | string, nullable | |
| created_at | datetime | |
| updated_at | datetime | |

### `favorites` (Kişi 2)
| Alan | Tip | Açıklama |
|------|-----|----------|
| user_id | FK → users.id | |
| event_id | FK → events.id | |
| created_at | datetime | |

### `ratings` (Kişi 2)
| Alan | Tip | Açıklama |
|------|-----|----------|
| user_id | FK → users.id | |
| event_id | FK → events.id | |
| rating | int (1-5) | |
| created_at | datetime | |

### `notifications` (Kişi 3)
| Alan | Tip | Açıklama |
|------|-----|----------|
| id | UUID / INT PK | |
| user_id | FK → users.id | |
| event_id | FK → events.id, nullable | |
| type | string | reminder, new_event, price_drop vb. |
| message | string | |
| sent_at | datetime, nullable | |
| read_at | datetime, nullable | |

## İlişkiler (özet)

- `events` → `venues` (N:1), `events` → `categories` (N:1)
- `events` ↔ `tags` (N:N, `event_tags` üzerinden)
- `users` ↔ `events` → `favorites`, `ratings` (N:N)
- `users` ↔ `categories` → `interests` (N:N, cold start için kullanılır)
- `users` → `notifications` (1:N)

## Açık Sorular

- Etkinlik fiyatları tek para birimi (TRY) mi olacak?
- Scraper kaynaklarında aynı etkinlik tekrar geldiğinde (dedup) hangi alan benzersiz kabul edilecek? (öneri: `source` + `source_url`)
