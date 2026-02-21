'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import {
  runOptimize,
  type OptimizeParams,
  type OptimizeResponse,
} from '@/lib/api';

const DEBOUNCE_MS = 500;

export function useOptimize(initialParams: OptimizeParams) {
  const [params, setParams] = useState<OptimizeParams>(initialParams);
  const [data, setData] = useState<OptimizeResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const fetchOptimize = useCallback(async (p: OptimizeParams) => {
    setLoading(true);
    setError(null);
    try {
      const result = await runOptimize(p);
      setData(result);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Request failed');
    } finally {
      setLoading(false);
    }
  }, []);

  const updateParams = useCallback(
    (updates: Partial<OptimizeParams>) => {
      const next = { ...params, ...updates };
      setParams(next);
      if (debounceRef.current) clearTimeout(debounceRef.current);
      debounceRef.current = setTimeout(() => {
        debounceRef.current = null;
        fetchOptimize(next);
      }, DEBOUNCE_MS);
    },
    [params, fetchOptimize]
  );

  const runNow = useCallback(() => {
    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
      debounceRef.current = null;
    }
    fetchOptimize(params);
  }, [params, fetchOptimize]);

  useEffect(() => {
    fetchOptimize(initialParams);
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return { params, setParams: updateParams, data, loading, error, runNow };
}
