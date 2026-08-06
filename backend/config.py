import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ARBITRUM_RPC_URL: str = os.environ.get(
        "ARBITRUM_RPC_URL",
        "https://arb1.arbitrum.io/rpc",
    )
    ETHEREUM_RPC_URL: str = os.environ.get(
        "ETHEREUM_RPC_URL",
        "https://eth.llamarpc.com",
    )
    DEXSCREENER_API_URL: str = "https://api.dexscreener.com/latest/dex"
    SCAN_INTERVAL_SECONDS: int = int(os.environ.get("SCAN_INTERVAL_SECONDS", "15"))
    MAX_POOLS_PER_TOKEN: int = int(os.environ.get("MAX_POOLS_PER_TOKEN", "20"))
    MAX_TOKENS_PER_SCAN: int = int(os.environ.get("MAX_TOKENS_PER_SCAN", "800"))
    MIN_LIQUIDITY_USD: float = float(os.environ.get("MIN_LIQUIDITY_USD", "5000"))
    MIN_VOLUME_24H_USD: float = float(os.environ.get("MIN_VOLUME_24H_USD", "10000"))
    MAX_SLIPPAGE_BPS: int = int(os.environ.get("MAX_SLIPPAGE_BPS", "1000"))
    GAS_PRICE_GWEI: float = float(os.environ.get("GAS_PRICE_GWEI", "0.1"))
    ARBITRUM_CHAIN_ID: int = 42161
    ETHEREUM_CHAIN_ID: int = 1
    BALANCER_V2_ROUTER: str = "0xBA12222222228d8Ba445958a75a0704d566BF2C8"
    FLASHLOAN_MAX_AMOUNT_USD: float = float(
        os.environ.get("FLASHLOAN_MAX_AMOUNT_USD", "10000000")
    )
    CACHE_TTL_SECONDS: int = int(os.environ.get("CACHE_TTL_SECONDS", "10"))
    OPPORTUNITY_MIN_PROFIT_BPS: int = int(
        os.environ.get("OPPORTUNITY_MIN_PROFIT_BPS", "0.5")
    )
    OPPORTUNITY_MIN_CONFIDENCE: float = float(
        os.environ.get("OPPORTUNITY_MIN_CONFIDENCE", "0.01")
    )
    OPPORTUNITY_MAX_PROFIT_BPS_CAP: int = int(
        os.environ.get("OPPORTUNITY_MAX_PROFIT_BPS_CAP", "1000")
    )
    OPPORTUNITY_MAX_PRICE_DEVIATION: float = float(
        os.environ.get("OPPORTUNITY_MAX_PRICE_DEVIATION", "3.0")
    )
    TRADE_SIZE_USD: float = float(os.environ.get("TRADE_SIZE_USD", "250.0"))
    PORT: int = int(os.environ.get("PORT", "8000"))
    HOST: str = os.environ.get("HOST", "0.0.0.0")

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
