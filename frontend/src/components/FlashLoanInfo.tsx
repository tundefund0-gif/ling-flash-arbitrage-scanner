import React from 'react';
import { formatUsd } from '../utils/format';
import type { FlashLoanQuote } from '../lib/types';

interface Props {
  quote: FlashLoanQuote;
}

export default function FlashLoanInfo({ quote }: Props) {
  return (
    <div className="flashloan-info">
      <h4>Flash Loan Quote</h4>
      <div className="flashloan-grid">
        <div className="flashloan-item">
          <span className="flashloan-label">Provider</span>
          <span className="flashloan-value">{quote.provider}</span>
        </div>
        <div className="flashloan-item">
          <span className="flashloan-label">Amount</span>
          <span className="flashloan-value">{formatUsd(quote.amount_usd)}</span>
        </div>
        <div className="flashloan-item">
          <span className="flashloan-label">Fee</span>
          <span className="flashloan-value">{quote.fee_bps} bps</span>
        </div>
        <div className="flashloan-item">
          <span className="flashloan-label">Total Cost</span>
          <span className="flashloan-value">{formatUsd(quote.total_cost_usd)}</span>
        </div>
        <div className="flashloan-item">
          <span className="flashloan-label">Available Liquidity</span>
          <span className="flashloan-value">{formatUsd(quote.available_liquidity_usd)}</span>
        </div>
        <div className="flashloan-item">
          <span className="flashloan-label">Duration</span>
          <span className="flashloan-value">{quote.duration_blocks} block(s)</span>
        </div>
      </div>
    </div>
  );
}