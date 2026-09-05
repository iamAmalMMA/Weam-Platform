from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.constants import UserRole
from app.db.session import get_db
from app.models.care_team import CareTeamMembership
from app.models.center import Center
from app.models.center_account import CenterAccountMembership, CenterSpecialist
from app.models.user import User
from app.schemas.provider import (
    CenterProfileCreate,
    CenterProfileUpdate,
    CenterSpecialistCreate,
    CenterSpecialistPublic,
    CenterSpecialistUpdate,
    ManagedCenterPublic,
    ProviderDashboardPublic,
)
from app.services.access import membership_is_active

router = APIRouter(prefix="/provider", tags=["provider-experience"])


def _require_provider_account(user: User) -> None:
    if user.role not in {UserRole.CARE_PROVIDER.value, UserRole.CENTER.value}:
        raise HTTPException(status_code=403, detail="Provider account required")


def _require_center_account(user: User) -> None:
    if user.role != UserRole.CENTER.value:
        raise HTTPException(status_code=403, detail="Center account required")


def _membership(db: Session, user_id: str) -> CenterAccountMembership | None:
    return db.scalar(
        select(CenterAccountMembership).where(
            CenterAccountMembership.user_id == user_id,
            CenterAccountMembership.is_active.is_(True),
        )
    )


def _managed_center(db: Session, user: User) -> Center:
    _require_center_account(user)
    membership = _membership(db, user.id)
    if not membership:
        raise HTTPException(status_code=404, detail="Center profile not found")
    center = db.get(Center, membership.center_id)
    if not center:
        raise HTTPException(status_code=404, detail="Center profile not found")
    return center


def _serialize_center(center: Center) -> ManagedCenterPublic:
    return ManagedCenterPublic(
        id=center.id,
        name=center.name,
        description=center.description,
        city=center.city,
        region=center.region,
        address=center.address,
        specialties=list(center.specialties or []),
        services=list(center.services or []),
        served_needs=list(center.served_needs or []),
        min_age_years=center.min_age_years,
        max_age_years=center.max_age_years,
        offers_in_person=center.offers_in_person,
        offers_remote=center.offers_remote,
        phone=center.phone,
        email=center.email,
        working_hours=center.working_hours,
        price_range=center.price_range,
        latitude=center.latitude,
        longitude=center.longitude,
        is_active=center.is_active,
        verification_status=center.verification_status,
        verification_note=center.verification_note,
        created_at=center.created_at,
        updated_at=center.updated_at,
    )


@router.get("/dashboard", response_model=ProviderDashboardPublic)
def provider_dashboard(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ProviderDashboardPublic:
    _require_provider_account(user)
    center: Center | None = None
    specialists_count = 0
    membership = _membership(db, user.id)
    if membership:
        center = db.get(Center, membership.center_id)
        specialists_count = int(
            db.scalar(
                select(func.count(CenterSpecialist.id)).where(
                    CenterSpecialist.center_id == membership.center_id,
                    CenterSpecialist.is_active.is_(True),
                )
            )
            or 0
        )

    care_memberships = db.scalars(
        select(CareTeamMembership).where(CareTeamMembership.user_id == user.id)
    ).all()
    authorized_children_count = sum(
        1
        for item in care_memberships
        if membership_is_active(item.access_status, item.expires_at)
    )
    return ProviderDashboardPublic(
        center=_serialize_center(center) if center else None,
        specialists_count=specialists_count,
        authorized_children_count=authorized_children_count,
        account_kind=user.role,
    )


@router.post("/center", response_model=ManagedCenterPublic, status_code=status.HTTP_201_CREATED)
def create_center_profile(
    payload: CenterProfileCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ManagedCenterPublic:
    _require_center_account(user)
    if _membership(db, user.id):
        raise HTTPException(status_code=409, detail="Center profile already exists")
    center = Center(
        **payload.model_dump(mode="json"),
        is_active=True,
        verification_status="unverified",
        source_type="center_self_registered",
    )
    db.add(center)
    db.flush()
    db.add(
        CenterAccountMembership(
            center_id=center.id,
            user_id=user.id,
            account_role="owner",
        )
    )
    db.commit()
    db.refresh(center)
    return _serialize_center(center)


@router.get("/center", response_model=ManagedCenterPublic)
def get_center_profile(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ManagedCenterPublic:
    return _serialize_center(_managed_center(db, user))


@router.patch("/center", response_model=ManagedCenterPublic)
def update_center_profile(
    payload: CenterProfileUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ManagedCenterPublic:
    center = _managed_center(db, user)
    values = payload.model_dump(exclude_unset=True, mode="json")
    required_fields = {
        "name",
        "description",
        "city",
        "address",
        "specialties",
        "services",
        "served_needs",
        "offers_in_person",
        "offers_remote",
        "phone",
        "working_hours",
    }
    if any(field in values and values[field] is None for field in required_fields):
        raise HTTPException(status_code=422, detail="Required center fields cannot be empty")
    for field, value in values.items():
        setattr(center, field, value)
    if center.min_age_years is not None and center.max_age_years is not None:
        if center.max_age_years < center.min_age_years:
            raise HTTPException(status_code=422, detail="Invalid age range")
    if not center.offers_in_person and not center.offers_remote:
        raise HTTPException(status_code=422, detail="At least one delivery mode is required")
    if center.verification_status == "verified":
        center.verification_status = "unverified"
        center.verification_note = "تم تحديث بيانات المركز وتحتاج إلى مراجعة جديدة."
        center.verified_at = None
        center.verified_by_user_id = None
    db.add(center)
    db.commit()
    db.refresh(center)
    return _serialize_center(center)


@router.get("/center/specialists", response_model=list[CenterSpecialistPublic])
def list_specialists(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[CenterSpecialist]:
    center = _managed_center(db, user)
    return list(
        db.scalars(
            select(CenterSpecialist)
            .where(CenterSpecialist.center_id == center.id)
            .order_by(CenterSpecialist.created_at.desc())
        ).all()
    )


@router.post(
    "/center/specialists",
    response_model=CenterSpecialistPublic,
    status_code=status.HTTP_201_CREATED,
)
def create_specialist(
    payload: CenterSpecialistCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> CenterSpecialist:
    center = _managed_center(db, user)
    item = CenterSpecialist(center_id=center.id, **payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def _specialist_or_404(db: Session, center_id: str, specialist_id: str) -> CenterSpecialist:
    item = db.get(CenterSpecialist, specialist_id)
    if not item or item.center_id != center_id:
        raise HTTPException(status_code=404, detail="Specialist not found")
    return item


@router.patch("/center/specialists/{specialist_id}", response_model=CenterSpecialistPublic)
def update_specialist(
    specialist_id: str,
    payload: CenterSpecialistUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> CenterSpecialist:
    center = _managed_center(db, user)
    item = _specialist_or_404(db, center.id, specialist_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/center/specialists/{specialist_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_specialist(
    specialist_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Response:
    center = _managed_center(db, user)
    item = _specialist_or_404(db, center.id, specialist_id)
    db.delete(item)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
