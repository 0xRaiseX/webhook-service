import base64
import hashlib
from cryptography.fernet import Fernet, InvalidToken


def _derive_fernet_key(raw_key: str) -> bytes:
    """Derive urlsafe base64 key for Fernet from arbitrary string."""
    digest = hashlib.sha256(raw_key.encode()).digest()
    return base64.urlsafe_b64encode(digest)


def encrypt_secret(secret: str, encryption_key: str) -> str:
    key = _derive_fernet_key(encryption_key)
    f = Fernet(key)
    token = f.encrypt(secret.encode())
    return f"v1:{token.decode()}"


def decrypt_secret(secret_enc: str, encryption_key: str) -> str:
    if not secret_enc:
        return ""
    if not secret_enc.startswith("v1:"):
        # backward compatibility: stored as plain
        return secret_enc
    token = secret_enc[3:].encode()
    key = _derive_fernet_key(encryption_key)
    f = Fernet(key)
    try:
        return f.decrypt(token).decode()
    except InvalidToken as exc:
        raise ValueError("Invalid secret token") from exc

