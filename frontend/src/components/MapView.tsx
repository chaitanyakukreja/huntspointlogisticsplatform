'use client';

import { useEffect, useRef, useState } from 'react';
import type { OptimizeResponse } from '@/lib/api';

const DEFAULT_CENTER: [number, number] = [-73.88, 40.82];
const DEFAULT_ZOOM = 15;

interface MapViewProps {
  data: OptimizeResponse | null;
  loading: boolean;
}

export function MapView({ data, loading }: MapViewProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<mapboxgl.Map | null>(null);
  const [mapReady, setMapReady] = useState(false);
  const [layerMode, setLayerMode] = useState<'pollution' | 'congestion'>('pollution');

  useEffect(() => {
    if (typeof window === 'undefined' || !containerRef.current) return;
    const token = process.env.NEXT_PUBLIC_MAPBOX_TOKEN;
    if (!token) {
      setMapReady(true);
      return;
    }
    let cancelled = false;
    import('mapbox-gl').then((mapboxgl) => {
      if (cancelled || !containerRef.current) return;
      mapboxgl.default.accessToken = token;
      const map = new mapboxgl.default.Map({
        container: containerRef.current,
        style: 'mapbox://styles/mapbox/light-v11',
        center: DEFAULT_CENTER,
        zoom: DEFAULT_ZOOM,
      });
      map.addControl(new mapboxgl.default.NavigationControl(), 'top-right');
      map.on('load', () => {
        if (cancelled) {
          map.remove();
          return;
        }
        mapRef.current = map;
        setMapReady(true);
      });
    });
    return () => {
      cancelled = true;
      if (mapRef.current) {
        mapRef.current.remove();
        mapRef.current = null;
      }
      setMapReady(false);
    };
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !mapReady || !data) return;

    const geojson = data.zones_geojson;
    const maxCongestion = Math.max(
      ...geojson.features.map((f) => f.properties.congestion),
      1
    );

    if (map.getLayer('zones-fill')) map.removeLayer('zones-fill');
    if (map.getSource('zones')) map.removeSource('zones');
    if (map.getLayer('zones-outline')) map.removeLayer('zones-outline');
    if (map.getLayer('hubs')) map.removeLayer('hubs');
    if (map.getSource('hubs')) map.removeSource('hubs');

    map.addSource('zones', {
      type: 'geojson',
      data: geojson as GeoJSON.FeatureCollection,
    });
    const prop = layerMode === 'pollution' ? 'pollution' : 'congestion';
    const fillColor =
      layerMode === 'pollution'
        ? ['interpolate', ['linear'], ['get', 'pollution'], 0, 'rgba(15,118,110,0.35)', 1, 'rgba(220,38,38,0.6)']
        : ['interpolate', ['linear'], ['get', 'congestion'], 0, 'rgba(15,118,110,0.35)', maxCongestion, 'rgba(220,38,38,0.6)'];

    map.addLayer({
      id: 'zones-fill',
      type: 'fill',
      source: 'zones',
      paint: {
        'fill-color': fillColor as unknown as string,
        'fill-opacity': 0.6,
      },
    });
    map.addLayer({
      id: 'zones-outline',
      type: 'line',
      source: 'zones',
      paint: { 'line-color': '#0f766e', 'line-width': 1.5 },
    });

    const hubPoints: GeoJSON.Feature[] = data.hubs.map((h) => ({
      type: 'Feature',
      geometry: { type: 'Point', coordinates: [h.lon, h.lat] },
      properties: { usage: h.usage, hub_id: h.hub_id },
    }));
    const maxUsage = Math.max(...data.hubs.map((h) => h.usage), 1);
    map.addSource('hubs', {
      type: 'geojson',
      data: { type: 'FeatureCollection', features: hubPoints },
    });
    map.addLayer({
      id: 'hubs',
      type: 'circle',
      source: 'hubs',
      paint: {
        'circle-radius': [
          '+',
          4,
          ['*', 12, ['/', ['get', 'usage'], maxUsage]],
        ],
        'circle-color': '#0f766e',
        'circle-stroke-width': 2,
        'circle-stroke-color': '#fff',
      },
    });
  }, [data, mapReady, layerMode]);

  const token = typeof window !== 'undefined' ? process.env.NEXT_PUBLIC_MAPBOX_TOKEN : null;

  if (!token) {
    return (
      <div className="w-full h-full rounded-xl border border-neutral-200 dark:border-neutral-800 bg-neutral-100 dark:bg-neutral-800 flex items-center justify-center">
        <div className="text-center p-6">
          <p className="text-neutral-600 dark:text-neutral-400 mb-2">
            Mapbox token not set
          </p>
          <p className="text-sm text-neutral-500">
            Add NEXT_PUBLIC_MAPBOX_TOKEN to .env.local to show the map. Zones and hubs will still appear in charts.
          </p>
          {data && (
            <div className="mt-4 p-4 bg-white dark:bg-neutral-900 rounded-lg text-left text-sm">
              <p>Zones: {data.zones_geojson.features.length}</p>
              <p>Hubs: {data.hubs.length}</p>
              <p>Assigned: {data.n_assigned}</p>
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="relative w-full h-full rounded-xl overflow-hidden border border-neutral-200 dark:border-neutral-800 shadow-sm">
      <div ref={containerRef} className="absolute inset-0" />
      <div className="absolute top-2 left-2 flex gap-2">
        <button
          type="button"
          onClick={() => setLayerMode('pollution')}
          className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-smooth ${
            layerMode === 'pollution'
              ? 'bg-teal-600 text-white'
              : 'bg-white/90 dark:bg-neutral-800/90 text-neutral-700 dark:text-neutral-300'
          }`}
        >
          Pollution
        </button>
        <button
          type="button"
          onClick={() => setLayerMode('congestion')}
          className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-smooth ${
            layerMode === 'congestion'
              ? 'bg-teal-600 text-white'
              : 'bg-white/90 dark:bg-neutral-800/90 text-neutral-700 dark:text-neutral-300'
          }`}
        >
          Congestion
        </button>
      </div>
      {loading && (
        <div className="absolute inset-0 bg-black/20 flex items-center justify-center">
          <div className="bg-white dark:bg-neutral-800 rounded-lg px-6 py-3 font-medium">
            Updating…
          </div>
        </div>
      )}
    </div>
  );
}
