"""
Placeholder matching logic for volunteer request suggestions.
"""

from __future__ import annotations

from typing import List, Tuple

import math
import random

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import HelpRequest, RequestStatusEnum, UrgencyLevelEnum

# Map urgency to weight multipliers
URGENCY_WEIGHTS = {
    UrgencyLevelEnum.LOW: 1.0,
    UrgencyLevelEnum.MEDIUM: 2.0,
    UrgencyLevelEnum.HIGH: 3.0,
}


def _haversine_km(
    *,
    lat1: float,
    lng1: float,
    lat2: float,
    lng2: float,
) -> float:
    """
    Compute great-circle distance between two latitude/longitude pairs.
    """

    r = 6371.0  # Earth radius (km)

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lng2 - lng1)

    a = (
        math.sin(d_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return r * c


def _mock_weather_severity() -> float:
    """
    Return a pseudo-random weather severity between 0.5 and 1.0.

    In production this should call a real weather API (e.g., NOAA, OpenWeather)
    and interpret snowfall/temperature/ice indexes to derive a severity scalar.
    """

    return random.uniform(0.5, 1.0)


def compute_request_scores(
    db: Session,
    *,
    volunteer_id: int,
    volunteer_lat: float,
    volunteer_lng: float,
) -> List[Tuple[HelpRequest, float]]:
    """
    Returns a list of (help_request, score) tuples ranked for the volunteer.

    Score formula blends urgency, weather, and distance:
        score = (urgency_weight * weather_severity) / (distance_km + 1)

    The +1 in the denominator prevents division by zero when the volunteer is
    at the same coordinates as the request.
    """

    open_requests = (
        db.execute(
            select(HelpRequest).where(HelpRequest.status == RequestStatusEnum.OPEN)
        )
        .scalars()
        .all()
    )

    scored_requests: List[Tuple[HelpRequest, float]] = []
    for help_request in open_requests:
        urgency_weight = URGENCY_WEIGHTS.get(help_request.urgency_level, 1.0)
        distance_km = _haversine_km(
            lat1=volunteer_lat,
            lng1=volunteer_lng,
            lat2=help_request.lat,
            lng2=help_request.lng,
        )
        weather_severity = _mock_weather_severity()

        score = (urgency_weight * weather_severity) / (distance_km + 1.0)
        scored_requests.append((help_request, score))

    # Sort descending so highest priority appears first
    return sorted(scored_requests, key=lambda item: item[1], reverse=True)

