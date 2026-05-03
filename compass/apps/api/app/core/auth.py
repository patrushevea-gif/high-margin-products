"""Supabase JWT verification + org context resolution — FastAPI dependency."""
from __future__ import annotations

import uuid

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db

_bearer = HTTPBearer(auto_error=False)


class CurrentUser(BaseModel):
    user_id: str
    email: str
    role: str = "researcher"          # global role from Supabase metadata
    org_id: uuid.UUID | None = None   # resolved from X-Organization-Id header + DB
    org_role: str = "researcher"      # role within the current organization


def _decode(token: str) -> dict:
    settings = get_settings()
    return jwt.decode(
        token,
        settings.supabase_jwt_secret,
        algorithms=["HS256"],
        options={"verify_aud": False},
    )


async def _resolve_org(
    user_id: str,
    org_id_header: str | None,
    db: AsyncSession,
) -> tuple[uuid.UUID | None, str]:
    """Return (org_id, org_role).

    If X-Organization-Id header present — verify membership and use it.
    Otherwise fall back to the user's first org membership.
    """
    from app.models.organization import OrganizationMember

    if org_id_header:
        try:
            org_uuid = uuid.UUID(org_id_header)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid X-Organization-Id header")

        row = await db.scalar(
            select(OrganizationMember).where(
                OrganizationMember.organization_id == org_uuid,
                OrganizationMember.user_id == user_id,
            )
        )
        if row is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not a member of this organization",
            )
        return org_uuid, row.role

    # No header — pick oldest membership
    row = await db.scalar(
        select(OrganizationMember)
        .where(OrganizationMember.user_id == user_id)
        .order_by(OrganizationMember.created_at)
        .limit(1)
    )
    if row is None:
        return None, "researcher"
    return row.organization_id, row.role


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    x_organization_id: str | None = Header(default=None, alias="X-Organization-Id"),
    db: AsyncSession = Depends(get_db),
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
    org_id, org_role = await _resolve_org(user_id, x_organization_id, db)
    return CurrentUser(user_id=user_id, email=email, role=role,
                       org_id=org_id, org_role=org_role)


async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    x_organization_id: str | None = Header(default=None, alias="X-Organization-Id"),
    db: AsyncSession = Depends(get_db),
) -> CurrentUser | None:
    if credentials is None:
        return None
    try:
        payload = _decode(credentials.credentials)
        user_id = payload.get("sub")
        if not user_id:
            return None
        email = payload.get("email", "")
        role = payload.get("user_metadata", {}).get("role", "researcher")
        org_id, org_role = await _resolve_org(user_id, x_organization_id, db)
        return CurrentUser(user_id=user_id, email=email, role=role,
                           org_id=org_id, org_role=org_role)
    except (JWTError, HTTPException):
        return None


def require_org_role(*allowed_roles: str):
    """Dependency factory — raises 403 if user's org_role is insufficient."""
    def _check(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if user.org_id is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No organization context. Pass X-Organization-Id header.",
            )
        if user.org_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of roles: {allowed_roles}. Your role: {user.org_role}",
            )
        return user
    return _check


require_admin = require_org_role("admin", "owner")
require_owner = require_org_role("owner")
