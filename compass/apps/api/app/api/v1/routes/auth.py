from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from app.core.config import get_settings
from app.core.auth import get_current_user, CurrentUser
import httpx

router = APIRouter()


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user_id: str
    email: str
    role: str


class RefreshRequest(BaseModel):
    refresh_token: str


async def _supabase_post(path: str, payload: dict) -> dict:
    settings = get_settings()
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(
            f"{settings.supabase_url}/auth/v1/{path}",
            headers={"apikey": settings.supabase_anon_key,
                     "Content-Type": "application/json"},
            json=payload,
        )
    if resp.status_code not in (200, 201):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail=resp.json().get("error_description", "Auth error"))
    return resp.json()


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest) -> TokenResponse:
    data = await _supabase_post(
        "token?grant_type=password",
        {"email": body.email, "password": body.password},
    )
    user = data.get("user", {})
    return TokenResponse(
        access_token=data["access_token"],
        refresh_token=data.get("refresh_token", ""),
        user_id=user.get("id", ""),
        email=user.get("email", body.email),
        role=user.get("user_metadata", {}).get("role", "researcher"),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(body: RefreshRequest) -> TokenResponse:
    data = await _supabase_post(
        "token?grant_type=refresh_token",
        {"refresh_token": body.refresh_token},
    )
    user = data.get("user", {})
    return TokenResponse(
        access_token=data["access_token"],
        refresh_token=data.get("refresh_token", ""),
        user_id=user.get("id", ""),
        email=user.get("email", ""),
        role=user.get("user_metadata", {}).get("role", "researcher"),
    )


@router.get("/me", response_model=CurrentUser)
async def me(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    return user


@router.post("/logout")
async def logout() -> dict[str, str]:
    # JWT is stateless — client drops the token; Supabase revoke is optional
    return {"status": "ok"}
