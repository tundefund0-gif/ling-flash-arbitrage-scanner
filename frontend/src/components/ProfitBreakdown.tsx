import React from 'react';
import { formatUsd, formatBps, formatPct, profitColor } from '../utils/format';

interface Props {
  grossProfitUsd: number;
  netProfitUsd: number;
  profitBps: number;
  profitPct: number;
  gasCostUsd: number;
  flashLoanAmountUsd: number;
  flashLoanFeeBps: number;
}

export default function ProfitBreakdown({
  grossProfitUsd,
  netProfitUsd,
  profitBps,
  profitPct,
  gasCostUsd,
  flashLoanAmountUsd,
  flashLoanFeeBps,
}: Props) {
  return (
    <div className="profit-breakdown">
      <h4>Profit Breakdown</h4>
      <div className="profit-row">
        <span className="profit-label">Gross Profit</span>
        <span className="profit-value" style={{ color: profitColor(grossProfitUsd) }}>{formatUsd(grossProfitUsd)}</span>
      </div>
      <div className="profit-row">
        <span className="profit-label">Gas Cost</span>
        <span className="profit-value profit-cost">-{formatUsd(gasCostUsd)}</span>
      </div>
      <div className="profit-row">
        <span className="profit-label">Flash Loan Fee</span>
        <span className="profit-value profit-cost">-{formatUsd(flashLoanAmountUsd * flashLoanFeeBps / 10000)}</span>
      </div>
      <div className="profit-row highlight">
        <span className="profit-label">Net Profit</span>
        <span className="profit-value" style={{ color: profitColor(netProfitUsd) }}>{formatUsd(netProfitUsd)}</span>
      </div>
      <div className="profit-row">
        <span className="profit-label">Spread</span>
        <span className="profit-value">{formatBps(profitBps)} ({formatPct(profitPct)})</span>
      </div>
    </div>
  );
}