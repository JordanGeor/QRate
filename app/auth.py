import os
import base64
import hashlib
import hmac
import time
import secrets

from dotenv import load_dotenv
from fastapi import Request, HTTPException
from sqlalchemy.orm import Session

from .models import User


load_dotenv()

COOKIE_NAME = "QRate_uid"
CSRF_COOKIE_NAME = "QRate_csrf"

SESSION_SECRET = os.getenv("SESSION_SECRET")
SESSION_MAX_AGE = 60 * 60 * 8
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "0") == "1"

# PBKDF2 settings
_ITERATIONS = 200_000
_SALT_BYTES = 16


def _sign_session(user_id: int) -> str:
    if not SESSION_SECRET:
        raise RuntimeError("SESSION_SECRET is not configured")

    expires_at = int(time.time()) + SESSION_MAX_AGE
    payload = f"{user_id}.{expires_at}"

    signature = hmac.new(
        SESSION_SECRET.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    return f"{payload}.{signature}"


def _verify_session(token: str) -> int | None:
    if not SESSION_SECRET:
        raise RuntimeError("SESSION_SECRET is not configured")

    try:
        user_id_str, expires_at_str, signature = token.split(".", 2)

        payload = f"{user_id_str}.{expires_at_str}"

        expected_signature = hmac.new(
            SESSION_SECRET.encode("utf-8"),
            payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(signature, expected_signature):
            return None

        expires_at = int(expires_at_str)

        if time.time() > expires_at:
            return None

        return int(user_id_str)

    except (ValueError, TypeError):
        return None


def hash_password(password: str) -> str:
    """
    Returns string format: pbkdf2$<iterations>$<salt_b64>$<hash_b64>
    """
    if password is None:
        raise ValueError("password required")

    salt = os.urandom(_SALT_BYTES)

    dk = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        _ITERATIONS,
    )

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

        dk = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            iters,
        )

        return hmac.compare_digest(dk, expected)

    except Exception:
        return False


def set_login_cookie(response, user_id: int):
    token = _sign_session(user_id)

    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        secure=COOKIE_SECURE,
        max_age=SESSION_MAX_AGE,
    )


def clear_login_cookie(response):
    response.delete_cookie(COOKIE_NAME)


def get_current_user(db: Session, request: Request) -> User:
    token = request.cookies.get(COOKIE_NAME)

    if not token:
        raise HTTPException(status_code=401, detail="Not logged in")

    user_id = _verify_session(token)

    if user_id is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired session",
        )

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid session")

    return user

def get_csrf_token(request: Request) -> str:
    token = request.cookies.get(CSRF_COOKIE_NAME)

    if token:
        return token

    return secrets.token_urlsafe(32)


def set_csrf_cookie(response, token: str):
    response.set_cookie(
        key=CSRF_COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="strict",
        secure=COOKIE_SECURE,
        max_age=SESSION_MAX_AGE,
    )


def verify_csrf_token(request: Request, form_token: str):
    cookie_token = request.cookies.get(CSRF_COOKIE_NAME)

    if not cookie_token or not form_token:
        raise HTTPException(status_code=403, detail="Invalid CSRF token")

    if not hmac.compare_digest(cookie_token, form_token):
        raise HTTPException(status_code=403, detail="Invalid CSRF token")