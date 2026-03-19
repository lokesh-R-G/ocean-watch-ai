from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from data.ocean_current_service import OceanCurrentServiceError, fetch_ocean_current
from data.satellite_service import SatelliteServiceError, fetch_latest_sentinel2_image
from data.wind_service import WindServiceError, fetch_wind
from detection.yolo_detector import detect_plastic_clusters_from_image, preload_yolo_model
from prediction.movement_model import predict_location_after_minutes
from utils.config import (
    ENABLE_RESPONSE_CACHING,
    OPENWEATHER_API_KEY,
    SENTINELHUB_CLIENT_ID,
    SENTINELHUB_CLIENT_SECRET,
)
from utils.schemas import AnalyzeRequest, AnalyzeResponse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def _validate_env_vars() -> None:
    """Validate required environment variables at startup."""
    logger.info("🔍 Validating environment configuration...")
    
    warnings = []
    
    if not SENTINELHUB_CLIENT_ID or not SENTINELHUB_CLIENT_SECRET:
        warnings.append("⚠️  SENTINELHUB credentials not set - satellite imagery will be unavailable")
    
    if not OPENWEATHER_API_KEY:
        logger.info("ℹ️  OPENWEATHER_API_KEY not set - using Open-Meteo free API (fallback)")
    
    if warnings:
        for warning in warnings:
            logger.warning(warning)
    
    logger.info("✅ Environment validation complete")


# Startup event for preloading YOLO model
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🚀 Starting Ocean Plastic Monitoring API")
    
    try:
        _validate_env_vars()
    except Exception as exc:
        logger.error(f"Environment validation failed: {exc}")
    
    try:
        logger.info("⏳ Preloading YOLO model (this may take 30-60 seconds)...")
        preload_yolo_model()
        logger.info("✅ YOLO model loaded successfully")
    except Exception as exc:
        logger.warning(f"⚠️  Failed to preload YOLO model: {exc}")
    
    logger.info("✅ API startup complete - ready to accept requests")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down Ocean Plastic Monitoring API")

app = FastAPI(
    title="Ocean Plastic Monitoring API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(time.time()))
    start_time = time.time()
    
    logger.info(f"[{request_id}] {request.method} {request.url.path}")
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        logger.info(f"[{request_id}] Status {response.status_code} | {process_time:.2f}s")
        return response
    except Exception as exc:
        process_time = time.time() - start_time
        logger.error(f"[{request_id}] Request failed after {process_time:.2f}s: {exc}")
        raise


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


def _bbox_center(bbox: dict) -> tuple[float, float]:
    lat = (bbox["min_lat"] + bbox["max_lat"]) / 2.0
    lon = (bbox["min_lon"] + bbox["max_lon"]) / 2.0
    return lat, lon


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(payload: AnalyzeRequest):
    request_id = str(time.time())
    logger.info(f"[{request_id}] Analyzing bbox: {payload.bbox.model_dump()}")
    start_time = time.time()
    
    bbox = payload.bbox.model_dump()
    center_lat, center_lon = _bbox_center(bbox)

    status = "ok"
    messages: list[str] = []

    detections: list[dict] = []
    satellite: dict = {
        "source": "unavailable",
        "stale": True,
    }

    # Fetch satellite image
    try:
        logger.info(f"[{request_id}] Fetching Sentinel-2 image...")
        satellite = fetch_latest_sentinel2_image(bbox)
        logger.info(f"[{request_id}] Satellite image fetched: {satellite.get('source')}, stale={satellite.get('stale')}")
    except SatelliteServiceError as exc:
        logger.warning(f"[{request_id}] Satellite service error: {exc}")
        status = "degraded"
        messages.append("Using cached satellite data")
        satellite = {
            "source": "sentinelhub-unavailable",
            "stale": True,
            "error": str(exc),
        }
    except Exception as exc:
        logger.error(f"[{request_id}] Unexpected satellite error: {exc}", exc_info=True)
        status = "degraded"
        messages.append("Using cached satellite data")
        satellite = {
            "source": "sentinelhub-error",
            "stale": True,
            "error": str(exc),
        }

    # Detect clusters
    try:
        if satellite.get("image") is not None:
            logger.info(f"[{request_id}] Running YOLO inference...")
            detections = detect_plastic_clusters_from_image(satellite["image"], geo_bbox=bbox)
            logger.info(f"[{request_id}] YOLO detection complete: {len(detections)} clusters")
        else:
            logger.warning(f"[{request_id}] No satellite image available for detection")
            detections = []
        
        if satellite.get("stale"):
            status = "degraded"
            if "Using cached satellite data" not in messages:
                messages.append("Using cached satellite data")
    except Exception as exc:
        logger.error(f"[{request_id}] Detection error: {exc}", exc_info=True)
        status = "degraded"
        detections = []

    # Fetch wind (parallel ready, but sequential for now)
    wind: dict = {
        "speed_mps": 0.0,
        "direction_deg": 0.0,
        "source": "wind-unavailable",
        "stale": True,
    }
    try:
        logger.info(f"[{request_id}] Fetching wind data...")
        wind = fetch_wind(center_lat, center_lon)
        logger.info(f"[{request_id}] Wind: {wind.get('speed_mps'):.2f} m/s from {wind.get('source')}")
        if wind.get("stale"):
            status = "degraded"
            if "Using cached data" not in messages:
                messages.append("Using cached data")
    except WindServiceError as exc:
        logger.warning(f"[{request_id}] Wind service error: {exc}")
        status = "degraded"
        wind = {
            "speed_mps": 0.0,
            "direction_deg": 0.0,
            "source": "wind-unavailable",
            "stale": True,
            "error": str(exc),
        }

    # Fetch ocean current (parallel ready, but sequential for now)
    current: dict = {
        "u_component_mps": 0.0,
        "v_component_mps": 0.0,
        "speed_mps": 0.0,
        "direction_deg": 0.0,
        "source": "ocean-current-unavailable",
        "stale": True,
    }
    try:
        logger.info(f"[{request_id}] Fetching ocean current data...")
        current = fetch_ocean_current(center_lat, center_lon)
        logger.info(f"[{request_id}] Ocean current: u={current.get('u_component_mps'):.4f}, v={current.get('v_component_mps'):.4f}")
        if current.get("stale"):
            status = "degraded"
            if "Using cached data" not in messages:
                messages.append("Using cached data")
    except OceanCurrentServiceError as exc:
        logger.warning(f"[{request_id}] Ocean current service error: {exc}")
        status = "degraded"
        current = {
            "u_component_mps": 0.0,
            "v_component_mps": 0.0,
            "speed_mps": 0.0,
            "direction_deg": 0.0,
            "source": "ocean-current-unavailable",
            "stale": True,
            "error": str(exc),
        }

    # Predict drift
    predicted = predict_location_after_minutes(
        latitude=center_lat,
        longitude=center_lon,
        wind_speed_mps=wind["speed_mps"],
        wind_direction_deg=wind["direction_deg"],
        current_u_mps=current["u_component_mps"],
        current_v_mps=current["v_component_mps"],
        minutes=120,
    )
    logger.info(f"[{request_id}] Drift prediction: ({predicted['latitude']:.4f}, {predicted['longitude']:.4f})")

    message = None
    if messages:
        message = " | ".join(messages)

    process_time = time.time() - start_time
    logger.info(f"[{request_id}] Analysis complete in {process_time:.2f}s | Status: {status}")

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
