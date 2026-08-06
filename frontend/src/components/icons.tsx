import React from 'react';

type P = { size?: number; color?: string; style?: React.CSSProperties };
const base = (size = 18, color = 'currentColor') => ({
  width: size, height: size, viewBox: '0 0 24 24', fill: 'none',
  stroke: color, strokeWidth: 2, strokeLinecap: 'round' as const, strokeLinejoin: 'round' as const,
});

export const IconBolt = ({ size, color }: P) => (
  <svg {...base(size, color)}><path d="M13 2 3 14h7l-1 8 10-12h-7l1-8z" /></svg>
);
export const IconTrend = ({ size, color }: P) => (
  <svg {...base(size, color)}><path d="M3 17l6-6 4 4 8-8" /><path d="M21 7v6h-6" /></svg>
);
export const IconLayers = ({ size, color }: P) => (
  <svg {...base(size, color)}><path d="M12 2 2 7l10 5 10-5-10-5z" /><path d="M2 17l10 5 10-5" /><path d="M2 12l10 5 10-5" /></svg>
);
export const IconDrop = ({ size, color }: P) => (
  <svg {...base(size, color)}><path d="M12 2s7 7.5 7 12a7 7 0 0 1-14 0c0-4.5 7-12 7-12z" /></svg>
);
export const IconGas = ({ size, color }: P) => (
  <svg {...base(size, color)}><path d="M3 21V5a2 2 0 0 1 2-2h7a2 2 0 0 1 2 2v16" /><path d="M3 13h13" /><path d="M16 8h2a2 2 0 0 1 2 2v7a2 2 0 0 0 2 2 2 2 0 0 0 2-2V9l-4-3" /></svg>
);
export const IconShield = ({ size, color }: P) => (
  <svg {...base(size, color)}><path d="M12 2 4 5v6c0 5 3.5 8.5 8 11 4.5-2.5 8-6 8-11V5l-8-3z" /></svg>
);
export const IconNetwork = ({ size, color }: P) => (
  <svg {...base(size, color)}><circle cx="12" cy="12" r="3" /><circle cx="5" cy="6" r="2" /><circle cx="19" cy="6" r="2" /><circle cx="5" cy="18" r="2" /><circle cx="19" cy="18" r="2" /><path d="M6.7 7.2 10 10.5M17.3 7.2 14 10.5M6.7 16.8 10 13.5M17.3 16.8 14 13.5" /></svg>
);
export const IconRefresh = ({ size, color }: P) => (
  <svg {...base(size, color)}><path d="M21 12a9 9 0 1 1-3-6.7" /><path d="M21 3v5h-5" /></svg>
);
export const IconClose = ({ size, color }: P) => (
  <svg {...base(size, color)}><path d="M18 6 6 18M6 6l12 12" /></svg>
);
export const IconArrow = ({ size, color }: P) => (
  <svg {...base(size, color)}><path d="M5 12h14M13 6l6 6-6 6" /></svg>
);
export const IconChevron = ({ size, color }: P) => (
  <svg {...base(size, color)}><path d="M9 6l6 6-6 6" /></svg>
);
export const IconFlask = ({ size, color }: P) => (
  <svg {...base(size, color)}><path d="M9 3h6M10 3v6l-5 9a2 2 0 0 0 2 3h10a2 2 0 0 0 2-3l-5-9V3" /></svg>
);
export const IconActivity = ({ size, color }: P) => (
  <svg {...base(size, color)}><path d="M22 12h-4l-3 9L9 3l-3 9H2" /></svg>
);

export const DexGlyph = ({ dex }: { dex: string }) => {
  const d = (dex || '').toLowerCase();
  let c = '#22d3ee';
  if (d.includes('uniswap')) c = '#ff007a';
  else if (d.includes('camelot')) c = '#f9d423';
  else if (d.includes('curve')) c = '#ffd23f';
  else if (d.includes('sushi')) c = '#fa52a0';
  else if (d.includes('balancer')) c = '#c2i'.length ? '#ededed' : '#fff';
  else if (d.includes('pancake')) c = '#d1884f';
  else if (d.includes('trader')) c = '#ef4444';
  else if (d.includes('solidly')) c = '#a855f7';
  return (
    <span style={{ width: 8, height: 8, borderRadius: 2, background: c, display: 'inline-block' }} />
  );
};
