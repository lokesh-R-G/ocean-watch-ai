import { useEffect, useRef } from "react";
import { MapContainer, TileLayer, CircleMarker, Polyline, Tooltip, useMap } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

// Mock plastic cluster data
const plasticClusters = [
  { id: 1, lat: 15.42, lng: 88.77, density: 0.9, size: 450, label: "Cluster Alpha" },
  { id: 2, lat: 14.85, lng: 87.32, density: 0.7, size: 280, label: "Cluster Beta" },
  { id: 3, lat: 16.10, lng: 89.50, density: 0.5, size: 150, label: "Cluster Gamma" },
  { id: 4, lat: 13.50, lng: 86.80, density: 0.3, size: 90, label: "Cluster Delta" },
  { id: 5, lat: 17.20, lng: 90.10, density: 0.6, size: 200, label: "Cluster Epsilon" },
  { id: 6, lat: 12.80, lng: 85.50, density: 0.4, size: 120, label: "Cluster Zeta" },
  { id: 7, lat: 14.20, lng: 89.90, density: 0.8, size: 380, label: "Cluster Eta" },
  { id: 8, lat: 16.80, lng: 87.80, density: 0.35, size: 100, label: "Cluster Theta" },
];

// Heatmap-like zones (larger circles with low opacity)
const heatZones = [
  { lat: 15.0, lng: 88.0, radius: 80000, color: "rgba(239, 68, 68, 0.15)" },
  { lat: 14.5, lng: 87.0, radius: 60000, color: "rgba(250, 204, 21, 0.12)" },
  { lat: 16.5, lng: 89.5, radius: 70000, color: "rgba(250, 204, 21, 0.10)" },
  { lat: 13.0, lng: 86.0, radius: 50000, color: "rgba(59, 130, 246, 0.12)" },
];

// Trajectory line (curved path)
const trajectoryPoints: [number, number][] = [
  [15.42, 88.77],
  [15.44, 88.79],
  [15.46, 88.80],
  [15.47, 88.81],
  [15.48, 88.82],
  [15.49, 88.83],
];

function getDensityColor(density: number): string {
  if (density > 0.7) return "#EF4444";
  if (density > 0.4) return "#FACC15";
  return "#3B82F6";
}

// Custom pulsing markers via DOM
const PulsingMarkers = () => {
  const map = useMap();
  const markersRef = useRef<L.Marker[]>([]);

  useEffect(() => {
    markersRef.current.forEach((m) => m.remove());
    markersRef.current = [];

    plasticClusters.forEach((cluster) => {
      const color = getDensityColor(cluster.density);
      const icon = L.divIcon({
        className: "pulse-marker",
        html: `<div style="
          width: 14px; height: 14px;
          background: ${color};
          border-radius: 50%;
          box-shadow: 0 0 12px ${color}, 0 0 24px ${color}40;
          position: relative;
        "><div style="
          position: absolute; top: 50%; left: 50%;
          width: 100%; height: 100%;
          border-radius: 50%;
          border: 2px solid ${color};
          transform: translate(-50%, -50%);
          animation: pulse-ring 2s cubic-bezier(0.4,0,0.6,1) infinite;
        "></div></div>`,
        iconSize: [14, 14],
        iconAnchor: [7, 7],
      });

      const marker = L.marker([cluster.lat, cluster.lng], { icon })
        .addTo(map)
        .bindTooltip(
          `<div style="
            background: rgba(15,23,42,0.95);
            border: 1px solid rgba(34,211,238,0.3);
            border-radius: 8px;
            padding: 8px 12px;
            font-family: Inter, sans-serif;
            color: #F8FAFC;
            font-size: 11px;
            backdrop-filter: blur(10px);
          ">
            <strong style="color: #22D3EE;">${cluster.label}</strong><br/>
            <span style="font-family: Space Mono, monospace; font-size: 10px; color: #94A3B8;">
              Density: ${(cluster.density * 100).toFixed(0)}% · ${cluster.size} tons
            </span>
          </div>`,
          { direction: "top", offset: [0, -10], className: "custom-tooltip" }
        );

      markersRef.current.push(marker);
    });

    return () => {
      markersRef.current.forEach((m) => m.remove());
    };
  }, [map]);

  return null;
};

const OceanMap = () => {
  return (
    <MapContainer
      center={[14.5, 88.0]}
      zoom={6}
      className="h-full w-full rounded-xl"
      zoomControl={true}
      attributionControl={true}
    >
      <TileLayer
        url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
        attribution='&copy; <a href="https://carto.com/">CARTO</a>'
      />

      {/* Heatmap zones */}
      {heatZones.map((zone, i) => (
        <CircleMarker
          key={`zone-${i}`}
          center={[zone.lat, zone.lng]}
          radius={zone.radius / 2000}
          pathOptions={{
            fillColor: zone.color,
            fillOpacity: 0.4,
            stroke: false,
          }}
        />
      ))}

      {/* Cluster circles with tooltips (backup for non-JS tooltip) */}
      {plasticClusters.map((cluster) => (
        <CircleMarker
          key={cluster.id}
          center={[cluster.lat, cluster.lng]}
          radius={cluster.density * 18 + 4}
          pathOptions={{
            fillColor: getDensityColor(cluster.density),
            fillOpacity: 0.2,
            color: getDensityColor(cluster.density),
            weight: 1,
            opacity: 0.3,
          }}
        >
          <Tooltip>
            <span className="font-mono text-xs">{cluster.label}: {cluster.size} tons</span>
          </Tooltip>
        </CircleMarker>
      ))}

      {/* Trajectory line */}
      <Polyline
        positions={trajectoryPoints}
        pathOptions={{
          color: "#22D3EE",
          weight: 2,
          opacity: 0.7,
          dashArray: "8 6",
        }}
      />

      <PulsingMarkers />
    </MapContainer>
  );
};

export default OceanMap;
