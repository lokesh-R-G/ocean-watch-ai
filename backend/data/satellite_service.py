from __future__ import annotations

from typing import Any

import numpy as np
from sentinelhub import BBox, CRS, DataCollection, MimeType, SHConfig, SentinelHubRequest

from utils.config import (
    EXTERNAL_API_BACKOFF_SECONDS,
    EXTERNAL_API_MAX_RETRIES,
    SATELLITE_IMAGE_HEIGHT,
    SATELLITE_IMAGE_WIDTH,
    SENTINELHUB_CLIENT_ID,
    SENTINELHUB_CLIENT_SECRET,
    SENTINELHUB_INSTANCE_ID,
)
from utils.retry import run_with_retries


class SatelliteServiceError(RuntimeError):
    pass


_evalscript = """
//VERSION=3
function setup() {
  return {
    input: ["B04", "B03", "B02"],
    output: { bands: 3, sampleType: "AUTO" }
  };
}

function evaluatePixel(sample) {
  return [sample.B04, sample.B03, sample.B02];
}
"""

_last_available: dict[str, Any] | None = None


def _build_config() -> SHConfig:
    config = SHConfig()
    config.sh_client_id = SENTINELHUB_CLIENT_ID
    config.sh_client_secret = SENTINELHUB_CLIENT_SECRET
    if SENTINELHUB_INSTANCE_ID:
        config.instance_id = SENTINELHUB_INSTANCE_ID

    if not config.sh_client_id or not config.sh_client_secret:
        raise SatelliteServiceError("Sentinel Hub credentials are not configured")

    return config


def _sanitize_bbox(raw_bbox: dict[str, float]) -> dict[str, float]:
    min_lat = float(raw_bbox["min_lat"])
    max_lat = float(raw_bbox["max_lat"])
    min_lon = float(raw_bbox["min_lon"])
    max_lon = float(raw_bbox["max_lon"])

    if min_lat >= max_lat or min_lon >= max_lon:
        raise SatelliteServiceError("Invalid bbox: minimum coordinates must be less than maximum")

    return {
        "min_lat": min_lat,
        "max_lat": max_lat,
        "min_lon": min_lon,
        "max_lon": max_lon,
    }


def _fetch_latest_from_sentinel_hub(clean_bbox: dict[str, float]) -> dict[str, Any]:
    sh_config = _build_config()
    request_bbox = BBox(
        bbox=(clean_bbox["min_lon"], clean_bbox["min_lat"], clean_bbox["max_lon"], clean_bbox["max_lat"]),
        crs=CRS.WGS84,
    )

    request = SentinelHubRequest(
        evalscript=_evalscript,
        input_data=[
            SentinelHubRequest.input_data(
                data_collection=DataCollection.SENTINEL2_L2A,
                time_interval=("NOW-1DAYS", "NOW"),
                mosaicking_order="mostRecent",
            )
        ],
        responses=[SentinelHubRequest.output_response("default", MimeType.PNG)],
        bbox=request_bbox,
        size=(SATELLITE_IMAGE_WIDTH, SATELLITE_IMAGE_HEIGHT),
        config=sh_config,
    )

    images = request.get_data()
    if not images:
        raise SatelliteServiceError("No Sentinel-2 image returned for the requested bbox")

    image = images[0]
    if image is None or image.size == 0:
        raise SatelliteServiceError("Sentinel Hub returned an empty image")

    if image.dtype != np.uint8:
        image = np.clip(image * 255.0, 0, 255).astype(np.uint8)

    return {
        "image": image,
        "bbox": clean_bbox,
        "source": "sentinelhub:SENTINEL2_L2A",
        "time_window": "NOW-1DAYS/NOW",
        "stale": False,
    }


def fetch_latest_sentinel2_image(raw_bbox: dict[str, float]) -> dict[str, Any]:
    global _last_available

    clean_bbox = _sanitize_bbox(raw_bbox)

    try:
        response = run_with_retries(
            operation=lambda: _fetch_latest_from_sentinel_hub(clean_bbox),
            retries=EXTERNAL_API_MAX_RETRIES,
            backoff_seconds=EXTERNAL_API_BACKOFF_SECONDS,
            retry_exceptions=(Exception,),
        )
        _last_available = response
        return response
    except Exception as exc:
        if _last_available is not None:
            stale_payload = dict(_last_available)
            stale_payload["stale"] = True
            stale_payload["message"] = f"Using last available data ({exc})"
            return stale_payload
        raise SatelliteServiceError(str(exc)) from exc
