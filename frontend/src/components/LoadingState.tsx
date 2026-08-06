import React from 'react';
import { IconRefresh } from './icons';

export default function LoadingState() {
  return (
    <div className="state">
      <div className="spinner" />
      <div>Scanning Arbitrum pools for live arbitrage opportunities…</div>
    </div>
  );
}
