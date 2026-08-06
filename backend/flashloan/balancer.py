from __future__ import annotations

import time
from typing import Optional

import requests

from config import settings
from models.schemas import FlashLoanQuote

BALANCER_V2_ROUTER = settings.BALANCER_V2_ROUTER
BALANCER_FLASHLOAN_FEE_BPS = 900
BALANCER_FLASHLOAN_PROTOCOL_FEE_BPS = 100

FLASHLOAN_PROVIDERS = {
    "balancer_v2": {
        "router": BALANCER_V2_ROUTER,
        "fee_bps": BALANCER_FLASHLOAN_FEE_BPS,
        "protocol_fee_bps": BALANCER_FLASHLOAN_PROTOCOL_FEE_BPS,
    },
}


def get_flash_loan_quote(
    token_address: str,
    amount_usd: float,
    chain_id: int = 42161,
) -> Optional[FlashLoanQuote]:
    if chain_id != 42161:
        return None

    provider = FLASHLOAN_PROVIDERS.get("balancer_v2")
    if provider is None:
        return None

    total_fee_bps = provider["fee_bps"] + provider["protocol_fee_bps"]

    try:
        amount_float = float(amount_usd)
    except (ValueError, TypeError):
        amount_float = 0.0

    total_cost_usd = amount_float * (1 + total_fee_bps / 10000)

    available_liquidity = _get_balancer_liquidity(token_address, chain_id)

    quote = FlashLoanQuote(
        provider="balancer_v2",
        token_address=token_address,
        token_symbol="",
        amount=amount_float,
        amount_usd=amount_float,
        fee_bps=total_fee_bps,
        total_cost_usd=round(total_cost_usd, 2),
        duration_blocks=1,
        available_liquidity_usd=available_liquidity,
    )

    return quote


def get_max_flashloan_amount(
    token_address: str,
    chain_id: int = 42161,
) -> float:
    liquidity = _get_balancer_liquidity(token_address, chain_id)
    if liquidity <= 0:
        return 0.0
    return min(liquidity * 0.8, settings.FLASHLOAN_MAX_AMOUNT_USD)


def _get_balancer_liquidity(token_address: str, chain_id: int) -> float:
    try:
        resp = requests.get(
            f"{settings.DEXSCREENER_API_URL}/tokens/{token_address}",
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        pairs = data.get("pairs", [])
        total_liquidity = 0.0
        for pair in pairs:
            liq = pair.get("liquidity", {})
            total_liquidity += float(liq.get("usd", 0) or 0)
        return total_liquidity
    except Exception:
        return 0.0


def get_balancer_pool_reserves(
    pool_address: str,
    chain_id: int = 42161,
) -> Optional[dict]:
    w3 = None
    try:
        from web3 import Web3
        rpc_url = (
            settings.ARBITRUM_RPC_URL
            if chain_id == 42161
            else settings.ETHEREUM_RPC_URL
        )
        w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={"timeout": 10}))
        if not w3 or not w3.is_connected():
            return None

        balancer_pool_abi = [
            {
                "inputs": [],
                "name": "getNormalizedWeights",
                "outputs": [{"name": "", "type": "uint256[]"}],
                "stateMutability": "view",
                "type": "function",
            },
            {
                "inputs": [],
                "name": "getBalances",
                "outputs": [{"name": "", "type": "uint256[]"}],
                "stateMutability": "view",
                "type": "function",
            },
            {
                "inputs": [],
                "name": "getTokens",
                "outputs": [{"name": "", "type": "address[]"}],
                "stateMutability": "view",
                "type": "function",
            },
            {
                "inputs": [],
                "name": "totalSupply",
                "outputs": [{"name": "", "type": "uint256"}],
                "stateMutability": "view",
                "type": "function",
            },
        ]

        contract = w3.eth.contract(
            address=Web3.to_checksum_address(pool_address),
            abi=balancer_pool_abi,
        )

        tokens = contract.functions.getTokens().call()
        balances = contract.functions.getBalances().call()
        weights = contract.functions.getNormalizedWeights().call()
        total_supply = contract.functions.totalSupply().call()

        token_balances = []
        for i, token in enumerate(tokens):
            token_balances.append(
                {
                    "token": token,
                    "balance": balances[i],
                    "weight": weights[i] if i < len(weights) else 0,
                }
            )

        return {
            "pool_address": pool_address,
            "tokens": token_balances,
            "total_supply": total_supply,
        }
    except Exception:
        return None
    finally:
        if w3:
            try:
                w3.provider.close()
            except Exception:
                pass