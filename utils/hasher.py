import hashlib
import hmac
import secrets


def hashPwd(password: str) -> str:
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 260_000) # noqa
    return f"{salt}:{key.hex()}"


def verifyPwd(password: str, hashed: str) -> bool:
    try:
        salt, key = hashed.split(":", 1)
    except ValueError:
        return False
    new_key = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 260_000) # noqa
    return hmac.compare_digest(new_key.hex(), key)
