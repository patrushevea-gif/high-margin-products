from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from app.core.config import get_settings
import httpx

router = APIRouter()
settings = get_settings()


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    role: str


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest) -> TokenResponse:
    """Authenticate via Supabase Auth."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{settings.supabase_url}/auth/v1/token?grant_type=password",
            headers={
                "apikey": settings.supabase_anon_key,
                "Content-Type": "application/json",
            },
            json={"email": body.email, "password": body.password},
        )
    if resp.status_code != 200:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    data = resp.json()
    return TokenResponse(
        access_token=data["access_token"],
        user_id=data["user"]["id"],
        role=data["user"].get("user_metadata", {}).get("role", "researcher"),
    )


@router.post("/logout")
async def logout() -> dict[str, str]:
    return {"status": "ok"}
