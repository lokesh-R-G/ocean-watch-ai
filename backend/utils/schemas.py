from pydantic import BaseModel, Field


class BBox(BaseModel):
    min_lat: float = Field(ge=-90.0, le=90.0)
    max_lat: float = Field(ge=-90.0, le=90.0)
    min_lon: float = Field(ge=-180.0, le=180.0)
    max_lon: float = Field(ge=-180.0, le=180.0)


class AnalyzeRequest(BaseModel):
    bbox: BBox


class Location(BaseModel):
    latitude: float
    longitude: float


class PredictedLocation(Location):
    eta_minutes: int


class Detection(BaseModel):
    label: str
    confidence: float
    bbox: list[float]
    center: Location | None = None


class AnalyzeResponse(BaseModel):
    status: str = "ok"
    message: str | None = None
    bbox: BBox
    current_location: Location
    predicted_location: PredictedLocation
    wind: dict
    current: dict
    satellite: dict
    detections: list[Detection]
