"""
Hunts Point Adaptive Logistics Optimization System
==================================================
Entry point: generate data, build model, solve, print results, and optionally visualize.
"""

import argparse
from data_generation import generate_all
from model import build_model, DEFAULT_WEIGHTS, HUB_COST, GREEN_ZONE_COST, TOTAL_BUDGET
from solver import solve, extract_results


def print_results(data: dict, results: dict) -> None:
    """Print truck assignments, hub utilization, green zones, and cost breakdown."""
    print("\n" + "=" * 60)
    print("HUNTS POINT ADAPTIVE LOGISTICS — OPTIMIZATION RESULTS")
    print("=" * 60)

    print("\n--- Solver status ---")
    print(f"  Status: {results['status']}")
    print(f"  Objective value: {results['objective_value']}")

    print("\n--- Truck → Hub → Time slot assignments (first 30) ---")
    assignments = results["assignments"]
    for i, (t, h, s) in enumerate(assignments[:30]):
        print(f"  Truck {t:3d} → Hub {h} → Slot {s:2d} (hour {s})")
    if len(assignments) > 30:
        print(f"  ... and {len(assignments) - 30} more assignments.")
    print(f"  Total assignments: {len(assignments)}")

    print("\n--- Hub utilization (aggregate per hub) ---")
    util_df = results["utilization_df"]
    hub_totals = util_df.groupby("hub_id").agg(
        assigned=("assigned", "sum"),
        capacity_total=("capacity", "first"),  # capacity is same per slot
        slots_used=("assigned", lambda x: (x > 0).sum()),
    )
    hub_totals["capacity_total"] = hub_totals["capacity_total"] * data["n_slots"]
    hub_totals["util_pct"] = (hub_totals["assigned"] / hub_totals["capacity_total"] * 100).round(1)
    print(hub_totals.to_string())
    print("\nPer-slot utilization (hubs with any usage):")
    used = util_df[util_df["assigned"] > 0]
    if not used.empty:
        print(used.head(20).to_string())
    else:
        print("  (none)")

    print("\n--- Selected green zones ---")
    print(f"  Green zone IDs: {results['green_zones']}")

    print("\n--- Total cost breakdown ---")
    cb = results["cost_breakdown"]
    if cb:
        print(f"  Congestion cost (raw):     {cb['congestion_cost']:.2f}")
        print(f"  Pollution cost (raw):     {cb['pollution_cost']:.2f}")
        print(f"  Distance cost (raw):      {cb['distance_cost']:.2f}")
        print(f"  Revenue:                  {cb['revenue']:.2f}")
        print(f"  Livability (score):       {cb['livability']:.2f}")
        print("  --- Weighted contributions ---")
        print(f"  Weighted congestion:      {cb['weighted_congestion']:.2f}")
        print(f"  Weighted pollution:       {cb['weighted_pollution']:.2f}")
        print(f"  Weighted distance:        {cb['weighted_distance']:.2f}")
        print(f"  Weighted revenue (neg):   {-cb['weighted_revenue']:.2f}")
        print(f"  Weighted livability (neg): {-cb['weighted_livability']:.2f}")
    print(f"\n  Final objective value:     {results['objective_value']}")


def run_visualizations(data: dict, results: dict) -> None:
    """Plot hub usage (bar chart) and time congestion distribution."""
    try:
        import os
        os.environ.setdefault("MPLCONFIGDIR", os.path.join(os.path.dirname(__file__), ".mplconfig"))
        import matplotlib
        matplotlib.use("Agg")  # Non-interactive backend; no display or font cache needed
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError:
        print("Matplotlib not installed. Skipping visualizations.")
        return

    util_df = results["utilization_df"]
    slot_counts = results["slot_counts"]

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))

    # 1) Hub usage: total trucks per hub (bar chart)
    hub_totals = util_df.groupby("hub_id")["assigned"].sum()
    hubs = list(hub_totals.index)
    ax1.bar(hubs, hub_totals.values, color="steelblue", edgecolor="black")
    ax1.set_xlabel("Hub ID")
    ax1.set_ylabel("Number of trucks assigned")
    ax1.set_title("Hub usage (total trucks per hub)")
    ax1.set_xticks(hubs)

    # 2) Time congestion: trucks per time slot
    slots = np.arange(len(slot_counts))
    ax2.bar(slots, slot_counts, color="coral", edgecolor="black", alpha=0.8)
    ax2.set_xlabel("Time slot (hour)")
    ax2.set_ylabel("Number of trucks")
    ax2.set_title("Time congestion distribution (trucks per slot)")

    plt.tight_layout()
    plt.savefig("hunts_point_results.png", dpi=150)
    print("\nVisualizations saved to hunts_point_results.png")
    plt.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Hunts Point Adaptive Logistics Optimizer")
    parser.add_argument("--no-plot", action="store_true", help="Skip generating plots")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for data generation")
    parser.add_argument("--time-limit", type=int, default=None, help="Solver time limit (seconds)")
    args = parser.parse_args()

    # 1. Generate synthetic data
    print("Generating synthetic data...")
    data = generate_all(
        n_trucks=200,
        n_hubs=5,
        n_zones=10,
        n_slots=24,
        seed=args.seed,
    )
    print(f"  Trucks: {data['n_trucks']}, Hubs: {data['n_hubs']}, Zones: {data['n_zones']}, Slots: {data['n_slots']}")

    # 2. Build optimization model
    print("Building optimization model...")
    prob = build_model(data, weights=DEFAULT_WEIGHTS)
    print("  Variables and constraints added.")

    # 3. Solve
    print("Solving...")
    solve(prob, time_limit_seconds=args.time_limit)
    results = extract_results(prob)

    # 4. Print interpretable results
    print_results(data, results)

    # 5. Optional visualizations
    if not args.no_plot:
        run_visualizations(data, results)


if __name__ == "__main__":
    main()
