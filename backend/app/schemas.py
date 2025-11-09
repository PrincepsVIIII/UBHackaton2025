"""
Pydantic schemas for API requests and responses.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional, Union

from pydantic import BaseModel, EmailStr, Field

from app.models import RequestStatusEnum, RoleEnum, UrgencyLevelEnum


class UserBase(BaseModel):
    email: EmailStr
    role: Optional[RoleEnum] = Field(default=None)


class UserResponse(UserBase):
    id: int
    created_at: datetime
    is_suspended: bool

    class Config:
        from_attributes = True


class ElderProfileBase(BaseModel):
    address: str
    mobility_notes: Optional[str] = None
    preferred_contact_method: Optional[str] = None


class ElderProfileCreate(ElderProfileBase):
    pass


class ElderProfileResponse(ElderProfileBase):
    user_id: int

    class Config:
        from_attributes = True


class VolunteerProfileBase(BaseModel):
    radius_miles: int
    has_vehicle: bool
    verified: bool = False
    completed_events_count: int = 0


class VolunteerProfileCreate(VolunteerProfileBase):
    pass


class VolunteerProfileResponse(VolunteerProfileBase):
    user_id: int

    class Config:
        from_attributes = True


class MeResponse(BaseModel):
    user: UserResponse
    profile: Optional[Union[ElderProfileResponse, VolunteerProfileResponse]] = None

    class Config:
        from_attributes = True


class OTPRequest(BaseModel):
    email: EmailStr
    role: RoleEnum


class OTPVerify(BaseModel):
    email: EmailStr
    code: str = Field(
        ...,
        min_length=6,
        max_length=6,
        pattern=r"^\d{6}$",
        description="Six digit verification code sent to the user's email.",
    )


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class HelpRequestBase(BaseModel):
    title: str
    description: str
    address_override: Optional[str] = None
    lat: float
    lng: float
    urgency_level: UrgencyLevelEnum
    weather_factor: float = Field(default=0.0, ge=0.0, le=1.0)


class HelpRequestCreate(HelpRequestBase):
    pass


class AssignmentResponse(BaseModel):
    id: int
    request_id: int
    volunteer_id: int
    assigned_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class HelpRequestResponse(HelpRequestBase):
    id: int
    elder_id: int
    status: RequestStatusEnum
    created_at: datetime
    assigned_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    completion_approved_at: Optional[datetime] = None
    current_assignment: Optional[AssignmentResponse] = None

    class Config:
        from_attributes = True


class HelpRequestListItem(BaseModel):
    id: int
    title: str
    lat: float
    lng: float
    urgency_level: UrgencyLevelEnum
    status: RequestStatusEnum

    class Config:
        from_attributes = True


class HelpRequestScoreResponse(BaseModel):
    request: HelpRequestListItem
    score: float = Field(default=1.0, ge=0.0)


class HelpRequestClaimResponse(BaseModel):
    request: HelpRequestResponse
    assignment: AssignmentResponse

