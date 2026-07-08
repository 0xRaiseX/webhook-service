# Subscriptions и фильтры (MVP)

Цель: описать как клиент подписывается на нормализованные события и как мы матчим их быстро и предсказуемо.

## Модель

- `Subscription`: принадлежит `project_id`.
- Поля:
  - `id`
  - `project_id`
  - `event_types`: список (`token.transfer`, `nft.transfer`, `contract.event`).
  - `filters`: см. ниже.
  - `endpoint_id`: куда доставлять.
  - `confirmations`: int, дефолт 12 (override финальности на подписку).
  - `status`: active/paused.
  - `created_at`, `updated_at`, `version`.

## Фильтры (комбинируются по AND, значения в списках — OR)

- `chain_id` (список).
- `contract_address` (список).
- `topic0` (список; для generic logs/contract.event).
- `from` / `to` адреса (списки).
- `token_address` (список).
- `token_id` (список или диапазоны для 1155/721).
- `tx_hash` (список) — для целевых транзакций / replays.
- `abi_event` (строка) — для `contract.event`.
- Для decoded полей — ограничимся ключевыми: `args.<name>` exact match (MVP).

## Matching и индексация

- Основные индексные ключи CanonicalEventStore для матчера:
  - `(chain_id, contract_address, topic0, log_index, tx_hash)`
  - `(type, project_id, created)`
- Матчер:
  1. Предфильтр по `event.type`.
  2. По цепи/контракту/топику — с использованием композитных индексов.
  3. Для адресов `from/to` и `token_address` — вторичные индексы.
  4. Для `args.<name>` в MVP: ограничить до заранее объявленных полей/ключей; хранить key-value таблицу для decoded args и индекс по `(arg_name, arg_value_hash)`.

## Финальность на подписку

- Подписка может указать `confirmations`. Scanner/Normalizer должны проверять min(`subscription.confirmations`, глобальный max).
- События не маршрутизируются в outbox до достижения финальности для каждой подписки, иначе появляется риск разных финальностей. Упростить: глобальный минимум из всех активных подписок по chain_id; подписки с большим числом подтверждений ждут дольше (через отдельную очередь задержки).

## API (MVP)

- `POST /v1/subscriptions`
  - `event_types`, `filters`, `endpoint_id`, `confirmations?`, `status?`.
- `GET /v1/subscriptions`
- `PATCH /v1/subscriptions/{id}` (pause/resume, update filters, confirmations).

## Валидация

- Ограничить число фильтров/списков per subscription (например, до 50 значений в одном списке).
- Ограничить число подписок per project (квоты).
- Проверять, что `endpoint_id` принадлежит `project_id`.

## Наблюдаемость

- Метрика: hit-rate матчера, latency матчинга.
- Кардинальность фильтров — мониторить для оптимизации индексов.
