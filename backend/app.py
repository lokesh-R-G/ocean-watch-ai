from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from data.ocean_current_service import OceanCurrentServiceError, fetch_ocean_current
from data.satellite_service import SatelliteServiceError, fetch_latest_sentinel2_image
from data.wind_service import WindServiceError, fetch_wind
from detection.yolo_detector import detect_plastic_clusters_from_image
from prediction.movement_model import predict_location_after_minutes
from utils.schemas import AnalyzeRequest, AnalyzeResponse

app = FastAPI(title="Ocean Plastic Monitoring API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


def _bbox_center(bbox: dict) -> tuple[float, float]:
    lat = (bbox["min_lat"] + bbox["max_lat"]) / 2.0
    lon = (bbox["min_lon"] + bbox["max_lon"]) / 2.0
    return lat, lon


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(payload: AnalyzeRequest):
    bbox = payload.bbox.model_dump()
    center_lat, center_lon = _bbox_center(bbox)

    status = "ok"
    messages: list[str] = []

    detections: list[dict] = []
    satellite: dict = {
        "source": "unavailable",
        "stale": True,
    }

    try:
        satellite = fetch_latest_sentinel2_image(bbox)
        detections = detect_plastic_clusters_from_image(satellite["image"], geo_bbox=bbox)
        if satellite.get("stale"):
            status = "degraded"
            messages.append("Using last available data")
    except Exception as exc:
        if isinstance(exc, SatelliteServiceError):
            status = "degraded"
            messages.append("Using last available data")
            satellite = {
                "source": "sentinelhub-unavailable",
                "stale": True,
                "error": str(exc),
            }
        else:
            status = "degraded"
            messages.append("Using last available data")
            satellite = {
                "source": "sentinelhub-unavailable",
                "stale": True,
                "error": str(exc),
            }

    wind: dict

    try:
        wind = fetch_wind(center_lat, center_lon)
        if wind.get("stale"):
            status = "degraded"
            messages.append("Using last available data")
    except WindServiceError as exc:
        status = "degraded"
        messages.append("Using last available data")
        wind = {
            "speed_mps": 0.0,
            "direction_deg": 0.0,
            "source": "wind-unavailable",
            "stale": True,
            "error": str(exc),
        }

    current: dict

    try:
        current = fetch_ocean_current(center_lat, center_lon)
        if current.get("stale"):
            status = "degraded"
            messages.append("Using last available data")
    except OceanCurrentServiceError as exc:
        status = "degraded"
        messages.append("Using last available data")
        current = {
            "u_component_mps": 0.0,
            "v_component_mps": 0.0,
            "speed_mps": 0.0,
            "direction_deg": 0.0,
            "source": "ocean-current-unavailable",
            "stale": True,
            "error": str(exc),
        }

    predicted = predict_location_after_minutes(
        latitude=center_lat,
        longitude=center_lon,
        wind_speed_mps=wind["speed_mps"],
        wind_direction_deg=wind["direction_deg"],
        current_u_mps=current["u_component_mps"],
        current_v_mps=current["v_component_mps"],
        minutes=120,
    )

    message = None
    if messages:
        message = "Using last available data"

    return {
        "status": status,
        "message": message,
        "bbox": bbox,
        "current_location": {
            "latitude": center_lat,
            "longitude": center_lon,
        },
        "predicted_location": {
            "latitude": predicted["latitude"],
            "longitude": predicted["longitude"],
            "eta_minutes": predicted["eta_minutes"],
        },
        "wind": wind,
        "current": current,
        "satellite": {
            "source": satellite.get("source", "unknown"),
            "time_window": satellite.get("time_window", "NOW-1DAYS/NOW"),
            "stale": bool(satellite.get("stale", False)),
            "error": satellite.get("error"),
        },
        "detections": detections,
    }
