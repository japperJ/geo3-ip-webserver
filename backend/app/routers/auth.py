from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.auth.jwt import encode_jwt
from app.auth.security import verify_password
from app.auth.store import get_user
from app.settings import settings

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest) -> TokenResponse:
    user = get_user(payload.email)
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    exp = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_exp_minutes)
    token = encode_jwt({"sub": user.email, "exp": int(exp.timestamp())})
    return TokenResponse(access_token=token, token_type="bearer")
