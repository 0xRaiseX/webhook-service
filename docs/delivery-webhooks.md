# Delivery, Outbox, Retries (MVP)

Цель: гарантировать at-least-once доставку, предсказуемые ретраи, подпись как у Stripe, и возможность re-delivery.

## Outbox и транзакционность

- CanonicalEventStore запись события и создание задач доставки в Outbox должны быть атомарными (в одной транзакции) для всех подходящих подписок.
- Outbox запись:
  - `delivery_id` (uuid)
  - `event_id`
  - `subscription_id`
  - `endpoint_id`
  - `project_id`
  - `next_attempt_at`
  - `attempt` (int)
  - `status` (pending/sent/failed/dead)
  - `payload_hash` (для дедупа)

## Политика ретраев (MVP)

- Экспоненциальная задержка: 1m, 5m, 15m, 1h, 6h (пример).
- Максимум попыток: 5; дальше — DLQ (`status=dead`), доступно в `GET /v1/deliveries`.
- RPS per endpoint: rate-limit и джиттер, чтобы избегать штормов.
- 2xx считается успехом. 410/404/401 трактовать как ошибка клиента — можно ускоренно помещать в DLQ.

## Подпись webhook (Stripe-like)

- Хедер: `Webhook-Signature: t=TIMESTAMP,v1=HMAC_SHA256(secret, "t.payload")`.
- Проверка: окно 5 минут; опционально `nonce` в payload для защиты от replay.
- Payload: полный canonical event JSON.
- Секрет хранить зашифрованным; возможность rotate (два секрета активны).

## Идемпотентность для получателя

- Клиент должен использовать `event.id` как идемпотентный ключ. Для повторных доставок тело идентично.
- `delivery_id` уникален на попытку доставки; логирование по нему.

## Replay / redelivery

- `POST /v1/events/{id}/replay` с опциональными `endpoint_id` или `subscription_id`. Добавляет задачу в Outbox c `attempt=0`.
- Проверка владения `project_id`.

## Наблюдаемость

- Метрики: success rate, retry rate, P95 latency, DLQ size, endpoint error rate.
- Логи попыток: `status_code`, `duration_ms`, `error_snippet`.

## Клиентские лучшие практики

- Сохранять/обрабатывать события идемпотентно по `event.id`.
- Отвечать 2xx только после успешной обработки.
- Подтверждать секреты при создании endpoint (опциональный `challenge`).
