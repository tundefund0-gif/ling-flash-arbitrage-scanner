import { useState, useEffect, useCallback, useRef } from 'react';
import { api } from '../lib/api';
import type { ScanResponse } from '../lib/types';

interface UseScannerReturn {
  isScanning: boolean;
  lastResult: ScanResponse | null;
  error: string | null;
  triggerScan: (request?: { chains?: number[]; tokens?: string[]; min_profit_bps?: number; min_confidence?: number; max_gas_cost_usd?: number; include_flashloan?: boolean; limit?: number }) => Promise<void>;
}

export function useScanner(): UseScannerReturn {
  const [isScanning, setIsScanning] = useState(false);
  const [lastResult, setLastResult] = useState<ScanResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const triggerScan = useCallback(async (request?: {
    chains?: number[];
    tokens?: string[];
    min_profit_bps?: number;
    min_confidence?: number;
    max_gas_cost_usd?: number;
    include_flashloan?: boolean;
    limit?: number;
  }) => {
    setIsScanning(true);
    setError(null);
    try {
      const result = await api.scan(request || {
        chains: [42161],
        min_profit_bps: 10,
        min_confidence: 0.3,
        include_flashloan: true,
        limit: 50,
      });
      setLastResult(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Scan failed');
    } finally {
      setIsScanning(false);
    }
  }, []);

  return { isScanning, lastResult, error, triggerScan };
}