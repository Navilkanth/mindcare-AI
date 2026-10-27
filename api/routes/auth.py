"""
MindCare AI — Auth Routes
POST /api/register  — create a new account
POST /api/login     — get a JWT token
GET  /api/me        — return current user info (token required)
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from auth.auth import (
    create_user,
    authenticate_user,
    create_access_token,
    decode_token,
    get_user,
)

router  = APIRouter()
bearer  = HTTPBearer(auto_error=False)


# ─── Pydantic schemas ─────────────────────────────────────────────────────────
class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=32)
    password: str = Field(..., min_length=6, max_length=128)


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str


# ─── Dependency — extract & validate token ───────────────────────────────────
def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(bearer),
) -> str:
    """
    FastAPI dependency that extracts the username from a Bearer JWT.
    Raises 401 if the token is missing or invalid.
    """
    if not creds:
        raise HTTPException(status_code=401, detail="Not authenticated")
    username = decode_token(creds.credentials)
    if not username:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    if not get_user(username):
        raise HTTPException(status_code=401, detail="User not found")
    return username


# ─── Endpoints ────────────────────────────────────────────────────────────────
@router.post("/register", response_model=TokenResponse, tags=["Auth"])
async def register(body: RegisterRequest):
    """Create a new user account and return a JWT."""
    try:
        create_user(body.username, body.password)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    token = create_access_token(body.username)
    return TokenResponse(access_token=token, username=body.username)


@router.post("/login", response_model=TokenResponse, tags=["Auth"])
async def login(body: LoginRequest):
    """Authenticate and return a JWT."""
    user = authenticate_user(body.username, body.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    token = create_access_token(user["username"])
    return TokenResponse(access_token=token, username=user["username"])


@router.get("/me", tags=["Auth"])
async def me(username: str = Depends(get_current_user)):
    """Return the currently authenticated user's info."""
    user = get_user(username)
    return {"username": user["username"], "created_at": user["created_at"]}
