import React, { useRef, useEffect, useMemo } from 'react';
import type { ArbitrageOpportunity } from '../lib/types';
import { formatUsd, profitColor } from '../utils/format';

interface Props {
  opportunities: ArbitrageOpportunity[];
}

export default function ProfitChart({ opportunities }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  const buckets = useMemo(() => {
    const b: Record<string, number> = {};
    const ranges: [number, number, string][] = [
      [0, 1, '0–1'],
      [1, 5, '1–5'],
      [5, 10, '5–10'],
      [10, 25, '10–25'],
      [25, 50, '25–50'],
      [50, 100, '50–100'],
      [100, 250, '100–250'],
      [250, 500, '250–500'],
      [500, 999999, '500+'],
    ];
    for (const [lo, hi, label] of ranges) {
      b[label] = 0;
    }
    for (const o of opportunities) {
      const v = o.net_profit_usd;
      for (const [lo, hi, label] of ranges) {
        if (v >= lo && v < hi) { b[label]++; break; }
      }
    }
    return b;
  }, [opportunities]);

  const maxCount = useMemo(() => Math.max(1, ...Object.values(buckets)), [buckets]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.parentElement?.getBoundingClientRect();
    if (!rect) return;
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    canvas.style.width = rect.width + 'px';
    canvas.style.height = rect.height + 'px';
    ctx.scale(dpr, dpr);

    const w = rect.width;
    const h = rect.height;
    const pad = { top: 20, right: 16, bottom: 36, left: 44 };
    const chartW = w - pad.left - pad.right;
    const chartH = h - pad.top - pad.bottom;
    const labels = Object.keys(buckets);
    const n = labels.length;
    const barW = Math.max(8, Math.min(32, (chartW / n) * 0.7));
    const gap = chartW / n;

    ctx.clearRect(0, 0, w, h);

    ctx.strokeStyle = 'rgba(255,255,255,0.06)';
    ctx.lineWidth = 1;
    for (let i = 0; i <= 4; i++) {
      const y = pad.top + (chartH / 4) * i;
      ctx.beginPath();
      ctx.moveTo(pad.left, y);
      ctx.lineTo(w - pad.right, y);
      ctx.stroke();
      ctx.fillStyle = 'rgba(255,255,255,0.3)';
      ctx.font = '10px sans-serif';
      ctx.textAlign = 'right';
      ctx.fillText(String(Math.round(maxCount * (1 - i / 4))), pad.left - 6, y + 3);
    }

    labels.forEach((label, i) => {
      const count = buckets[label];
      const barH = (count / maxCount) * chartH;
      const x = pad.left + gap * i + (gap - barW) / 2;
      const y = pad.top + chartH - barH;

      const grad = ctx.createLinearGradient(x, y, x, pad.top + chartH);
      grad.addColorStop(0, '#6366f1');
      grad.addColorStop(1, '#22d3ee');
      ctx.fillStyle = grad;
      ctx.beginPath();
      ctx.roundRect(x, y, barW, barH, [3, 3, 0, 0]);
      ctx.fill();

      ctx.fillStyle = 'rgba(255,255,255,0.5)';
      ctx.font = '10px sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText(label, x + barW / 2, pad.top + chartH + 14);
    });
  }, [buckets, maxCount]);

  return (
    <div className="chart-card">
      <h4>Profit Distribution</h4>
      <canvas ref={canvasRef} style={{ width: '100%', height: 180 }} />
    </div>
  );
}