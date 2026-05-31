"""
auth/utils.py — Password hashing with pbkdf2_sha256

WHY pbkdf2_sha256 instead of bcrypt:
  bcrypt has a hard 72-byte limit and raises a ValueError on longer passwords.
  pbkdf2_sha256 has NO length restriction — the user can type a password
  of any length and it will always work correctly.
"""

from passlib.context import CryptContext

# pbkdf2_sha256: secure, widely used, and has NO password length limit
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    """Hash any password regardless of length. Safe to store in DB."""
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against its stored hash. Returns True on match."""
    return pwd_context.verify(plain_password, hashed_password)
