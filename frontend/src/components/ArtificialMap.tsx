'use client';

import type { ArtificialMapData } from '@/lib/api';

interface ArtificialMapProps {
  data: ArtificialMapData | null | undefined;
  loading?: boolean;
  width?: number;
  height?: number;
}

export function ArtificialMap({
  data,
  loading = false,
  width = 420,
  height = 420,
}: ArtificialMapProps) {
  if (!data) {
    return (
      <div
        className="rounded-xl border border-neutral-200 dark:border-neutral-800 bg-neutral-100 dark:bg-neutral-800 flex items-center justify-center text-neutral-500 text-sm"
        style={{ width, height }}
      >
        Run simulation to see artificial map
      </div>
    );
  }

  const { rows, cols, zone_cells, zone_meta, hubs, routes } = data;
  const cellW = width / cols;
  const cellH = height / rows;

  const toPx = (x: number, y: number) => ({
    x: x * width,
    y: y * height,
  });

  // Zone colors: pollution (red tint) vs green zone (green tint)
  const zoneColor = (zoneId: number) => {
    const meta = zone_meta.find((z) => z.zone_id === zoneId);
    if (!meta) return 'rgb(200, 220, 200)';
    if (meta.is_green) return 'rgb(180, 220, 180)';
    const p = meta.pollution;
    const r = Math.round(200 + 55 * p);
    const g = Math.round(220 - 80 * p);
    const b = 200;
    return `rgb(${r},${g},${b})`;
  };

  return (
    <div
      className="relative rounded-xl border border-neutral-200 dark:border-neutral-800 overflow-hidden bg-white dark:bg-neutral-900"
      style={{ width, height }}
    >
      <svg width={width} height={height} className="block">
        {/* Grid cells by zone */}
        {Object.entries(zone_cells).map(([zoneIdStr, cells]) => {
          const zoneId = parseInt(zoneIdStr, 10);
          const fill = zoneColor(zoneId);
          return (
            <g key={zoneId}>
              {cells.map((cell, idx) => (
                <rect
                  key={`${zoneId}-${idx}`}
                  x={cell.j * cellW}
                  y={cell.i * cellH}
                  width={cellW + 0.5}
                  height={cellH + 0.5}
                  fill={fill}
                  stroke="rgba(0,0,0,0.12)"
                  strokeWidth={0.5}
                />
              ))}
            </g>
          );
        })}
        {/* Routes (polylines) */}
        {routes.slice(0, 80).map((path, idx) => (
          <polyline
            key={idx}
            points={path.map((p) => `${toPx(p.x, p.y).x},${toPx(p.x, p.y).y}`).join(' ')}
            fill="none"
            stroke="rgba(15, 118, 110, 0.5)"
            strokeWidth={1.2}
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        ))}
        {/* Hubs */}
        {hubs.map((hub) => {
          const { x, y } = toPx(hub.x, hub.y);
          return (
            <g key={hub.hub_id}>
              <circle
                cx={x}
                cy={y}
                r={Math.max(6, 4 + hub.hub_id * 0.5)}
                fill="#0f766e"
                stroke="#fff"
                strokeWidth={2}
              />
              <text
                x={x}
                y={y + 1}
                textAnchor="middle"
                fontSize={9}
                fill="#fff"
                fontWeight="bold"
              >
                {hub.hub_id}
              </text>
            </g>
          );
        })}
      </svg>
      <div className="absolute bottom-2 left-2 right-2 flex justify-between text-xs text-neutral-500">
        <span>Zones: {zone_meta.length} · Hubs: {hubs.length}</span>
        <span>Routes: {routes.length}</span>
      </div>
      {loading && (
        <div className="absolute inset-0 bg-black/10 flex items-center justify-center">
          <span className="bg-white dark:bg-neutral-800 px-3 py-1 rounded text-sm">Updating…</span>
        </div>
      )}
    </div>
  );
}
