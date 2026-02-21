'use client';

import type { OptimizeResponse } from '@/lib/api';
import { MapView } from './MapView';
import { ArtificialMap } from './ArtificialMap';
import { ChartsSection } from './ChartsSection';

interface CompanyViewProps {
  data: OptimizeResponse | null;
  loading: boolean;
  error: string | null;
  onRefresh: () => void;
}

function formatUpdated(iso: string | null | undefined) {
  if (!iso) return null;
  try {
    const d = new Date(iso);
    const now = new Date();
    const diff = Math.round((now.getTime() - d.getTime()) / 60000);
    if (diff < 1) return 'Just now';
    if (diff < 60) return `${diff} min ago`;
    return d.toLocaleTimeString();
  } catch {
    return null;
  }
}

export function CompanyView({ data, loading, error, onRefresh }: CompanyViewProps) {
  const summary = data?.platform_summary;
  const deliveries = data?.deliveries ?? [];

  return (
    <div className="space-y-6">
      <div className="flex flex-col lg:flex-row gap-6">
        <aside className="w-full lg:w-72 flex-shrink-0 space-y-4">
          <div className="rounded-xl border border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-900 p-5">
            <h3 className="text-sm font-semibold text-neutral-800 dark:text-neutral-200 mb-3">
              Fleet at a glance
            </h3>
            {summary ? (
              <ul className="text-sm space-y-2 text-neutral-600 dark:text-neutral-400">
                <li className="flex justify-between">
                  <span>Trucks assigned</span>
                  <span className="font-medium text-neutral-900 dark:text-white">{summary.n_trucks_assigned}</span>
                </li>
                <li className="flex justify-between">
                  <span>Total distance</span>
                  <span className="font-medium">{summary.total_distance.toLocaleString()}</span>
                </li>
                <li className="flex justify-between">
                  <span>Congestion cost</span>
                  <span className="font-medium">{summary.total_congestion_cost.toFixed(0)}</span>
                </li>
                <li className="flex justify-between">
                  <span>Revenue</span>
                  <span className="font-medium text-teal-600 dark:text-teal-400">${summary.revenue.toLocaleString()}</span>
                </li>
              </ul>
            ) : (
              <div className="animate-pulse space-y-2">
                {[1, 2, 3, 4].map((i) => (
                  <div key={i} className="h-4 bg-neutral-200 dark:bg-neutral-700 rounded w-full" />
                ))}
              </div>
            )}
            <button
              type="button"
              onClick={onRefresh}
              disabled={loading}
              className="mt-4 w-full py-2 rounded-lg bg-neutral-100 dark:bg-neutral-800 hover:bg-neutral-200 dark:hover:bg-neutral-700 text-sm font-medium text-neutral-700 dark:text-neutral-300 disabled:opacity-50 transition-colors"
            >
              {loading ? 'Refreshing…' : 'Refresh data'}
            </button>
          </div>
        </aside>
        <div className="flex-1 flex flex-col gap-6 min-w-0">
          {data?.last_updated && (
            <p className="text-xs text-neutral-500">
              Last updated {formatUpdated(data.last_updated) ?? data.last_updated}
            </p>
          )}
          <section className="h-[340px] lg:h-[380px]">
            <MapView data={data} loading={loading} />
          </section>
          {deliveries.length > 0 && (
            <section className="rounded-xl border border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-900 overflow-hidden">
              <h3 className="text-sm font-semibold text-neutral-800 dark:text-neutral-200 p-4 pb-0">
                Runs & deliveries
              </h3>
              <div className="overflow-x-auto max-h-64 overflow-y-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-neutral-200 dark:border-neutral-700 text-left text-neutral-500">
                      <th className="p-3 font-medium">ID</th>
                      <th className="p-3 font-medium">From → To</th>
                      <th className="p-3 font-medium">Driver</th>
                      <th className="p-3 font-medium">Time</th>
                      <th className="p-3 font-medium">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {deliveries.slice(0, 20).map((d) => (
                      <tr key={d.delivery_id} className="border-b border-neutral-100 dark:border-neutral-800 hover:bg-neutral-50 dark:hover:bg-neutral-800/50">
                        <td className="p-3 font-mono text-xs">{d.delivery_id}</td>
                        <td className="p-3">{d.from_address} → {d.to_address}</td>
                        <td className="p-3">{d.driver_name}</td>
                        <td className="p-3">{d.scheduled_time}</td>
                        <td className="p-3 capitalize">{d.status.replace('_', ' ')}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          )}
          <section>
            <h2 className="text-sm font-semibold text-neutral-700 dark:text-neutral-300 mb-2">
              Route overview
            </h2>
            <ArtificialMap data={data?.artificial_map ?? null} loading={loading} />
          </section>
          <section>
            <ChartsSection data={data} loading={loading} />
          </section>
        </div>
      </div>
    </div>
  );
}
