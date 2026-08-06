import React from 'react';
import type { ScannerSummary, ArbitrageOpportunity } from '../lib/types';
import { IconBolt, IconTrend, IconDrop, IconLayers } from './icons';
import { formatUsd, formatBps, formatNumber } from '../utils/format';

interface Props {
  summary: ScannerSummary | null;
  opportunities: ArbitrageOpportunity[];
}

export default function SummaryCards({ summary, opportunities }: Props) {
  const total = opportunities.length;
  const totalProfit = opportunities.reduce((s, o) => s + o.net_profit_usd, 0);
  const best = opportunities.reduce((m, o) => (o.net_profit_usd > m.net_profit_usd ? o : m), opportunities[0]);
  const avgBps = total ? opportunities.reduce((s, o) => s + o.profit_bps, 0) / total : 0;
  const avgConf = total ? opportunities.reduce((s, o) => s + o.confidence_score, 0) / total : 0;
  const crossChain = summary?.chains_active?.length ?? 1;

  const cards = [
    {
      ic: <IconBolt size={20} color="#22d3ee" />,
      label: 'Live Opportunities',
      value: formatNumber(total, 0),
      sub: `${summary?.pools_scanned ? formatNumber(summary.pools_scanned, 0) : 0} pools · ${summary?.tokens_scanned ? formatNumber(summary.tokens_scanned, 0) : 0} tokens`,
      grad: false,
    },
    {
      ic: <IconTrend size={20} color="#34d399" />,
      label: 'Total Net Profit',
      value: formatUsd(totalProfit),
      sub: `${crossChain} chain · after gas & fees`,
      grad: true,
    },
    {
      ic: <IconDrop size={20} color="#a855f7" />,
      label: 'Best Single Arb',
      value: best ? formatUsd(best.net_profit_usd) : '$0',
      sub: best ? `${best.token_in_symbol} · ${formatBps(best.profit_bps)}` : '—',
      grad: false,
    },
    {
      ic: <IconLayers size={20} color="#6366f1" />,
      label: 'Avg Spread / Confidence',
      value: `${avgBps.toFixed(0)} bps`,
      sub: `conf ${(avgConf * 100).toFixed(0)}%`,
      grad: false,
    },
  ];

  return (
    <div className="summary-grid">
      {cards.map((c, i) => (
        <div className="stat-card" key={i}>
          <div className="ic">{c.ic}</div>
          <div className="stat-label">{c.label}</div>
          <div className={`stat-value tabnum ${c.grad ? 'grad' : ''}`}>{c.value}</div>
          <div className="stat-sub">{c.sub}</div>
        </div>
      ))}
    </div>
  );
}
