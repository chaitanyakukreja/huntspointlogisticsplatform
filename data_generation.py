"""
Hunts Point Adaptive Logistics Optimization System
==================================================
Synthetic data generation for trucks, hubs, zones, and time slots.
Designed for easy replacement with real GIS data later.
"""

import numpy as np
import pandas as pd
from typing import Dict, Tuple, Any


def set_seed(seed: int = 42) -> None:
    """Set random seed for reproducibility."""
    np.random.seed(seed)


def generate_trucks(n_trucks: int, n_zones: int) -> pd.DataFrame:
    """
    Generate truck fleet with random origin zones.
    Each truck is identified by index and has an origin zone.
    """
    trucks = pd.DataFrame({
        "truck_id": range(n_trucks),
        "origin_zone": np.random.randint(0, n_zones, size=n_trucks),
    })
    return trucks


def generate_hubs(n_hubs: int, n_zones: int, n_slots: int) -> pd.DataFrame:
    """
    Generate charging hubs with:
    - capacity: 10–50 trucks per slot (same for all slots at a hub, or can vary)
    - revenue per truck served
    - zone location (which zone the hub is in)
    """
    hubs = pd.DataFrame({
        "hub_id": range(n_hubs),
        "zone_id": np.random.randint(0, n_zones, size=n_hubs),
        "capacity_per_slot": np.random.randint(10, 51, size=n_hubs),
        "revenue_per_truck": np.round(np.random.uniform(20, 100, size=n_hubs), 2),
    })
    return hubs


def generate_zones(n_zones: int) -> pd.DataFrame:
    """
    Generate zones with pollution level and residential sensitivity (0–1).
    """
    zones = pd.DataFrame({
        "zone_id": range(n_zones),
        "pollution_level": np.round(np.random.uniform(0, 1, size=n_zones), 3),
        "residential_sensitivity": np.round(np.random.uniform(0, 1, size=n_zones), 3),
    })
    return zones


def generate_time_slots(n_slots: int, peak_multiplier: float = 1.0) -> pd.DataFrame:
    """
    Generate time slots with congestion multiplier.
    Peak hours (e.g., 7–9, 17–19) have higher congestion.
    peak_multiplier scales the peak-hour congestion (e.g. 1.5 = 50% more intense).
    """
    # Assume slots 0..23 represent hours 0..23
    hour = np.arange(n_slots)
    # Peak: morning 7–9, evening 17–19
    peak = ((hour >= 7) & (hour <= 9)) | ((hour >= 17) & (hour <= 19))
    base_peak = np.random.uniform(1.2, 2.0, n_slots)
    base_off = np.random.uniform(0.5, 1.0, n_slots)
    congestion = np.where(peak, base_peak * peak_multiplier, base_off)
    time_slots = pd.DataFrame({
        "slot_id": range(n_slots),
        "hour": hour,
        "congestion_multiplier": np.round(congestion, 3),
    })
    return time_slots


def generate_distances(n_zones: int, grid_style: bool = True) -> np.ndarray:
    """
    Generate zone-to-zone distance matrix.
    If grid_style, use approximate grid distances; else random symmetric matrix.
    """
    if grid_style:
        # Place zones on a rough grid and use L1 distance
        side = int(np.ceil(np.sqrt(n_zones)))
        coords = np.array([[i % side, i // side] for i in range(n_zones)])[:n_zones]
        dist = np.zeros((n_zones, n_zones))
        for i in range(n_zones):
            for j in range(n_zones):
                dist[i, j] = np.abs(coords[i] - coords[j]).sum()
        # Scale to something like miles (e.g., 1–10)
        dist = np.round(dist * np.random.uniform(0.5, 2.0, (n_zones, n_zones)), 2)
        # Symmetrize
        dist = (dist + dist.T) / 2
        np.fill_diagonal(dist, 0)
    else:
        dist = np.random.uniform(1, 15, (n_zones, n_zones))
        dist = (dist + dist.T) / 2
        np.fill_diagonal(dist, 0)
    return dist


def generate_all(
    n_trucks: int = 200,
    n_hubs: int = 5,
    n_zones: int = 10,
    n_slots: int = 24,
    seed: int = 42,
    peak_multiplier: float = 1.0,
) -> Dict[str, Any]:
    """
    Generate all synthetic data and return a single dictionary.
    Easy to swap with real data loader later.
    """
    set_seed(seed)
    trucks = generate_trucks(n_trucks, n_zones)
    hubs = generate_hubs(n_hubs, n_zones, n_slots)
    zones = generate_zones(n_zones)
    time_slots = generate_time_slots(n_slots, peak_multiplier=peak_multiplier)
    distances = generate_distances(n_zones)

    return {
        "trucks": trucks,
        "hubs": hubs,
        "zones": zones,
        "time_slots": time_slots,
        "distances": distances,
        "n_trucks": n_trucks,
        "n_hubs": n_hubs,
        "n_zones": n_zones,
        "n_slots": n_slots,
    }


if __name__ == "__main__":
    data = generate_all()
    print("Trucks (first 5):")
    print(data["trucks"].head())
    print("\nHubs:")
    print(data["hubs"])
    print("\nZones:")
    print(data["zones"])
    print("\nTime slots (first 10):")
    print(data["time_slots"].head(10))
    print("\nDistance matrix shape:", data["distances"].shape)
