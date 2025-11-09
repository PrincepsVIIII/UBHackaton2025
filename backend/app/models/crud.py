"""
Data-access helpers for user and profile management.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, Optional

from datetime import datetime

from sqlalchemy import and_, delete, func, select, update
from sqlalchemy.orm import Session

from app.models import (
    Assignment,
    ElderProfile,
    EmailOTP,
    EventLog,
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
    role: Optional[RoleEnum] = None,
    is_suspended: bool = False,
) -> User:
    user = User(email=email, role=role, is_suspended=is_suspended)
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


def list_help_requests_for_elder(
    db: Session,
    elder_id: int,
    statuses: Optional[Iterable[RequestStatusEnum]] = None,
) -> list[HelpRequest]:
    stmt = select(HelpRequest).where(HelpRequest.elder_id == elder_id)
    if statuses:
        stmt = stmt.where(HelpRequest.status.in_(list(statuses)))
    stmt = stmt.order_by(HelpRequest.created_at.desc())
    return db.execute(stmt).scalars().all()


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


def upsert_email_otp(
    db: Session,
    *,
    email: str,
    code_hash: str,
    role: RoleEnum,
    expires_at: datetime,
) -> EmailOTP:
    db.execute(delete(EmailOTP).where(EmailOTP.email == email))
    otp = EmailOTP(
        email=email,
        code_hash=code_hash,
        role=role,
        expires_at=expires_at,
    )
    db.add(otp)
    db.commit()
    db.refresh(otp)
    return otp


def get_email_otp(db: Session, email: str) -> Optional[EmailOTP]:
    return db.execute(select(EmailOTP).where(EmailOTP.email == email)).scalar_one_or_none()


def delete_email_otp(db: Session, otp: EmailOTP) -> None:
    db.delete(otp)
    db.commit()


def count_open_requests_for_elder(db: Session, elder_id: int) -> int:
    open_statuses = [RequestStatusEnum.OPEN, RequestStatusEnum.ASSIGNED]
    return (
        db.execute(
            select(func.count(HelpRequest.id)).where(
                and_(
                    HelpRequest.elder_id == elder_id,
                    HelpRequest.status.in_(open_statuses),
                )
            )
        )
        .scalar_one()
    )


def volunteer_has_active_assignment(db: Session, volunteer_id: int) -> bool:
    return (
        db.execute(
            select(func.count(Assignment.id)).where(
                and_(
                    Assignment.volunteer_id == volunteer_id,
                    Assignment.completed_at.is_(None),
                )
            )
        )
        .scalar_one()
        > 0
    )


def get_active_assignment_for_volunteer(db: Session, volunteer_id: int) -> Optional[Assignment]:
    return (
        db.execute(
            select(Assignment)
            .where(
                and_(
                    Assignment.volunteer_id == volunteer_id,
                    Assignment.completed_at.is_(None),
                )
            )
            .order_by(Assignment.assigned_at.desc())
        )
        .scalars()
        .first()
    )


def mark_request_assigned(
    db: Session,
    *,
    request_id: int,
    volunteer_id: int,
) -> Optional[tuple[HelpRequest, Assignment]]:
    now = datetime.utcnow()
    # SQLite does not support SELECT ... FOR UPDATE; this compare-and-update
    # pattern can be swapped for row-level locking when running against Postgres.
    update_stmt = (
        update(HelpRequest)
        .where(
            and_(
                HelpRequest.id == request_id,
                HelpRequest.status == RequestStatusEnum.OPEN,
            )
        )
        .values(
            status=RequestStatusEnum.ASSIGNED,
            assigned_at=now,
        )
    )
    result = db.execute(update_stmt)
    if result.rowcount == 0:
        return None

    assignment = Assignment(
        request_id=request_id,
        volunteer_id=volunteer_id,
        assigned_at=now,
    )
    db.add(assignment)
    db.flush()
    help_request = db.get(HelpRequest, request_id)
    db.refresh(assignment)
    return help_request, assignment


def mark_request_cancelled(db: Session, request: HelpRequest) -> HelpRequest:
    request.status = RequestStatusEnum.CANCELLED
    request.cancelled_at = datetime.utcnow()
    db.add(request)
    db.flush()
    return request


def mark_request_completion_pending(db: Session, request: HelpRequest) -> HelpRequest:
    request.status = RequestStatusEnum.COMPLETION_PENDING_APPROVAL
    request.completed_at = datetime.utcnow()
    db.add(request)
    db.flush()
    return request


def mark_request_completed_final(db: Session, request: HelpRequest) -> HelpRequest:
    request.status = RequestStatusEnum.COMPLETED
    request.completion_approved_at = datetime.utcnow()
    db.add(request)
    db.flush()
    return request


def log_event(
    db: Session,
    *,
    event_type: str,
    user_id: Optional[int],
    request_id: Optional[int],
    metadata: Optional[Dict[str, Any]] = None,
) -> EventLog:
    event = EventLog(
        event_type=event_type,
        user_id=user_id,
        request_id=request_id,
        event_metadata=metadata or {},
    )
    db.add(event)
    db.flush()
    return event

