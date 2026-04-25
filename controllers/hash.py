import hashlib
import os

def hash_password(password: str) -> str:
    """Şifreyi hashler."""
    salt = os.urandom(32)  # Rastgele salt
    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return salt.hex() + key.hex()

def verify_password(password: str, hashed: str) -> bool:
    """Şifreyi doğrular."""
    salt = bytes.fromhex(hashed[:64])
    key = bytes.fromhex(hashed[64:])
    new_key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return key == new_key