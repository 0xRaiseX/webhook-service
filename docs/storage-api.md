# Storage, Schema, HTTP API (MVP)

Цель: хранить 90 дней событий и доставок, поддерживать быстрый поиск/фильтрацию и управление сущностями.

## Хранилище

- **CanonicalEventStore** (реляционное, партиционирование по дню/неделе).
  - Колонки: `id`, `type`, `created`, `project_id`, `api_version`, `source (jsonb)`, `data (jsonb)`, `links (jsonb)`.
  - Индексы:
    - `(project_id, created desc)`
    - `(type, project_id, created desc)`
    - `(source->>'chain_id', source->>'contract_address')`
    - `(source->>'tx_hash')`
  - TTL/retention: 90 дней, затем архив/удаление.
- **RawEventStore**: компактные logs/tx refs; партиционирование как у CanonicalEventStore.
- **DeliveryAttemptStore / Outbox**:
  - Outbox (pending tasks) с индексом `next_attempt_at`.
  - Attempts history: `(event_id, endpoint_id, status, created_at)`, хранение 90 дней.

## Курсоры и пагинация

- `GET /events` — cursor pagination по `created` + `id` (stable, deterministic).
- Лимит page: 100–500.

## HTTP API (детализация MVP)

### Управление
- `POST /v1/endpoints` — создать endpoint (URL, secret, rate_limits?).
- `PATCH /v1/endpoints/{id}` — rotate secret, pause/resume.
- `POST /v1/subscriptions` — задать `event_types`, `filters`, `confirmations`, `endpoint_id`.
- `PATCH /v1/subscriptions/{id}` — обновить фильтры/статус.

### События
- `GET /v1/events?type=&from=&to=&chain_id=&contract_address=&cursor=` — фильтры на нормализованные поля, курсор.
- `GET /v1/events/{id}` — по детерминированному `id`.
- `POST /v1/events/{id}/replay` — добавить задачу доставки.

### Доставки
- `GET /v1/deliveries?event_id=&endpoint_id=&status=&cursor=` — история попыток и DLQ.

### Аутентификация
- API Key в заголовке (`Authorization: Bearer <key>`).
- Ключ привязан к `project_id`, имеет scope (admin/read).

## Схемы таблиц (эскиз)

`events`:
- `id` pk (text)
- `type` text
- `created` timestamptz
- `project_id` text
- `api_version` text
- `source` jsonb
- `data` jsonb
- `links` jsonb
- `chain_id` generated (source->>'chain_id')
- `contract_address` generated (source->>'contract_address')
- `tx_hash` generated (source->>'tx_hash')

`outbox`:
- `delivery_id` uuid pk
- `event_id` text
- `subscription_id` text
- `endpoint_id` text
- `project_id` text
- `attempt` int
- `next_attempt_at` timestamptz
- `status` text
- `payload_hash` text

`delivery_attempts`:
- `id` uuid pk
- `delivery_id` uuid
- `event_id` text
- `endpoint_id` text
- `status_code` int
- `status` text
- `duration_ms` int
- `error` text
- `created_at` timestamptz

## Retention и стоимость

- 90-дневный TTL через партиции; возможность дешевого архива для аналитики.
- Логи доставки можно аггрегировать после 90 дней в метрики.

## Наблюдаемость

- Метрики: ingestion lag, normalize error rate, delivery success/retry/DLQ, query latency.
- Трассировка: span от ingestion до доставки (trace `event.id`).
