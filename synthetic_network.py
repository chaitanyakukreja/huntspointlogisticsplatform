"""
Synthetic road network: grid-based graph for truck routing.
Zones are regions on the grid; hubs and truck origins are cell positions.
Used for route generation and artificial map visualization.
"""

import numpy as np
from typing import Dict, List, Tuple, Any
from collections import deque


def build_grid_network(
    rows: int = 12,
    cols: int = 12,
    n_zones: int = 10,
    n_hubs: int = 5,
    seed: int = 42,
) -> Dict[str, Any]:
    """
    Build a grid world: rows x cols. Each cell (i, j) belongs to one zone.
    Hubs are placed at cell positions. Returns network dict for routing and map.
    """
    rng = np.random.default_rng(seed)
    # Assign each cell to a zone (contiguous-ish via simple partition)
    side = int(np.ceil(np.sqrt(n_zones)))
    zone_grid = np.zeros((rows, cols), dtype=int)
    for i in range(rows):
        for j in range(cols):
            # Map cell to zone in a grid pattern
            ci, cj = i * side // rows, j * side // cols
            zone_grid[i, j] = min(ci * side + cj, n_zones - 1)

    # Hub positions: one per hub, in different zones if possible
    hub_cells: List[Tuple[int, int]] = []
    for h in range(n_hubs):
        z = h % n_zones
        cells_in_zone = list(zip(*np.where(zone_grid == z)))
        if not cells_in_zone:
            cells_in_zone = [(rows // 2, cols // 2)]
        r, c = cells_in_zone[rng.integers(0, len(cells_in_zone))]
        hub_cells.append((int(r), int(c)))

    # Truck origins: for each truck we store (zone_id, cell_row, cell_col)
    # We'll generate truck cells when we have n_trucks; here we only have zone_grid
    return {
        "rows": rows,
        "cols": cols,
        "zone_grid": zone_grid,
        "hub_cells": hub_cells,
        "n_zones": n_zones,
        "n_hubs": n_hubs,
    }


def truck_origin_cells(
    network: Dict[str, Any],
    origin_zones: np.ndarray,
    seed: int = 42,
) -> List[Tuple[int, int]]:
    """For each truck (index = truck_id), return (row, col) of origin cell in its zone."""
    rng = np.random.default_rng(seed)
    zone_grid = network["zone_grid"]
    rows, cols = zone_grid.shape
    origins = []
    for z in origin_zones:
        cells_in_zone = list(zip(*np.where(zone_grid == z)))
        if not cells_in_zone:
            cells_in_zone = [(rows // 2, cols // 2)]
        r, c = cells_in_zone[rng.integers(0, len(cells_in_zone))]
        origins.append((int(r), int(c)))
    return origins


def neighbors(row: int, col: int, rows: int, cols: int) -> List[Tuple[int, int]]:
    """4-neighbor connectivity (no diagonals)."""
    out = []
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        r2, c2 = row + dr, col + dc
        if 0 <= r2 < rows and 0 <= c2 < cols:
            out.append((r2, c2))
    return out


def shortest_path_grid(
    start: Tuple[int, int],
    end: Tuple[int, int],
    rows: int,
    cols: int,
    block_cells: List[Tuple[int, int]] | None = None,
) -> List[Tuple[int, int]]:
    """
    BFS shortest path on grid from start to end.
    block_cells: optional list of (r,c) to avoid.
    """
    block = set(block_cells or [])
    if start in block or end in block:
        return [start]
    q: deque = deque([start])
    parent: Dict[Tuple[int, int], Tuple[int, int] | None] = {start: None}
    while q:
        cur = q.popleft()
        if cur == end:
            path = []
            while cur is not None:
                path.append(cur)
                cur = parent[cur]
            return path[::-1]
        for n in neighbors(cur[0], cur[1], rows, cols):
            if n not in parent and n not in block:
                parent[n] = cur
                q.append(n)
    return [start]


def compute_routes(
    network: Dict[str, Any],
    assignments: List[Tuple[int, int, int]],
    truck_origin_cells_list: List[Tuple[int, int]],
) -> List[List[Tuple[int, int]]]:
    """
    assignments: list of (truck_id, hub_id, slot_id).
    truck_origin_cells_list[i] = (row, col) for truck i.
    Returns list of routes: each route is [(r0,c0), (r1,c1), ...] from origin to hub.
    """
    rows = network["rows"]
    cols = network["cols"]
    hub_cells = network["hub_cells"]
    routes = []
    for (t, h, _) in assignments:
        start = truck_origin_cells_list[t]
        end = hub_cells[h]
        path = shortest_path_grid(start, end, rows, cols)
        routes.append(path)
    return routes


def network_to_map_data(
    network: Dict[str, Any],
    zones_df: Any,
    routes: List[List[Tuple[int, int]]],
    green_zones: List[int],
) -> Dict[str, Any]:
    """
    Serialize for frontend artificial map: grid size, zone colors, hub positions, routes.
    Coordinates in 0..1 normalized (x = col/cols, y = row/rows) so map can scale.
    """
    rows = network["rows"]
    cols = network["cols"]
    zone_grid = network["zone_grid"]
    hub_cells = network["hub_cells"]
    n_zones = network["n_zones"]

    # Zone cells: for each zone, list of { i, j, x, y } (normalized)
    zone_cells: Dict[int, List[Dict[str, float]]] = {z: [] for z in range(n_zones)}
    for i in range(rows):
        for j in range(cols):
            z = int(zone_grid[i, j])
            zone_cells[z].append({
                "i": i, "j": j,
                "x": (j + 0.5) / cols,
                "y": (i + 0.5) / rows,
            })

    # Hub positions (normalized)
    hubs = [
        {
            "hub_id": h,
            "row": int(r), "col": int(c),
            "x": (c + 0.5) / cols,
            "y": (r + 0.5) / rows,
        }
        for h, (r, c) in enumerate(hub_cells)
    ]

    # Routes as normalized polyline
    route_polylines = []
    for path in routes:
        poly = [{"x": (c + 0.5) / cols, "y": (r + 0.5) / rows} for (r, c) in path]
        route_polylines.append(poly)

    # Zone metadata (pollution for color)
    zone_meta = []
    for z in range(n_zones):
        pl = 0.5
        if zones_df is not None and "pollution_level" in zones_df.columns:
            row = zones_df[zones_df["zone_id"] == z]
            if not row.empty:
                pl = float(row["pollution_level"].iloc[0])
        zone_meta.append({
            "zone_id": z,
            "pollution": pl,
            "is_green": z in green_zones,
        })

    return {
        "rows": rows,
        "cols": cols,
        "zone_cells": zone_cells,
        "zone_meta": zone_meta,
        "hubs": hubs,
        "routes": route_polylines,
    }
