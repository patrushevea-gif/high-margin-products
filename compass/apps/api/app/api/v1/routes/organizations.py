"""Organization management — create, invite, list members, switch context."""
from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser, get_current_user, require_admin, require_owner
from app.core.database import get_db
from app.models.organization import AuditLog, Organization, OrganizationMember

router = APIRouter()


# ── schemas ────────────────────────────────────────────────────────────────────

class OrgCreate(BaseModel):
    name: str
    slug: str | None = None


class OrgOut(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    plan: str
    hypotheses_limit: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class MemberOut(BaseModel):
    id: uuid.UUID
    user_id: str
    email: str
    role: str
    accepted_at: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True


class InviteRequest(BaseModel):
    email: EmailStr
    role: str = "researcher"


class UpdateRoleRequest(BaseModel):
    role: str


class OrgContextOut(BaseModel):
    org_id: uuid.UUID
    name: str
    slug: str
    plan: str
    role: str                  # current user's role in this org
    members_count: int
    hypotheses_limit: int


# ── helpers ────────────────────────────────────────────────────────────────────

def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug[:80]


async def _audit(
    db: AsyncSession,
    org_id: uuid.UUID,
    user: CurrentUser,
    action: str,
    resource_type: str | None = None,
    resource_id: str | None = None,
    meta: dict | None = None,
) -> None:
    db.add(AuditLog(
        organization_id=org_id,
        user_id=user.user_id,
        email=user.email,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        meta=meta or {},
    ))


# ── endpoints ──────────────────────────────────────────────────────────────────

@router.post("", response_model=OrgOut, status_code=201)
async def create_organization(
    body: OrgCreate,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> OrgOut:
    """Create a new organization; the creator becomes owner."""
    slug = body.slug or _slugify(body.name)
    # Ensure uniqueness
    existing = await db.scalar(select(Organization).where(Organization.slug == slug))
    if existing:
        slug = f"{slug}-{uuid.uuid4().hex[:6]}"

    org = Organization(name=body.name, slug=slug)
    db.add(org)
    await db.flush()

    member = OrganizationMember(
        organization_id=org.id,
        user_id=user.user_id,
        email=user.email,
        role="owner",
        accepted_at=datetime.now(timezone.utc),
    )
    db.add(member)
    await _audit(db, org.id, user, "org.created", "organization", str(org.id))
    await db.commit()
    await db.refresh(org)
    return OrgOut.model_validate(org)


@router.get("", response_model=list[OrgOut])
async def list_my_organizations(
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[OrgOut]:
    """List all organizations the current user belongs to."""
    rows = await db.scalars(
        select(Organization)
        .join(OrganizationMember,
              OrganizationMember.organization_id == Organization.id)
        .where(OrganizationMember.user_id == user.user_id)
        .order_by(Organization.created_at)
    )
    return [OrgOut.model_validate(o) for o in rows.all()]


@router.get("/context", response_model=OrgContextOut)
async def get_org_context(
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> OrgContextOut:
    """Return current org context (name, plan, role, limits)."""
    if user.org_id is None:
        raise HTTPException(status_code=404, detail="No organization context")

    org = await db.get(Organization, user.org_id)
    if org is None:
        raise HTTPException(status_code=404, detail="Organization not found")

    members_count = await db.scalar(
        select(func.count()).select_from(OrganizationMember)
        .where(OrganizationMember.organization_id == user.org_id)
    ) or 0

    return OrgContextOut(
        org_id=org.id,
        name=org.name,
        slug=org.slug,
        plan=org.plan,
        role=user.org_role,
        members_count=members_count,
        hypotheses_limit=org.hypotheses_limit,
    )


@router.get("/{org_id}/members", response_model=list[MemberOut])
async def list_members(
    org_id: uuid.UUID,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[MemberOut]:
    # Verify requester is a member
    me = await db.scalar(
        select(OrganizationMember).where(
            OrganizationMember.organization_id == org_id,
            OrganizationMember.user_id == user.user_id,
        )
    )
    if me is None:
        raise HTTPException(status_code=403, detail="Not a member")

    rows = await db.scalars(
        select(OrganizationMember)
        .where(OrganizationMember.organization_id == org_id)
        .order_by(OrganizationMember.created_at)
    )
    return [MemberOut.model_validate(r) for r in rows.all()]


@router.post("/{org_id}/invite", response_model=MemberOut, status_code=201)
async def invite_member(
    org_id: uuid.UUID,
    body: InviteRequest,
    user: CurrentUser = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> MemberOut:
    """Invite a user by email. They appear as pending (accepted_at=null)."""
    if body.role not in ("viewer", "researcher", "admin"):
        raise HTTPException(status_code=400, detail="Invalid role")

    existing = await db.scalar(
        select(OrganizationMember).where(
            OrganizationMember.organization_id == org_id,
            OrganizationMember.email == body.email,
        )
    )
    if existing:
        raise HTTPException(status_code=409, detail="User already invited or a member")

    member = OrganizationMember(
        organization_id=org_id,
        user_id="pending",   # will be filled when user accepts via Supabase magic link
        email=body.email,
        role=body.role,
        invited_by=user.user_id,
    )
    db.add(member)
    await _audit(db, org_id, user, "member.invited", "member", body.email,
                 {"role": body.role})
    await db.commit()
    await db.refresh(member)
    return MemberOut.model_validate(member)


@router.patch("/{org_id}/members/{member_id}/role")
async def update_member_role(
    org_id: uuid.UUID,
    member_id: uuid.UUID,
    body: UpdateRoleRequest,
    user: CurrentUser = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    if body.role not in ("viewer", "researcher", "admin"):
        raise HTTPException(status_code=400, detail="Invalid role. Cannot set owner via API.")

    member = await db.get(OrganizationMember, member_id)
    if member is None or member.organization_id != org_id:
        raise HTTPException(status_code=404, detail="Member not found")
    if member.role == "owner":
        raise HTTPException(status_code=403, detail="Cannot change owner role")

    old_role = member.role
    member.role = body.role
    await _audit(db, org_id, user, "member.role_changed", "member", str(member_id),
                 {"old_role": old_role, "new_role": body.role})
    await db.commit()
    return {"member_id": str(member_id), "role": body.role}


@router.delete("/{org_id}/members/{member_id}", status_code=204)
async def remove_member(
    org_id: uuid.UUID,
    member_id: uuid.UUID,
    user: CurrentUser = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> None:
    member = await db.get(OrganizationMember, member_id)
    if member is None or member.organization_id != org_id:
        raise HTTPException(status_code=404, detail="Member not found")
    if member.role == "owner":
        raise HTTPException(status_code=403, detail="Cannot remove the organization owner")
    if member.user_id == user.user_id:
        raise HTTPException(status_code=403, detail="Cannot remove yourself")

    await _audit(db, org_id, user, "member.removed", "member", str(member_id),
                 {"email": member.email})
    await db.delete(member)
    await db.commit()


@router.get("/{org_id}/audit-log")
async def get_audit_log(
    org_id: uuid.UUID,
    limit: int = 50,
    offset: int = 0,
    user: CurrentUser = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    rows = await db.scalars(
        select(AuditLog)
        .where(AuditLog.organization_id == org_id)
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return [
        {
            "id": str(r.id),
            "user_id": r.user_id,
            "email": r.email,
            "action": r.action,
            "resource_type": r.resource_type,
            "resource_id": r.resource_id,
            "meta": r.meta,
            "created_at": r.created_at.isoformat(),
        }
        for r in rows.all()
    ]


@router.patch("/{org_id}/settings")
async def update_org_settings(
    org_id: uuid.UUID,
    body: dict,
    user: CurrentUser = Depends(require_owner),
    db: AsyncSession = Depends(get_db),
) -> dict:
    org = await db.get(Organization, org_id)
    if org is None:
        raise HTTPException(status_code=404, detail="Organization not found")

    allowed_keys = {"name", "settings"}
    update_data = {k: v for k, v in body.items() if k in allowed_keys}
    for k, v in update_data.items():
        setattr(org, k, v)

    await _audit(db, org_id, user, "org.settings_updated", "organization", str(org_id),
                 {"updated_keys": list(update_data.keys())})
    await db.commit()
    return {"status": "updated", "updated": list(update_data.keys())}
