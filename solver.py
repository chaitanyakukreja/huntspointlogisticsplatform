"""
Hunts Point Adaptive Logistics Optimization System
==================================================
Solve the MIP and extract assignments, utilization, and cost breakdown.
"""

from typing import Dict, Any, List, Tuple
import numpy as np
import pandas as pd
from pulp import LpProblem, LpStatus, value


def solve(prob: LpProblem, time_limit_seconds: int | None = None) -> LpProblem:
    """
    Solve the optimization problem. Modifies prob in place.
    Optional time_limit_seconds for large instances.
    """
    if time_limit_seconds is not None:
        prob.solve(timeLimit=time_limit_seconds)
    else:
        prob.solve()
    return prob


def get_assignments(prob: LpProblem) -> List[Tuple[int, int, int]]:
    """Return list of (truck_id, hub_id, slot_id) for each assignment where x[t,h,s]=1."""
    x = prob._x
    assignments = []
    for (t, h, s), var in x.items():
        if var.varValue is not None and var.varValue >= 0.99:
            assignments.append((t, h, s))
    return assignments


def get_active_hubs(prob: LpProblem) -> List[int]:
    """Return list of hub IDs that are active (y[h]=1)."""
    y = prob._y
    return [h for h, var in y.items() if var.varValue is not None and var.varValue >= 0.99]


def get_green_zones(prob: LpProblem) -> List[int]:
    """Return list of zone IDs selected as green zones (g[z]=1)."""
    g = prob._g
    return [z for z, var in g.items() if var.varValue is not None and var.varValue >= 0.99]


def compute_cost_breakdown(prob: LpProblem, assignments: List[Tuple[int, int, int]]) -> Dict[str, float]:
    """
    Compute total congestion cost, pollution cost, distance cost, revenue, and livability
    from the solution (using assignment list and prob._data).
    """
    data = prob._data
    weights = prob._weights
    trucks_df = data["trucks"]
    hubs_df = data["hubs"]
    zones_df = data["zones"]
    time_slots_df = data["time_slots"]
    distances = data["distances"]

    origin_zone = trucks_df["origin_zone"].values
    hub_zone = hubs_df["zone_id"].values
    revenue_per_truck = hubs_df["revenue_per_truck"].values
    pollution = zones_df["pollution_level"].values
    residential = zones_df["residential_sensitivity"].values
    congestion_mult = time_slots_df["congestion_multiplier"].values

    congestion_cost = 0.0
    pollution_cost = 0.0
    distance_cost = 0.0
    revenue = 0.0

    for (t, h, s) in assignments:
        congestion_cost += congestion_mult[s]
        pollution_cost += pollution[origin_zone[t]] * residential[hub_zone[h]]
        distance_cost += distances[origin_zone[t], hub_zone[h]]
        revenue += revenue_per_truck[h]

    green_zones = get_green_zones(prob)
    livability = sum(1.0 + residential[z] for z in green_zones)

    return {
        "congestion_cost": congestion_cost,
        "pollution_cost": pollution_cost,
        "distance_cost": distance_cost,
        "revenue": revenue,
        "livability": livability,
        "weighted_congestion": weights["congestion"] * congestion_cost,
        "weighted_pollution": weights["pollution"] * pollution_cost,
        "weighted_distance": weights["distance"] * distance_cost,
        "weighted_revenue": weights["revenue"] * revenue,
        "weighted_livability": weights["livability"] * livability,
    }


def hub_utilization(prob: LpProblem, assignments: List[Tuple[int, int, int]]) -> pd.DataFrame:
    """
    For each hub and slot, count assigned trucks and capacity.
    Returns DataFrame with hub_id, slot_id, assigned, capacity, utilization_pct.
    """
    data = prob._data
    n_hubs = prob._n_hubs
    n_slots = prob._n_slots
    capacity = data["hubs"]["capacity_per_slot"].values

    # Count assignments per (hub, slot)
    count = np.zeros((n_hubs, n_slots))
    for (t, h, s) in assignments:
        count[h, s] += 1

    rows = []
    for h in range(n_hubs):
        for s in range(n_slots):
            cap = capacity[h]
            assigned = count[h, s]
            util = (assigned / cap * 100) if cap > 0 else 0
            rows.append({
                "hub_id": h,
                "slot_id": s,
                "assigned": int(assigned),
                "capacity": cap,
                "utilization_pct": round(util, 1),
            })
    return pd.DataFrame(rows)


def slot_congestion_distribution(assignments: List[Tuple[int, int, int]], n_slots: int) -> np.ndarray:
    """Return per-slot truck counts (for congestion distribution plot)."""
    counts = np.zeros(n_slots)
    for (_, _, s) in assignments:
        counts[s] += 1
    return counts


def compute_cost_breakdown_from_assignments(
    data: Dict[str, Any],
    assignments: List[Tuple[int, int, int]],
    green_zones: List[int],
    weights: Dict[str, float],
) -> Dict[str, float]:
    """Compute cost breakdown from assignment list (no prob object). Used for baseline."""
    trucks_df = data["trucks"]
    hubs_df = data["hubs"]
    zones_df = data["zones"]
    time_slots_df = data["time_slots"]
    distances = data["distances"]
    origin_zone = trucks_df["origin_zone"].values
    hub_zone = hubs_df["zone_id"].values
    revenue_per_truck = hubs_df["revenue_per_truck"].values
    pollution = zones_df["pollution_level"].values
    residential = zones_df["residential_sensitivity"].values
    congestion_mult = time_slots_df["congestion_multiplier"].values

    congestion_cost = pollution_cost = distance_cost = revenue = 0.0
    for (t, h, s) in assignments:
        congestion_cost += congestion_mult[s]
        pollution_cost += pollution[origin_zone[t]] * residential[hub_zone[h]]
        distance_cost += distances[origin_zone[t], hub_zone[h]]
        revenue += revenue_per_truck[h]
    livability = sum(1.0 + residential[z] for z in green_zones)

    return {
        "congestion_cost": congestion_cost,
        "pollution_cost": pollution_cost,
        "distance_cost": distance_cost,
        "revenue": revenue,
        "livability": livability,
        "weighted_congestion": weights["congestion"] * congestion_cost,
        "weighted_pollution": weights["pollution"] * pollution_cost,
        "weighted_distance": weights["distance"] * distance_cost,
        "weighted_revenue": weights["revenue"] * revenue,
        "weighted_livability": weights["livability"] * livability,
    }


def run_baseline(
    data: Dict[str, Any],
    total_budget: float = 500,
    hub_cost: float = 100,
    green_zone_cost: float = 50,
    seed: int = 0,
) -> Dict[str, Any]:
    """
    Baseline assignment without optimization: activate hubs/green zones by budget,
    then assign trucks greedily to (hub, slot). Returns same shape as extract_results.
    """
    import random
    rng = random.Random(seed)
    n_trucks = data["n_trucks"]
    n_hubs = data["n_hubs"]
    n_zones = data["n_zones"]
    n_slots = data["n_slots"]
    capacity = data["hubs"]["capacity_per_slot"].values
    residential = data["zones"]["residential_sensitivity"].values

    # Decide active hubs and green zones by budget (simple: max hubs, rest green)
    n_active_hubs = min(n_hubs, int(total_budget // hub_cost))
    budget_left = total_budget - n_active_hubs * hub_cost
    n_green = min(n_zones, max(0, int(budget_left // green_zone_cost)))
    active_hubs = list(range(n_active_hubs))
    green_zones = list(range(n_green))  # first n_green zones as green

    # Per-slot capacity remaining: (hub, slot) -> remaining
    cap_remaining = {(h, s): capacity[h] for h in active_hubs for s in range(n_slots)}
    assignments: List[Tuple[int, int, int]] = []
    truck_order = list(range(n_trucks))
    rng.shuffle(truck_order)

    for t in truck_order:
        options = [(h, s) for h in active_hubs for s in range(n_slots) if cap_remaining[h, s] > 0]
        if not options:
            break
        h, s = rng.choice(options)
        assignments.append((t, h, s))
        cap_remaining[h, s] -= 1

    weights = {
        "congestion": 1.0,
        "pollution": 1.5,
        "distance": 1.0,
        "revenue": 2.0,
        "livability": 1.2,
    }
    cost_breakdown = compute_cost_breakdown_from_assignments(data, assignments, green_zones, weights)
    utilization_df = hub_utilization_from_assignments(data, assignments)
    slot_counts = slot_congestion_distribution(assignments, n_slots)
    obj = (
        cost_breakdown["weighted_congestion"] + cost_breakdown["weighted_pollution"]
        + cost_breakdown["weighted_distance"]
        - cost_breakdown["weighted_revenue"] - cost_breakdown["weighted_livability"]
    )
    return {
        "status": "Baseline",
        "objective_value": obj,
        "assignments": assignments,
        "active_hubs": active_hubs,
        "green_zones": green_zones,
        "cost_breakdown": cost_breakdown,
        "utilization_df": utilization_df,
        "slot_counts": slot_counts,
        "n_assigned": len(assignments),
    }


def hub_utilization_from_assignments(data: Dict[str, Any], assignments: List[Tuple[int, int, int]]) -> pd.DataFrame:
    """Hub utilization table from assignment list (no prob)."""
    n_hubs = data["n_hubs"]
    n_slots = data["n_slots"]
    capacity = data["hubs"]["capacity_per_slot"].values
    count = np.zeros((n_hubs, n_slots))
    for (_, h, s) in assignments:
        count[h, s] += 1
    rows = []
    for h in range(n_hubs):
        for s in range(n_slots):
            cap = capacity[h]
            assigned = int(count[h, s])
            util = (assigned / cap * 100) if cap > 0 else 0
            rows.append({"hub_id": h, "slot_id": s, "assigned": assigned, "capacity": cap, "utilization_pct": round(util, 1)})
    return pd.DataFrame(rows)


def extract_results(prob: LpProblem) -> Dict[str, Any]:
    """
    Full result extraction: status, assignments, active hubs, green zones,
    cost breakdown, hub utilization DataFrame, and slot counts.
    """
    status = LpStatus[prob.status]
    assignments = get_assignments(prob)
    active_hubs = get_active_hubs(prob)
    green_zones = get_green_zones(prob)
    cost_breakdown = compute_cost_breakdown(prob, assignments) if assignments else {}
    utilization_df = hub_utilization(prob, assignments)
    slot_counts = slot_congestion_distribution(assignments, prob._n_slots)
    objective_value = value(prob.objective) if prob.objective else None

    return {
        "status": status,
        "objective_value": objective_value,
        "assignments": assignments,
        "active_hubs": active_hubs,
        "green_zones": green_zones,
        "cost_breakdown": cost_breakdown,
        "utilization_df": utilization_df,
        "slot_counts": slot_counts,
        "n_assigned": len(assignments),
    }
