'use client';

import type { OptimizeParams } from '@/lib/api';

interface ControlPanelProps {
  params: OptimizeParams;
  onParamsChange: (u: Partial<OptimizeParams>) => void;
  onRun: () => void;
  loading: boolean;
  error: string | null;
}

export function ControlPanel({ params, onParamsChange, onRun, loading, error }: ControlPanelProps) {
  return (
    <div className="flex flex-col gap-6 p-6 bg-white dark:bg-neutral-900 rounded-xl border border-neutral-200 dark:border-neutral-800 shadow-sm transition-smooth">
      <h2 className="text-lg font-semibold text-neutral-900 dark:text-white">
        Simulation controls
      </h2>

      <div className="flex flex-col gap-4">
        <label className="flex flex-col gap-1.5">
          <span className="text-sm font-medium text-neutral-600 dark:text-neutral-400">
            Trucks
          </span>
          <input
            type="range"
            min={10}
            max={500}
            step={10}
            value={params.num_trucks}
            onChange={(e) => onParamsChange({ num_trucks: Number(e.target.value) })}
            className="w-full h-2 rounded-lg appearance-none bg-neutral-200 dark:bg-neutral-700 accent-teal-600"
          />
          <span className="text-sm text-neutral-500">{params.num_trucks}</span>
        </label>

        <label className="flex flex-col gap-1.5">
          <span className="text-sm font-medium text-neutral-600 dark:text-neutral-400">
            Hubs
          </span>
          <input
            type="range"
            min={1}
            max={20}
            value={params.num_hubs}
            onChange={(e) => onParamsChange({ num_hubs: Number(e.target.value) })}
            className="w-full h-2 rounded-lg appearance-none bg-neutral-200 dark:bg-neutral-700 accent-teal-600"
          />
          <span className="text-sm text-neutral-500">{params.num_hubs}</span>
        </label>

        <label className="flex flex-col gap-1.5">
          <span className="text-sm font-medium text-neutral-600 dark:text-neutral-400">
            Budget
          </span>
          <input
            type="range"
            min={100}
            max={2000}
            step={50}
            value={params.budget}
            onChange={(e) => onParamsChange({ budget: Number(e.target.value) })}
            className="w-full h-2 rounded-lg appearance-none bg-neutral-200 dark:bg-neutral-700 accent-teal-600"
          />
          <span className="text-sm text-neutral-500">{params.budget}</span>
        </label>

        <label className="flex flex-col gap-1.5">
          <span className="text-sm font-medium text-neutral-600 dark:text-neutral-400">
            Peak congestion intensity
          </span>
          <input
            type="range"
            min={0.5}
            max={3}
            step={0.1}
            value={params.peak_multiplier}
            onChange={(e) =>
              onParamsChange({ peak_multiplier: Number(e.target.value) })
            }
            className="w-full h-2 rounded-lg appearance-none bg-neutral-200 dark:bg-neutral-700 accent-teal-600"
          />
          <span className="text-sm text-neutral-500">
            {params.peak_multiplier.toFixed(1)}
          </span>
        </label>

        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={params.with_optimization}
            onChange={(e) =>
              onParamsChange({ with_optimization: e.target.checked })
            }
            className="w-4 h-4 rounded border-neutral-300 text-teal-600 focus:ring-teal-500"
          />
          <span className="text-sm font-medium text-neutral-700 dark:text-neutral-300">
            With optimization
          </span>
        </label>
      </div>

      <button
        onClick={onRun}
        disabled={loading}
        className="mt-2 px-4 py-2.5 rounded-lg bg-teal-600 hover:bg-teal-700 disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium transition-smooth"
      >
        {loading ? 'Running…' : 'Run simulation'}
      </button>

      {error && (
        <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
      )}
    </div>
  );
}
