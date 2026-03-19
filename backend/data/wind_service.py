from __future__ import annotations

import time

import requests

from utils.config import (
    EXTERNAL_API_BACKOFF_SECONDS,
    EXTERNAL_API_MAX_RETRIES,
    OPEN_METEO_URL,
    OPENWEATHER_API_KEY,
    OPENWEATHER_URL,
    REQUEST_TIMEOUT_SECONDS,
)
from utils.retry import run_with_retries


class WindServiceError(RuntimeError):
    pass


_last_available: dict | None = None
_response_cache: dict = {"result": None, "cached_at": 0, "bbox_key": None}
CACHE_TTL_SECONDS = 1800  # 30 minutes


def _get_cache_key(lat: float, lon: float) -> str:
    """Generate a cache key for a coordinate (rounded to 2 decimals for grouping nearby requests)."""
    return f"{lat:.2f},{lon:.2f}"


def _fetch_openweather(lat: float, lon: float) -> dict:
    if not OPENWEATHER_API_KEY:
        raise WindServiceError("OPENWEATHER_API_KEY is not set")

    response = run_with_retries(
        operation=lambda: requests.get(
            OPENWEATHER_URL,
            params={"lat": lat, "lon": lon, "appid": OPENWEATHER_API_KEY, "units": "metric"},
            timeout=REQUEST_TIMEOUT_SECONDS,
        ),
        retries=EXTERNAL_API_MAX_RETRIES,
        backoff_seconds=EXTERNAL_API_BACKOFF_SECONDS,
        retry_exceptions=(Exception,),
    )
    response.raise_for_status()
    payload = response.json()

    wind = payload.get("wind", {})
    speed_mps = float(wind.get("speed", 0.0))
    direction_deg = float(wind.get("deg", 0.0))

    return {
        "speed_mps": speed_mps,
        "direction_deg": direction_deg,
        "source": "openweather",
    }


def _fetch_open_meteo(lat: float, lon: float) -> dict:
    response = run_with_retries(
        operation=lambda: requests.get(
            OPEN_METEO_URL,
            params={
                "latitude": lat,
                "longitude": lon,
                "current": "wind_speed_10m,wind_direction_10m",
                "wind_speed_unit": "ms",
            },
            timeout=REQUEST_TIMEOUT_SECONDS,
        ),
        retries=EXTERNAL_API_MAX_RETRIES,
        backoff_seconds=EXTERNAL_API_BACKOFF_SECONDS,
        retry_exceptions=(Exception,),
    )
    response.raise_for_status()
    payload = response.json().get("current", {})

    return {
        "speed_mps": float(payload.get("wind_speed_10m", 0.0)),
        "direction_deg": float(payload.get("wind_direction_10m", 0.0)),
        "source": "open-meteo-fallback",
    }


def fetch_wind(lat: float, lon: float) -> dict:
    global _last_available, _response_cache

    # Check cache
    cache_key = _get_cache_key(lat, lon)
    now = time.time()
    
    if (_response_cache["result"] is not None and 
        _response_cache["bbox_key"] == cache_key and 
        (now - _response_cache["cached_at"]) < CACHE_TTL_SECONDS):
        # Return cached result
        cached = dict(_response_cache["result"])
        cached["cache_hit"] = True
        return cached

    errors: list[str] = []

    try:
        result = _fetch_openweather(lat, lon)
        result["stale"] = False
        _last_available = result
        _response_cache["result"] = result
        _response_cache["cached_at"] = now
        _response_cache["bbox_key"] = cache_key
        return result
    except Exception as exc:
        errors.append(str(exc))

    try:
        result = _fetch_open_meteo(lat, lon)
        result["stale"] = False
        _last_available = result
        _response_cache["result"] = result
        _response_cache["cached_at"] = now
        _response_cache["bbox_key"] = cache_key
        return result
    except Exception as exc:
        errors.append(str(exc))

    if _last_available is not None:
        stale_result = dict(_last_available)
        stale_result["stale"] = True
        stale_result["source"] = f"{stale_result.get('source', 'unknown')}-cache"
        stale_result["message"] = "Using last available data"
        return stale_result

    raise WindServiceError(" | ".join(errors))
