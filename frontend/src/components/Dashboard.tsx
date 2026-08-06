import React, { useState } from 'react';
import type { ArbitrageOpportunity, ScannerSummary, ScanFilters } from '../lib/types';
import SummaryCards from './SummaryCards';
import ProfitChart from './ProfitChart';
import FilterBar from './FilterBar';
import OpportunityTable from './OpportunityTable';
import OpportunityDetail from './OpportunityDetail';
import type { TokenMap } from './RouteChips';
import { formatDuration } from '../utils/format';

export default function Dashboard({
  summary,
  opportunities,
  tokenMap,
  filters,
  setFilters,
  onScan,
  scanning,
  lastScanAt,
}: {
  summary: ScannerSummary | null;
  opportunities: ArbitrageOpportunity[];
  tokenMap: TokenMap;
  filters: ScanFilters;
  setFilters: React.Dispatch<React.SetStateAction<ScanFilters>>;
  onScan: () => void;
  scanning: boolean;
  lastScanAt: string | null;
}) {
  const [selected, setSelected] = useState<ArbitrageOpportunity | null>(null);

  return (
    <>
      <SummaryCards summary={summary} opportunities={opportunities} />

      <ProfitChart opportunities={opportunities} />

      <FilterBar filters={filters} setFilters={setFilters} onScan={onScan} scanning={scanning} />

      <div className="subhead-row">
        <h2>Arbitrage Opportunities</h2>
        <span className="hint">
          {opportunities.length} shown
          {lastScanAt ? ` · updated ${formatDuration(Date.now() - new Date(lastScanAt).getTime())} ago` : ''}
        </span>
      </div>

      <OpportunityTable opportunities={opportunities} tokenMap={tokenMap} onSelect={setSelected} />

      <div className="engine-note">
        <b>Engine:</b> prices are derived per-pool from on-chain liquidity (no stale aggregates), profit is
        slippage-aware via a constant-product model, and only pools whose local price is consistent with the
        market are considered. All figures are indicative scanner signals.
      </div>

      {selected && (
        <OpportunityDetail opp={selected} tokenMap={tokenMap} onClose={() => setSelected(null)} />
      )}
    </>
  );
}
