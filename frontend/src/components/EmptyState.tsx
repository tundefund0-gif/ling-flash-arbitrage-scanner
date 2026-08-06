import React from 'react';
import { IconBolt } from './icons';

export default function EmptyState({ onScan, scanning }: { onScan?: () => void; scanning?: boolean }) {
  return (
    <div className="state">
      <div className="em">📊</div>
      <div>No arbitrage opportunities match the current filters.</div>
      <div style={{ color: 'var(--muted-2)', fontSize: 13, marginTop: 6 }}>
        Try lowering the minimum profit or confidence threshold.
      </div>
      {onScan && (
        <button className="btn btn-primary empty-cta" onClick={onScan} disabled={scanning}>
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: 8 }}><IconBolt size={15} /> {scanning ? 'Scanning…' : 'Run Scan'}</span>
        </button>
      )}
    </div>
  );
}
