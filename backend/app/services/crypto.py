import base64
import hashlib
from cryptography.fernet import Fernet
from app.config import settings

def _get_fernet() -> Fernet:
    # Derive a 32-byte URL-safe base64-encoded key from the secret key
    digest = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
    key = base64.urlsafe_b64encode(digest)
    return Fernet(key)

def encrypt_value(plain_text: str) -> str:
    """Encrypt a string using Fernet AES-128-CBC / HMAC-SHA256."""
    if not plain_text:
        return ""
    f = _get_fernet()
    return f.encrypt(plain_text.encode("utf-8")).decode("utf-8")

def decrypt_value(cipher_text: str) -> str:
    """Decrypt an encrypted string."""
    if not cipher_text:
        return ""
    try:
        f = _get_fernet()
        return f.decrypt(cipher_text.encode("utf-8")).decode("utf-8")
    except Exception:
        return ""
