"""
Lightweight geocoding helpers backed by OpenStreetMap's Nominatim service.
"""

from __future__ import annotations

from typing import Optional, Tuple

import asyncio
import httpx

_CACHE: dict[str, Tuple[float, float]] = {}
_LOCK = asyncio.Lock()

_BASE_URL = "https://nominatim.openstreetmap.org/search"
_USER_AGENT = "UBHackaton2025/1.0 (contact@example.com)"


async def geocode_address(address: str) -> Optional[Tuple[float, float]]:
    """
    Resolve a human readable address to latitude/longitude coordinates.

    Uses an in-memory cache to avoid repeated lookups and applies a small
    amount of rounding for consistency.
    """

    normalized = address.strip()
    if not normalized:
        return None

    cache_key = normalized.lower()
    async with _LOCK:
        if cache_key in _CACHE:
            return _CACHE[cache_key]

    params = {"q": normalized, "format": "json", "limit": 1}
    headers = {"User-Agent": _USER_AGENT}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(_BASE_URL, params=params, headers=headers)
            response.raise_for_status()
    except httpx.HTTPError:
        return None

    payload = response.json()
    if not payload:
        return None

    try:
        lat = round(float(payload[0]["lat"]), 6)
        lng = round(float(payload[0]["lon"]), 6)
    except (KeyError, ValueError, TypeError, IndexError):
        return None

    coords = (lat, lng)
    async with _LOCK:
        _CACHE[cache_key] = coords
    return coords


