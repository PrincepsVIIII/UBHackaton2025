"""
Help request and assignment endpoints.
"""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_elder, get_current_volunteer
from app.db.session import get_db
from app.models import HelpRequest, RequestStatusEnum, User, crud
from app.schemas import (
    AssignmentResponse,
    HelpRequestClaimResponse,
    HelpRequestCreate,
    HelpRequestResponse,
    HelpRequestScoreResponse,
)
from app.services.matching import compute_request_scores

router = APIRouter(tags=["requests"])


def _active_assignment_schema(help_request: HelpRequest) -> AssignmentResponse | None:
    active_assignment = next(
        (assignment for assignment in help_request.assignments if assignment.completed_at is None),
        None,
    )
    return (
        AssignmentResponse.from_orm(active_assignment)
        if active_assignment is not None
        else None
    )


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
        current_assignment=_active_assignment_schema(help_request),
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
    scored_requests = compute_request_scores(
        db,
        volunteer_id=current_volunteer.id,
        volunteer_lat=volunteer_lat,
        volunteer_lng=volunteer_lng,
    )
    return [
        HelpRequestScoreResponse(
            request=_help_request_to_schema(help_request),
            score=score,
        )
        for help_request, score in scored_requests
    ]


@router.post(
    "/requests/{request_id}/claim",
    response_model=HelpRequestClaimResponse,
)
async def claim_request(
    request_id: int,
    current_volunteer: User = Depends(get_current_volunteer),
    db: Session = Depends(get_db),
):
    help_request = crud.get_help_request_by_id(db, request_id=request_id)
    if help_request is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Help request not found.")

    if help_request.status != RequestStatusEnum.OPEN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Help request is not available for claiming.",
        )

    volunteer = db.merge(current_volunteer)

    try:
        assignment = crud.claim_help_request(db, request=help_request, volunteer=volunteer)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    db.refresh(help_request)

    return HelpRequestClaimResponse(
        request=_help_request_to_schema(help_request),
        assignment=AssignmentResponse.from_orm(assignment),
    )

