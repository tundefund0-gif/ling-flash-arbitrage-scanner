import React, { useState, useCallback, useEffect, useMemo } from 'react';
import { useOpportunities } from './hooks/useOpportunities';
import { useWebSocket } from './hooks/useWebSocket';
import { useScanner } from './hooks/useScanner';
import SummaryCards from './components/SummaryCards';
import NetworkPulse from './components/NetworkPulse';
import FilterBar from './components/FilterBar';
import Dashboard from './components/Dashboard';
import LoadingState from './components/LoadingState';
import ErrorState from './components/ErrorState';
import EmptyState from './components/EmptyState';
import { IconBolt, IconRefresh, IconNetwork, IconLayers } from './components/icons';
import { api } from './lib/api';
import type { ScanFilters } from './lib/types';
import type { TokenMap } from './components/RouteChips';
import { useTokenMapFromOpps } from './components/RouteChips';
import { formatUsd } from './utils/format';

const DEFAULT_FILTERS: ScanFilters = {
  chain: 42161,
  token: '',
  minProfitBps: 0,
  minConfidence: 0,
  maxGasCostUsd: 50,
  limit: 500,
};

export default function App() {
  const [filters, setFilters] = useState<ScanFilters>(DEFAULT_FILTERS);
  const [activeTab, setActiveTab] = useState<'dashboard' | 'tokens' | 'networks'>('dashboard');
  const [tokenList, setTokenList] = useState<any[]>([]);

  const { opportunities, summary, networks, loading, error, refresh, lastScanAt } = useOpportunities(
    {
      chain: filters.chain,
      token: filters.token || undefined,
      minProfitBps: filters.minProfitBps,
      limit: filters.limit,
      minConfidence: filters.minConfidence,
    },
    true,
    15000,
  );

  const { connected: wsConnected } = useWebSocket();
  const { isScanning, triggerScan } = useScanner();

  useEffect(() => {
    api.tokens(42161, 300).then((r) => setTokenList(r.tokens || [])).catch(() => {});
  }, []);

  const oppMap = useTokenMapFromOpps(opportunities);
  const tokenMap: TokenMap = useMemo(() => {
    const m: TokenMap = { ...oppMap };
    for (const t of tokenList) {
      const a = t.address?.toLowerCase();
      if (a && !m[a]) m[a] = { symbol: t.symbol, name: t.name };
    }
    return m;
  }, [oppMap, tokenList]);

  const handleScan = useCallback(async () => {
    await triggerScan({
      chains: [filters.chain],
      min_profit_bps: filters.minProfitBps,
      min_confidence: filters.minConfidence,
      max_gas_cost_usd: filters.maxGasCostUsd,
      include_flashloan: true,
      limit: filters.limit,
    });
    refresh();
  }, [filters, triggerScan, refresh]);

  return (
    <>
      <div className="bg-canvas" />
      <div className="bg-grid" />
      <div className="bg-blob b1" />
      <div className="bg-blob b2" />
      <div className="bg-blob b3" />

      <div className="app-shell">
        <div className="topbar">
          <div className="brand">
            <div className="brand-logo"><IconBolt size={22} color="#06070d" /></div>
            <div>
              <div className="brand-title">Arbitrum <span className="accent">Arbitrage</span> Scanner</div>
              <div className="brand-sub">Real-time cross-DEX · triangular · multi-hop opportunity engine</div>
            </div>
          </div>
          <div className="topbar-right">
            <span className="live-pill"><span className="live-dot" />{wsConnected ? 'Live' : 'Polling'}</span>
            <div className="tabs">
              <button className={`tab ${activeTab === 'dashboard' ? 'active' : ''}`} onClick={() => setActiveTab('dashboard')}>Dashboard</button>
              <button className={`tab ${activeTab === 'tokens' ? 'active' : ''}`} onClick={() => setActiveTab('tokens')}>Tokens</button>
              <button className={`tab ${activeTab === 'networks' ? 'active' : ''}`} onClick={() => setActiveTab('networks')}>Networks</button>
            </div>
            <button className="btn" onClick={refresh} disabled={loading}>
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}><IconRefresh size={15} /> Refresh</span>
            </button>
          </div>
        </div>

        {error && <ErrorState message={error} onRetry={refresh} />}
        {loading && !opportunities.length && <LoadingState />}

        {!loading && !error && activeTab === 'dashboard' && (
          opportunities.length === 0 ? (
            <EmptyState onScan={handleScan} scanning={isScanning} />
          ) : (
            <Dashboard
              summary={summary}
              opportunities={opportunities}
              tokenMap={tokenMap}
              filters={filters}
              setFilters={setFilters}
              onScan={handleScan}
              scanning={isScanning}
              lastScanAt={lastScanAt}
            />
          )
        )}

        {!loading && !error && activeTab === 'networks' && (
          <div className="split">
            <div className="subhead-row"><h2><IconNetwork size={18} style={{ verticalAlign: '-3px', marginRight: 6 }} />Network Telemetry</h2></div>
            <NetworkPulse networks={networks} />
          </div>
        )}

        {!loading && !error && activeTab === 'tokens' && (
          <div className="split">
            <div className="subhead-row"><h2><IconLayers size={18} style={{ verticalAlign: '-3px', marginRight: 6 }} />Tracked Tokens</h2><span className="hint">{tokenList.length} discovered</span></div>
            <div className="card" style={{ padding: 18 }}>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10 }}>
                {tokenList.map((t, i) => (
                  <div key={i} className="chip" style={{ padding: '8px 12px' }}>
                    <span className="tok" style={{ fontWeight: 700 }}>{t.symbol}</span>
                    <span style={{ color: 'var(--muted-2)', fontSize: 11, marginLeft: 8 }}>{formatUsd(t.price_usd || 0)}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        <div style={{ textAlign: 'center', color: 'var(--muted-2)', fontSize: 12, marginTop: 30 }}>
          DexScreener data · indicative signals only · not financial advice
        </div>
      </div>
    </>
  );
}
