from __future__ import annotations

import base64
from typing import Any

import cv2
import numpy as np
from ultralytics import YOLO


PLASTIC_PROXY_LABELS = {
    "bottle",
    "cup",
    "wine glass",
    "bowl",
    "fork",
    "knife",
    "spoon",
    "toothbrush",
    "cell phone",
}

_model: YOLO | None = None


def _get_model() -> YOLO:
    global _model
    if _model is None:
        _model = YOLO("yolov8n.pt")
    return _model


def preload_yolo_model() -> None:
    """Preload YOLO model at application startup to avoid cold-start delay."""
    _ = _get_model()
    # Run a dummy inference to warm up the model
    import numpy as np
    dummy_image = np.zeros((256, 256, 3), dtype=np.uint8)
    model = _get_model()
    _ = model.predict(source=dummy_image, conf=0.2, verbose=False)


def _decode_image(image_base64: str) -> np.ndarray:
    payload = image_base64.split(",", 1)[-1]
    image_bytes = base64.b64decode(payload)
    image_np = np.frombuffer(image_bytes, dtype=np.uint8)
    decoded = cv2.imdecode(image_np, cv2.IMREAD_COLOR)
    if decoded is None:
        raise ValueError("Unable to decode base64 image")
    return decoded


def _pixel_to_geo(x: float, y: float, width: int, height: int, bbox: dict[str, float]) -> tuple[float, float]:
    lat_span = bbox["max_lat"] - bbox["min_lat"]
    lon_span = bbox["max_lon"] - bbox["min_lon"]

    latitude = bbox["max_lat"] - (y / max(height, 1)) * lat_span
    longitude = bbox["min_lon"] + (x / max(width, 1)) * lon_span
    return latitude, longitude


def detect_plastic_clusters_from_image(image: np.ndarray, geo_bbox: dict[str, float] | None = None) -> list[dict[str, Any]]:
    model = _get_model()
    results = model.predict(source=image, conf=0.2, verbose=False)

    detections: list[dict[str, Any]] = []
    image_height, image_width = image.shape[:2]

    for result in results:
        names = result.names
        for box in result.boxes:
            class_id = int(box.cls[0].item())
            label = names[class_id]
            confidence = float(box.conf[0].item())
            x1, y1, x2, y2 = [float(v) for v in box.xyxy[0].tolist()]

            if label not in PLASTIC_PROXY_LABELS:
                continue

            center_x = (x1 + x2) / 2.0
            center_y = (y1 + y2) / 2.0

            detection: dict[str, Any] = {
                "label": label,
                "confidence": round(confidence, 4),
                "bbox": [round(x1, 2), round(y1, 2), round(x2, 2), round(y2, 2)],
            }

            if geo_bbox is not None:
                center_lat, center_lon = _pixel_to_geo(center_x, center_y, image_width, image_height, geo_bbox)
                detection["center"] = {
                    "latitude": round(center_lat, 6),
                    "longitude": round(center_lon, 6),
                }

            detections.append(detection)

    return detections


def detect_plastic_clusters(image_base64: str | None) -> list[dict[str, Any]]:
    if not image_base64:
        return []

    image = _decode_image(image_base64)
    return detect_plastic_clusters_from_image(image)
