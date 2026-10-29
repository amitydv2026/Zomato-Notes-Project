"""
JWT Authentication utilities for Zomato Notes.

Provides:
  - Password hashing / verification  (bcrypt directly)
  - JWT token creation / decoding    (HS256 via python-jose)
  - FastAPI dependency  get_current_user  that parses the Bearer token
    and returns the authenticated User ORM object.
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
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

# ── Password hashing ──────────────────────────────────────────────────────────
_BCRYPT_ROUNDS = 10   # cost 10 (~75ms) — secure industry default, avoids timeout on Render free tier


def hash_password(plain: str) -> str:
    """Return the bcrypt hash of *plain* as a UTF-8 string."""
    hashed = bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt(rounds=_BCRYPT_ROUNDS))
    return hashed.decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """
    Return True if *plain* matches the stored *hashed* password.

    Safely handles legacy plaintext passwords (pre-JWT migration):
    if *hashed* is not a valid bcrypt hash, bcrypt.checkpw raises
    an exception — we catch it and return False so the login endpoint
    returns a clean 401 instead of a 500.
    Users with legacy plaintext passwords must re-register.
    """
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        # stored value is not a bcrypt hash (legacy plaintext password)
        return False


# ── JWT creation ──────────────────────────────────────────────────────────────
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Encode *data* into a signed JWT.

    The ``sub`` claim should be set to the user's email (string) so
    ``get_current_user`` can look the user up by email.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta if expires_delta else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode["exp"] = expire
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


# ── OAuth2 bearer scheme ──────────────────────────────────────────────────────
# Points FastAPI's OpenAPI UI to the /auth/login endpoint for "Try it out".
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# ── Dependency: require a valid, non-expired JWT ──────────────────────────────
def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> models.User:
    """
    FastAPI dependency — decode the Bearer JWT and return the User row.

    Raises HTTP 401 if the token is missing, expired, or has an invalid
    signature; raises HTTP 401 if the user embedded in the token no longer
    exists in the database.
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
