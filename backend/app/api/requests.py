"""
Help request and assignment endpoints.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_elder, get_current_volunteer
from app.core.config import settings
from app.db.session import get_db
from app.models import Assignment, HelpRequest, RequestStatusEnum, User, crud
from app.schemas import (
    AssignmentResponse,
    HelpRequestClaimResponse,
    HelpRequestCreate,
    HelpRequestListItem,
    HelpRequestResponse,
    HelpRequestScoreResponse,
)
from app.services.matching import compute_request_scores, anonymize_coordinates

router = APIRouter(tags=["requests"])


def _active_assignment_schema(help_request: HelpRequest) -> AssignmentResponse | None:
    active_assignment = next(
        (
            assignment
            for assignment in sorted(
                help_request.assignments,
                key=lambda a: a.assigned_at or datetime.min,
                reverse=True,
            )
            if assignment.completed_at is None
        ),
        None,
    )
    return AssignmentResponse.from_orm(active_assignment) if active_assignment else None


def _help_request_to_schema(help_request: HelpRequest) -> HelpRequestResponse:
    return HelpRequestResponse(
        id=help_request.id,
        elder_id=help_request.elder_id,
        title=help_request.title,
        description=help_request.description,
        address_override=help_request.address_override,
        lat=help_request.lat,
        lng=help_request.lng,
        urgency_level=help_request.urgency_level,
        weather_factor=help_request.weather_factor,
        status=help_request.status,
        created_at=help_request.created_at,
        assigned_at=help_request.assigned_at,
        cancelled_at=help_request.cancelled_at,
        completed_at=help_request.completed_at,
        completion_approved_at=help_request.completion_approved_at,
        current_assignment=_active_assignment_schema(help_request),
    )


def _help_request_list_item(help_request: HelpRequest) -> HelpRequestListItem:
    lat, lng = anonymize_coordinates(help_request.lat, help_request.lng)
    return HelpRequestListItem(
        id=help_request.id,
        title=help_request.title,
        lat=lat,
        lng=lng,
        urgency_level=help_request.urgency_level,
        status=help_request.status,
    )


@router.post(
    "/help-request",
    response_model=HelpRequestResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_help_request(
    payload: HelpRequestCreate,
    current_elder: User = Depends(get_current_elder),
    db: Session = Depends(get_db),
):
    elder = db.merge(current_elder)

    if elder.is_suspended:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Suspended users cannot create requests.",
        )

    open_count = crud.count_open_requests_for_elder(db, elder.id)
    if open_count >= settings.max_open_requests_per_elder:
        crud.log_event(
            db,
            event_type="request_rate_limit_blocked",
            user_id=elder.id,
            request_id=None,
            metadata={
                "open_count": open_count,
                "limit": settings.max_open_requests_per_elder,
            },
        )
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="You have reached the maximum number of active requests.",
        )

    help_request = crud.create_help_request(
        db,
        elder=elder,
        title=payload.title,
        description=payload.description,
        address_override=payload.address_override,
        lat=payload.lat,
        lng=payload.lng,
        urgency_level=payload.urgency_level,
        weather_factor=payload.weather_factor,
    )
    crud.log_event(
        db,
        event_type="request_created",
        user_id=elder.id,
        request_id=help_request.id,
        metadata={"role": elder.role.value if elder.role else None},
    )
    db.commit()
    db.refresh(help_request)
    return _help_request_to_schema(help_request)


@router.get(
    "/requests/open",
    response_model=List[HelpRequestScoreResponse],
)
async def list_open_requests(
    current_volunteer: User = Depends(get_current_volunteer),
    volunteer_lat: float = Query(..., description="Current volunteer latitude"),
    volunteer_lng: float = Query(..., description="Current volunteer longitude"),
    db: Session = Depends(get_db),
):
    volunteer = db.merge(current_volunteer)

    if volunteer.is_suspended:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Suspended users cannot access volunteer operations.",
        )

    scored_requests = compute_request_scores(
        db,
        volunteer_id=volunteer.id,
        volunteer_lat=volunteer_lat,
        volunteer_lng=volunteer_lng,
    )
    return [
        HelpRequestScoreResponse(
            request=_help_request_list_item(help_request),
            score=score,
        )
        for help_request, score in scored_requests
    ]


@router.get(
    "/elder/requests",
    response_model=List[HelpRequestResponse],
)
async def list_elder_requests(
    status: Optional[str] = Query(
        None,
        description="Filter by request status grouping: active or history.",
    ),
    current_elder: User = Depends(get_current_elder),
    db: Session = Depends(get_db),
):
    elder = db.merge(current_elder)

    status_groups: dict[str, list[RequestStatusEnum]] = {
        "active": [
            RequestStatusEnum.OPEN,
            RequestStatusEnum.ASSIGNED,
            RequestStatusEnum.COMPLETION_PENDING_APPROVAL,
        ],
        "history": [
            RequestStatusEnum.COMPLETED,
            RequestStatusEnum.CANCELLED,
        ],
    }

    if status is not None and status not in status_groups:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid status filter. Use 'active' or 'history'.",
        )

    help_requests = crud.list_help_requests_for_elder(
        db, elder.id, status_groups.get(status)
    )
    return [_help_request_to_schema(help_request) for help_request in help_requests]


@router.get(
    "/requests/{request_id}",
    response_model=HelpRequestResponse,
)
async def get_request_detail(
    request_id: int,
    current_volunteer: User = Depends(get_current_volunteer),
    db: Session = Depends(get_db),
):
    help_request = crud.get_help_request_by_id(db, request_id=request_id)
    if help_request is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Help request not found.")

    db.refresh(help_request)
    volunteer = db.merge(current_volunteer)

    if volunteer.is_suspended:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Suspended users cannot access volunteer operations.",
        )

    is_assigned = any(
        assignment.volunteer_id == volunteer.id and assignment.completed_at is None
        for assignment in help_request.assignments
    )
    if not is_assigned:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Request details available only to the assigned volunteer.",
        )

    return _help_request_to_schema(help_request)


@router.post(
    "/requests/{request_id}/cancel",
    response_model=HelpRequestResponse,
)
async def cancel_request(
    request_id: int,
    current_elder: User = Depends(get_current_elder),
    db: Session = Depends(get_db),
):
    help_request = crud.get_help_request_by_id(db, request_id=request_id)
    if help_request is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Help request not found.",
        )

    elder = db.merge(current_elder)

    if help_request.elder_id != elder.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the request owner can cancel this request.",
        )

    if help_request.status != RequestStatusEnum.OPEN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Request cannot be cancelled in its current state.",
        )

    help_request = db.merge(help_request)

    try:
        updated_request = crud.mark_request_cancelled(db, help_request)
        crud.log_event(
            db,
            event_type="request_cancelled",
            user_id=elder.id,
            request_id=updated_request.id,
            metadata={},
        )
        db.commit()
    except Exception as exc:  # pragma: no cover - defensive rollback
        db.rollback()
        raise exc

    db.refresh(updated_request)
    return _help_request_to_schema(updated_request)


@router.get(
    "/volunteer/active",
    response_model=Optional[HelpRequestClaimResponse],
)
async def get_active_assignment(
    current_volunteer: User = Depends(get_current_volunteer),
    db: Session = Depends(get_db),
):
    volunteer = db.merge(current_volunteer)

    assignment = crud.get_active_assignment_for_volunteer(db, volunteer.id)
    if assignment is None:
        return None

    db.refresh(assignment)

    help_request = assignment.request
    if help_request is None:
        help_request = crud.get_help_request_by_id(db, assignment.request_id)

    if help_request is None:
        return None

    db.refresh(help_request)

    return HelpRequestClaimResponse(
        request=_help_request_to_schema(help_request),
        assignment=AssignmentResponse.from_orm(assignment),
    )


@router.post(
    "/requests/{request_id}/claim",
    response_model=HelpRequestClaimResponse,
)
async def claim_request(
    request_id: int,
    current_volunteer: User = Depends(get_current_volunteer),
    db: Session = Depends(get_db),
):
    volunteer = db.merge(current_volunteer)

    if volunteer.is_suspended:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Suspended users cannot claim requests.",
        )

    if crud.volunteer_has_active_assignment(db, volunteer.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="active assignment exists",
        )

    help_request = crud.get_help_request_by_id(db, request_id=request_id)
    if help_request is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Help request not found.",
        )

    if help_request.status != RequestStatusEnum.OPEN:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="already claimed",
        )

    try:
        # SQLite lacks row-level locking, so we rely on an atomic UPDATE + rowcount
        # check. Swap this for SELECT ... FOR UPDATE when migrating to Postgres.
        assignment_result = crud.mark_request_assigned(
            db,
            request_id=help_request.id,
            volunteer_id=volunteer.id,
        )
        if assignment_result is None:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="already claimed",
            )
        assigned_request, assignment = assignment_result
        crud.log_event(
            db,
            event_type="request_assigned",
            user_id=volunteer.id,
            request_id=assigned_request.id,
            metadata={"assignment_id": assignment.id},
        )
        db.commit()
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - defensive rollback
        db.rollback()
        raise exc

    db.refresh(assigned_request)
    db.refresh(assignment)

    return HelpRequestClaimResponse(
        request=_help_request_to_schema(assigned_request),
        assignment=AssignmentResponse.from_orm(assignment),
    )


@router.post(
    "/requests/{request_id}/approve-completion",
    response_model=HelpRequestResponse,
)
async def approve_request_completion(
    request_id: int,
    current_elder: User = Depends(get_current_elder),
    db: Session = Depends(get_db),
):
    help_request = crud.get_help_request_by_id(db, request_id=request_id)
    if help_request is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Help request not found.",
        )

    elder = db.merge(current_elder)

    if help_request.elder_id != elder.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the request owner can approve completion.",
        )

    if help_request.status != RequestStatusEnum.COMPLETION_PENDING_APPROVAL:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Request is not pending completion approval.",
        )

    help_request = db.merge(help_request)

    completed_assignment: Optional[Assignment] = next(
        (
            assignment
            for assignment in sorted(
                help_request.assignments,
                key=lambda a: a.completed_at or datetime.min,
                reverse=True,
            )
            if assignment.completed_at is not None
        ),
        None,
    )

    if completed_assignment is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No completed assignment found for this request.",
        )

    try:
        updated_request = crud.mark_request_completed_final(db, help_request)

        volunteer_user = crud.get_user_by_id(db, completed_assignment.volunteer_id)
        if volunteer_user and volunteer_user.volunteer_profile:
            volunteer_user.volunteer_profile.completed_events_count += 1
            db.add(volunteer_user.volunteer_profile)

        crud.log_event(
            db,
            event_type="completion_approved_by_elder",
            user_id=elder.id,
            request_id=updated_request.id,
            metadata={"assignment_id": completed_assignment.id},
        )
        db.commit()
    except Exception as exc:  # pragma: no cover - defensive rollback
        db.rollback()
        raise exc

    db.refresh(updated_request)
    return _help_request_to_schema(updated_request)


@router.post(
    "/requests/{request_id}/complete",
    response_model=HelpRequestClaimResponse,
)
async def complete_request(
    request_id: int,
    current_volunteer: User = Depends(get_current_volunteer),
    db: Session = Depends(get_db),
):
    volunteer = db.merge(current_volunteer)

    help_request = crud.get_help_request_by_id(db, request_id=request_id)
    if help_request is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Help request not found.",
        )

    if help_request.status != RequestStatusEnum.ASSIGNED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Request is not currently assigned.",
        )

    help_request = db.merge(help_request)

    active_assignment = next(
        (
            assignment
            for assignment in help_request.assignments
            if assignment.completed_at is None
        ),
        None,
    )

    if active_assignment is None or active_assignment.volunteer_id != volunteer.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the assigned volunteer can complete this request.",
        )

    active_assignment.completed_at = datetime.utcnow()

    try:
        updated_request = crud.mark_request_completion_pending(db, help_request)
        crud.log_event(
            db,
            event_type="request_completed_by_volunteer",
            user_id=volunteer.id,
            request_id=updated_request.id,
            metadata={"assignment_id": active_assignment.id},
        )
        db.commit()
    except Exception as exc:  # pragma: no cover - defensive rollback
        db.rollback()
        raise exc

    db.refresh(updated_request)
    db.refresh(active_assignment)

    return HelpRequestClaimResponse(
        request=_help_request_to_schema(updated_request),
        assignment=AssignmentResponse.from_orm(active_assignment),
    )

