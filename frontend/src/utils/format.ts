export function formatUsd(value: number, decimals = 2): string {
  if (value === undefined || value === null) return '$0.00';
  if (Math.abs(value) >= 1_000_000) return `$${(value / 1_000_000).toFixed(2)}M`;
  if (Math.abs(value) >= 1_000) return `$${(value / 1_000).toFixed(2)}K`;
  return `$${value.toFixed(decimals)}`;
}

export function formatBps(value: number): string {
  return `${value.toFixed(1)} bps`;
}

export function formatPct(value: number, decimals = 2): string {
  return `${value.toFixed(decimals)}%`;
}

export function formatGwei(value: number): string {
  return `${value.toFixed(2)} Gwei`;
}

export function formatAddress(addr: string): string {
  if (!addr) return '';
  return `${addr.slice(0, 6)}...${addr.slice(-4)}`;
}

export function formatNumber(value: number, decimals = 4): string {
  if (Math.abs(value) >= 1_000_000) return `${(value / 1_000_000).toFixed(2)}M`;
  if (Math.abs(value) >= 1_000) return `${(value / 1_000).toFixed(2)}K`;
  return value.toFixed(decimals);
}

export function formatDuration(ms: number): string {
  if (ms < 1000) return `${ms.toFixed(0)}ms`;
  if (ms < 60_000) return `${(ms / 1000).toFixed(1)}s`;
  return `${(ms / 60_000).toFixed(1)}m`;
}

export function timeAgo(dateStr: string): string {
  const now = Date.now();
  const then = new Date(dateStr).getTime();
  const diff = now - then;
  if (diff < 5000) return 'just now';
  if (diff < 60_000) return `${Math.floor(diff / 1000)}s ago`;
  if (diff < 3_600_000) return `${Math.floor(diff / 60_000)}m ago`;
  if (diff < 86_400_000) return `${Math.floor(diff / 3_600_000)}h ago`;
  return `${Math.floor(diff / 86_400_000)}d ago`;
}

export function clamp(value: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, value));
}

export function scoreColor(score: number): string {
  if (score >= 0.8) return '#10b981';
  if (score >= 0.6) return '#22c55e';
  if (score >= 0.4) return '#eab308';
  if (score >= 0.2) return '#f97316';
  return '#ef4444';
}

export function profitColor(netProfitUsd: number): string {
  if (netProfitUsd > 100) return '#10b981';
  if (netProfitUsd > 10) return '#22c55e';
  if (netProfitUsd > 1) return '#eab308';
  return '#ef4444';
}

export function riskColor(risk: string): string {
  switch (risk) {
    case 'low': return '#10b981';
    case 'medium': return '#eab308';
    case 'high': return '#ef4444';
    default: return '#6b7280';
  }
}

export function competitionLabel(score: number): string {
  if (score >= 0.7) return 'Low';
  if (score >= 0.4) return 'Moderate';
  if (score >= 0.2) return 'High';
  return 'Very High';
}

export function confidenceLabel(score: number): string {
  if (score >= 0.8) return 'Very High';
  if (score >= 0.6) return 'High';
  if (score >= 0.4) return 'Medium';
  if (score >= 0.2) return 'Low';
  return 'Very Low';
}