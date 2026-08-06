import React from 'react';
import { formatUsd, formatBps, scoreColor, profitColor } from '../utils/format';

interface Props {
  score: number;
  label: string;
  size?: 'sm' | 'md' | 'lg';
}

export default function ScoreBadge({ score, label, size = 'md' }: Props) {
  const sizeClass = `score-badge-${size}`;
  return (
    <div className={`score-badge ${sizeClass}`}>
      <div className="score-badge-circle" style={{ borderColor: scoreColor(score) }}>
        <span className="score-badge-value" style={{ color: scoreColor(score) }}>
          {(score * 100).toFixed(0)}%
        </span>
      </div>
      <span className="score-badge-label">{label}</span>
    </div>
  );
}