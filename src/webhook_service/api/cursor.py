import base64
import json
from datetime import datetime
from typing import Optional, Tuple


def encode_cursor(created: datetime, id_: str) -> str:
    payload = {"created": created.isoformat(), "id": id_}
    raw = json.dumps(payload).encode()
    return base64.urlsafe_b64encode(raw).decode()


def decode_cursor(cursor: str) -> Tuple[datetime, str]:
    raw = base64.urlsafe_b64decode(cursor.encode())
    obj = json.loads(raw)
    return datetime.fromisoformat(obj["created"]), obj["id"]


def apply_cursor(stmt, model, cursor: Optional[str], created_field: str = "created", id_field: str = "id"):
    if not cursor:
        return stmt
    created, id_ = decode_cursor(cursor)
    created_col = getattr(model, created_field)
    id_col = getattr(model, id_field)
    return stmt.where((created_col < created) | ((created_col == created) & (id_col < id_)))

