export interface TokenInfo {
  address: string;
  symbol: string;
  name: string;
  decimals: number;
  total_supply?: string;
  price_usd?: number;
  market_cap?: number;
  volume_24h_usd?: number;
  change_24h_pct?: number;
  chain_id: number;
  logo_url?: string;
  last_updated: string;
}

export interface PoolInfo {
  address: string;
  token0: TokenInfo;
  token1: TokenInfo;
  reserve0: string;
  reserve1: string;
  total_liquidity_usd: number;
  volume_24h_usd: number;
  volume_24h_change_pct?: number;
  fee_rate: number;
  pool_type: string;
  dex_name: string;
  chain_id: number;
  price_token0_per_token1: number;
  price_token1_per_token0: number;
  last_updated: string;
}

export interface RouteLeg {
  pool_address: string;
  dex_name: string;
  pool_type: string;
  token_in: string;
  token_out: string;
  amount_in: number;
  amount_out: number;
  price_impact_bps: number;
  fee_bps: number;
  reserve_in_usd: number;
  reserve_out_usd: number;
}

export interface ArbitrageOpportunity {
  id: string;
  chain_id: number;
  chain_name: string;
  token_in_address: string;
  token_in_symbol: string;
  token_in_name: string;
  token_out_address: string;
  token_out_symbol: string;
  token_out_name: string;
  buy_pool: PoolInfo;
  sell_pool: PoolInfo;
  buy_amount_in: number;
  sell_amount_out: number;
  gross_profit_usd: number;
  net_profit_usd: number;
  profit_bps: number;
  profit_pct: number;
  gas_cost_usd: number;
  gas_limit: number;
  flash_loan_amount_usd: number;
  flash_loan_fee_bps: number;
  confidence_score: number;
  confidence_factors: Record<string, number>;
  competition_score: number;
  competition_metrics: Record<string, number>;
  route_legs: RouteLeg[];
  spread_bps: number;
  liquidity_depth_usd: number;
  execution_risk: string;
  recommended_action: string;
  created_at: string;
  expires_at: string;
}

export interface ScannerSummary {
  total_opportunities: number;
  total_profit_usd: number;
  avg_profit_bps: number;
  best_profit_usd: number;
  best_profit_bps: number;
  pools_scanned: number;
  tokens_scanned: number;
  chains_active: string[];
  scan_latency_ms: number;
  last_scan_at: string;
  gas_price_gwei: number;
  arb_gas_price_gwei: number;
}

export interface NetworkTelemetry {
  chain_id: number;
  chain_name: string;
  block_number: number;
  gas_price_gwei: number;
  base_fee_gwei: number;
  priority_fee_gwei: number;
  block_time_seconds: number;
  pools_scanned: number;
  tokens_tracked: number;
  last_update_at: string;
}

export interface FlashLoanQuote {
  provider: string;
  token_address: string;
  token_symbol: string;
  amount: number;
  amount_usd: number;
  fee_bps: number;
  total_cost_usd: number;
  duration_blocks: number;
  available_liquidity_usd: number;
}

export interface ScanRequest {
  chains: number[];
  tokens?: string[];
  min_profit_bps: number;
  min_confidence: number;
  max_gas_cost_usd: number;
  include_flashloan: boolean;
  limit: number;
}

export interface ScanResponse {
  success: boolean;
  opportunities: ArbitrageOpportunity[];
  summary: ScannerSummary;
  networks: NetworkTelemetry[];
  scanned_at: string;
  scan_duration_ms: number;
}

export interface ConfidenceBreakdown {
  liquidity: number;
  volume: number;
  spread: number;
  gas_efficiency: number;
  token_quality: number;
  pool_stability: number;
}

export interface CompetitionMetrics {
  dex_competition: number;
  liquidity_depth: number;
  spread_attractiveness: number;
  pool_maturity: number;
  volume_consistency: number;
}

export interface ScanFilters {
  chain: number;
  token: string;
  minProfitBps: number;
  minConfidence: number;
  maxGasCostUsd: number;
  limit: number;
}