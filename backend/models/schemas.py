from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class TokenInfo(BaseModel):
    address: str
    symbol: str
    name: str
    decimals: int
    total_supply: Optional[str] = None
    price_usd: Optional[float] = None
    market_cap: Optional[float] = None
    volume_24h_usd: Optional[float] = None
    change_24h_pct: Optional[float] = None
    chain_id: int
    logo_url: Optional[str] = None
    last_updated: datetime = Field(default_factory=datetime.utcnow)


class PoolInfo(BaseModel):
    address: str
    token0: TokenInfo
    token1: TokenInfo
    reserve0: float
    reserve1: float
    total_liquidity_usd: float
    volume_24h_usd: float
    volume_24h_change_pct: Optional[float] = None
    fee_rate: float
    pool_type: str
    dex_name: str
    chain_id: int
    price_token0_per_token1: float
    price_token1_per_token0: float
    token0_price_usd: float = 0.0
    token1_price_usd: float = 0.0
    last_updated: datetime = Field(default_factory=datetime.utcnow)


class RouteLeg(BaseModel):
    pool_address: str
    dex_name: str
    pool_type: str
    token_in: str
    token_out: str
    amount_in: float
    amount_out: float
    price_impact_bps: float
    fee_bps: float
    reserve_in_usd: float
    reserve_out_usd: float


class ArbitrageOpportunity(BaseModel):
    id: str
    chain_id: int
    chain_name: str
    token_in_address: str
    token_in_symbol: str
    token_in_name: str
    token_out_address: str
    token_out_symbol: str
    token_out_name: str
    buy_pool: PoolInfo
    sell_pool: PoolInfo
    buy_amount_in: float
    sell_amount_out: float
    gross_profit_usd: float
    net_profit_usd: float
    profit_bps: float
    profit_pct: float
    gas_cost_usd: float
    gas_limit: int
    flash_loan_amount_usd: float
    flash_loan_fee_bps: int
    confidence_score: float
    confidence_factors: dict
    competition_score: float
    competition_metrics: dict
    route_legs: list[RouteLeg]
    spread_bps: float
    liquidity_depth_usd: float
    execution_risk: str
    recommended_action: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime = Field(default_factory=datetime.utcnow)


class ScannerSummary(BaseModel):
    total_opportunities: int
    total_profit_usd: float
    avg_profit_bps: float
    best_profit_usd: float
    best_profit_bps: float
    pools_scanned: int
    tokens_scanned: int
    chains_active: list[str]
    scan_latency_ms: float
    last_scan_at: datetime
    gas_price_gwei: float
    arb_gas_price_gwei: float


class NetworkTelemetry(BaseModel):
    chain_id: int
    chain_name: str
    block_number: int
    gas_price_gwei: float
    base_fee_gwei: float
    priority_fee_gwei: float
    block_time_seconds: float
    pools_scanned: int
    tokens_tracked: int
    last_update_at: datetime


class FlashLoanQuote(BaseModel):
    provider: str
    token_address: str
    token_symbol: str
    amount: float
    amount_usd: float
    fee_bps: int
    total_cost_usd: float
    duration_blocks: int
    available_liquidity_usd: float


class ScanRequest(BaseModel):
    chains: list[int] = Field(default_factory=lambda: [42161])
    tokens: Optional[list[str]] = None
    min_profit_bps: int = 10
    min_confidence: float = 0.3
    max_gas_cost_usd: float = 50.0
    include_flashloan: bool = True
    limit: int = 50


class ScanResponse(BaseModel):
    success: bool
    opportunities: list[ArbitrageOpportunity]
    summary: ScannerSummary
    networks: list[NetworkTelemetry]
    scanned_at: datetime
    scan_duration_ms: float
