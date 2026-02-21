'use client';

import { useState, useMemo } from 'react';
import type { OptimizeResponse } from '@/lib/api';
import { ChartsSection } from './ChartsSection';

interface BusinessViewProps {
  data: OptimizeResponse | null;
  loading: boolean;
}

export function BusinessView({ data, loading }: BusinessViewProps) {
  const [selectedZone, setSelectedZone] = useState(0);
  const summary = data?.platform_summary;
  const zoneTraffic = summary?.incoming_by_zone?.filter((x) => x.zone_id === selectedZone) ?? [];
  const quiet = summary?.quiet_slots_by_zone?.find((q) => q.zone_id === selectedZone);
  const pollution = data?.pollution_per_zone?.find((p) => p.zone_id === selectedZone);

  const deliveriesToZone = useMemo(() => {
    const list = data?.deliveries ?? [];
    const hubZone = data?.hubs?.map((h) => h.zone_id) ?? [];
    return list.filter((d) => hubZone[d.to_hub_id] === selectedZone);
  }, [data?.deliveries, data?.hubs, selectedZone]);

  const zoneNames = [
    'Food Center Dr', 'Southern Blvd', 'Oak Point', 'Barreto Point',
    'Lafayette Ave', 'Bruckner Blvd', 'Hunts Point Terminal', 'Metro Fresh',
    'Bronx Produce', 'Distribution Center',
  ];

  return (
    <div className="space-y-6">
      <section className="rounded-xl border border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-900 p-6">
        <h2 className="text-lg font-semibold text-neutral-900 dark:text-white mb-1">
          Incoming traffic & coordination
        </h2>
        <p className="text-sm text-neutral-500 mb-4">
          See when trucks are scheduled in your zone and quieter windows for receiving.
        </p>
        <label className="block text-sm font-medium text-neutral-600 dark:text-neutral-400 mb-2">
          My zone
        </label>
        <select
          value={selectedZone}
          onChange={(e) => setSelectedZone(Number(e.target.value))}
          className="w-full max-w-xs rounded-lg border border-neutral-300 dark:border-neutral-600 bg-white dark:bg-neutral-800 px-3 py-2 text-sm"
        >
          {zoneNames.map((name, i) => (
            <option key={i} value={i}>
              Zone {i} — {name}
            </option>
          ))}
        </select>

        {loading && !data && (
          <div className="mt-4 space-y-3 animate-pulse">
            <div className="h-16 bg-neutral-200 dark:bg-neutral-700 rounded-lg" />
            <div className="h-16 bg-neutral-200 dark:bg-neutral-700 rounded-lg" />
          </div>
        )}
        {data && summary && (
          <div className="mt-4 space-y-4">
            {deliveriesToZone.length > 0 && (
              <div>
                <h3 className="text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">
                  Scheduled for your zone
                </h3>
                <div className="grid gap-2 sm:grid-cols-2">
                  {deliveriesToZone.slice(0, 8).map((d) => (
                    <div
                      key={d.delivery_id}
                      className="rounded-lg border border-neutral-200 dark:border-neutral-700 p-3 text-sm"
                    >
                      <span className="font-mono text-xs text-neutral-500">{d.delivery_id}</span>
                      <p className="font-medium text-neutral-900 dark:text-white mt-0.5">
                        {d.from_address} → {d.to_address}
                      </p>
                      <p className="text-neutral-500">{d.scheduled_time} · {d.driver_name}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
            <div>
              <h3 className="text-sm font-medium text-neutral-700 dark:text-neutral-300">
                Incoming trucks by time (Zone {selectedZone})
              </h3>
              <div className="mt-2 flex flex-wrap gap-2">
                {zoneTraffic.length === 0 ? (
                  <p className="text-sm text-neutral-500">No trucks at hubs in this zone in the current plan.</p>
                ) : (
                  zoneTraffic
                    .sort((a, b) => a.slot_id - b.slot_id)
                    .map((x) => (
                      <span
                        key={`${x.zone_id}-${x.slot_id}`}
                        className="inline-flex items-center rounded-full bg-neutral-100 dark:bg-neutral-700 px-2.5 py-0.5 text-xs"
                      >
                        {x.slot_id}:00 → {x.trucks} truck{x.trucks !== 1 ? 's' : ''}
                      </span>
                    ))
                )}
              </div>
            </div>
            {quiet && (
              <div className="p-3 rounded-lg bg-teal-50 dark:bg-teal-900/20 border border-teal-200 dark:border-teal-800">
                <p className="text-sm font-medium text-teal-800 dark:text-teal-200">
                  Quieter time windows (fewer trucks)
                </p>
                <p className="text-sm text-teal-700 dark:text-teal-300 mt-0.5">
                  Consider receiving at: {quiet.suggested_slots.slice(0, 5).map((s) => `${s}:00`).join(', ')}
                </p>
              </div>
            )}
            {pollution && (
              <p className="text-sm text-neutral-600 dark:text-neutral-400">
                Zone pollution level: {(pollution.pollution_level * 100).toFixed(0)}% · Trucks in zone: {pollution.truck_count}
              </p>
            )}
          </div>
        )}
      </section>

      <section>
        <h2 className="text-sm font-semibold text-neutral-700 dark:text-neutral-300 mb-2">
          Congestion & pollution overview
        </h2>
        <ChartsSection data={data} loading={loading} />
      </section>
    </div>
  );
}
