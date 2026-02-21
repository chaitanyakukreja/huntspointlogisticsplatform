'use client';

import { useState } from 'react';
import type { PlatformRole } from '@/lib/api';
import { useDemoData } from '@/hooks/useDemoData';
import { PlatformNav } from '@/components/PlatformNav';
import { DriverView } from '@/components/DriverView';
import { CompanyView } from '@/components/CompanyView';
import { BusinessView } from '@/components/BusinessView';

export default function Home() {
  const [role, setRole] = useState<PlatformRole>('driver');
  const { data, loading, error, fromApi, refresh } = useDemoData();

  return (
    <div className="min-h-screen bg-neutral-50 dark:bg-neutral-950">
      <header className="border-b border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-900 px-6 py-4">
        <div className="max-w-[1600px] mx-auto flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-xl font-semibold text-neutral-900 dark:text-white">
              Hunts Point Logistics Platform
            </h1>
            <p className="text-sm text-neutral-500 mt-0.5">
              Smarter coordination for truck drivers, fleets, and local business.
            </p>
          </div>
          <PlatformNav role={role} onRoleChange={setRole} />
        </div>
      </header>

      <main className="p-6 max-w-[1600px] mx-auto">
        {error && (
          <div className="mb-4 p-4 rounded-lg bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300 text-sm">
            {error}
            <button type="button" onClick={refresh} className="ml-2 underline">Retry</button>
          </div>
        )}
        {!fromApi && data && (
          <div className="mb-4 p-3 rounded-lg bg-amber-50 dark:bg-amber-900/20 text-amber-800 dark:text-amber-200 text-sm">
            Showing sample data. Start the backend (<code className="text-xs">uvicorn api:app --port 8000</code>) and click Refresh for live data.
          </div>
        )}
        {loading && !data && (
          <div className="flex flex-col items-center justify-center py-20 text-neutral-500">
            <div className="w-8 h-8 border-2 border-teal-500 border-t-transparent rounded-full animate-spin mb-4" />
            <p className="text-sm">Loading your view…</p>
          </div>
        )}
        {data && role === 'driver' && <DriverView data={data} loading={loading} />}
        {data && role === 'company' && <CompanyView data={data} loading={loading} error={error} onRefresh={refresh} />}
        {data && role === 'business' && <BusinessView data={data} loading={loading} />}
        {!loading && !data && !error && (
          <div className="py-20 text-center text-neutral-500 text-sm">
            No data yet. Check your connection and retry.
          </div>
        )}
      </main>
    </div>
  );
}
