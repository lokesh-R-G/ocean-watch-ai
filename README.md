# AI Ocean Plastic Monitoring System (Bay of Bengal)

This workspace now includes a complete full-stack implementation:

- FastAPI backend in `backend/`
- Static frontend dashboard in `frontend-static/`

## Backend (FastAPI)

### Structure

- `backend/detection/` YOLOv8 image detection
- `backend/data/` wind + ocean current API services
- `backend/prediction/` physics-based movement model
- `backend/utils/` config + schemas

### Install

```bash
cd backend
pip install -r requirements.txt
```

Optional environment variables (`backend/.env.example`):

- `OPENWEATHER_API_KEY` (if absent, wind uses real Open-Meteo fallback)
- `SENTINELHUB_CLIENT_ID`
- `SENTINELHUB_CLIENT_SECRET`
- `SENTINELHUB_INSTANCE_ID` (optional)
- `SATELLITE_IMAGE_WIDTH`
- `SATELLITE_IMAGE_HEIGHT`
- `REQUEST_TIMEOUT_SECONDS`
- `WIND_DRAG_FACTOR`
- `EXTERNAL_API_MAX_RETRIES`
- `EXTERNAL_API_BACKOFF_SECONDS`

### Run

```bash
cd backend
uvicorn app:app --reload
```

API endpoint:

- `POST /analyze`

Request JSON:

```json
{
	"bbox": {
		"min_lat": 13.9,
		"max_lat": 16.4,
		"min_lon": 88.7,
		"max_lon": 92.1
	}
}
```

Response JSON:

```json
{
	"status": "ok",
	"message": null,
	"bbox": {"min_lat": 13.9, "max_lat": 16.4, "min_lon": 88.7, "max_lon": 92.1},
	"current_location": {"latitude": 15.15, "longitude": 90.4},
	"predicted_location": {"latitude": 15.001, "longitude": 89.999, "eta_minutes": 120},
	"satellite": {"source": "sentinelhub:SENTINEL2_L2A", "time_window": "NOW-1DAYS/NOW", "stale": false},
	"wind": {"speed_mps": 2.3, "direction_deg": 95.0, "source": "openweather", "stale": false},
	"current": {"u_component_mps": -0.03, "v_component_mps": 0.02, "source": "noaa-erddap:erdQMekm1day", "stale": false},
	"detections": []
}
```

## Frontend (Static)

Uses HTML/CSS/JavaScript + Leaflet map.

### Run

- Open `frontend-static/` using VS Code Live Server, or
- Run:

```bash
cd frontend-static
python -m http.server 5500
```

Open:

- `http://localhost:5500`

The dashboard sends:

- `fetch("http://localhost:8000/analyze", { method: "POST" })`

and visualizes:

- Requested bbox rectangle
- Current location marker
- Predicted location marker
- Detection markers from geo-mapped YOLO outputs
- Predicted trajectory polyline
- Heatmap (plastic density proxy)
- Left/right/bottom panel metrics
