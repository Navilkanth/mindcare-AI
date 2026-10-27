"""
MindCare AI — Auth helpers
JSON-based user store + bcrypt passwords + JWT tokens
"""
import json
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

# ─── Paths ────────────────────────────────────────────────────────────────────
_HERE       = os.path.dirname(__file__)
USERS_FILE  = os.path.join(_HERE, "users.json")

# ─── Crypto settings ──────────────────────────────────────────────────────────
SECRET_KEY    = os.getenv("JWT_SECRET", "mindcare-super-secret-change-in-prod-2024")
ALGORITHM     = "HS256"
TOKEN_EXPIRE  = 60 * 24  # minutes → 24 hours

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ─── JSON store helpers ───────────────────────────────────────────────────────
def _load() -> list[dict]:
    """Load users list from JSON file."""
    if not os.path.exists(USERS_FILE):
        return []
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("users", [])


def _save(users: list[dict]) -> None:
    """Persist users list to JSON file."""
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump({"users": users}, f, indent=2, ensure_ascii=False)


# ─── User operations ─────────────────────────────────────────────────────────
def get_user(username: str) -> Optional[dict]:
    """Return user dict or None."""
    return next((u for u in _load() if u["username"] == username), None)


def create_user(username: str, password: str) -> dict:
    """
    Register a new user.
    Raises ValueError if username already taken.
    """
    users = _load()
    if any(u["username"] == username for u in users):
        raise ValueError("Username already taken")
    user = {
        "username": username,
        "hashed_password": pwd_ctx.hash(password),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    users.append(user)
    _save(users)
    return user


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_ctx.verify(plain, hashed)


def authenticate_user(username: str, password: str) -> Optional[dict]:
    """Return user dict if credentials are valid, else None."""
    user = get_user(username)
    if not user:
        return None
    if not verify_password(password, user["hashed_password"]):
        return None
    return user


# ─── JWT ─────────────────────────────────────────────────────────────────────
def create_access_token(username: str) -> str:
    """Issue a signed JWT valid for TOKEN_EXPIRE minutes."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=TOKEN_EXPIRE)
    payload = {"sub": username, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Optional[str]:
    """
    Decode a JWT and return the username (sub).
    Returns None if the token is invalid or expired.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None
