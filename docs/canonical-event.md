# Canonical Web3 Event Envelope (MVP)

Цель: стабильный, версионируемый контракт события (аналог Stripe event), единый для всех источников. Доставка — at-least-once, идемпотентность через детерминированный `id`.

## Envelope

- `id`: детерминированный, глобально уникальный (`sha256(chain_id|tx_hash|log_index|api_version)` для логов).
- `type`: строка-тип, семантически стабильный, версионируемый (`token.transfer`, `nft.transfer`, `contract.event`).
- `created`: unix timestamp (секунды).
- `project_id`: владелец подписки.
- `api_version`: версия нормализации/схемы.
- `source`: web3-метаданные — `chain_id`, `network`, `block_number`, `block_hash`, `tx_hash`, `tx_index`, `log_index`, `contract_address`.
- `data`: нормализованный payload + `raw` fallback.
- `links` (optional): ссылки на эксплорер/provider.

## Правила финальности и идемпотентности

- Минимум `N` подтверждений (по умолчанию 12) до публикации в CanonicalEventStore и доставки.
- При reorg внутри окна: перескан блока, перегенерация `id`; наружу не выходит до финальности.
- Идемпотентность для клиента: `event.id`; для попыток доставки — `delivery.id`.

## Семейства типов (MVP)

- `token.transfer` — ERC20 Transfer.
- `nft.transfer` — ERC721/1155 Transfer/TransferSingle/TransferBatch.
- `contract.event` — generic ABI-decoded event (клиент дал ABI или популярный известный ABI).

## JSON Schema (MVP, draft)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Web3CanonicalEvent",
  "type": "object",
  "required": ["id", "type", "created", "project_id", "api_version", "source", "data"],
  "properties": {
    "id": { "type": "string", "minLength": 16 },
    "type": { "type": "string" },
    "created": { "type": "integer" },
    "project_id": { "type": "string" },
    "api_version": { "type": "string" },
    "source": {
      "type": "object",
      "required": ["chain_id", "block_number", "block_hash", "tx_hash", "tx_index", "log_index", "contract_address"],
      "properties": {
        "chain_id": { "type": "string" },
        "network": { "type": "string" },
        "block_number": { "type": "integer" },
        "block_hash": { "type": "string" },
        "tx_hash": { "type": "string" },
        "tx_index": { "type": "integer" },
        "log_index": { "type": "integer" },
        "contract_address": { "type": "string" }
      }
    },
    "data": {
      "type": "object",
      "required": ["normalized"],
      "properties": {
        "normalized": { "type": "object" },
        "raw": { "type": "object" }
      }
    },
    "links": {
      "type": "object",
      "properties": {
        "explorer_tx": { "type": "string" },
        "explorer_block": { "type": "string" }
      }
    }
  }
}
```

## Нормализованные payloads (MVP)

`token.transfer`:
- `from`, `to` (string, address)
- `amount` (string, decimal string)
- `token_address`, `token_decimals`, `token_symbol`

`nft.transfer`:
- `from`, `to`
- `token_id` (string)
- `token_address`, `token_standard` (erc721|erc1155)
- `amount` (для 1155)

`contract.event`:
- `abi_event`: имя события
- `args`: decoded key-value map
- `topic0`: hex

## Пример события (сокращенный)

```json
{
  "id": "evt_98c5f2...",
  "type": "token.transfer",
  "created": 1736790000,
  "project_id": "proj_123",
  "api_version": "2026-01-13",
  "source": {
    "chain_id": "1",
    "network": "ethereum",
    "block_number": 19500000,
    "block_hash": "0xabc...",
    "tx_hash": "0xdef...",
    "tx_index": 12,
    "log_index": 3,
    "contract_address": "0xToken..."
  },
  "data": {
    "normalized": {
      "from": "0xFrom",
      "to": "0xTo",
      "amount": "1000000000000000000",
      "token_address": "0xToken...",
      "token_decimals": 18,
      "token_symbol": "TKN"
    },
    "raw": {
      "topics": ["0xddf252ad...", "0xFrom", "0xTo"],
      "data": "0x...",
      "abi_event": "Transfer(address,address,uint256)"
    }
  }
}
```
