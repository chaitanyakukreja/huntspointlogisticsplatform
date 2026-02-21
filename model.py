"""
Hunts Point Adaptive Logistics Optimization System
==================================================
Optimization model definition using PuLP.
Decision variables: x[t,h,s], y[h], g[z].
Objective: weighted sum of congestion, pollution, distance (min) vs revenue, livability (max).
"""

from typing import Dict, Any
import numpy as np
import pandas as pd
from pulp import (
    LpProblem,
    LpMinimize,
    LpVariable,
    LpBinary,
    lpSum,
    LpStatus,
)

# Default objective weights (minimize congestion, pollution, distance; maximize revenue, livability)
DEFAULT_WEIGHTS = {
    "congestion": 1.0,
    "pollution": 1.5,
    "distance": 1.0,
    "revenue": 2.0,
    "livability": 1.2,
}

# Budget parameters
HUB_COST = 100
GREEN_ZONE_COST = 50
TOTAL_BUDGET = 500


def build_model(
    data: Dict[str, Any],
    weights: Dict[str, float] | None = None,
    total_budget: float | None = None,
    hub_cost: float | None = None,
    green_zone_cost: float | None = None,
) -> LpProblem:
    """
    Build the MIP model from data dictionary.
    Returns the PuLP problem object with variables and constraints set.
    """
    weights = weights or DEFAULT_WEIGHTS
    budget = total_budget if total_budget is not None else TOTAL_BUDGET
    hcost = hub_cost if hub_cost is not None else HUB_COST
    gcost = green_zone_cost if green_zone_cost is not None else GREEN_ZONE_COST
    trucks_df = data["trucks"]
    hubs_df = data["hubs"]
    zones_df = data["zones"]
    time_slots_df = data["time_slots"]
    distances = data["distances"]

    n_trucks = data["n_trucks"]
    n_hubs = data["n_hubs"]
    n_zones = data["n_zones"]
    n_slots = data["n_slots"]

    # Index sets
    T = range(n_trucks)
    H = range(n_hubs)
    S = range(n_slots)
    Z = range(n_zones)

    # Precompute coefficients for objective (so we can use lpSum efficiently)
    # Truck t origin zone
    origin_zone = trucks_df["origin_zone"].values
    # Hub h zone and capacity and revenue
    hub_zone = hubs_df["zone_id"].values
    capacity = hubs_df["capacity_per_slot"].values
    revenue_per_truck = hubs_df["revenue_per_truck"].values
    # Zone pollution and residential sensitivity
    pollution = zones_df["pollution_level"].values
    residential = zones_df["residential_sensitivity"].values
    # Slot congestion
    congestion_mult = time_slots_df["congestion_multiplier"].values

    prob = LpProblem("HuntsPoint_Logistics", LpMinimize)

    # ----- Decision variables -----
    # x[t,h,s] = 1 if truck t is assigned to hub h at time slot s
    x = {}
    for t in T:
        for h in H:
            for s in S:
                x[t, h, s] = LpVariable(f"x_{t}_{h}_{s}", cat=LpBinary)

    # y[h] = 1 if hub h is active
    y = {h: LpVariable(f"y_{h}", cat=LpBinary) for h in H}

    # g[z] = 1 if zone z is selected as green zone
    g = {z: LpVariable(f"g_{z}", cat=LpBinary) for z in Z}

    # ----- Objective: minimize (costs - benefits) -----
    # Congestion cost: sum over t,h,s of x[t,h,s] * congestion_mult[s]
    congestion_expr = lpSum(
        x[t, h, s] * congestion_mult[s] for t in T for h in H for s in S
    )

    # Pollution exposure: truck from zone with pollution, going to hub in zone with residential sensitivity
    # Cost = x[t,h,s] * pollution[origin[t]] * residential[hub_zone[h]]
    pollution_expr = lpSum(
        x[t, h, s] * pollution[origin_zone[t]] * residential[hub_zone[h]]
        for t in T for h in H for s in S
    )

    # Travel distance: x[t,h,s] * distance[origin_zone[t], hub_zone[h]]
    distance_expr = lpSum(
        x[t, h, s] * distances[origin_zone[t], hub_zone[h]]
        for t in T for h in H for s in S
    )

    # Revenue (maximize = minimize negative): - sum x * revenue[h]
    revenue_expr = lpSum(
        x[t, h, s] * revenue_per_truck[h] for t in T for h in H for s in S
    )

    # Livability (maximize = minimize negative): benefit from green zones
    # Livability = sum_z g[z] * (e.g. residential_sensitivity or 1)
    livability_expr = lpSum(g[z] * (1.0 + residential[z]) for z in Z)

    # Weighted objective: minimize cost terms, subtract benefit terms
    prob += (
        weights["congestion"] * congestion_expr
        + weights["pollution"] * pollution_expr
        + weights["distance"] * distance_expr
        - weights["revenue"] * revenue_expr
        - weights["livability"] * livability_expr
    ), "Total_Objective"

    # ----- Constraints -----
    # 1. Each truck assigned exactly once
    for t in T:
        prob += lpSum(x[t, h, s] for h in H for s in S) == 1, f"Assign_once_{t}"

    # 2. Hub capacity per slot: sum_t x[t,h,s] <= capacity[h] * y[h]
    for h in H:
        for s in S:
            prob += (
                lpSum(x[t, h, s] for t in T) <= capacity[h] * y[h],
                f"Capacity_{h}_{s}",
            )

    # 3. Truck can only go to active hubs (x[t,h,s] <= y[h])
    for t in T:
        for h in H:
            for s in S:
                prob += x[t, h, s] <= y[h], f"Active_hub_{t}_{h}_{s}"

    # 4. Budget: sum_h (hub_cost * y[h]) + sum_z (green_zone_cost * g[z]) <= budget
    prob += (
        lpSum(hcost * y[h] for h in H) + lpSum(gcost * g[z] for z in Z)
        <= budget
    ), "Budget"

    # Store variables and problem in a way solver can use
    prob._x = x
    prob._y = y
    prob._g = g
    prob._n_trucks = n_trucks
    prob._n_hubs = n_hubs
    prob._n_zones = n_zones
    prob._n_slots = n_slots
    prob._data = data
    prob._weights = weights

    return prob
