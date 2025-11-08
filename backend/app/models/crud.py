"""
Data-access helpers for user and profile management.
"""

from __future__ import annotations

from typing import Iterable, Optional

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    Assignment,
    ElderProfile,
    HelpRequest,
    RequestStatusEnum,
    RoleEnum,
    User,
    VolunteerProfile,
)


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.execute(select(User).where(User.email == email)).scalar_one_or_none()


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    return db.get(User, user_id)


def create_user(
    db: Session,
    *,
    email: str,
    name: Optional[str] = None,
    phone: Optional[str] = None,
    role: Optional[RoleEnum] = None,
) -> User:
    user = User(email=email, name=name, phone=phone, role=role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def ensure_user_role(db: Session, user: User, role: RoleEnum) -> User:
    """
    Assigns the provided role to the user if unset. Raises ValueError if the
    user already has a conflicting role.
    """

    if user.role is None:
        user.role = role
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    if user.role != role:
        raise ValueError(
            f"User already has role '{user.role.value}' and cannot switch to '{role.value}'."
        )

    return user


def create_elder_profile(
    db: Session, user: User, *, address: str, mobility_notes: Optional[str], preferred_contact_method: Optional[str]
) -> ElderProfile:
    if user.elder_profile:
        raise ValueError("Elder profile already exists for user.")

    profile = ElderProfile(
        user_id=user.id,
        address=address,
        mobility_notes=mobility_notes,
        preferred_contact_method=preferred_contact_method,
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


def create_volunteer_profile(
    db: Session,
    user: User,
    *,
    radius_miles: int,
    has_vehicle: bool,
    verified: bool,
    completed_events_count: int,
) -> VolunteerProfile:
    if user.volunteer_profile:
        raise ValueError("Volunteer profile already exists for user.")

    profile = VolunteerProfile(
        user_id=user.id,
        radius_miles=radius_miles,
        has_vehicle=has_vehicle,
        verified=verified,
        completed_events_count=completed_events_count,
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


def create_help_request(
    db: Session,
    *,
    elder: User,
    title: str,
    description: str,
    address_override: Optional[str],
    lat: float,
    lng: float,
    urgency_level,
    weather_factor: float,
) -> HelpRequest:
    help_request = HelpRequest(
        elder_id=elder.id,
        title=title,
        description=description,
        address_override=address_override,
        lat=lat,
        lng=lng,
        urgency_level=urgency_level,
        weather_factor=weather_factor,
        status=RequestStatusEnum.OPEN,
    )
    db.add(help_request)
    db.commit()
    db.refresh(help_request)
    return help_request


def get_help_request_by_id(db: Session, request_id: int) -> Optional[HelpRequest]:
    return db.get(HelpRequest, request_id)


def list_open_help_requests(db: Session) -> Iterable[HelpRequest]:
    return (
        db.execute(
            select(HelpRequest).where(HelpRequest.status == RequestStatusEnum.OPEN)
        )
        .scalars()
        .all()
    )


def create_assignment(
    db: Session,
    *,
    request: HelpRequest,
    volunteer: User,
) -> Assignment:
    assignment = Assignment(
        request_id=request.id,
        volunteer_id=volunteer.id,
    )
    db.add(assignment)
    return assignment


def claim_help_request(
    db: Session, *, request: HelpRequest, volunteer: User
) -> Assignment:
    if request.status != RequestStatusEnum.OPEN:
        raise ValueError("Help request is not available for assignment.")

    assignment = create_assignment(db, request=request, volunteer=volunteer)
    request.status = RequestStatusEnum.ASSIGNED
    db.add(request)
    db.commit()
    db.refresh(request)
    db.refresh(assignment)
    return assignment


def touch_user_last_login(db: Session, user: User) -> User:
    """
    Updates the user's last_login timestamp to now.
    """

    user.last_login = datetime.utcnow()
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

