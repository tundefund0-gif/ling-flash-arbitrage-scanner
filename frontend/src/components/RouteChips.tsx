import React from 'react';
export interface TokenMap {
  [addr: string]: { symbol: string; name: string };
}

export function useTokenMapFromOpps(opps: any[]): TokenMap {
  const map: TokenMap = {};
  for (const o of opps) {
    const push = (p: any) => {
      if (p?.token0) map[p.token0.address?.toLowerCase()] = { symbol: p.token0.symbol, name: p.token0.name };
      if (p?.token1) map[p.token1.address?.toLowerCase()] = { symbol: p.token1.symbol, name: p.token1.name };
    };
    push(o.buy_pool);
    push(o.sell_pool);
  }
  return map;
}

export function sym(tokenMap: TokenMap, addr: string, fallback = '?'): string {
  const a = (addr || '').toLowerCase();
  return tokenMap[a]?.symbol || (addr ? `${addr.slice(0, 6)}…` : fallback);
}

export function TokenBadge({ tokenMap, addr }: { tokenMap: TokenMap; addr: string }) {
  const s = sym(tokenMap, addr, '?');
  return (
    <span className="tok-badge" style={{
      display: 'inline-grid', placeItems: 'center', width: 22, height: 22, borderRadius: '50%',
      background: 'linear-gradient(135deg,#6366f1,#22d3ee)', color: '#06070d',
      fontSize: 9, fontWeight: 800, marginRight: 6,
    }}>{s.slice(0, 2).toUpperCase()}</span>
  );
}

export function RouteChips({ legs, tokenMap }: { legs: any[]; tokenMap: TokenMap }) {
  if (!legs || !legs.length) return null;
  return (
    <div className="route">
      {legs.map((leg, i) => (
        <React.Fragment key={i}>
          <span className="chip">
            <span className="tok">{sym(tokenMap, leg.token_in)}</span>
          </span>
          <span className="arrow">→</span>
          <span className="chip">
            <span className="dex">{leg.dex_name}</span>
          </span>
          {i === legs.length - 1 && (
            <>
              <span className="arrow">→</span>
              <span className="chip"><span className="tok">{sym(tokenMap, leg.token_out)}</span></span>
            </>
          )}
        </React.Fragment>
      ))}
    </div>
  );
}
