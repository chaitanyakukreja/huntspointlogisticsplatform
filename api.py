"""
Hunts Point Logistics Platform — FastAPI backend.
Multi-role: drivers, trucking companies, businesses/industrial. Coordination, optimization, energy.
"""

from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from data_generation import generate_all
from model import build_model, HUB_COST, GREEN_ZONE_COST
from solver import solve, extract_results, run_baseline
from geo_utils import (
    build_zones_geojson,
    build_hubs_for_map,
    pollution_per_zone,
    congestion_per_time,
)
from synthetic_network import (
    build_grid_network,
    truck_origin_cells,
    compute_routes,
    network_to_map_data,
)


app = FastAPI(
    title="Hunts Point Logistics Platform",
    description="Coordination & optimization for drivers, companies, and businesses",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class OptimizeRequest(BaseModel):
    num_trucks: int = Field(200, ge=10, le=500)
    num_hubs: int = Field(5, ge=1, le=20)
    budget: float = Field(500, ge=100, le=2000)
    peak_multiplier: float = Field(1.0, ge=0.5, le=3.0)
    with_optimization: bool = Field(True, description="True = run PuLP optimizer, False = baseline")


class OptimizeResponse(BaseModel):
    truck_assignments: List[dict]
    hub_usage: List[dict]
    congestion_per_time: List[dict]
    pollution_per_zone: List[dict]
    green_zones: List[int]
    zones_geojson: dict
    hubs: List[dict]
    status: str
    objective_value: Optional[float]
    n_assigned: int
    artificial_map: Optional[dict] = None
    platform_summary: Optional[dict] = None
    deliveries: Optional[List[dict]] = None
    last_updated: Optional[str] = None


def _build_platform_summary(
    data: Dict[str, Any],
    assignments: List[tuple],
    truck_assignments: List[dict],
    hub_usage: List[dict],
    congestion_per_time_list: List[dict],
    pollution_per_zone_list: List[dict],
    cost_breakdown: Dict[str, float],
    time_slots_df: Any,
    hub_zone: Any,
    green_zones: List[int],
) -> Dict[str, Any]:
    """Build role-friendly summary: coordination, energy, by-zone traffic."""
    n_slots = len(congestion_per_time_list)
    peak_slots = [s for s in range(n_slots) if 7 <= s <= 9 or 17 <= s <= 19]

    # Driver: per-truck energy tip (off-peak = save energy)
    driver_tips = []
    for ta in truck_assignments:
        t, h, s = ta["truck_id"], ta["hub_id"], ta["slot_id"]
        is_off_peak = s not in peak_slots
        tip = (
            f"Charge at Hub {h}, {s}:00. Off-peak — good for energy saving."
            if is_off_peak
            else f"Charge at Hub {h}, {s}:00. Peak hour — consider pre-charging to save energy."
        )
        driver_tips.append({"truck_id": t, "hub_id": h, "slot_id": s, "tip": tip})

    # Business: incoming trucks per zone per slot
    zone_slot_counts: Dict[int, Dict[int, int]] = {}
    for (_, h, s) in assignments:
        z = int(hub_zone[h])
        if z not in zone_slot_counts:
            zone_slot_counts[z] = {}
        zone_slot_counts[z][s] = zone_slot_counts[z].get(s, 0) + 1
    incoming_by_zone = [
        {"zone_id": z, "slot_id": s, "trucks": c}
        for z, slots in zone_slot_counts.items()
        for s, c in slots.items()
    ]

    # Quiet slots (fewest trucks) per zone for business
    quiet_slots = []
    for z in range(data["n_zones"]):
        slot_counts = [d["trucks"] for d in incoming_by_zone if d["zone_id"] == z]
        if not slot_counts:
            quiet_slots.append({"zone_id": z, "suggested_slots": [0, 1, 2]})
        else:
            by_slot = {d["slot_id"]: d["trucks"] for d in incoming_by_zone if d["zone_id"] == z}
            sorted_slots = sorted(range(n_slots), key=lambda s: by_slot.get(s, 0))
            quiet_slots.append({"zone_id": z, "suggested_slots": sorted_slots[:5]})

    return {
        "total_distance": round(cost_breakdown.get("distance_cost", 0), 1),
        "total_congestion_cost": round(cost_breakdown.get("congestion_cost", 0), 1),
        "revenue": round(cost_breakdown.get("revenue", 0), 1),
        "driver_tips": driver_tips,
        "incoming_by_zone": incoming_by_zone,
        "quiet_slots_by_zone": quiet_slots,
        "green_zones": green_zones,
        "n_trucks_assigned": len(assignments),
    }


@app.post("/optimize", response_model=OptimizeResponse)
def optimize(params: OptimizeRequest):
    """Run optimization (or baseline) and return results for map and charts."""
    try:
        # 1. Generate data
        data = generate_all(
            n_trucks=params.num_trucks,
            n_hubs=params.num_hubs,
            n_zones=10,
            n_slots=24,
            seed=42,
            peak_multiplier=params.peak_multiplier,
        )
        n_trucks = data["n_trucks"]

        if params.with_optimization:
            # 2. Build and solve model
            prob = build_model(
                data,
                total_budget=params.budget,
                hub_cost=HUB_COST,
                green_zone_cost=GREEN_ZONE_COST,
            )
            solve(prob, time_limit_seconds=90)
            results = extract_results(prob)
            if results["status"] not in ("Optimal", "Feasible"):
                raise HTTPException(
                    status_code=422,
                    detail=f"Solver status: {results['status']}",
                )
        else:
            results = run_baseline(
                data,
                total_budget=params.budget,
                hub_cost=HUB_COST,
                green_zone_cost=GREEN_ZONE_COST,
                seed=42,
            )

        assignments = results["assignments"]
        utilization_df = results["utilization_df"]
        slot_counts = results["slot_counts"]

        # 3. Build API response
        truck_assignments = [
            {"truck_id": t, "hub_id": h, "slot_id": s}
            for (t, h, s) in assignments
        ]
        hub_agg = utilization_df.groupby("hub_id").agg(
            assigned=("assigned", "sum"),
            capacity=("capacity", "first"),
        ).reset_index()
        hub_usage = [
            {
                "hub_id": int(row["hub_id"]),
                "assigned": int(row["assigned"]),
                "capacity": int(row["capacity"]),
                "utilization_pct": round(100 * row["assigned"] / row["capacity"], 1) if row["capacity"] else 0,
            }
            for _, row in hub_agg.iterrows()
        ]
        congestion_per_time_list = congestion_per_time(slot_counts)
        pollution_per_zone_list = pollution_per_zone(data, assignments)
        zones_geojson = build_zones_geojson(
            data,
            assignments,
            results["green_zones"],
            slot_counts,
        )
        hubs = build_hubs_for_map(data, assignments, utilization_df)

        # 4. Synthetic network and routes for artificial map
        network = build_grid_network(
            rows=12, cols=12,
            n_zones=data["n_zones"],
            n_hubs=data["n_hubs"],
            seed=42,
        )
        origin_zones = data["trucks"]["origin_zone"].values
        truck_origin_cells_list = truck_origin_cells(network, origin_zones, seed=42)
        routes = compute_routes(network, assignments, truck_origin_cells_list)
        artificial_map = network_to_map_data(
            network,
            data["zones"],
            routes,
            results["green_zones"],
        )

        # 5. Platform summary: coordination, energy, role-friendly slices
        cost_breakdown = results.get("cost_breakdown") or {}
        time_slots_df = data["time_slots"]
        hub_zone_arr = data["hubs"]["zone_id"].values
        platform_summary = _build_platform_summary(
            data=data,
            assignments=assignments,
            truck_assignments=truck_assignments,
            hub_usage=hub_usage,
            congestion_per_time_list=congestion_per_time_list,
            pollution_per_zone_list=pollution_per_zone_list,
            cost_breakdown=cost_breakdown,
            time_slots_df=time_slots_df,
            hub_zone=hub_zone_arr,
            green_zones=results["green_zones"],
        )
        origin_zone_by_truck = data["trucks"]["origin_zone"].tolist()
        deliveries = build_deliveries(truck_assignments, origin_zone_by_truck)

        return OptimizeResponse(
            truck_assignments=truck_assignments,
            hub_usage=hub_usage,
            congestion_per_time=congestion_per_time_list,
            pollution_per_zone=pollution_per_zone_list,
            green_zones=results["green_zones"],
            zones_geojson=zones_geojson,
            hubs=hubs,
            status=results["status"],
            objective_value=results.get("objective_value"),
            n_assigned=results["n_assigned"],
            artificial_map=artificial_map,
            platform_summary=platform_summary,
            deliveries=deliveries,
            last_updated=None,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Instant demo: no solver, production-grade synthetic data
from demo_data import build_instant_demo, build_deliveries


@app.get("/demo", response_model=OptimizeResponse)
def get_demo():
    """Return instant synthetic data: deliveries, runs, fleet. No simulation."""
    return OptimizeResponse(**build_instant_demo())


@app.get("/health")
def health():
    return {"status": "ok"}
