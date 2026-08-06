import React from 'react';
import type { ScanFilters } from '../lib/types';
import { IconBolt } from './icons';

export default function FilterBar({
  filters,
  setFilters,
  onScan,
  scanning,
}: {
  filters: ScanFilters;
  setFilters: React.Dispatch<React.SetStateAction<ScanFilters>>;
  onScan: () => void;
  scanning: boolean;
}) {
  return (
    <div className="card filterbar">
      <div className="field">
        <label>Min Profit (bps)</label>
        <div className="range-row">
          <input
            className="range"
            type="range"
            min={0}
            max={200}
            step={1}
            value={filters.minProfitBps}
            onChange={(e) => setFilters((f) => ({ ...f, minProfitBps: Number(e.target.value) }))}
          />
          <span className="tabnum" style={{ fontWeight: 700, minWidth: 42 }}>{filters.minProfitBps}</span>
        </div>
      </div>

      <div className="field">
        <label>Min Confidence</label>
        <div className="range-row">
          <input
            className="range"
            type="range"
            min={0}
            max={100}
            step={5}
            value={Math.round(filters.minConfidence * 100)}
            onChange={(e) => setFilters((f) => ({ ...f, minConfidence: Number(e.target.value) / 100 }))}
          />
          <span className="tabnum" style={{ fontWeight: 700, minWidth: 42 }}>{Math.round(filters.minConfidence * 100)}%</span>
        </div>
      </div>

      <div className="field">
        <label>Max Gas ($)</label>
        <select className="select" value={filters.maxGasCostUsd} onChange={(e) => setFilters((f) => ({ ...f, maxGasCostUsd: Number(e.target.value) }))}>
          <option value={10}>$10</option>
          <option value={25}>$25</option>
          <option value={50}>$50</option>
          <option value={100}>$100</option>
          <option value={1000}>Any</option>
        </select>
      </div>

      <div className="field">
        <label>Token Filter</label>
        <input
          className="input"
          placeholder="e.g. ARB, WETH"
          value={filters.token}
          onChange={(e) => setFilters((f) => ({ ...f, token: e.target.value }))}
        />
      </div>

      <div className="field">
        <label>Limit</label>
        <select className="select" value={filters.limit} onChange={(e) => setFilters((f) => ({ ...f, limit: Number(e.target.value) }))}>
          <option value={50}>50</option>
          <option value={100}>100</option>
          <option value={200}>200</option>
          <option value={500}>500</option>
          <option value={1000}>1000</option>
        </select>
      </div>

      <div className="spacer" />
      <button className="btn btn-primary" onClick={onScan} disabled={scanning}>
        <span style={{ display: 'inline-flex', alignItems: 'center', gap: 8 }}>
          <IconBolt size={16} /> {scanning ? 'Scanning…' : 'Run Scan'}
        </span>
      </button>
    </div>
  );
}
