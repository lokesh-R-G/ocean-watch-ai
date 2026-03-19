from __future__ import annotations

import math
import time

import requests

from utils.config import (
    EXTERNAL_API_BACKOFF_SECONDS,
    EXTERNAL_API_MAX_RETRIES,
    NOAA_DATASET_ID,
    NOAA_ERDDAP_BASE,
    REQUEST_TIMEOUT_SECONDS,
)
from utils.retry import run_with_retries


class OceanCurrentServiceError(RuntimeError):
    pass


_time_cache: dict[str, float | str | None] = {"value": None, "fetched_at": 0.0}
CACHE_TTL_SECONDS = 3600
_response_cache: dict = {"result": None, "cached_at": 0, "bbox_key": None}
RESPONSE_CACHE_TTL_SECONDS = 1800  # 30 minutes
_last_available: dict | None = None


def _to_360_longitude(lon: float) -> float:
    return lon % 360


def _get_cache_key(lat: float, lon: float) -> str:
    """Generate a cache key for a coordinate (rounded to 2 decimals for grouping nearby requests)."""
    return f"{lat:.2f},{lon:.2f}"


def _get_latest_dataset_time() -> str:
    now = time.time()
    if _time_cache["value"] and now - float(_time_cache["fetched_at"] or 0) < CACHE_TTL_SECONDS:
        return str(_time_cache["value"])

    info_url = f"{NOAA_ERDDAP_BASE}/info/{NOAA_DATASET_ID}/index.json"
    response = run_with_retries(
        operation=lambda: requests.get(info_url, timeout=REQUEST_TIMEOUT_SECONDS),
        retries=EXTERNAL_API_MAX_RETRIES,
        backoff_seconds=EXTERNAL_API_BACKOFF_SECONDS,
        retry_exceptions=(Exception,),
    )
    response.raise_for_status()
    payload = response.json()

    rows = payload.get("table", {}).get("rows", [])
    latest_time = None
    for row in rows:
        if row[0] == "attribute" and row[1] == "NC_GLOBAL" and row[2] == "time_coverage_end":
            latest_time = row[4]
            break

    if not latest_time:
        raise OceanCurrentServiceError("Unable to read NOAA dataset latest timestamp")

    _time_cache["value"] = latest_time
    _time_cache["fetched_at"] = now
    return str(latest_time)


def _vector_to_direction_deg(u: float, v: float) -> float:
    return (math.degrees(math.atan2(u, v)) + 360) % 360


def fetch_ocean_current(lat: float, lon: float) -> dict:
    global _last_available, _response_cache

    clamped_lat = max(-75.0, min(75.0, lat))
    lon_360 = _to_360_longitude(lon)
    
    # Check cache
    cache_key = _get_cache_key(clamped_lat, lon_360)
    now = time.time()
    
    if (_response_cache["result"] is not None and 
        _response_cache["bbox_key"] == cache_key and 
        (now - _response_cache["cached_at"]) < RESPONSE_CACHE_TTL_SECONDS):
        # Return cached result
        cached = dict(_response_cache["result"])
        cached["cache_hit"] = True
        return cached

    try:
        dataset_time = _get_latest_dataset_time()

        query = (
            f"u_current[({dataset_time})][(0.0)][({clamped_lat:.2f})][({lon_360:.2f})],"
            f"v_current[({dataset_time})][(0.0)][({clamped_lat:.2f})][({lon_360:.2f})]"
        )
        url = f"{NOAA_ERDDAP_BASE}/griddap/{NOAA_DATASET_ID}.json?{''.join(query)}"

        response = run_with_retries(
            operation=lambda: requests.get(url, timeout=REQUEST_TIMEOUT_SECONDS),
            retries=EXTERNAL_API_MAX_RETRIES,
            backoff_seconds=EXTERNAL_API_BACKOFF_SECONDS,
            retry_exceptions=(Exception,),
        )
        response.raise_for_status()
        payload = response.json()

        rows = payload.get("table", {}).get("rows", [])
        if not rows:
            raise OceanCurrentServiceError("No ocean current rows returned from NOAA")

        row = rows[0]
        u_component = float(row[4])
        v_component = float(row[5])
        speed = math.sqrt(u_component * u_component + v_component * v_component)

        result = {
            "u_component_mps": u_component,
            "v_component_mps": v_component,
            "speed_mps": speed,
            "direction_deg": _vector_to_direction_deg(u_component, v_component),
            "source": f"noaa-erddap:{NOAA_DATASET_ID}",
            "dataset_time": dataset_time,
            "stale": False,
        }
        _last_available = result
        _response_cache["result"] = result
        _response_cache["cached_at"] = now
        _response_cache["bbox_key"] = cache_key
        return result
    except Exception as exc:
        if _last_available is not None:
            stale_result = dict(_last_available)
            stale_result["stale"] = True
            stale_result["source"] = f"{stale_result.get('source', 'unknown')}-cache"
            stale_result["message"] = "Using last available data"
            return stale_result
        raise OceanCurrentServiceError(str(exc)) from exc
