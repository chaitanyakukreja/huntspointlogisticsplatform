"""
Generate GeoJSON and coordinates for zones and hubs (synthetic).
Uses a fixed bbox so the same zone layout is consistent for the frontend.
"""

from typing import Dict, Any, List
import numpy as np
import json

# Rough Hunts Point, Bronx NYC bbox (lon, lat)
DEFAULT_BBOX = [-73.89, 40.81, -73.87, 40.83]


def zone_grid_cells(n_zones: int, bbox: List[float] | None = None) -> List[List[List[float]]]:
    """Return list of polygon rings (lon,lat) for each zone as a grid. Each ring is closed."""
    bbox = bbox or DEFAULT_BBOX
    west, south, east, north = bbox
    side = int(np.ceil(np.sqrt(n_zones)))
    dx = (east - west) / side
    dy = (north - south) / side
    polygons = []
    for i in range(n_zones):
        col, row = i % side, i // side
        x0 = west + col * dx
        y0 = south + row * dy
        x1 = x0 + dx
        y1 = y0 + dy
        # GeoJSON: first and last point same (closed ring)
        ring = [
            [x0, y0], [x1, y0], [x1, y1], [x0, y1], [x0, y0]
        ]
        polygons.append(ring)
    return polygons


def zone_centroid(ring: List[List[float]]) -> List[float]:
    """Lon, lat of polygon centroid (simple box = center)."""
    xs = [p[0] for p in ring[:-1]]
    ys = [p[1] for p in ring[:-1]]
    return [float(np.mean(xs)), float(np.mean(ys))]


def build_zones_geojson(
    data: Dict[str, Any],
    assignments: List[tuple],
    green_zones: List[int],
    slot_counts: np.ndarray,
) -> Dict[str, Any]:
    """
    Build GeoJSON FeatureCollection for zones with properties:
    zone_id, pollution, congestion (truck activity), is_green.
    """
    zones_df = data["zones"]
    hubs_df = data["hubs"]
    n_zones = data["n_zones"]
    n_slots = data["n_slots"]
    polygons = zone_grid_cells(n_zones)
    green_set = set(green_zones)

    # Congestion per zone: sum of trucks whose hub is in this zone, weighted by slot congestion
    # We don't have per-zone congestion in time; we use slot_counts for time and zone pollution for map
    hub_zone = hubs_df["zone_id"].values
    zone_truck_count = np.zeros(n_zones)
    for (_, h, _) in assignments:
        z = hub_zone[h]
        zone_truck_count[z] += 1

    features = []
    for z in range(n_zones):
        ring = polygons[z]
        pollution = float(zones_df.loc[zones_df["zone_id"] == z, "pollution_level"].iloc[0])
        congestion = float(zone_truck_count[z])  # trucks assigned to hubs in this zone
        features.append({
            "type": "Feature",
            "geometry": {"type": "Polygon", "coordinates": [ring]},
            "properties": {
                "zone_id": z,
                "pollution": round(pollution, 3),
                "congestion": int(congestion),
                "is_green": z in green_set,
            },
        })
    return {"type": "FeatureCollection", "features": features}


def build_hubs_for_map(
    data: Dict[str, Any],
    assignments: List[tuple],
    utilization_df: Any,
) -> List[Dict[str, Any]]:
    """Return list of { hub_id, zone_id, lat, lon, usage } for map. usage = total trucks."""
    hubs_df = data["hubs"]
    n_zones = data["n_zones"]
    polygons = zone_grid_cells(n_zones)
    hub_zone = hubs_df["zone_id"].values
    usage = utilization_df.groupby("hub_id")["assigned"].sum().to_dict()
    out = []
    for h in range(data["n_hubs"]):
        z = int(hub_zone[h])
        centroid = zone_centroid(polygons[z])
        out.append({
            "hub_id": h,
            "zone_id": z,
            "lon": centroid[0],
            "lat": centroid[1],
            "usage": int(usage.get(h, 0)),
        })
    return out


def pollution_per_zone(data: Dict[str, Any], assignments: List[tuple]) -> List[Dict[str, Any]]:
    """Return list of { zone_id, pollution_level, truck_count } for charts."""
    zones_df = data["zones"]
    hubs_df = data["hubs"]
    n_zones = data["n_zones"]
    hub_zone = hubs_df["zone_id"].values
    zone_truck_count = np.zeros(n_zones)
    for (_, h, _) in assignments:
        zone_truck_count[hub_zone[h]] += 1
    out = []
    for z in range(n_zones):
        pl = float(zones_df.loc[zones_df["zone_id"] == z, "pollution_level"].iloc[0])
        out.append({"zone_id": z, "pollution_level": round(pl, 3), "truck_count": int(zone_truck_count[z])})
    return out


def congestion_per_time(slot_counts: np.ndarray) -> List[Dict[str, Any]]:
    """Return list of { slot_id, hour, trucks } for charts."""
    return [{"slot_id": s, "hour": s, "trucks": int(slot_counts[s])} for s in range(len(slot_counts))]
