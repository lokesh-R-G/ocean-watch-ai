const BAY_OF_BENGAL = [15.0, 90.0];
const map = L.map('map').setView(BAY_OF_BENGAL, 5);
const MAX_BBOX_AREA_DEG2 = 25;

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  maxZoom: 18,
  attribution: '&copy; OpenStreetMap contributors',
}).addTo(map);

let currentMarker = L.marker(BAY_OF_BENGAL).addTo(map).bindPopup('Current location');
let predictedMarker = L.marker(BAY_OF_BENGAL).addTo(map).bindPopup('Predicted location (+120 min)');
let trajectoryLine = L.polyline([BAY_OF_BENGAL, BAY_OF_BENGAL], { color: '#18a6d9', weight: 3 }).addTo(map);
let heatLayer = L.heatLayer([[...BAY_OF_BENGAL, 0.3]], { radius: 35, blur: 20, maxZoom: 10 }).addTo(map);
let requestedBboxRect = null;
const detectionLayer = L.layerGroup().addTo(map);

function setStatus(text) {
  document.getElementById('status').textContent = text;
}

function getBboxFromMap() {
  const bounds = map.getBounds();

  const bbox = {
    min_lat: Number(bounds.getSouth().toFixed(6)),
    max_lat: Number(bounds.getNorth().toFixed(6)),
    min_lon: Number(bounds.getWest().toFixed(6)),
    max_lon: Number(bounds.getEast().toFixed(6)),
  };

  const latSpan = bbox.max_lat - bbox.min_lat;
  const lonSpan = bbox.max_lon - bbox.min_lon;
  const area = latSpan * lonSpan;

  if (area > MAX_BBOX_AREA_DEG2) {
    alert('Region too large, please zoom in');
    return null;
  }

  return bbox;
}

function renderRequestedBbox(bbox) {
  if (requestedBboxRect) {
    map.removeLayer(requestedBboxRect);
  }

  requestedBboxRect = L.rectangle(
    [
      [bbox.min_lat, bbox.min_lon],
      [bbox.max_lat, bbox.max_lon],
    ],
    {
      color: '#00ffd1',
      weight: 2,
      fillOpacity: 0.04,
    }
  ).addTo(map);
}

function updateUI(payload) {
  const status = payload.status || 'ok';
  const message = payload.message || '';
  const bbox = payload.bbox;
  const current = payload.current_location;
  const predicted = payload.predicted_location;
  const wind = payload.wind;
  const ocean = payload.current;
  const detections = payload.detections || [];

  if (bbox) {
    renderRequestedBbox(bbox);
  }

  currentMarker.setLatLng([current.latitude, current.longitude]);
  predictedMarker.setLatLng([predicted.latitude, predicted.longitude]);
  trajectoryLine.setLatLngs([
    [current.latitude, current.longitude],
    [predicted.latitude, predicted.longitude],
  ]);

  detectionLayer.clearLayers();

  const heatPoints = [];
  detections.forEach((detection) => {
    const center = detection.center;
    if (center && Number.isFinite(center.latitude) && Number.isFinite(center.longitude)) {
      const marker = L.circleMarker([center.latitude, center.longitude], {
        radius: 5,
        color: '#ff7f50',
        fillColor: '#ff7f50',
        fillOpacity: 0.85,
        weight: 1,
      }).bindPopup(`${detection.label} (${(detection.confidence * 100).toFixed(1)}%)`);

      detectionLayer.addLayer(marker);
      heatPoints.push([center.latitude, center.longitude, Math.max(0.1, detection.confidence)]);
    }
  });

  const densityScore = detections.length > 0 ? Math.min(1, detections.length / 10) : 0.05;
  if (heatPoints.length > 0) {
    heatLayer.setLatLngs(heatPoints);
  } else {
    heatLayer.setLatLngs([[current.latitude, current.longitude, densityScore]]);
  }

  document.getElementById('densityScore').textContent = densityScore.toFixed(2);
  document.getElementById('clusterCount').textContent = String(detections.length);
  document.getElementById('selectedLat').textContent = current.latitude.toFixed(4);
  document.getElementById('selectedLon').textContent = current.longitude.toFixed(4);
  document.getElementById('windSpeed').textContent = Number(wind.speed_mps).toFixed(2);
  document.getElementById('windDirection').textContent = Number(wind.direction_deg).toFixed(1);
  document.getElementById('windSource').textContent = wind.source || '-';

  document.getElementById('currentCoord').textContent = `${current.latitude.toFixed(4)}, ${current.longitude.toFixed(4)}`;
  document.getElementById('predictedCoord').textContent = `${predicted.latitude.toFixed(4)}, ${predicted.longitude.toFixed(4)}`;
  document.getElementById('uvComponents').textContent = `${Number(ocean.u_component_mps).toFixed(4)}, ${Number(ocean.v_component_mps).toFixed(4)}`;
  document.getElementById('currentSource').textContent = ocean.source || '-';

  if (status === 'degraded' && message) {
    setStatus(`Degraded: ${message}`);
  } else {
    setStatus('Analysis complete');
  }
}

async function analyze() {
  const bbox = getBboxFromMap();
  if (!bbox) {
    return;
  }

  const payload = {
    bbox,
  };

  setStatus('Analyzing...');
  try {
    const response = await fetch('http://localhost:8000/analyze', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const errorBody = await response.text();
      throw new Error(`Backend error ${response.status}: ${errorBody}`);
    }

    const result = await response.json();
    updateUI(result);
  } catch (error) {
    console.error(error);
    setStatus(`Error: ${error.message}`);
  }
}

document.getElementById('analyzeBtn').addEventListener('click', analyze);
