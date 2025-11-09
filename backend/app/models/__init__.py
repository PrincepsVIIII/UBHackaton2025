"""
SQLAlchemy ORM models for the Buffalo Winter Elder Help Routing backend.
"""

from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.db.session import Base


class RoleEnum(str, enum.Enum):
    ELDER = "elder"
    VOLUNTEER = "volunteer"


class UrgencyLevelEnum(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class RequestStatusEnum(str, enum.Enum):
    OPEN = "open"
    ASSIGNED = "assigned"
    COMPLETION_PENDING_APPROVAL = "completed_pending_approval"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint(
            "role IN ('elder', 'volunteer') OR role IS NULL",
            name="ck_users_role_valid",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    role = Column(Enum(RoleEnum, name="user_role_enum", values_callable=lambda x: [e.value for e in x]), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    is_suspended = Column(Boolean, nullable=False, default=False)

    elder_profile = relationship(
        "ElderProfile",
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False,
    )
    volunteer_profile = relationship(
        "VolunteerProfile",
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False,
    )
    help_requests = relationship(
        "HelpRequest",
        back_populates="elder",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    volunteer_assignments = relationship(
        "Assignment",
        back_populates="volunteer",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class ElderProfile(Base):
    __tablename__ = "elder_profiles"

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    address = Column(String(255), nullable=False)
    mobility_notes = Column(Text, nullable=True)
    preferred_contact_method = Column(String(100), nullable=True)

    user = relationship("User", back_populates="elder_profile")


class VolunteerProfile(Base):
    __tablename__ = "volunteer_profiles"

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    radius_miles = Column(Integer, nullable=False)
    has_vehicle = Column(Boolean, nullable=False, default=False)
    verified = Column(Boolean, nullable=False, default=False)
    completed_events_count = Column(Integer, nullable=False, default=0)

    user = relationship("User", back_populates="volunteer_profile")


class HelpRequest(Base):
    __tablename__ = "help_requests"
    __table_args__ = (
        CheckConstraint(
            "weather_factor >= 0.0 AND weather_factor <= 1.0",
            name="ck_help_requests_weather_factor_range",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    elder_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    address_override = Column(String(255), nullable=True)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    urgency_level = Column(
        Enum(UrgencyLevelEnum, name="urgency_level_enum"),
        nullable=False,
    )
    weather_factor = Column(Float, nullable=False, default=0.0)
    status = Column(
        Enum(RequestStatusEnum, name="request_status_enum"),
        nullable=False,
        default=RequestStatusEnum.OPEN,
    )
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    assigned_at = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    completion_approved_at = Column(DateTime, nullable=True)

    elder = relationship("User", back_populates="help_requests")
    assignments = relationship(
        "Assignment",
        back_populates="request",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class Assignment(Base):
    __tablename__ = "assignments"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(
        Integer,
        ForeignKey("help_requests.id", ondelete="CASCADE"),
        nullable=False,
    )
    volunteer_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    assigned_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    request = relationship("HelpRequest", back_populates="assignments")
    volunteer = relationship("User", back_populates="volunteer_assignments")


class EmailOTP(Base):
    __tablename__ = "email_otps"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), nullable=False, index=True)
    code_hash = Column(String(128), nullable=False)
    role = Column(Enum(RoleEnum, name="email_otp_role_enum", values_callable=lambda x: [e.value for e in x]), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class EventLog(Base):
    __tablename__ = "event_logs"

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String(255), nullable=False)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    request_id = Column(
        Integer,
        ForeignKey("help_requests.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    event_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

