'use client';

import { useState, useMemo } from 'react';
import type { OptimizeResponse } from '@/lib/api';
import { ArtificialMap } from './ArtificialMap';

interface DriverViewProps {
  data: OptimizeResponse | null;
  loading: boolean;
}

const STATUS_STYLE: Record<string, string> = {
  scheduled: 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-300',
  en_route: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300',
  at_hub: 'bg-teal-100 text-teal-800 dark:bg-teal-900/30 dark:text-teal-300',
  completed: 'bg-neutral-100 text-neutral-700 dark:bg-neutral-700 dark:text-neutral-200',
};

function DeliveryCard({
  delivery,
  onSelectTruck,
  isSelected,
}: {
  delivery: {
    delivery_id: string;
    from_address: string;
    to_address: string;
    scheduled_time: string;
    driver_name: string;
    status: string;
    truck_id: number;
  };
  onSelectTruck: (t: number) => void;
  isSelected: boolean;
}) {
  return (
    <button
      type="button"
      onClick={() => onSelectTruck(delivery.truck_id)}
      className={`w-full text-left rounded-xl border p-4 transition-all ${
        isSelected
          ? 'border-teal-500 bg-teal-50 dark:bg-teal-900/20 dark:border-teal-500'
          : 'border-neutral-200 dark:border-neutral-700 hover:border-neutral-300 dark:hover:border-neutral-600 bg-white dark:bg-neutral-900'
      }`}
    >
      <div className="flex justify-between items-start gap-2">
        <span className="text-xs font-mono text-neutral-500">{delivery.delivery_id}</span>
        <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${STATUS_STYLE[delivery.status] || STATUS_STYLE.scheduled}`}>
          {delivery.status.replace('_', ' ')}
        </span>
      </div>
      <p className="mt-2 font-medium text-neutral-900 dark:text-white truncate">
        {delivery.from_address} → {delivery.to_address}
      </p>
      <p className="mt-1 text-sm text-neutral-500">
        {delivery.scheduled_time} · {delivery.driver_name}
      </p>
    </button>
  );
}

function SkeletonCard() {
  return (
    <div className="rounded-xl border border-neutral-200 dark:border-neutral-700 p-4 animate-pulse">
      <div className="h-4 w-16 bg-neutral-200 dark:bg-neutral-700 rounded" />
      <div className="mt-2 h-5 w-full bg-neutral-200 dark:bg-neutral-700 rounded" />
      <div className="mt-1 h-4 w-32 bg-neutral-200 dark:bg-neutral-700 rounded" />
    </div>
  );
}

export function DriverView({ data, loading }: DriverViewProps) {
  const [selectedTruck, setSelectedTruck] = useState(0);
  const summary = data?.platform_summary;
  const assignment = data?.truck_assignments?.find((a) => a.truck_id === selectedTruck);
  const tip = summary?.driver_tips?.find((t) => t.truck_id === selectedTruck);
  const route = data?.artificial_map?.routes?.[data.truck_assignments?.findIndex((a) => a.truck_id === selectedTruck) ?? 0];

  const deliveries = data?.deliveries ?? [];
  const myDeliveries = useMemo(() => {
    const byTruck = new Map<number, typeof deliveries>();
    deliveries.forEach((d) => {
      if (!byTruck.has(d.truck_id)) byTruck.set(d.truck_id, []);
      byTruck.get(d.truck_id)!.push(d);
    });
    return byTruck;
  }, [deliveries]);

  const firstDeliveryForTruck = (truckId: number) =>
    myDeliveries.get(truckId)?.[0] ?? deliveries.find((d) => d.truck_id === truckId);

  return (
    <div className="space-y-6">
      <section className="rounded-xl border border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-900 p-6">
        <h2 className="text-lg font-semibold text-neutral-900 dark:text-white mb-1">
          Today&apos;s runs
        </h2>
        <p className="text-sm text-neutral-500 mb-4">
          Pick a run to see your assigned hub, time slot, and energy tip.
        </p>
        {loading && !data && (
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {[1, 2, 3, 4, 5, 6].map((i) => (
              <SkeletonCard key={i} />
            ))}
          </div>
        )}
        {data && (
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {deliveries.slice(0, 24).map((d) => (
              <DeliveryCard
                key={d.delivery_id}
                delivery={d}
                onSelectTruck={setSelectedTruck}
                isSelected={selectedTruck === d.truck_id}
              />
            ))}
          </div>
        )}
      </section>

      <section className="rounded-xl border border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-900 p-6">
        <h2 className="text-lg font-semibold text-neutral-900 dark:text-white mb-1">
          My trip & charging
        </h2>
        <p className="text-sm text-neutral-500 mb-4">
          Truck {selectedTruck} — assigned hub, slot, and energy-saving tip.
        </p>
        <div className="flex flex-wrap gap-4 text-sm mb-3">
          <span className="font-medium text-neutral-600 dark:text-neutral-400">Truck</span>
          <select
            value={selectedTruck}
            onChange={(e) => setSelectedTruck(Number(e.target.value))}
            className="rounded-lg border border-neutral-300 dark:border-neutral-600 bg-white dark:bg-neutral-800 px-3 py-2 text-sm"
          >
            {data?.truck_assignments?.slice(0, 50).map((a) => (
              <option key={a.truck_id} value={a.truck_id}>
                Truck {a.truck_id} {firstDeliveryForTruck(a.truck_id) ? `· ${firstDeliveryForTruck(a.truck_id)?.driver_name}` : ''}
              </option>
            ))}
          </select>
        </div>
        {assignment && (
          <>
            <div className="flex flex-wrap gap-4 text-sm text-neutral-700 dark:text-neutral-300">
              <span><strong>Hub</strong> {assignment.hub_id}</span>
              <span><strong>Time</strong> {assignment.slot_id}:00</span>
            </div>
            {tip && (
              <div className="mt-3 p-3 rounded-lg bg-teal-50 dark:bg-teal-900/20 border border-teal-200 dark:border-teal-800">
                <p className="text-sm font-medium text-teal-800 dark:text-teal-200">Energy tip</p>
                <p className="text-sm text-teal-700 dark:text-teal-300 mt-0.5">{tip.tip}</p>
              </div>
            )}
          </>
        )}
      </section>

      {data?.artificial_map && (
        <section>
          <h3 className="text-sm font-semibold text-neutral-700 dark:text-neutral-300 mb-2">
            Your route
          </h3>
          <ArtificialMap
            data={{
              ...data.artificial_map,
              routes: route ? [route] : [],
            }}
            loading={loading}
            width={420}
            height={320}
          />
        </section>
      )}
    </div>
  );
}
