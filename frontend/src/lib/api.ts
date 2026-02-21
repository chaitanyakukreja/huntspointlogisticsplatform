/**
 * API client for FastAPI /optimize endpoint.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

export interface OptimizeParams {
  num_trucks: number;
  num_hubs: number;
  budget: number;
  peak_multiplier: number;
  with_optimization: boolean;
}

export interface HubUsageItem {
  hub_id: number;
  assigned: number;
  capacity: number;
  utilization_pct: number;
}

export interface CongestionPerTimeItem {
  slot_id: number;
  hour: number;
  trucks: number;
}

export interface PollutionPerZoneItem {
  zone_id: number;
  pollution_level: number;
  truck_count: number;
}

export interface HubMapItem {
  hub_id: number;
  zone_id: number;
  lon: number;
  lat: number;
  usage: number;
}

export interface ZoneFeature {
  type: 'Feature';
  geometry: { type: 'Polygon'; coordinates: number[][][] };
  properties: {
    zone_id: number;
    pollution: number;
    congestion: number;
    is_green: boolean;
  };
}

export interface ArtificialMapData {
  rows: number;
  cols: number;
  zone_cells: Record<string, { i: number; j: number; x: number; y: number }[]>;
  zone_meta: { zone_id: number; pollution: number; is_green: boolean }[];
  hubs: { hub_id: number; row: number; col: number; x: number; y: number }[];
  routes: { x: number; y: number }[][];
}

export interface Delivery {
  delivery_id: string;
  truck_id: number;
  driver_id: number;
  driver_name: string;
  from_zone_id: number;
  from_address: string;
  to_hub_id: number;
  to_address: string;
  scheduled_slot: number;
  scheduled_time: string;
  status: string;
}

export interface PlatformSummary {
  total_distance: number;
  total_congestion_cost: number;
  revenue: number;
  driver_tips: { truck_id: number; hub_id: number; slot_id: number; tip: string }[];
  incoming_by_zone: { zone_id: number; slot_id: number; trucks: number }[];
  quiet_slots_by_zone: { zone_id: number; suggested_slots: number[] }[];
  green_zones: number[];
  n_trucks_assigned: number;
}

export interface OptimizeResponse {
  truck_assignments: { truck_id: number; hub_id: number; slot_id: number }[];
  hub_usage: HubUsageItem[];
  congestion_per_time: CongestionPerTimeItem[];
  pollution_per_zone: PollutionPerZoneItem[];
  green_zones: number[];
  zones_geojson: { type: 'FeatureCollection'; features: ZoneFeature[] };
  hubs: HubMapItem[];
  status: string;
  objective_value: number | null;
  n_assigned: number;
  artificial_map?: ArtificialMapData | null;
  platform_summary?: PlatformSummary | null;
  deliveries?: Delivery[] | null;
  last_updated?: string | null;
}

export type PlatformRole = 'driver' | 'company' | 'business';

export async function runOptimize(params: OptimizeParams): Promise<OptimizeResponse> {
  const res = await fetch(`${API_BASE}/optimize`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || String(err));
  }
  return res.json();
}

const DEMO_TIMEOUT_MS = 8000;

/** Fetch with timeout so we don't hang when backend is down. */
function fetchWithTimeout(url: string, ms: number): Promise<Response> {
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), ms);
  return fetch(url, { signal: ctrl.signal }).finally(() => clearTimeout(t));
}

/** Fallback demo data when API is unavailable — app always loads. */
export function getFallbackDemo(): OptimizeResponse {
  const drivers = ['Mike Smith', 'Carlos Garcia', 'James Chen', 'Maria Rodriguez', 'David Lee'];
  const origins = ['Bronx Produce Co.', 'Hunts Point Terminal', 'Fresh Direct Depot', 'Food Center Drive', 'Southern Blvd Warehouse'];
  const hubs = ['Hub 1 — Hunts Point Charging', 'Hub 2 — Food Center', 'Hub 3 — Oak Point', 'Hub 4 — Lafayette'];
  const statuses = ['scheduled', 'en_route', 'at_hub', 'completed'];
  const truckAssignments = Array.from({ length: 24 }, (_, i) => ({
    truck_id: i,
    hub_id: i % 4,
    slot_id: (i * 5) % 24,
  }));
  const deliveries: Delivery[] = truckAssignments.map((a, i) => ({
    delivery_id: `D-${1000 + i}`,
    truck_id: a.truck_id,
    driver_id: a.truck_id,
    driver_name: drivers[i % drivers.length],
    from_zone_id: i % 5,
    from_address: origins[i % origins.length],
    to_hub_id: a.hub_id,
    to_address: hubs[a.hub_id],
    scheduled_slot: a.slot_id,
    scheduled_time: `${String(a.slot_id).padStart(2, '0')}:00`,
    status: statuses[i % statuses.length],
  }));
  const hubUsage = [12, 8, 10, 6].map((assigned, hub_id) => ({
    hub_id,
    assigned,
    capacity: 20,
    utilization_pct: (100 * assigned) / 20,
  }));
  const congestionPerTime = Array.from({ length: 24 }, (_, s) => ({
    slot_id: s,
    hour: s,
    trucks: truckAssignments.filter((a) => a.slot_id === s).length || (s % 4 === 0 ? 2 : 0),
  }));
  const pollutionPerZone = Array.from({ length: 10 }, (_, z) => ({
    zone_id: z,
    pollution_level: 0.2 + 0.6 * (z / 10),
    truck_count: z < 5 ? 3 : 2,
  }));
  const features = Array.from({ length: 10 }, (_, z) => ({
    type: 'Feature' as const,
    geometry: { type: 'Polygon' as const, coordinates: [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]] },
    properties: { zone_id: z, pollution: 0.5, congestion: 2, is_green: [0, 2, 5].includes(z) },
  }));
  const hubList: HubMapItem[] = [
    { hub_id: 0, zone_id: 0, lon: -73.88, lat: 40.82, usage: 12 },
    { hub_id: 1, zone_id: 1, lon: -73.875, lat: 40.82, usage: 8 },
    { hub_id: 2, zone_id: 2, lon: -73.88, lat: 40.815, usage: 10 },
    { hub_id: 3, zone_id: 3, lon: -73.875, lat: 40.815, usage: 6 },
  ];
  const zoneCells: Record<string, { i: number; j: number; x: number; y: number }[]> = {};
  for (let z = 0; z < 10; z++) zoneCells[z] = [{ i: 0, j: 0, x: 0.5, y: 0.5 }];
  const artificialMap: ArtificialMapData = {
    rows: 12,
    cols: 12,
    zone_cells: zoneCells,
    zone_meta: pollutionPerZone.map((p) => ({ zone_id: p.zone_id, pollution: p.pollution_level, is_green: [0, 2, 5].includes(p.zone_id) })),
    hubs: hubList.map((h, i) => ({ hub_id: h.hub_id, row: 2 + i, col: 2 + i, x: (2.5 + i) / 12, y: (2.5 + i) / 12 })),
    routes: truckAssignments.map(() => [{ x: 0.2, y: 0.2 }, { x: 0.5, y: 0.5 }, { x: 0.8, y: 0.8 }]),
  };
  const driverTips = truckAssignments.map((a) => ({
    truck_id: a.truck_id,
    hub_id: a.hub_id,
    slot_id: a.slot_id,
    tip: `Charge at ${hubs[a.hub_id]}, ${String(a.slot_id).padStart(2, '0')}:00. Off-peak — good for energy saving.`,
  }));
  const platformSummary: PlatformSummary = {
    total_distance: 420,
    total_congestion_cost: 85,
    revenue: 3200,
    driver_tips: driverTips,
    incoming_by_zone: [{ zone_id: 0, slot_id: 6, trucks: 3 }, { zone_id: 1, slot_id: 10, trucks: 2 }],
    quiet_slots_by_zone: Array.from({ length: 10 }, (_, z) => ({ zone_id: z, suggested_slots: [0, 1, 2, 3, 4] })),
    green_zones: [0, 2, 5],
    n_trucks_assigned: 24,
  };
  return {
    truck_assignments: truckAssignments,
    hub_usage: hubUsage,
    congestion_per_time: congestionPerTime,
    pollution_per_zone: pollutionPerZone,
    green_zones: [0, 2, 5],
    zones_geojson: { type: 'FeatureCollection', features },
    hubs: hubList,
    status: 'Optimal',
    objective_value: -10000,
    n_assigned: 24,
    artificial_map: artificialMap,
    platform_summary: platformSummary,
    deliveries,
    last_updated: new Date().toISOString(),
  };
}

export interface DemoResult {
  data: OptimizeResponse;
  fromApi: boolean;
}

/** Fetch demo from API; on failure or timeout use fallback so app always loads. */
export async function fetchDemo(): Promise<DemoResult> {
  try {
    const res = await fetchWithTimeout(`${API_BASE}/demo`, DEMO_TIMEOUT_MS);
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || String(err));
    }
    const data = await res.json();
    return { data, fromApi: true };
  } catch {
    return { data: getFallbackDemo(), fromApi: false };
  }
}
