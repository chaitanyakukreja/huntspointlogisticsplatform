'use client';

import { useCallback, useEffect, useState } from 'react';
import { fetchDemo, type OptimizeResponse } from '@/lib/api';

export function useDemoData() {
  const [data, setData] = useState<OptimizeResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [fromApi, setFromApi] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchDemo();
      setData(result.data);
      setFromApi(result.fromApi);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  return { data, loading, error, fromApi, refresh: load };
}
