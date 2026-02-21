# Hunts Point — Full-Stack Simulation

## Backend (FastAPI)

```bash
cd syntruckdata
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn api:app --reload --host 127.0.0.1 --port 8000
```

- **POST /optimize** — body: `{ num_trucks, num_hubs, budget, peak_multiplier, with_optimization }`
- **GET /health** — health check

## Frontend (Next.js)

```bash
cd frontend
npm install
cp .env.example .env.local
# Edit .env.local: set NEXT_PUBLIC_API_URL=http://127.0.0.1:8000 and optionally NEXT_PUBLIC_MAPBOX_TOKEN
npm run dev
```

Open http://localhost:3000. Use the left panel sliders and "With optimization" toggle; results update the map and charts (debounced 500ms). Map requires a free [Mapbox](https://account.mapbox.com/) token.

## Synthetic data and artificial map

- **Synthetic network**: Grid-based road network (zones as cell regions, hubs at cells). Truck routes are shortest paths on the grid (BFS).
- **Generate data**: `python generate_synthetic_data.py --trucks 100 --hubs 5 --run-optimizer --out data/sample.json` to create a dataset and optionally run the optimizer and save assignments + artificial map.
- **Decision model** (`route_model.py`): Shortest-path routing on the grid; optional ML classifier (sklearn) to predict hub/slot from features, trainable on optimizer outputs.
- **Artificial map**: In the frontend, the "Artificial map (synthetic grid mockup)" section shows a schematic grid: zones (colored by pollution/green), hubs (numbered circles), and truck routes (teal polylines). No real map required.

## Flow

1. Sliders change → debounced POST /optimize.
2. Response → zones (GeoJSON), hubs (lon/lat, usage), congestion per time, pollution per zone, and **artificial_map** (grid zones, hubs, routes).
3. Map: zone fill by pollution or congestion; hub circles sized by usage.
4. Artificial map: grid mockup with zones, hubs, and routes.
5. Charts: congestion vs time, pollution by zone, hub utilization.
