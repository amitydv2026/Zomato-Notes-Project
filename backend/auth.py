"""
JWT Authentication utilities for Zomato Notes.

Provides:
  - Password hashing / verification  (PBKDF2-SHA256 via stdlib hashlib)
  - JWT token creation / decoding    (HS256 via python-jose)
  - FastAPI dependency  get_current_user  that parses the Bearer token
    and returns the authenticated User ORM object.

Why PBKDF2 instead of bcrypt:
  The bcrypt C extension causes 500 errors on Render's free tier due to
  binary/runtime incompatibilities. PBKDF2-SHA256 with 260,000 iterations
  is Python stdlib (no C extension, no install issues), NIST-recommended,
  and used by Django as its default password hasher.
"""

import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from database import get_db
import models

# ── Config ────────────────────────────────────────────────────────────────────
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "changeme-use-a-long-random-secret-in-production")
JWT_ALGORITHM  = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))  # 24 h

# ── Password hashing (PBKDF2-SHA256, Python stdlib) ───────────────────────────
_ITERATIONS  = 260_000   # OWASP 2023 recommended minimum for PBKDF2-SHA256
_HASH_NAME   = "sha256"
_SALT_BYTES  = 32        # 256-bit random salt per password
_SEPARATOR   = "$"       # stored format:  pbkdf2$salt_hex$hash_hex


def hash_password(plain: str) -> str:
    """
    Hash *plain* with PBKDF2-SHA256 and return a self-contained string:
        pbkdf2$<salt_hex>$<hash_hex>
    The salt is randomly generated per call so identical passwords produce
    different stored values.
    """
    salt = secrets.token_bytes(_SALT_BYTES)
    dk = hashlib.pbkdf2_hmac(_HASH_NAME, plain.encode("utf-8"), salt, _ITERATIONS)
    return f"pbkdf2{_SEPARATOR}{salt.hex()}{_SEPARATOR}{dk.hex()}"


def verify_password(plain: str, stored: str) -> bool:
    """
    Return True if *plain* matches *stored*.

    Handles three cases:
    1. New PBKDF2 hash  — full verification
    2. Legacy bcrypt hash (starts with $2b$) — always False, user must re-register
    3. Anything else (old plaintext) — always False
    """
    try:
        if not stored.startswith("pbkdf2$"):
            # Legacy account (bcrypt or plaintext) — reject cleanly
            return False

        _, salt_hex, hash_hex = stored.split(_SEPARATOR, 2)
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(hash_hex)

        dk = hashlib.pbkdf2_hmac(_HASH_NAME, plain.encode("utf-8"), salt, _ITERATIONS)

        # Constant-time comparison prevents timing attacks
        return hmac.compare_digest(dk, expected)
    except Exception:
        return False


# ── JWT creation ──────────────────────────────────────────────────────────────
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Encode *data* into a signed JWT.
    The ``sub`` claim should be the user's email so get_current_user
    can look the user up by email.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta if expires_delta else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode["exp"] = expire
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


# ── OAuth2 bearer scheme ──────────────────────────────────────────────────────
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# ── Dependency: require a valid, non-expired JWT ──────────────────────────────
def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> models.User:
    """
    FastAPI dependency — decode the Bearer JWT and return the User row.
    Raises HTTP 401 if the token is missing, expired, invalid, or the
    user no longer exists.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        email: Optional[str] = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(models.User).filter(models.User.email == email).first()
    if user is None:
        raise credentials_exception

    return user
