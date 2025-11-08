"""
Profile management endpoints.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import RoleEnum, User, crud
from app.schemas import (
    ElderProfileCreate,
    ElderProfileResponse,
    MeResponse,
    UserResponse,
    VolunteerProfileCreate,
    VolunteerProfileResponse,
)

router = APIRouter(tags=["profile"])


@router.get("/me", response_model=MeResponse)
async def read_me(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns the authenticated user's base info and associated profile.
    """

    current_user = db.merge(current_user)

    profile = None
    if current_user.role == RoleEnum.ELDER and current_user.elder_profile:
        profile = ElderProfileResponse.from_orm(current_user.elder_profile)
    elif current_user.role == RoleEnum.VOLUNTEER and current_user.volunteer_profile:
        profile = VolunteerProfileResponse.from_orm(current_user.volunteer_profile)

    return MeResponse(
        user=UserResponse.from_orm(current_user),
        profile=profile,
    )


@router.post(
    "/profile/elder",
    response_model=ElderProfileResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_elder_profile(
    payload: ElderProfileCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Creates an elder profile for the authenticated user.
    """

    db_user = db.merge(current_user)

    try:
        crud.ensure_user_role(db, db_user, RoleEnum.ELDER)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    try:
        profile = crud.create_elder_profile(
            db,
            db_user,
            address=payload.address,
            mobility_notes=payload.mobility_notes,
            preferred_contact_method=payload.preferred_contact_method,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    return ElderProfileResponse.from_orm(profile)


@router.post(
    "/profile/volunteer",
    response_model=VolunteerProfileResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_volunteer_profile(
    payload: VolunteerProfileCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Creates a volunteer profile for the authenticated user.
    """

    db_user = db.merge(current_user)

    try:
        crud.ensure_user_role(db, db_user, RoleEnum.VOLUNTEER)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    try:
        profile = crud.create_volunteer_profile(
            db,
            db_user,
            radius_miles=payload.radius_miles,
            has_vehicle=payload.has_vehicle,
            verified=payload.verified,
            completed_events_count=payload.completed_events_count,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    return VolunteerProfileResponse.from_orm(profile)

