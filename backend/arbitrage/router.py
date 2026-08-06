from __future__ import annotations

from typing import Optional

from models.schemas import PoolInfo, RouteLeg


def _get_pool_price(pool: PoolInfo, token_in: str, token_out: str) -> float:
    """Spot price of token_in in terms of token_out within this pool.

    Derived from each token's pool-local USD price (computed from the on-chain
    liquidity split), so it reflects the pool's real last-traded price rather
    than a stale aggregate.
    """
    t0 = pool.token0.address.lower()
    t1 = pool.token1.address.lower()
    ti = token_in.lower()
    to = token_out.lower()

    if t0 == ti and t1 == to:
        return pool.price_token0_per_token1
    elif t1 == ti and t0 == to:
        if pool.price_token0_per_token1 > 0:
            return 1.0 / pool.price_token0_per_token1
    return 0.0


def get_amount_out(
    pool: PoolInfo,
    token_in: str,
    token_out: str,
    amount_in: float,
    trade_size_usd: Optional[float] = None,
) -> float:
    """Executable output amount for swapping `amount_in` of token_in for
    token_out on `pool`, accounting for the pool fee AND price impact
    (constant-product approximation: impact ≈ tradeSize / (2 * liquidity)).

    `amount_in` is expressed in USD-equivalent units (as used throughout the
    engine), so `trade_size_usd` defaults to `amount_in`.
    """
    price = _get_pool_price(pool, token_in, token_out)
    if price <= 0 or amount_in <= 0:
        return 0.0

    fee = pool.fee_rate
    liq = pool.total_liquidity_usd
    if trade_size_usd is None:
        trade_size_usd = amount_in

    if liq > 0:
        impact = min((trade_size_usd / liq) / 2.0, 0.5)
    else:
        impact = 0.5

    return amount_in * price * (1.0 - fee) * (1.0 - impact)


def _price_impact_bps(amount_in: float, pool: PoolInfo) -> float:
    if pool.total_liquidity_usd <= 0 or amount_in <= 0:
        return 0.0
    return min((amount_in / pool.total_liquidity_usd) / 2.0 * 10000, 5000)


def find_best_route(
    token_in_address: str,
    token_out_address: str,
    amount_in: float,
    pools: list[PoolInfo],
    chain_id: int,
) -> Optional[dict]:
    if not pools:
        return None

    best_route = None
    best_out = 0.0

    for pool in pools:
        if pool.total_liquidity_usd < 10:
            continue
        out = get_amount_out(pool, token_in_address, token_out_address, amount_in)
        if out > best_out:
            best_out = out
            token_in_price = (
                pool.token0.price_usd
                if pool.token0.address.lower() == token_in_address.lower()
                else pool.token1.price_usd
            )
            token_out_price = (
                pool.token1.price_usd
                if pool.token0.address.lower() == token_in_address.lower()
                else pool.token0.price_usd
            )
            best_route = {
                "pool_address": pool.address,
                "dex_name": pool.dex_name,
                "pool_type": pool.pool_type,
                "token_in": token_in_address,
                "token_out": token_out_address,
                "amount_in": amount_in,
                "amount_out": out,
                "price_impact_bps": _price_impact_bps(amount_in, pool),
                "fee_bps": pool.fee_rate * 10000,
                "reserve_in_usd": amount_in * (token_in_price or 0),
                "reserve_out_usd": out * (token_out_price or 0),
                "price": _get_pool_price(pool, token_in_address, token_out_address),
            }

    return best_route


def find_cross_pool_arb(
    token_in_address: str,
    token_out_address: str,
    amount_in: float,
    buy_pools: list[PoolInfo],
    sell_pools: list[PoolInfo],
) -> Optional[dict]:
    best_buy = None
    best_sell = None
    best_profit = 0.0

    for buy_pool in buy_pools:
        if buy_pool.total_liquidity_usd < 10:
            continue
        intermediate = get_amount_out(buy_pool, token_in_address, token_out_address, amount_in)
        if intermediate <= 0:
            continue

        for sell_pool in sell_pools:
            if sell_pool.total_liquidity_usd < 10:
                continue
            final_amount = get_amount_out(sell_pool, token_out_address, token_in_address, intermediate)
            if final_amount > amount_in and final_amount > best_profit:
                best_profit = final_amount
                best_buy = buy_pool
                best_sell = sell_pool

    if best_buy is None or best_sell is None:
        return None

    return {
        "buy_pool": best_buy,
        "sell_pool": best_sell,
        "amount_in": amount_in,
        "amount_out": best_profit,
        "profit_amount": best_profit - amount_in,
        "profit_bps": ((best_profit - amount_in) / amount_in) * 10000,
    }


def find_triangular_arb(
    token_a: str,
    token_b: str,
    token_c: str,
    amount_in: float,
    pools_ab: list[PoolInfo],
    pools_bc: list[PoolInfo],
    pools_ca: list[PoolInfo],
    min_liquidity: float = 10,
) -> Optional[dict]:
    best_route = None
    best_profit = 0.0

    for pool_ab in pools_ab:
        if pool_ab.total_liquidity_usd < min_liquidity:
            continue
        amount_b = get_amount_out(pool_ab, token_a, token_b, amount_in)
        if amount_b <= 0:
            continue

        for pool_bc in pools_bc:
            if pool_bc.total_liquidity_usd < min_liquidity:
                continue
            amount_c = get_amount_out(pool_bc, token_b, token_c, amount_b)
            if amount_c <= 0:
                continue

            for pool_ca in pools_ca:
                if pool_ca.total_liquidity_usd < min_liquidity:
                    continue
                amount_a_final = get_amount_out(pool_ca, token_c, token_a, amount_c)
                if amount_a_final > amount_in and amount_a_final > best_profit:
                    best_profit = amount_a_final
                    best_route = {
                        "pool_ab": pool_ab,
                        "pool_bc": pool_bc,
                        "pool_ca": pool_ca,
                        "amount_in": amount_in,
                        "amount_out": amount_a_final,
                        "profit_amount": amount_a_final - amount_in,
                        "profit_bps": ((amount_a_final - amount_in) / amount_in) * 10000,
                        "legs": [
                            {"pool": pool_ab, "token_in": token_a, "token_out": token_b, "price": _get_pool_price(pool_ab, token_a, token_b), "fee": pool_ab.fee_rate},
                            {"pool": pool_bc, "token_in": token_b, "token_out": token_c, "price": _get_pool_price(pool_bc, token_b, token_c), "fee": pool_bc.fee_rate},
                            {"pool": pool_ca, "token_in": token_c, "token_out": token_a, "price": _get_pool_price(pool_ca, token_c, token_a), "fee": pool_ca.fee_rate},
                        ],
                    }

    if best_profit <= amount_in:
        return None

    return best_route


def find_all_triangular_arbs(
    token_addresses: list[str],
    pools_by_pair: dict[tuple[str, str], list[PoolInfo]],
    amount_in: float = 1000.0,
    min_liquidity: float = 10,
) -> list[dict]:
    opportunities = []

    for i in range(len(token_addresses)):
        token_a = token_addresses[i]
        for j in range(i + 1, len(token_addresses)):
            token_b = token_addresses[j]
            for k in range(j + 1, len(token_addresses)):
                token_c = token_addresses[k]

                pair_ab = (token_a, token_b) if (token_a, token_b) in pools_by_pair else ((token_b, token_a) if (token_b, token_a) in pools_by_pair else None)
                pair_bc = (token_b, token_c) if (token_b, token_c) in pools_by_pair else ((token_c, token_b) if (token_c, token_b) in pools_by_pair else None)
                pair_ca = (token_c, token_a) if (token_c, token_a) in pools_by_pair else ((token_a, token_c) if (token_a, token_c) in pools_by_pair else None)

                if not (pair_ab and pair_bc and pair_ca):
                    continue

                result = find_triangular_arb(
                    token_a, token_b, token_c,
                    amount_in, pools_by_pair[pair_ab], pools_by_pair[pair_bc], pools_by_pair[pair_ca],
                )
                if result:
                    result["token_path"] = f"{token_a}->{token_b}->{token_c}->{token_a}"
                    opportunities.append(result)

    return opportunities


def _canon_cycle(path: list[str]) -> tuple:
    cycle = path[:-1] if len(path) > 1 and path[0] == path[-1] else path
    if not cycle:
        return tuple(path)
    mi = cycle.index(min(cycle))
    rotated = cycle[mi:] + cycle[:mi]
    return tuple(rotated)


def find_all_multi_hop_arbs(
    token_addresses: list[str],
    pools_by_pair: dict[tuple[str, str], list[PoolInfo]],
    amount_in: float = 1000.0,
    max_hops: int = 4,
    min_liquidity: float = 10,
    min_profit_bps: float = 1.0,
    max_results: int = 15000,
) -> list[dict]:
    """Find multi-hop arbitrage opportunities (2-4 hops) via DFS cycle detection.

    Returns cycle results with resolved route legs (pool + token_in + token_out
    + spot price + fee) so callers can build a full ArbitrageOpportunity. Profit
    is evaluated with slippage-aware get_amount_out and the real pool fee.
    """
    addresses = {a.lower() for a in token_addresses}

    # Directed graph: a -> { b: (best_pool, ) } chosen by executable output for
    # the reference trade size.
    graph: dict[str, dict[str, PoolInfo]] = {}
    for (token_a, token_b), pools in pools_by_pair.items():
        for (src, dst) in ((token_a, token_b), (token_b, token_a)):
            if src not in addresses or dst not in addresses:
                continue
            best_pool = None
            best_out = 0.0
            for p in pools:
                if p.total_liquidity_usd < min_liquidity:
                    continue
                out = get_amount_out(p, src, dst, amount_in)
                if out > best_out:
                    best_out = out
                    best_pool = p
            if best_pool is not None:
                graph.setdefault(src, {})[dst] = best_pool

    opportunities: list[dict] = []
    seen_paths_set = set()

    def dfs(current: str, start: str, path: list[str], amount: float, depth: int):
        if len(opportunities) >= max_results:
            return
        if depth >= 2 and current == start:
            if amount > amount_in * (1 + min_profit_bps / 10000.0):
                canon = _canon_cycle(path)
                if canon not in seen_paths_set:
                    seen_paths_set.add(canon)
                    legs = []
                    amt = amount_in
                    for i in range(len(path) - 1):
                        a, b = path[i], path[i + 1]
                        pool = graph[a][b]
                        legs.append({
                            "pool": pool,
                            "token_in": a,
                            "token_out": b,
                            "price": _get_pool_price(pool, a, b),
                            "fee": pool.fee_rate,
                        })
                        amt = get_amount_out(pool, a, b, amt)
                    opportunities.append({
                        "path": "->".join(path),
                        "legs": legs,
                        "amount_in": amount_in,
                        "amount_out": amount,
                        "profit_bps": ((amount - amount_in) / amount_in) * 10000,
                        "hops": depth,
                    })
            return
        if depth >= max_hops:
            return

        for nxt, pool in graph.get(current, {}).items():
            nxt_amount = get_amount_out(pool, current, nxt, amount)
            if nxt_amount <= 0:
                continue
            if nxt not in path or (nxt == start and depth >= 1):
                dfs(nxt, start, path + [nxt], nxt_amount, depth + 1)

    for token in token_addresses:
        if token in graph:
            dfs(token, token, [token], amount_in, 0)

    return opportunities
