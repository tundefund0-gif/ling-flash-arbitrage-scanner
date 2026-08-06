const API_BASE = '/api';

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const resp = await fetch(url, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!resp.ok) {
    throw new Error(`API error: ${resp.status} ${resp.statusText}`);
  }
  return resp.json();
}

export const api = {
  health: () => fetchJson<{ status: string; timestamp: string }>(`${API_BASE}/healthz`),

  summary: () => fetchJson<{ total_opportunities: number; total_profit_usd: number; avg_profit_bps: number; best_profit_usd: number; best_profit_bps: number; pools_scanned: number; tokens_scanned: number; chains_active: string[]; scan_latency_ms: number; last_scan_at: string; gas_price_gwei: number; arb_gas_price_gwei: number }>(`${API_BASE}/scanner/summary`),

  networks: () => fetchJson<{ chain_id: number; chain_name: string; block_number: number; gas_price_gwei: number; base_fee_gwei: number; priority_fee_gwei: number; block_time_seconds: number; pools_scanned: number; tokens_tracked: number; last_update_at: string }[]>(`${API_BASE}/scanner/networks`),

  tokens: (chain = 42161, limit = 50) => fetchJson<{ chain_id: number; count: number; tokens: any[] }>(`${API_BASE}/scanner/tokens?chain=${chain}&limit=${limit}`),

  opportunities: (params?: { chain?: number; token?: string; minProfitBps?: number; limit?: number; minConfidence?: number }) => {
    const q = new URLSearchParams();
    if (params?.chain) q.set('chain', String(params.chain));
    if (params?.token) q.set('token', params.token);
    if (params?.minProfitBps) q.set('minProfitBps', String(params.minProfitBps));
    if (params?.limit) q.set('limit', String(params.limit));
    if (params?.minConfidence !== undefined) q.set('minConfidence', String(params.minConfidence));
    const qs = q.toString();
    return fetchJson<{ success: boolean; opportunities: any[]; total: number; filtered: number; limit: number }>(`${API_BASE}/scanner/opportunities${qs ? '?' + qs : ''}`);
  },

  opportunityDetail: (id: string) => fetchJson<{ success: boolean; opportunity: any }>(`${API_BASE}/scanner/opportunities/${id}`),

  scan: (request: any) => fetchJson<{ success: boolean; opportunities: any[]; summary: any; networks: any[]; scanned_at: string; scan_duration_ms: number }>(`${API_BASE}/scanner/scan`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  }),
};