import React from 'react';
import type { ArbitrageOpportunity } from '../lib/types';
import { RouteChips, TokenBadge, type TokenMap, sym } from './RouteChips';
import { IconClose, IconArrow } from './icons';
import { formatUsd, formatBps, formatPct, scoreColor } from '../utils/format';

export default function OpportunityDetail({
  opp,
  tokenMap,
  onClose,
}: {
  opp: ArbitrageOpportunity;
  tokenMap: TokenMap;
  onClose: () => void;
}) {
  if (!opp) return null;

  const net = opp.net_profit_usd;
  const gross = opp.gross_profit_usd;
  const gas = opp.gas_cost_usd;
  const cf = opp.confidence_factors || {};
  const cm = opp.competition_metrics || {};

  const bars = (obj: Record<string, number>, color: string) =>
    Object.entries(obj).map(([k, v]) => (
      <div className="barrow" key={k}>
        <div className="bl"><span style={{ textTransform: 'capitalize' }}>{k.replace(/_/g, ' ')}</span><span className="tabnum">{(v * 100).toFixed(0)}%</span></div>
        <div className="bartrack"><i style={{ width: `${Math.round((v as number) * 100)}%`, background: color }} /></div>
      </div>
    ));

  return (
    <>
      <div className="scrim" onClick={onClose} />
      <aside className="drawer">
        <div className="drawer-head">
          <div className="tok-cell">
            <TokenBadge tokenMap={tokenMap} addr={opp.token_in_address} />
            <div>
              <h2>{opp.token_in_symbol} Arbitrage</h2>
              <div className="tag" style={{ marginTop: 6 }}>{opp.route_legs.length}-hop cycle · {opp.execution_risk} risk</div>
            </div>
          </div>
          <button className="x-btn" onClick={onClose}><IconClose size={16} /></button>
        </div>

        <div className="metric-grid">
          <div className="metric">
            <div className="l">Net Profit</div>
            <div className="n" style={{ color: net > 0 ? 'var(--green)' : 'var(--red)' }}>{formatUsd(net)}</div>
          </div>
          <div className="metric">
            <div className="l">Gross Profit</div>
            <div className="n">{formatUsd(gross)}</div>
          </div>
          <div className="metric">
            <div className="l">Spread</div>
            <div className="n">{formatBps(opp.profit_bps)}</div>
          </div>
          <div className="metric">
            <div className="l">Gas Cost</div>
            <div className="n">{formatUsd(gas)}</div>
          </div>
        </div>

        <div className="section-title">Execution Route</div>
        <div className="flow">
          {opp.route_legs.map((leg, i) => (
            <React.Fragment key={i}>
              <div className="flow-step">
                <div className="num">{i + 1}</div>
                <div>
                  <div className="pair">
                    {sym(tokenMap, leg.token_in)} <span style={{ color: 'var(--muted-2)' }}>→</span> {sym(tokenMap, leg.token_out)}
                  </div>
                  <div className="dex">{leg.dex_name} · {leg.pool_type}</div>
                </div>
                <div className="amt">
                  <div>in {formatUsd(leg.amount_in)}</div>
                  <div>out {formatUsd(leg.amount_out)}</div>
                </div>
              </div>
              {i < opp.route_legs.length - 1 && <div className="flow-connector">↓</div>}
            </React.Fragment>
          ))}
        </div>

        <div className="section-title">Profit Breakdown</div>
        <div className="metric-grid">
          <div className="metric">
            <div className="l">Gross</div><div className="n">{formatUsd(gross)}</div>
          </div>
          <div className="metric">
            <div className="l">Gas & Fees</div><div className="n" style={{ color: 'var(--amber)' }}>−{formatUsd(gas)}</div>
          </div>
          <div className="metric">
            <div className="l">Flashloan Fee</div><div className="n" style={{ color: 'var(--muted)' }}>{(opp.flash_loan_fee_bps / 100).toFixed(1)}%</div>
          </div>
          <div className="metric">
            <div className="l">ROI</div><div className="n">{formatPct(opp.profit_pct)}</div>
          </div>
        </div>

        <div className="section-title">Confidence Factors</div>
        {bars(cf, 'linear-gradient(90deg,#6366f1,#22d3ee)')}

        <div className="section-title" style={{ marginTop: 18 }}>Competition Metrics</div>
        {bars(cm, 'linear-gradient(90deg,#34d399,#22d3ee)')}

        <div className="reco">
          <b>Strategy:</b> {opp.recommended_action}
        </div>

        <div className="section-title" style={{ marginTop: 18 }}>Pools</div>
        {[opp.buy_pool, opp.sell_pool].map((p, i) => (
          <div className="kv" key={i}>
            <span className="k">{i === 0 ? 'Entry' : 'Exit'} · {p.dex_name}</span>
            <span className="mono">{p.address.slice(0, 10)}…{p.address.slice(-6)}</span>
          </div>
        ))}

        <div className="engine-note">
          Prices derived from each pool's on-chain liquidity split; profit is slippage-aware
          (constant-product model) and net of gas. Figures are indicative, not executable quotes.
        </div>
      </aside>
    </>
  );
}
