'use client';

import type { PlatformRole } from '@/lib/api';

interface PlatformNavProps {
  role: PlatformRole;
  onRoleChange: (r: PlatformRole) => void;
}

const ROLES: { id: PlatformRole; label: string; short: string }[] = [
  { id: 'driver', label: 'I’m a driver', short: 'Driver' },
  { id: 'company', label: 'I run a fleet', short: 'Company' },
  { id: 'business', label: 'I’m a business', short: 'Business' },
];

export function PlatformNav({ role, onRoleChange }: PlatformNavProps) {
  return (
    <nav className="flex gap-1 p-1 bg-neutral-100 dark:bg-neutral-800 rounded-lg">
      {ROLES.map((r) => (
        <button
          key={r.id}
          type="button"
          onClick={() => onRoleChange(r.id)}
          className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
            role === r.id
              ? 'bg-white dark:bg-neutral-700 text-teal-700 dark:text-teal-300 shadow'
              : 'text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-white'
          }`}
        >
          {r.short}
        </button>
      ))}
    </nav>
  );
}
