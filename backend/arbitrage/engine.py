from __future__ import annotations

import uuid
import time
from datetime import datetime, timedelta
from typing import Optional

from config import settings
from models.schemas import (
    ArbitrageOpportunity,
    PoolInfo,
    RouteLeg,
    TokenInfo,
)
from scanner.dexscreener import (
    scan_all_pools_for_tokens_async,
    discover_top_tokens_with_pools_async,
)
from scanner.rpc import get_gas_price, get_block_number, get_block_time
from arbitrage.router import (
    _get_pool_price,
    _price_impact_bps,
    get_amount_out,
    find_all_triangular_arbs,
    find_all_multi_hop_arbs,
)
from gas.calculator import estimate_gas_cost
from flashloan.balancer import get_flash_loan_quote
from scoring.confidence import calculate_confidence_score
from scoring.competition import calculate_competition_score


async def scan_opportunities(
    chains: list[int] = None,
    token_addresses: list[str] = None,
    min_profit_bps: int = None,
    min_confidence: float = None,
    max_gas_cost_usd: float = None,
    include_flashloan: bool = True,
    limit: int = None,
) -> dict:
    start_time = time.time()
    chains = chains or [settings.ARBITRUM_CHAIN_ID]
    min_profit_bps = min_profit_bps if min_profit_bps is not None else settings.OPPORTUNITY_MIN_PROFIT_BPS
    min_confidence = min_confidence if min_confidence is not None else settings.OPPORTUNITY_MIN_CONFIDENCE
    max_gas_cost_usd = max_gas_cost_usd or 50.0
    limit = limit or 500

    all_opportunities = []
    pools_scanned = 0
    tokens_scanned = 0

    for chain_id in chains:
        chain_opportunities, chain_pools, chain_tokens = await _scan_chain_async(
            chain_id=chain_id,
            token_addresses=token_addresses,
            include_flashloan=include_flashloan,
        )
        all_opportunities.extend(chain_opportunities)
        pools_scanned += chain_pools
        tokens_scanned += chain_tokens

    all_opportunities.sort(key=lambda o: o.net_profit_usd, reverse=True)

    filtered = [
        opp
        for opp in all_opportunities
        if opp.net_profit_usd > 0
        and opp.profit_bps >= min_profit_bps
        and opp.profit_bps <= settings.OPPORTUNITY_MAX_PROFIT_BPS_CAP
        and opp.confidence_score >= min_confidence
        and opp.gas_cost_usd <= max_gas_cost_usd
    ]

    filtered = filtered[:limit]

    scan_duration_ms = (time.time() - start_time) * 1000

    summary = _build_summary(
        opportunities=filtered,
        pools_scanned=pools_scanned,
        tokens_scanned=tokens_scanned,
        scan_duration_ms=scan_duration_ms,
        chains=chains,
    )

    networks = _build_network_telemetry(chains)

    return {
        "opportunities": filtered,
        "summary": summary,
        "networks": networks,
        "scan_duration_ms": scan_duration_ms,
        "scanned_at": datetime.utcnow(),
    }


async def _scan_chain_async(
    chain_id: int,
    token_addresses: list[str] = None,
    include_flashloan: bool = True,
    top_n: int = 300,
) -> tuple[list[ArbitrageOpportunity], int, int]:
    opportunities: list[ArbitrageOpportunity] = []

    if token_addresses:
        token_map = await scan_all_pools_for_tokens_async(token_addresses, chain_id)
        addrs = list(token_map.keys())
    else:
        tokens, token_map = await discover_top_tokens_with_pools_async(
            chain_id, settings.MAX_TOKENS_PER_SCAN
        )
        addrs = [t.address for t in tokens]

    all_pools: list[PoolInfo] = []
    for pools in token_map.values():
        all_pools.extend(pools)

    unique_pools = _deduplicate_pools(all_pools)

    # Drop pools whose pool-local price is wildly inconsistent with the token's
    # aggregate USD price — these are stale/broken listings (not real arbs).
    sane_pools = [p for p in unique_pools if _pool_price_sane(p)]
    filtered_out = len(unique_pools) - len(sane_pools)
    unique_pools = sane_pools

    pools_by_pair: dict[tuple[str, str], list[PoolInfo]] = {}
    token_liquidity: dict[str, float] = {}
    for pool in unique_pools:
        a = pool.token0.address.lower()
        b = pool.token1.address.lower()
        key = (a, b) if a < b else (b, a)
        pools_by_pair.setdefault(key, []).append(pool)
        for tk in (pool.token0, pool.token1):
            token_liquidity[tk.address.lower()] = (
                token_liquidity.get(tk.address.lower(), 0) + pool.total_liquidity_usd
            )

    # Rank tokens by connected liquidity; cycles concentrate on liquid hubs
    ranked = sorted(token_liquidity.keys(), key=lambda x: token_liquidity[x], reverse=True)
    top_tokens = ranked[:top_n]

    gas_info = estimate_gas_cost(chain_id=chain_id)
    gas_cost_usd = gas_info["estimated_cost_usd"]
    gas_limit = gas_info["gas_limit"]
    fl_fee = 1000
    fl_amount = 1000.0
    if include_flashloan and top_tokens:
        q = get_flash_loan_quote(
            token_address=top_tokens[0], amount_usd=1000.0, chain_id=chain_id
        )
        if q:
            fl_fee = q.fee_bps
            fl_amount = q.amount_usd

    # 1) Cross-pool arbitrage: every pair with >= 2 pools, all pool combinations
    cross = _find_cross_pool_opps(
        chain_id=chain_id,
        pools_by_pair=pools_by_pair,
        gas_cost_usd=gas_cost_usd,
        gas_limit=gas_limit,
        include_flashloan=include_flashloan,
        fl_fee=fl_fee,
        fl_amount=fl_amount,
    )
    opportunities.extend(cross)

    # 2) Triangular arbitrage over the top tokens
    triangular = find_all_triangular_arbs(top_tokens, pools_by_pair, min_liquidity=10, amount_in=settings.TRADE_SIZE_USD)
    for result in triangular:
        opp = _build_cycle_opportunity(
            chain_id=chain_id,
            cycle=result,
            gas_cost_usd=gas_cost_usd,
            gas_limit=gas_limit,
            include_flashloan=include_flashloan,
            fl_fee=fl_fee,
            fl_amount=fl_amount,
        )
        if opp is not None:
            opportunities.append(opp)

    # 3) Multi-hop arbitrage (DFS cycles) over the top tokens
    multi_hop = find_all_multi_hop_arbs(
        top_tokens,
        pools_by_pair,
        amount_in=settings.TRADE_SIZE_USD,
        max_hops=4,
        min_liquidity=10,
        min_profit_bps=max(0.1, settings.OPPORTUNITY_MIN_PROFIT_BPS),
        max_results=15000,
    )
    for result in multi_hop:
        opp = _build_cycle_opportunity(
            chain_id=chain_id,
            cycle=result,
            gas_cost_usd=gas_cost_usd,
            gas_limit=gas_limit,
            include_flashloan=include_flashloan,
            fl_fee=fl_fee,
            fl_amount=fl_amount,
        )
        if opp is not None:
            opportunities.append(opp)

    return opportunities, len(unique_pools), len(addrs)


def _find_cross_pool_opps(
    chain_id: int,
    pools_by_pair: dict[tuple[str, str], list[PoolInfo]],
    gas_cost_usd: float,
    gas_limit: int,
    include_flashloan: bool,
    fl_fee: int,
    fl_amount: float,
) -> list[ArbitrageOpportunity]:
    opps: list[ArbitrageOpportunity] = []
    for (token_a, token_b), pools in pools_by_pair.items():
        if len(pools) < 2:
            continue
        eligible = [p for p in pools if p.total_liquidity_usd >= 10]
        if len(eligible) < 2:
            continue
        for i in range(len(eligible)):
            for j in range(i + 1, len(eligible)):
                buy_pool = eligible[i]
                sell_pool = eligible[j]
                price_ab = _get_pool_price(buy_pool, token_a, token_b)
                price_ba = _get_pool_price(sell_pool, token_b, token_a)
                if price_ab <= 0 or price_ba <= 0:
                    continue
                legs = [
                    {
                        "pool": buy_pool,
                        "token_in": token_a,
                        "token_out": token_b,
                        "price": price_ab,
                        "fee": buy_pool.fee_rate,
                    },
                    {
                        "pool": sell_pool,
                        "token_in": token_b,
                        "token_out": token_a,
                        "price": price_ba,
                        "fee": sell_pool.fee_rate,
                    },
                ]
                amount_out = get_amount_out(buy_pool, token_a, token_b, settings.TRADE_SIZE_USD)
                amount_out = get_amount_out(sell_pool, token_b, token_a, amount_out)
                cycle = {
                    "legs": legs,
                    "amount_in": settings.TRADE_SIZE_USD,
                    "amount_out": amount_out,
                    "profit_bps": 0.0,
                    "hops": 2,
                }
                cycle["profit_bps"] = (
                    (cycle["amount_out"] - cycle["amount_in"]) / cycle["amount_in"]
                ) * 10000
                opp = _build_cycle_opportunity(
                    chain_id=chain_id,
                    cycle=cycle,
                    gas_cost_usd=gas_cost_usd,
                    gas_limit=gas_limit,
                    include_flashloan=include_flashloan,
                    fl_fee=fl_fee,
                    fl_amount=fl_amount,
                )
                if opp is not None:
                    opps.append(opp)
    return opps


def _build_cycle_opportunity(
    chain_id: int,
    cycle: dict,
    gas_cost_usd: float,
    gas_limit: int,
    include_flashloan: bool = True,
    fl_fee: int = 1000,
    fl_amount: float = 1000.0,
) -> Optional[ArbitrageOpportunity]:
    try:
        legs = cycle["legs"]
        if not legs:
            return None

        amount_in = cycle["amount_in"]
        # Recompute amount out with slippage-aware executable pricing (fees +
        # price impact accounted for via get_amount_out).
        carry = amount_in
        leg_amounts = []
        for leg in legs:
            out = get_amount_out(leg["pool"], leg["token_in"], leg["token_out"], carry)
            leg_amounts.append((carry, out))
            carry = out
        amount_out = carry

        gross_profit = amount_out - amount_in
        if gross_profit <= 0:
            return None

        net_profit_usd = gross_profit - gas_cost_usd
        if net_profit_usd <= 0:
            return None

        profit_bps = (gross_profit / amount_in) * 10000
        profit_pct = (gross_profit / amount_in) * 100

        buy_pool = legs[0]["pool"]
        sell_pool = legs[-1]["pool"]
        start_token_addr = legs[0]["token_in"]
        end_token_addr = legs[-1]["token_out"]

        token_in = _token_from_pool(buy_pool, start_token_addr)
        token_out = _token_from_pool(sell_pool, end_token_addr)

        confidence = calculate_confidence_score(
            buy_pool=buy_pool,
            sell_pool=sell_pool,
            profit_bps=profit_bps,
            gas_cost_usd=gas_cost_usd,
            net_profit_usd=net_profit_usd,
            token_in=token_in,
            token_out=token_out,
        )

        competition = calculate_competition_score(
            buy_pool=buy_pool,
            sell_pool=sell_pool,
            profit_bps=profit_bps,
            chain_id=chain_id,
        )

        route_legs = []
        for idx, leg in enumerate(legs):
            pool = leg["pool"]
            t_in = _token_from_pool(pool, leg["token_in"])
            t_out = _token_from_pool(pool, leg["token_out"])
            amt_in_leg, amt_out_leg = leg_amounts[idx]
            route_legs.append(
                RouteLeg(
                    pool_address=pool.address,
                    dex_name=pool.dex_name,
                    pool_type=pool.pool_type,
                    token_in=leg["token_in"],
                    token_out=leg["token_out"],
                    amount_in=amt_in_leg,
                    amount_out=amt_out_leg,
                    price_impact_bps=_price_impact_bps(amt_in_leg, pool),
                    fee_bps=leg["fee"] * 10000,
                    reserve_in_usd=amt_in_leg * (t_in.price_usd or 0),
                    reserve_out_usd=amt_out_leg * (t_out.price_usd or 0),
                )
            )

        spread_bps = profit_bps
        liquidity_depth = min(leg["pool"].total_liquidity_usd for leg in legs)

        if net_profit_usd > 100:
            execution_risk = "low"
        elif net_profit_usd > 10:
            execution_risk = "medium"
        else:
            execution_risk = "high"

        dex_path = " -> ".join(
            f"{_token_symbol(leg['pool'], leg['token_in'])}({leg['pool'].dex_name})"
            for leg in legs
        )
        recommended_action = (
            f"Flash loan {fl_amount:.2f} {token_in.symbol} via Balancer, route: {dex_path}"
            if include_flashloan
            else f"Route: {dex_path}"
        )

        return ArbitrageOpportunity(
            id=str(uuid.uuid4())[:12],
            chain_id=chain_id,
            chain_name="Arbitrum" if chain_id == 42161 else "Ethereum",
            token_in_address=start_token_addr,
            token_in_symbol=token_in.symbol,
            token_in_name=token_in.name,
            token_out_address=start_token_addr,
            token_out_symbol=token_in.symbol,
            token_out_name=token_in.name,
            buy_pool=buy_pool,
            sell_pool=sell_pool,
            buy_amount_in=amount_in,
            sell_amount_out=amount_out,
            gross_profit_usd=gross_profit,
            net_profit_usd=net_profit_usd,
            profit_bps=profit_bps,
            profit_pct=profit_pct,
            gas_cost_usd=gas_cost_usd,
            gas_limit=gas_limit,
            flash_loan_amount_usd=fl_amount,
            flash_loan_fee_bps=fl_fee,
            confidence_score=confidence["score"],
            confidence_factors=confidence["factors"],
            competition_score=competition["score"],
            competition_metrics=competition["metrics"],
            route_legs=route_legs,
            spread_bps=spread_bps,
            liquidity_depth_usd=liquidity_depth,
            execution_risk=execution_risk,
            recommended_action=recommended_action,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(minutes=5),
        )
    except Exception:
        return None


def _token_from_pool(pool: PoolInfo, address: str) -> TokenInfo:
    addr = address.lower()
    if pool.token0.address.lower() == addr:
        return pool.token0
    return pool.token1


def _token_symbol(pool: PoolInfo, address: str) -> str:
    return _token_from_pool(pool, address).symbol


def _pool_price_sane(pool: PoolInfo) -> bool:
    """Reject pools whose pool-local USD price deviates absurdly from the
    token's aggregate USD price. Such pools are stale/broken listings, not
    real arbitrage, and would otherwise manufacture fake opportunities."""
    max_dev = settings.OPPORTUNITY_MAX_PRICE_DEVIATION
    checks = [
        (pool.token0, pool.token0_price_usd),
        (pool.token1, pool.token1_price_usd),
    ]
    for tok, pd_price in checks:
        agg = tok.price_usd
        if agg and agg > 0 and pd_price > 0:
            ratio = pd_price / agg
            if ratio > max_dev or ratio < (1.0 / max_dev):
                return False
    return True


def _deduplicate_pools(pools: list[PoolInfo]) -> list[PoolInfo]:
    seen = set()
    unique = []
    for pool in pools:
        key = pool.address.lower()
        if key not in seen:
            seen.add(key)
            unique.append(pool)
    return unique


def _build_summary(
    opportunities: list[ArbitrageOpportunity],
    pools_scanned: int,
    tokens_scanned: int,
    scan_duration_ms: float,
    chains: list[int],
) -> dict:
    if not opportunities:
        return {
            "total_opportunities": 0,
            "total_profit_usd": 0,
            "avg_profit_bps": 0,
            "best_profit_usd": 0,
            "best_profit_bps": 0,
            "pools_scanned": pools_scanned,
            "tokens_scanned": tokens_scanned,
            "chains_active": [str(c) for c in chains],
            "scan_latency_ms": round(scan_duration_ms, 2),
            "last_scan_at": datetime.utcnow(),
            "gas_price_gwei": 0,
            "arb_gas_price_gwei": 0,
        }

    gas_info = estimate_gas_cost(chain_id=chains[0] if chains else 42161)

    return {
        "total_opportunities": len(opportunities),
        "total_profit_usd": round(sum(o.net_profit_usd for o in opportunities), 2),
        "avg_profit_bps": round(sum(o.profit_bps for o in opportunities) / len(opportunities), 2),
        "best_profit_usd": round(max(o.net_profit_usd for o in opportunities), 2),
        "best_profit_bps": round(max(o.profit_bps for o in opportunities), 2),
        "pools_scanned": pools_scanned,
        "tokens_scanned": tokens_scanned,
        "chains_active": [str(c) for c in chains],
        "scan_latency_ms": round(scan_duration_ms, 2),
        "last_scan_at": datetime.utcnow(),
        "gas_price_gwei": gas_info["gas_price_gwei"],
        "arb_gas_price_gwei": gas_info["gas_price_gwei"],
    }


def _build_network_telemetry(chains: list[int]) -> list[dict]:
    telemetry = []
    for chain_id in chains:
        gn = get_gas_price(chain_id)
        bn = get_block_number(chain_id)
        bt = get_block_time(chain_id)
        chain_name = "Arbitrum" if chain_id == 42161 else "Ethereum"
        telemetry.append(
            {
                "chain_id": chain_id,
                "chain_name": chain_name,
                "block_number": bn or 0,
                "gas_price_gwei": gn.get("gas_price_gwei", 0),
                "base_fee_gwei": gn.get("base_fee_gwei", 0),
                "priority_fee_gwei": gn.get("priority_fee_gwei", 0),
                "block_time_seconds": round(bt, 2),
                "pools_scanned": 0,
                "tokens_tracked": 0,
                "last_update_at": datetime.utcnow(),
            }
        )
    return telemetry
