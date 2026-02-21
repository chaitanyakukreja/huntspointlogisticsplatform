"""
Instant demo payload for Hunts Point Logistics Platform.
No solver — production-grade synthetic deliveries and runs.
"""

from typing import Any, Dict, List
import random
from datetime import datetime, timezone

# Synthetic names for production feel
ORIGIN_NAMES = [
    "Bronx Produce Co.", "Hunts Point Terminal", "Fresh Direct Depot",
    "Metro Fresh Market", "Southern Blvd Warehouse", "Food Center Drive",
    "Barreto Point Distribution", "Lafayette Ave Depot", "Oak Point Terminal",
    "Bruckner Blvd Logistics",
]
HUB_NAMES = [
    "Hub 1 — Hunts Point Charging", "Hub 2 — Food Center", "Hub 3 — Oak Point",
    "Hub 4 — Lafayette",
]
DRIVER_FIRST = ["Mike", "Carlos", "James", "Maria", "David", "Ana", "Jose", "Lisa", "Robert", "Yuki"]
DRIVER_LAST = ["Smith", "Garcia", "Chen", "Williams", "Rodriguez", "Martinez", "Lee", "Brown", "Davis", "Wilson"]

def _driver_name(truck_id: int) -> str:
    i, j = truck_id % len(DRIVER_FIRST), truck_id % len(DRIVER_LAST)
    return f"{DRIVER_FIRST[i]} {DRIVER_LAST[j]}"

def build_deliveries(truck_assignments: List[Dict], origin_zone_by_truck: List[int]) -> List[Dict]:
    """Build delivery records with from/to, driver, status for UI."""
    out = []
    statuses = ["scheduled", "en_route", "at_hub", "completed"]
    for i, ta in enumerate(truck_assignments):
        t = ta["truck_id"]
        h = ta["hub_id"]
        s = ta["slot_id"]
        z = origin_zone_by_truck[t] if t < len(origin_zone_by_truck) else t % 10
        from_name = ORIGIN_NAMES[z % len(ORIGIN_NAMES)]
        to_name = HUB_NAMES[h % len(HUB_NAMES)]
        status = statuses[i % len(statuses)] if i < 60 else "scheduled"
        out.append({
            "delivery_id": f"D-{1000 + i}",
            "truck_id": t,
            "driver_id": t,
            "driver_name": _driver_name(t),
            "from_zone_id": z,
            "from_address": from_name,
            "to_hub_id": h,
            "to_address": to_name,
            "scheduled_slot": s,
            "scheduled_time": f"{s:02d}:00",
            "status": status,
        })
    return out

def build_instant_demo() -> Dict[str, Any]:
    """Build full demo response without running the optimizer. Instant."""
    n_trucks = 48
    n_hubs = 4
    n_zones = 10
    n_slots = 24
    random.seed(42)
    origin_zone_by_truck = [random.randint(0, n_zones - 1) for _ in range(n_trucks)]
    # Assign each truck to a hub and slot (spread across hubs and slots)
    truck_assignments = []
    for t in range(n_trucks):
        h = t % n_hubs
        s = (t * 7) % n_slots  # spread over day
        truck_assignments.append({"truck_id": t, "hub_id": h, "slot_id": s})

    hub_capacity = [20, 18, 22, 16]
    hub_usage = [
        {"hub_id": h, "assigned": sum(1 for a in truck_assignments if a["hub_id"] == h), "capacity": hub_capacity[h], "utilization_pct": round(100 * sum(1 for a in truck_assignments if a["hub_id"] == h) / hub_capacity[h], 1)}
        for h in range(n_hubs)
    ]
    slot_counts = [0] * n_slots
    for a in truck_assignments:
        slot_counts[a["slot_id"]] += 1
    congestion_per_time = [{"slot_id": s, "hour": s, "trucks": slot_counts[s]} for s in range(n_slots)]
    zone_truck_count = [0] * n_zones
    for a in truck_assignments:
        z = origin_zone_by_truck[a["truck_id"]]
        zone_truck_count[z] += 1
    pollution_per_zone = [
        {"zone_id": z, "pollution_level": round(0.2 + 0.6 * (z / n_zones), 3), "truck_count": zone_truck_count[z]}
        for z in range(n_zones)
    ]
    green_zones = [0, 2, 5, 7]
    # Minimal zones_geojson
    from geo_utils import zone_grid_cells
    polygons = zone_grid_cells(n_zones)
    features = []
    for z in range(n_zones):
        features.append({
            "type": "Feature",
            "geometry": {"type": "Polygon", "coordinates": [polygons[z]]},
            "properties": {"zone_id": z, "pollution": 0.5, "congestion": zone_truck_count[z], "is_green": z in green_zones},
        })
    zones_geojson = {"type": "FeatureCollection", "features": features}
    hub_zone = [0, 1, 2, 3]
    hubs = []
    for h in range(n_hubs):
        c = zone_grid_cells(n_zones)[hub_zone[h]]
        cx = (c[0][0] + c[2][0]) / 2
        cy = (c[0][1] + c[2][1]) / 2
        hubs.append({"hub_id": h, "zone_id": hub_zone[h], "lon": cx, "lat": cy, "usage": hub_usage[h]["assigned"]})

    # Minimal artificial_map
    rows, cols = 12, 12
    zone_grid = [[(i * 3 + j) % n_zones for j in range(cols)] for i in range(rows)]
    zone_cells = {z: [] for z in range(n_zones)}
    for i in range(rows):
        for j in range(cols):
            z = zone_grid[i][j]
            zone_cells[z].append({"i": i, "j": j, "x": (j + 0.5) / cols, "y": (i + 0.5) / rows})
    hub_cells = [(2, 2), (2, 9), (9, 2), (9, 9)]
    routes = []
    for a in truck_assignments:
        r0, c0 = 1 + (a["truck_id"] % 10), 1 + (a["truck_id"] % 8)
        rh, ch = hub_cells[a["hub_id"]]
        path = []
        while (r0, c0) != (rh, ch):
            path.append({"x": (c0 + 0.5) / cols, "y": (r0 + 0.5) / rows})
            if r0 < rh: r0 += 1
            elif r0 > rh: r0 -= 1
            elif c0 < ch: c0 += 1
            else: c0 -= 1
        path.append({"x": (ch + 0.5) / cols, "y": (rh + 0.5) / rows})
        routes.append(path)
    zone_meta = [{"zone_id": z, "pollution": 0.3 + 0.5 * (z / n_zones), "is_green": z in green_zones} for z in range(n_zones)]
    artificial_map = {
        "rows": rows, "cols": cols, "zone_cells": zone_cells, "zone_meta": zone_meta,
        "hubs": [{"hub_id": h, "row": hub_cells[h][0], "col": hub_cells[h][1], "x": (hub_cells[h][1] + 0.5) / cols, "y": (hub_cells[h][0] + 0.5) / rows} for h in range(n_hubs)],
        "routes": routes,
    }

    # Platform summary
    driver_tips = []
    peak = {7, 8, 9, 17, 18, 19}
    for ta in truck_assignments:
        t, h, s = ta["truck_id"], ta["hub_id"], ta["slot_id"]
        tip = f"Charge at {HUB_NAMES[h]}, {s:02d}:00. Off-peak — good for energy saving." if s not in peak else f"Charge at {HUB_NAMES[h]}, {s:02d}:00. Peak hour — consider pre-charging."
        driver_tips.append({"truck_id": t, "hub_id": h, "slot_id": s, "tip": tip})
    zone_slot_counts: Dict[int, Dict[int, int]] = {}
    for a in truck_assignments:
        z = hub_zone[a["hub_id"]]
        s = a["slot_id"]
        if z not in zone_slot_counts:
            zone_slot_counts[z] = {}
        zone_slot_counts[z][s] = zone_slot_counts[z].get(s, 0) + 1
    incoming_by_zone = [{"zone_id": z, "slot_id": s, "trucks": c} for z, slots in zone_slot_counts.items() for s, c in slots.items()]
    quiet_slots_by_zone = []
    for z in range(n_zones):
        by_slot = {d["slot_id"]: d["trucks"] for d in incoming_by_zone if d["zone_id"] == z}
        sorted_slots = sorted(range(n_slots), key=lambda s: by_slot.get(s, 0))
        quiet_slots_by_zone.append({"zone_id": z, "suggested_slots": sorted_slots[:5]})
    total_distance = sum(3 + (a["truck_id"] % 5) for a in truck_assignments) * 2.5
    platform_summary = {
        "total_distance": round(total_distance, 1),
        "total_congestion_cost": round(sum(slot_counts) * 1.2, 1),
        "revenue": round(len(truck_assignments) * 85, 1),
        "driver_tips": driver_tips,
        "incoming_by_zone": incoming_by_zone,
        "quiet_slots_by_zone": quiet_slots_by_zone,
        "green_zones": green_zones,
        "n_trucks_assigned": len(truck_assignments),
    }

    deliveries = build_deliveries(truck_assignments, origin_zone_by_truck)

    return {
        "truck_assignments": truck_assignments,
        "hub_usage": hub_usage,
        "congestion_per_time": congestion_per_time,
        "pollution_per_zone": pollution_per_zone,
        "green_zones": green_zones,
        "zones_geojson": zones_geojson,
        "hubs": hubs,
        "status": "Optimal",
        "objective_value": -12000.0,
        "n_assigned": len(truck_assignments),
        "artificial_map": artificial_map,
        "platform_summary": platform_summary,
        "deliveries": deliveries,
        "last_updated": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
