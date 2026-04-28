"""Supabase JWT verification — FastAPI dependency."""
from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel

from app.core.config import get_settings

_bearer = HTTPBearer(auto_error=False)


class CurrentUser(BaseModel):
    user_id: str
    email: str
    role: str = "researcher"


def _decode(token: str) -> dict:
    settings = get_settings()
    return jwt.decode(
        token,
        settings.supabase_jwt_secret,
        algorithms=["HS256"],
        options={"verify_aud": False},
    )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> CurrentUser:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Not authenticated")
    try:
        payload = _decode(credentials.credentials)
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid token")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Token missing sub claim")

    email = payload.get("email", "")
    role = payload.get("user_metadata", {}).get("role", "researcher")
    return CurrentUser(user_id=user_id, email=email, role=role)


async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> CurrentUser | None:
    """Like get_current_user but returns None instead of 401 — for public endpoints."""
    if credentials is None:
        return None
    try:
        payload = _decode(credentials.credentials)
        user_id = payload.get("sub")
        if not user_id:
            return None
        email = payload.get("email", "")
        role = payload.get("user_metadata", {}).get("role", "researcher")
        return CurrentUser(user_id=user_id, email=email, role=role)
    except JWTError:
        return None
