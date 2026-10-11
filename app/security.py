import hashlib
import hmac
import secrets


ITERATIONS = 310_000


def hash_password(password: str) -> tuple[str, str]:
    salt = secrets.token_bytes(16)
    password_hash = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, ITERATIONS
    )
    return salt.hex(), password_hash.hex()


def verify_password(password: str, salt_hex: str, password_hash_hex: str) -> bool:
    try:
        salt = bytes.fromhex(salt_hex)
        expected_hash = bytes.fromhex(password_hash_hex)
    except ValueError:
        return False
    actual_hash = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, ITERATIONS
    )
    return hmac.compare_digest(actual_hash, expected_hash)
