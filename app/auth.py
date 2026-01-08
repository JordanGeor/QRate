import os
import base64
import hashlib
import hmac
from fastapi import Request, HTTPException
from sqlalchemy.orm import Session
from .models import User

COOKIE_NAME = "QRate_uid"

# PBKDF2 settings
_ITERATIONS = 200_000
_SALT_BYTES = 16

def hash_password(password: str) -> str:
    """
    Returns string format: pbkdf2$<iterations>$<salt_b64>$<hash_b64>
    """
    if password is None:
        raise ValueError("password required")
    salt = os.urandom(_SALT_BYTES)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _ITERATIONS)
    return "pbkdf2${}${}${}".format(
        _ITERATIONS,
        base64.b64encode(salt).decode("ascii"),
        base64.b64encode(dk).decode("ascii"),
    )

def verify_password(password: str, stored: str) -> bool:
    """
    Verifies pbkdf2$... hashes.
    """
    try:
        scheme, iters, salt_b64, hash_b64 = stored.split("$", 3)
        if scheme != "pbkdf2":
            return False
        iters = int(iters)
        salt = base64.b64decode(salt_b64.encode("ascii"))
        expected = base64.b64decode(hash_b64.encode("ascii"))
        dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iters)
        return hmac.compare_digest(dk, expected)
    except Exception:
        return False

def set_login_cookie(response, user_id: int):
    response.set_cookie(
        key=COOKIE_NAME,
        value=str(user_id),
        httponly=True,
        samesite="lax",
    )

def clear_login_cookie(response):
    response.delete_cookie(COOKIE_NAME)

def get_current_user(db: Session, request: Request) -> User:
    uid = request.cookies.get(COOKIE_NAME)
    if not uid:
        raise HTTPException(status_code=401, detail="Not logged in")
    user = db.query(User).filter(User.id == int(uid)).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid session")
    return user
