import { useState, useEffect, useCallback, useRef } from 'react';
import { api } from '../lib/api';
import type { ArbitrageOpportunity, ScannerSummary, NetworkTelemetry } from '../lib/types';

interface UseOpportunitiesReturn {
  opportunities: ArbitrageOpportunity[];
  summary: ScannerSummary | null;
  networks: NetworkTelemetry[];
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
  lastScanAt: string | null;
}

export function useOpportunities(
  filters: { chain?: number; token?: string; minProfitBps?: number; limit?: number; minConfidence?: number } = {},
  autoRefresh = true,
  refreshIntervalMs = 15000,
): UseOpportunitiesReturn {
  const [opportunities, setOpportunities] = useState<ArbitrageOpportunity[]>([]);
  const [summary, setSummary] = useState<ScannerSummary | null>(null);
  const [networks, setNetworks] = useState<NetworkTelemetry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastScanAt, setLastScanAt] = useState<string | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchData = useCallback(async () => {
    try {
      setError(null);
      const [oppResult, summaryResult, networksResult] = await Promise.all([
        api.opportunities(filters),
        api.summary(),
        api.networks(),
      ]);

      setOpportunities(oppResult.opportunities || []);
      setSummary(summaryResult);
      setNetworks(networksResult);
      setLastScanAt(new Date().toISOString());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch data');
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    fetchData();

    if (autoRefresh) {
      intervalRef.current = setInterval(fetchData, refreshIntervalMs);
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [fetchData, autoRefresh, refreshIntervalMs]);

  return {
    opportunities,
    summary,
    networks,
    loading,
    error,
    refresh: fetchData,
    lastScanAt,
  };
}