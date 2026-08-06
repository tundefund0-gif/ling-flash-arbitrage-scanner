from __future__ import annotations

from typing import Optional

from models.schemas import PoolInfo, TokenInfo


def calculate_confidence_score(
    buy_pool: PoolInfo,
    sell_pool: PoolInfo,
    profit_bps: float,
    gas_cost_usd: float,
    net_profit_usd: float,
    token_in: TokenInfo,
    token_out: TokenInfo,
) -> dict:
    factors = {}
    scores = []

    liquidity_score = _score_liquidity(buy_pool, sell_pool)
    factors["liquidity"] = liquidity_score
    scores.append(liquidity_score * 0.25)

    volume_score = _score_volume(buy_pool, sell_pool)
    factors["volume"] = volume_score
    scores.append(volume_score * 0.20)

    spread_score = _score_spread(profit_bps)
    factors["spread"] = spread_score
    scores.append(spread_score * 0.20)

    gas_efficiency_score = _score_gas_efficiency(gas_cost_usd, net_profit_usd)
    factors["gas_efficiency"] = gas_efficiency_score
    scores.append(gas_efficiency_score * 0.15)

    token_quality_score = _score_token_quality(token_in, token_out)
    factors["token_quality"] = token_quality_score
    scores.append(token_quality_score * 0.10)

    pool_stability_score = _score_pool_stability(buy_pool, sell_pool)
    factors["pool_stability"] = pool_stability_score
    scores.append(pool_stability_score * 0.10)

    overall_score = max(0.0, min(1.0, sum(scores)))

    return {
        "score": round(overall_score, 4),
        "factors": factors,
        "breakdown": {
            "liquidity": round(liquidity_score, 4),
            "volume": round(volume_score, 4),
            "spread": round(spread_score, 4),
            "gas_efficiency": round(gas_efficiency_score, 4),
            "token_quality": round(token_quality_score, 4),
            "pool_stability": round(pool_stability_score, 4),
        },
    }


def _score_liquidity(buy_pool: PoolInfo, sell_pool: PoolInfo) -> float:
    min_liquidity = min(buy_pool.total_liquidity_usd, sell_pool.total_liquidity_usd)
    if min_liquidity <= 0:
        return 0.0
    if min_liquidity > 10_000_000:
        return 1.0
    if min_liquidity > 1_000_000:
        return 0.9
    if min_liquidity > 500_000:
        return 0.7
    if min_liquidity > 100_000:
        return 0.5
    if min_liquidity > 50_000:
        return 0.3
    if min_liquidity > 10_000:
        return 0.2
    return 0.1


def _score_volume(buy_pool: PoolInfo, sell_pool: PoolInfo) -> float:
    min_volume = min(buy_pool.volume_24h_usd, sell_pool.volume_24h_usd)
    if min_volume <= 0:
        return 0.0
    if min_volume > 5_000_000:
        return 1.0
    if min_volume > 1_000_000:
        return 0.85
    if min_volume > 500_000:
        return 0.65
    if min_volume > 100_000:
        return 0.45
    if min_volume > 50_000:
        return 0.25
    if min_volume > 10_000:
        return 0.15
    return 0.1


def _score_spread(profit_bps: float) -> float:
    if profit_bps <= 0:
        return 0.0
    if profit_bps > 500:
        return 1.0
    if profit_bps > 200:
        return 0.9
    if profit_bps > 100:
        return 0.7
    if profit_bps > 50:
        return 0.5
    if profit_bps > 20:
        return 0.3
    if profit_bps > 10:
        return 0.2
    if profit_bps > 5:
        return 0.15
    return 0.1


def _score_gas_efficiency(gas_cost_usd: float, net_profit_usd: float) -> float:
    if net_profit_usd <= 0:
        return 0.0
    gas_ratio = gas_cost_usd / net_profit_usd if net_profit_usd > 0 else 1.0
    if gas_ratio < 0.01:
        return 1.0
    if gas_ratio < 0.05:
        return 0.9
    if gas_ratio < 0.1:
        return 0.7
    if gas_ratio < 0.2:
        return 0.5
    if gas_ratio < 0.5:
        return 0.3
    if gas_ratio < 1.0:
        return 0.2
    return 0.1


def _score_token_quality(token_in: TokenInfo, token_out: TokenInfo) -> float:
    score = 0.5

    if token_in.price_usd and token_in.price_usd > 0:
        score += 0.1
    if token_out.price_usd and token_out.price_usd > 0:
        score += 0.1

    if token_in.market_cap and token_in.market_cap > 1_000_000:
        score += 0.1
    if token_out.market_cap and token_out.market_cap > 1_000_000:
        score += 0.1

    if token_in.volume_24h_usd and token_in.volume_24h_usd > 100_000:
        score += 0.05
    if token_out.volume_24h_usd and token_out.volume_24h_usd > 100_000:
        score += 0.05

    return min(score, 1.0)


def _score_pool_stability(buy_pool: PoolInfo, sell_pool: PoolInfo) -> float:
    score = 0.5

    if buy_pool.volume_24h_usd > buy_pool.total_liquidity_usd * 0.1:
        score += 0.15
    if sell_pool.volume_24h_usd > sell_pool.total_liquidity_usd * 0.1:
        score += 0.15

    if buy_pool.volume_24h_change_pct is not None and buy_pool.volume_24h_change_pct > -20:
        score += 0.1
    if sell_pool.volume_24h_change_pct is not None and sell_pool.volume_24h_change_pct > -20:
        score += 0.1

    return min(score, 1.0)