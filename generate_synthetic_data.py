"""
Generate synthetic data for the logistics optimizer and optionally save to JSON.
Use this to create reproducible mock datasets or feed into the decision/ML model.
"""

import json
import argparse
from pathlib import Path

from data_generation import generate_all
from synthetic_network import (
    build_grid_network,
    truck_origin_cells,
    compute_routes,
    network_to_map_data,
)
from model import build_model
from solver import solve, extract_results


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic logistics data")
    parser.add_argument("--trucks", type=int, default=100)
    parser.add_argument("--hubs", type=int, default=5)
    parser.add_argument("--zones", type=int, default=10)
    parser.add_argument("--slots", type=int, default=24)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--peak-multiplier", type=float, default=1.0)
    parser.add_argument("--budget", type=float, default=500)
    parser.add_argument("--out", type=str, default=None, help="Save summary to this JSON path")
    parser.add_argument("--run-optimizer", action="store_true", help="Run optimizer and include assignments + routes")
    args = parser.parse_args()

    data = generate_all(
        n_trucks=args.trucks,
        n_hubs=args.hubs,
        n_zones=args.zones,
        n_slots=args.slots,
        seed=args.seed,
        peak_multiplier=args.peak_multiplier,
    )

    out = {
        "n_trucks": data["n_trucks"],
        "n_hubs": data["n_hubs"],
        "n_zones": data["n_zones"],
        "n_slots": data["n_slots"],
        "seed": args.seed,
        "peak_multiplier": args.peak_multiplier,
        "budget": args.budget,
    }

    if args.run_optimizer:
        prob = build_model(data, total_budget=args.budget)
        solve(prob, time_limit_seconds=60)
        results = extract_results(prob)
        assignments = results["assignments"]
        out["status"] = results["status"]
        out["objective_value"] = results.get("objective_value")
        out["n_assigned"] = results["n_assigned"]
        out["green_zones"] = results["green_zones"]

        network = build_grid_network(
            rows=12, cols=12,
            n_zones=data["n_zones"],
            n_hubs=data["n_hubs"],
            seed=args.seed,
        )
        origin_zones = data["trucks"]["origin_zone"].values
        truck_origin_cells_list = truck_origin_cells(network, origin_zones, seed=args.seed)
        routes = compute_routes(network, assignments, truck_origin_cells_list)
        artificial_map = network_to_map_data(
            network, data["zones"], routes, results["green_zones"],
        )
        out["artificial_map"] = artificial_map
        out["truck_assignments"] = [
            {"truck_id": t, "hub_id": h, "slot_id": s}
            for (t, h, s) in assignments
        ]

    if args.out:
        path = Path(args.out)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(out, f, indent=2)
        print(f"Wrote {path}")
    else:
        print(json.dumps({k: v for k, v in out.items() if k not in ("artificial_map", "truck_assignments")}, indent=2))
        if "artificial_map" in out:
            print("... (artificial_map and truck_assignments omitted in stdout)")


if __name__ == "__main__":
    main()
