'use client';

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from 'recharts';
import type { OptimizeResponse } from '@/lib/api';

interface ChartsSectionProps {
  data: OptimizeResponse | null;
  loading: boolean;
}

export function ChartsSection({ data, loading }: ChartsSectionProps) {
  if (!data) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white dark:bg-neutral-900 rounded-xl border border-neutral-200 dark:border-neutral-800 p-4 h-64 flex items-center justify-center text-neutral-500">
          Run simulation to see charts
        </div>
      </div>
    );
  }

  const congestionData = data.congestion_per_time.map((d) => ({
    hour: d.hour,
    trucks: d.trucks,
    name: `${d.hour}h`,
  }));
  const pollutionData = data.pollution_per_zone.map((d) => ({
    zone: `Zone ${d.zone_id}`,
    pollution: d.pollution_level,
    trucks: d.truck_count,
  }));
  const hubData = data.hub_usage.map((d) => ({
    name: `Hub ${d.hub_id}`,
    assigned: d.assigned,
    capacity: d.capacity,
    utilization: d.utilization_pct,
  }));

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 transition-smooth">
      <div className="bg-white dark:bg-neutral-900 rounded-xl border border-neutral-200 dark:border-neutral-800 p-4 shadow-sm">
        <h3 className="text-sm font-semibold text-neutral-700 dark:text-neutral-300 mb-3">
          Congestion vs time
        </h3>
        <div className="h-48">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={congestionData} margin={{ top: 4, right: 4, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" className="stroke-neutral-200 dark:stroke-neutral-700" />
              <XAxis dataKey="name" tick={{ fontSize: 10 }} />
              <YAxis tick={{ fontSize: 10 }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'var(--panel)',
                  border: '1px solid var(--border)',
                  borderRadius: '8px',
                }}
                labelFormatter={(_, payload) => payload[0]?.payload?.hour != null ? `Hour ${payload[0].payload.hour}` : ''}
              />
              <Bar dataKey="trucks" fill="#0f766e" radius={[4, 4, 0, 0]} name="Trucks" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="bg-white dark:bg-neutral-900 rounded-xl border border-neutral-200 dark:border-neutral-800 p-4 shadow-sm">
        <h3 className="text-sm font-semibold text-neutral-700 dark:text-neutral-300 mb-3">
          Pollution by zone
        </h3>
        <div className="h-48">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={pollutionData} margin={{ top: 4, right: 4, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" className="stroke-neutral-200 dark:stroke-neutral-700" />
              <XAxis dataKey="zone" tick={{ fontSize: 10 }} />
              <YAxis tick={{ fontSize: 10 }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'var(--panel)',
                  border: '1px solid var(--border)',
                  borderRadius: '8px',
                }}
              />
              <Bar dataKey="pollution" fill="#b91c1c" radius={[4, 4, 0, 0]} name="Pollution" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="bg-white dark:bg-neutral-900 rounded-xl border border-neutral-200 dark:border-neutral-800 p-4 shadow-sm">
        <h3 className="text-sm font-semibold text-neutral-700 dark:text-neutral-300 mb-3">
          Hub utilization
        </h3>
        <div className="h-48">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={hubData} margin={{ top: 4, right: 4, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" className="stroke-neutral-200 dark:stroke-neutral-700" />
              <XAxis dataKey="name" tick={{ fontSize: 10 }} />
              <YAxis tick={{ fontSize: 10 }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'var(--panel)',
                  border: '1px solid var(--border)',
                  borderRadius: '8px',
                }}
                formatter={(value: number, name: string) => [
                  name === 'utilization' ? `${value}%` : value,
                  name === 'assigned' ? 'Assigned' : name === 'capacity' ? 'Capacity' : 'Utilization %',
                ]}
              />
              <Bar dataKey="assigned" fill="#0f766e" radius={[4, 4, 0, 0]} name="Assigned" />
              <Bar dataKey="capacity" fill="#94a3b8" radius={[4, 4, 0, 0]} name="Capacity" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {loading && (
        <div className="fixed inset-0 pointer-events-none flex items-center justify-center">
          <div className="bg-black/10 dark:bg-black/30 rounded-lg px-4 py-2 text-sm font-medium">
            Updating…
          </div>
        </div>
      )}
    </div>
  );
}
