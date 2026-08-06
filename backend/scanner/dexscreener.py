from __future__ import annotations

import asyncio
import time
from typing import Optional

import aiohttp

from config import settings
from models.schemas import PoolInfo, TokenInfo

DEXSCREENER_BASE = settings.DEXSCREENER_API_URL

CHAIN_ID_TO_DEXSCREENER = {
    42161: "arbitrum",
    1: "ethereum",
}

DEXSCREENER_CHAIN_NAME = {
    42161: "Arbitrum",
    1: "ethereum",
}


class DexScreenerClient:
    def __init__(self, timeout: int = 15):
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(timeout=self.timeout)
        return self._session

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    async def _fetch(self, url: str) -> Optional[dict]:
        try:
            session = await self._get_session()
            async with session.get(url) as resp:
                if resp.status == 200:
                    return await resp.json()
        except Exception:
            pass
        return None

    async def fetch_token_pairs(self, token_address: str) -> Optional[dict]:
        url = f"{DEXSCREENER_BASE}/tokens/{token_address}"
        return await self._fetch(url)

    async def fetch_pairs_for_chain(self, chain: str, limit: int = 1000) -> Optional[dict]:
        url = f"{DEXSCREENER_BASE}/pairs/{chain}"
        return await self._fetch(url)

    async def search_query(self, query: str) -> Optional[dict]:
        url = f"{DEXSCREENER_BASE}/search?q={query}"
        return await self._fetch(url)

    async def fetch_trending_pairs(self, chain: str, limit: int = 100) -> Optional[dict]:
        url = f"{DEXSCREENER_BASE}/pairs/{chain}/trending?limit={limit}"
        return await self._fetch(url)


_client = DexScreenerClient()


async def close_client():
    await _client.close()


def _parse_change_from_pair(pair_data: dict) -> Optional[float]:
    price_change = pair_data.get("priceChange", {})
    if isinstance(price_change, dict):
        h24 = price_change.get("h24")
        if h24 is not None:
            return float(h24)
    return None


def _detect_pool_type(pair: dict) -> str:
    dex = pair.get("dexId", pair.get("dex", "")).lower()
    if "balancer" in dex:
        return "balancer"
    if "uniswap" in dex:
        return "uniswap_v3" if "v3" in dex else "uniswap_v2"
    if "sushiswap" in dex or "sushi" in dex:
        return "sushiswap"
    if "curve" in dex:
        return "curve"
    if "pancakeswap" in dex:
        return "pancakeswap"
    if "traderjoe" in dex or "joe" in dex:
        return "traderjoe"
    if "camelot" in dex:
        return "camelot"
    return dex if dex else "unknown"


def parse_pools_from_dexscreener(data: dict, chain_id: int) -> list[PoolInfo]:
    if not data or "pairs" not in data:
        return []
    pairs = data.get("pairs") or []
    pools: list[PoolInfo] = []
    for pair in pairs:
        try:
            pool = _parse_pair_to_pool(pair, chain_id)
            if pool is not None:
                pools.append(pool)
        except Exception:
            continue
    return pools


def _parse_pair_to_pool(pair: dict, chain_id: int) -> Optional[PoolInfo]:
    base_token = pair.get("baseToken", {})
    quote_token = pair.get("quoteToken", {})
    if not base_token or not quote_token:
        return None

    base_info = base_token.get("info", {})
    quote_info = quote_token.get("info", {})

    token0 = TokenInfo(
        address=base_token.get("address", ""),
        symbol=base_token.get("symbol", "UNKNOWN"),
        name=base_token.get("name", "Unknown"),
        decimals=int(base_token.get("decimals", 18)),
        price_usd=float(base_token.get("priceUsd", 0) or 0),
        chain_id=chain_id,
        logo_url=base_info.get("logoUrl"),
    )
    token1 = TokenInfo(
        address=quote_token.get("address", ""),
        symbol=quote_token.get("symbol", "UNKNOWN"),
        name=quote_token.get("name", "Unknown"),
        decimals=int(quote_token.get("decimals", 18)),
        price_usd=float(quote_token.get("priceUsd", 0) or 0),
        chain_id=chain_id,
        logo_url=quote_info.get("logoUrl"),
    )

    liquidity = pair.get("liquidity", {})
    volume = pair.get("volume", {})

    reserve0 = float(pair.get("reserve0", "0") or 0)
    reserve1 = float(pair.get("reserve1", "0") or 0)

    total_liquidity = float(liquidity.get("usd", 0) or 0)
    vol_24h = float(volume.get("h24", 0) or 0)
    vol_24h_change = pair.get("volume", {}).get("h24Change", None)

    fee_rate = float(pair.get("fee", 0.003) or 0.003)

    pool_type = _detect_pool_type(pair)
    dex_name = pair.get("dexId", pair.get("dex", "unknown"))

    price_usd = float(pair.get("priceUsd", 0) or 0)
    price_native = float(pair.get("priceNative", 0) or 0)

    if price_usd > 0 and token0.price_usd <= 0:
        token0.price_usd = price_usd
    if price_native > 0 and token0.price_usd <= 0:
        token0.price_usd = price_native

    if price_usd > 0 and token1.price_usd <= 0:
        token1.price_usd = price_usd / price_native if price_native > 0 else 0

    # --- Accurate, assumption-free pool pricing ---
    # DexScreener does not return raw reserves, but it returns the liquidity
    # split: liquidity.base / liquidity.quote are the decimal-adjusted reserve
    # amounts of the base (token0) / quote (token1) tokens. Combined with the
    # pair's own USD price for the base token, we can derive each token's TRUE
    # USD price *within this pool* (i.e. its last-traded on-chain price).
    liq_base_amt = float(liquidity.get("base", 0) or 0)
    liq_quote_amt = float(liquidity.get("quote", 0) or 0)

    # token0 (base) USD price sourced from the pair's own price when available
    token0_usd_pd = price_usd if price_usd > 0 else (token0.price_usd or 0)
    token1_usd_pd = 0.0

    if token0_usd_pd > 0 and liq_base_amt > 0 and liq_quote_amt > 0 and total_liquidity > 0:
        base_value = token0_usd_pd * liq_base_amt
        quote_value = total_liquidity - base_value
        if quote_value > 0 and liq_quote_amt > 0:
            token1_usd_pd = quote_value / liq_quote_amt
    if token1_usd_pd <= 0:
        # Fallback: derive from native price ratio if present
        if price_native > 0 and token0_usd_pd > 0:
            token1_usd_pd = token0_usd_pd / price_native if price_native > 0 else 0
        elif token1.price_usd > 0:
            token1_usd_pd = token1.price_usd
        elif token0_usd_pd > 0 and price_native > 0:
            token1_usd_pd = token0_usd_pd / price_native

    if token0_usd_pd > 0 and token1_usd_pd > 0:
        price_t0_per_t1 = token0_usd_pd / token1_usd_pd
    else:
        price_t0_per_t1 = price_native if price_native > 0 else 0
        if price_t0_per_t1 == 0 and token0.price_usd > 0 and token1.price_usd > 0:
            price_t0_per_t1 = token0.price_usd / token1.price_usd
    price_t1_per_t0 = 1.0 / price_t0_per_t1 if price_t0_per_t1 > 0 else 0

    return PoolInfo(
        address=pair.get("pairAddress", pair.get("id", "")),
        token0=token0,
        token1=token1,
        reserve0=reserve0,
        reserve1=reserve1,
        total_liquidity_usd=total_liquidity,
        volume_24h_usd=vol_24h,
        volume_24h_change_pct=vol_24h_change,
        fee_rate=fee_rate,
        pool_type=pool_type,
        dex_name=dex_name,
        chain_id=chain_id,
        price_token0_per_token1=price_t0_per_t1,
        price_token1_per_token0=price_t1_per_t0,
        token0_price_usd=token0_usd_pd,
        token1_price_usd=token1_usd_pd,
    )


def parse_token_from_pair(base_token: dict, pair_data: dict) -> Optional[TokenInfo]:
    if not base_token or not base_token.get("address"):
        return None
    price_usd = float(pair_data.get("priceUsd", 0) or 0)
    return TokenInfo(
        address=base_token.get("address", ""),
        symbol=base_token.get("symbol", "UNKNOWN"),
        name=base_token.get("name", "Unknown Token"),
        decimals=18,
        price_usd=price_usd,
        market_cap=float(pair_data.get("fdv", 0) or 0),
        volume_24h_usd=float(pair_data.get("volume", {}).get("h24", 0) or 0),
        change_24h_pct=_parse_change_from_pair(pair_data),
        chain_id=settings.ARBITRUM_CHAIN_ID,
        logo_url=None,
    )


SEED_SYMBOLS = [
    "WETH", "USDC", "USDT", "WBTC", "ARB", "DAI", "FRAX", "LUSD", "MIM", "USDe",
    "LINK", "GMX", "MAGIC", "CRV", "UNI", "SUSHI", "AAVE", "COMP", "SNX", "PENDLE",
    "RDNT", "GRAIL", "BAL", "CVX", "FXS", "1INCH", "STG", "SYN", "ACX", "VELO",
    "JONES", "JOE", "TRADER", "AURA", "SPELL", "OHM", "KLIMA", "TIME", "HOP", "WINR",
    "XAI", "GNS", "DPX", "SPA", "LPT", "PERP", "RNDR", "AKT", "OCEAN", "UMA",
    "BADGER", "DODO", "ELK", "GNO", "HFT", "KNC", "LDO", "MASK", "OGN", "QNT",
    "RENBTC", "SDL", "WOO", "ZRO", "DMT", "USDD", "FRAXBP", "TRIBAL", "VSTA", "PLV",
]


async def _bfs_discover(chain_id: int, limit: int, collect_pools: bool):
    if chain_id != 42161:
        return [], {}

    tokens: list[TokenInfo] = []
    seen: set[str] = set()
    token_pools: dict[str, list[PoolInfo]] = {}

    def _add_token(base: dict, pair: dict) -> Optional[str]:
        if not base or not base.get("address"):
            return None
        addr = base["address"].lower()
        if addr in seen:
            return None
        token = parse_token_from_pair(base, pair)
        if token and token.price_usd and token.price_usd > 0:
            seen.add(addr)
            tokens.append(token)
            return addr
        return None

    sem = asyncio.Semaphore(15)
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=20)) as session:
        # Seed with hub tokens discovered via search queries
        for sym in SEED_SYMBOLS:
            if len(tokens) >= limit:
                break
            url = f"{DEXSCREENER_BASE}/search?q={sym}"
            try:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        for pair in data.get("pairs", []) or []:
                            if pair.get("chainId") != "arbitrum":
                                continue
                            for base in [pair.get("baseToken"), pair.get("quoteToken")]:
                                _add_token(base, pair)
            except Exception:
                pass
            await asyncio.sleep(0.1)

        # BFS expansion: collect counterpart tokens AND their pools in one pass
        frontier = [t.address for t in tokens]

        async def _fetch_token_pairs(addr: str):
            async with sem:
                url = f"{DEXSCREENER_BASE}/tokens/{addr}"
                try:
                    async with session.get(url) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            return addr, data.get("pairs", []) or []
                except Exception:
                    pass
                return addr, []

        while frontier and len(tokens) < limit:
            batch = frontier[:40]
            frontier = frontier[40:]
            results = await asyncio.gather(*[_fetch_token_pairs(a) for a in batch])
            for addr, pairs in results:
                if collect_pools:
                    parsed = []
                    for pair in pairs:
                        try:
                            pool = _parse_pair_to_pool(pair, chain_id)
                            if pool is not None:
                                parsed.append(pool)
                        except Exception:
                            continue
                    if parsed:
                        token_pools[addr] = parsed
                for pair in pairs:
                    if pair.get("chainId") != "arbitrum":
                        continue
                    for base in [pair.get("baseToken"), pair.get("quoteToken")]:
                        new_addr = _add_token(base, pair)
                        if new_addr and new_addr not in frontier and len(tokens) < limit:
                            frontier.append(new_addr)

    return tokens[:limit], token_pools


async def discover_top_tokens_async(chain_id: int, limit: int = 500) -> list[TokenInfo]:
    tokens, _ = await _bfs_discover(chain_id, limit, collect_pools=False)
    return tokens


async def discover_top_tokens_with_pools_async(
    chain_id: int, limit: int = 500
) -> tuple[list[TokenInfo], dict[str, list[PoolInfo]]]:
    return await _bfs_discover(chain_id, limit, collect_pools=True)


async def scan_all_pools_for_token_async(session: aiohttp.ClientSession, token_address: str, chain_id: int) -> list[PoolInfo]:
    url = f"{DEXSCREENER_BASE}/tokens/{token_address}"
    try:
        async with session.get(url) as resp:
            if resp.status == 200:
                data = await resp.json()
                return parse_pools_from_dexscreener(data, chain_id)
    except Exception:
        pass
    return []


async def scan_all_pools_for_tokens_async(token_addresses: list[str], chain_id: int, concurrency: int = 20) -> dict[str, list[PoolInfo]]:
    results = {}
    semaphore = asyncio.Semaphore(concurrency)

    async def fetch_one(addr: str):
        async with semaphore:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15)) as session:
                pools = await scan_all_pools_for_token_async(session, addr, chain_id)
                if pools:
                    return addr, pools
        return addr, None

    tasks = [fetch_one(addr) for addr in token_addresses]
    results_list = await asyncio.gather(*tasks, return_exceptions=True)

    for result in results_list:
        if isinstance(result, tuple) and result[1]:
            results[result[0]] = result[1]

    return results


def scan_all_pools_for_token(token_address: str, chain_id: int) -> list[PoolInfo]:
    import asyncio
    import aiohttp
    
    async def _fetch():
        async with aiohttp.ClientSession() as session:
            return await scan_all_pools_for_token_async(session, token_address, chain_id)
    
    return asyncio.run(_fetch())


def scan_all_pools_for_tokens(token_addresses: list[str], chain_id: int) -> dict[str, list[PoolInfo]]:
    import asyncio
    return asyncio.run(scan_all_pools_for_tokens_async(token_addresses, chain_id))


async def scan_all_pools_for_top_tokens_async(chain_id: int, token_limit: int = 500) -> dict[str, list[PoolInfo]]:
    tokens = await discover_top_tokens_async(chain_id, token_limit)
    token_addresses = [t.address for t in tokens]
    return await scan_all_pools_for_tokens_async(token_addresses, chain_id)


def scan_all_pools_for_top_tokens(chain_id: int, token_limit: int = 50) -> dict[str, list[PoolInfo]]:
    import asyncio
    return asyncio.run(scan_all_pools_for_top_tokens_async(chain_id, token_limit))


def get_pair_by_tokens(token0_addr: str, token1_addr: str, chain_id: int) -> Optional[PoolInfo]:
    pools0 = scan_all_pools_for_token(token0_addr, chain_id)
    for pool in pools0:
        if pool.token0.address.lower() == token1_addr.lower() or pool.token1.address.lower() == token1_addr.lower():
            return pool
    return None