import React from 'react';
import { formatUsd, formatGwei } from '../utils/format';

interface Props {
  gasLimit: number;
  gasPriceGwei: number;
  estimatedCostUsd: number;
  operation: string;
}

export default function GasEstimate({ gasLimit, gasPriceGwei, estimatedCostUsd, operation }: Props) {
  return (
    <div className="gas-estimate">
      <h4>Gas Estimate</h4>
      <div className="gas-grid">
        <div className="gas-item">
          <span className="gas-label">Operation</span>
          <span className="gas-value">{operation}</span>
        </div>
        <div className="gas-item">
          <span className="gas-label">Gas Limit</span>
          <span className="gas-value">{gasLimit.toLocaleString()}</span>
        </div>
        <div className="gas-item">
          <span className="gas-label">Gas Price</span>
          <span className="gas-value">{formatGwei(gasPriceGwei)}</span>
        </div>
        <div className="gas-item highlight">
          <span className="gas-label">Est. Cost</span>
          <span className="gas-value">{formatUsd(estimatedCostUsd)}</span>
        </div>
      </div>
    </div>
  );
}