import React from 'react';
import type { NetworkTelemetry } from '../lib/types';
import { IconNetwork } from './icons';
import { formatGwei, formatNumber } from '../utils/format';

export default function NetworkPulse({ networks }: { networks: NetworkTelemetry[] }) {
  return (
    <div className="net-grid">
      {(networks && networks.length ? networks : [{ chain_id: 42161, chain_name: 'Arbitrum', block_number: 0, gas_price_gwei: 0, base_fee_gwei: 0, priority_fee_gwei: 0, block_time_seconds: 0.25 }]).map((n, i) => (
        <div className="card net-card" key={i}>
          <div className="nh">
            <div className="nm"><IconNetwork size={18} color="#22d3ee" style={{ marginRight: 8, verticalAlign: '-3px' }} />{n.chain_name}</div>
            <span className="tag">#{n.chain_id}</span>
          </div>
          <div className="net-stat"><span>Block</span><span className="tabnum">#{formatNumber(n.block_number, 0)}</span></div>
          <div className="net-stat"><span>Gas Price</span><span className="tabnum">{formatGwei(n.gas_price_gwei)}</span></div>
          <div className="net-stat"><span>Base Fee</span><span className="tabnum">{formatGwei(n.base_fee_gwei)}</span></div>
          <div className="net-stat"><span>Priority Fee</span><span className="tabnum">{formatGwei(n.priority_fee_gwei)}</span></div>
          <div className="net-stat"><span>Block Time</span><span className="tabnum">{n.block_time_seconds}s</span></div>
        </div>
      ))}
    </div>
  );
}
