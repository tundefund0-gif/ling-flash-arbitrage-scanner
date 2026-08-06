import React, { useState, useMemo, useEffect } from 'react';
import type { ArbitrageOpportunity } from '../lib/types';
import { RouteChips, TokenBadge, type TokenMap } from './RouteChips';
import { formatUsd, formatBps, scoreColor } from '../utils/format';

type SortKey = 'net_profit_usd' | 'profit_bps' | 'confidence_score' | 'gas_cost_usd' | 'execution_risk';

const riskPill = (r: string) => (r === 'low' ? 'green' : r === 'medium' ? 'amber' : 'red');
const hopPill = (n: number) => (n === 2 ? 'cyan' : n === 3 ? 'violet' : 'amber');

const PAGE_SIZES = [25, 50, 100];

export default function OpportunityTable({
  opportunities,
  tokenMap,
  onSelect,
}: {
  opportunities: ArbitrageOpportunity[];
  tokenMap: TokenMap;
  onSelect: (o: ArbitrageOpportunity) => void;
}) {
  const [sort, setSort] = useState<{ key: SortKey; dir: 'asc' | 'desc' }>({
    key: 'net_profit_usd',
    dir: 'desc',
  });
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(50);

  const sorted = useMemo(() => {
    const arr = [...opportunities];
    const dir = sort.dir === 'asc' ? 1 : -1;
    const key = sort.key;
    const rank = (r: string) => (r === 'low' ? 0 : r === 'medium' ? 1 : 2);
    arr.sort((a: any, b: any) => {
      const va = key === 'execution_risk' ? rank(a[key]) : a[key];
      const vb = key === 'execution_risk' ? rank(b[key]) : b[key];
      return (va - vb) * dir;
    });
    return arr;
  }, [opportunities, sort]);

  const totalPages = Math.max(1, Math.ceil(sorted.length / pageSize));
  const paged = useMemo(() => sorted.slice(page * pageSize, (page + 1) * pageSize), [sorted, page, pageSize]);

  useEffect(() => {
    if (page >= totalPages) setPage(Math.max(0, totalPages - 1));
  }, [page, totalPages]);

  const toggle = (key: SortKey) =>
    setSort((s) => (s.key === key ? { key, dir: s.dir === 'desc' ? 'asc' : 'desc' } : { key, dir: 'desc' }));

  const Th = ({ k, children, right }: { k: SortKey; children: React.ReactNode; right?: boolean }) => (
    <th onClick={() => toggle(k)} style={{ textAlign: right ? 'right' : 'left' }}>
      {children}
      <span className="arrow">{sort.key === k ? (sort.dir === 'desc' ? '▾' : '▴') : '⇅'}</span>
    </th>
  );

  return (
    <div className="table-wrap">
      <div className="table-scroll">
        <table className="opps">
          <thead>
            <tr>
              <th>Route</th>
              <th style={{ textAlign: 'center' }}>Hops</th>
              <Th k="net_profit_usd" right>Net Profit</Th>
              <Th k="profit_bps">Spread</Th>
              <Th k="confidence_score">Confidence</Th>
              <Th k="execution_risk">Risk</Th>
              <Th k="gas_cost_usd" right>Gas</Th>
            </tr>
          </thead>
          <tbody>
            {paged.map((o) => {
              const hops = o.route_legs.length;
              return (
                <tr key={o.id} onClick={() => onSelect(o)}>
                  <td>
                    <div className="tok-cell">
                      <TokenBadge tokenMap={tokenMap} addr={o.token_in_address} />
                      <div>
                        <div style={{ fontWeight: 700 }}>{o.token_in_symbol}</div>
                        <RouteChips legs={o.route_legs} tokenMap={tokenMap} />
                      </div>
                    </div>
                  </td>
                  <td style={{ textAlign: 'center' }}>
                    <span className={`pill ${hopPill(hops)}`}>{hops}-hop</span>
                  </td>
                  <td style={{ textAlign: 'right' }}>
                    <span className="profit-strong" style={{ color: o.net_profit_usd > 0 ? 'var(--green)' : 'var(--red)' }}>
                      {formatUsd(o.net_profit_usd)}
                    </span>
                  </td>
                  <td>
                    <span className="pill green">{formatBps(o.profit_bps)}</span>
                  </td>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <div className="cbar"><i style={{ width: `${Math.round(o.confidence_score * 100)}%`, background: scoreColor(o.confidence_score) }} /></div>
                      <span className="tabnum" style={{ fontSize: 12, color: 'var(--muted)' }}>{(o.confidence_score * 100).toFixed(0)}%</span>
                    </div>
                  </td>
                  <td>
                    <span className={`pill ${riskPill(o.execution_risk)}`}>{o.execution_risk}</span>
                  </td>
                  <td style={{ textAlign: 'right' }} className="tabnum">{formatUsd(o.gas_cost_usd)}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      <div className="pagination">
        <span className="pag-info">{sorted.length} total</span>
        <button className="pag-btn" disabled={page === 0} onClick={() => setPage((p) => p - 1)}>‹</button>
        <span className="pag-page">{page + 1} / {totalPages}</span>
        <button className="pag-btn" disabled={page >= totalPages - 1} onClick={() => setPage((p) => p + 1)}>›</button>
        <select className="pag-size" value={pageSize} onChange={(e) => { setPageSize(Number(e.target.value)); setPage(0); }}>
          {PAGE_SIZES.map((s) => <option key={s} value={s}>{s}/page</option>)}
        </select>
      </div>
    </div>
  );
}
