from __future__ import annotations

from typing import Optional

from models.schemas import PoolInfo


def calculate_competition_score(
    buy_pool: PoolInfo,
    sell_pool: PoolInfo,
    profit_bps: float,
    chain_id: int = 42161,
) -> dict:
    metrics = {}
    scores = []

    dex_competition = _score_dex_competition(buy_pool, sell_pool)
    metrics["dex_competition"] = dex_competition
    scores.append(dex_competition * 0.30)

    liquidity_depth_score = _score_liquidity_depth(buy_pool, sell_pool)
    metrics["liquidity_depth"] = liquidity_depth_score
    scores.append(liquidity_depth_score * 0.25)

    spread_attractiveness = _score_spread_attractiveness(profit_bps)
    metrics["spread_attractiveness"] = spread_attractiveness
    scores.append(spread_attractiveness * 0.20)

    pool_age_score = _score_pool_maturity(buy_pool, sell_pool)
    metrics["pool_maturity"] = pool_age_score
    scores.append(pool_age_score * 0.15)

    volume_consistency = _score_volume_consistency(buy_pool, sell_pool)
    metrics["volume_consistency"] = volume_consistency
    scores.append(volume_consistency * 0.10)

    overall_score = max(0.0, min(1.0, sum(scores)))

    return {
        "score": round(overall_score, 4),
        "metrics": metrics,
        "interpretation": _interpret_score(overall_score),
    }


def _score_dex_competition(buy_pool: PoolInfo, sell_pool: PoolInfo) -> float:
    buy_dex = buy_pool.dex_name.lower()
    sell_dex = sell_pool.dex_name.lower()

    high_competition_dexes = ["uniswap", "sushiswap", "pancakeswap", "curve"]

    buy_is_major = any(d in buy_dex for d in high_competition_dexes)
    sell_is_major = any(d in sell_dex for d in high_competition_dexes)

    if buy_is_major and sell_is_major:
        return 0.3
    if buy_is_major or sell_is_major:
        return 0.5
    return 0.8


def _score_liquidity_depth(buy_pool: PoolInfo, sell_pool: PoolInfo) -> float:
    min_liq = min(buy_pool.total_liquidity_usd, sell_pool.total_liquidity_usd)
    if min_liq <= 0:
        return 0.0
    if min_liq > 5_000_000:
        return 0.9
    if min_liq > 1_000_000:
        return 0.7
    if min_liq > 500_000:
        return 0.5
    if min_liq > 100_000:
        return 0.3
    return 0.1


def _score_spread_attractiveness(profit_bps: float) -> float:
    if profit_bps > 200:
        return 0.9
    if profit_bps > 100:
        return 0.7
    if profit_bps > 50:
        return 0.5
    if profit_bps > 20:
        return 0.3
    if profit_bps > 10:
        return 0.15
    return 0.05


def _score_pool_maturity(buy_pool: PoolInfo, sell_pool: PoolInfo) -> float:
    buy_vol = buy_pool.volume_24h_usd
    sell_vol = sell_pool.volume_24h_usd

    buy_liq = buy_pool.total_liquidity_usd
    sell_liq = sell_pool.total_liquidity_usd

    buy_ratio = buy_vol / buy_liq if buy_liq > 0 else 0
    sell_ratio = sell_vol / sell_liq if sell_liq > 0 else 0

    score = 0.5
    if buy_ratio > 0.5:
        score += 0.2
    if sell_ratio > 0.5:
        score += 0.2
    if buy_ratio > 1.0:
        score += 0.1
    if sell_ratio > 1.0:
        score += 0.1

    return min(score, 1.0)


def _score_volume_consistency(buy_pool: PoolInfo, sell_pool: PoolInfo) -> float:
    buy_change = buy_pool.volume_24h_change_pct
    sell_change = sell_pool.volume_24h_change_pct

    score = 0.5

    if buy_change is not None:
        if buy_change > -10:
            score += 0.2
        if buy_change > 0:
            score += 0.1
    if sell_change is not None:
        if sell_change > -10:
            score += 0.2
        if sell_change > 0:
            score += 0.1

    return min(score, 1.0)


def _interpret_score(score: float) -> str:
    if score >= 0.7:
        return "low_competition"
    if score >= 0.4:
        return "moderate_competition"
    if score >= 0.2:
        return "high_competition"
    return "very_high_competition"