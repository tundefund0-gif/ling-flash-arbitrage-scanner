from __future__ import annotations

import time
from typing import Optional

from config import settings
from scanner.rpc import get_gas_price, get_block_number


ARBITRUM_OVERHEAD_GAS = 21000
ARBITRUM_SWAP_GAS = 150000
ARBITRUM_APPROVE_GAS = 46000
ARBITRUM_FLASHLOAN_GAS = 350000
ARBITRUM_MULTICALL_GAS = 300000

ARBITRUM_L1_GAS_PRICE_MULTIPLIER = 0.001


def estimate_gas_cost(
    chain_id: int = 42161,
    gas_limit: int = None,
    operation: str = "swap",
) -> dict:
    gas_info = get_gas_price(chain_id)
    gas_price_gwei = float(gas_info.get("gas_price_gwei", settings.GAS_PRICE_GWEI))

    if gas_limit is None:
        gas_limit = _get_default_gas_limit(operation)

    gas_price_wei = gas_price_gwei * 1e9
    gas_cost_wei = gas_limit * gas_price_wei

    arb_gas_price = gas_price_gwei * ARBITRUM_L1_GAS_PRICE_MULTIPLIER
    l1_gas_cost_wei = gas_limit * arb_gas_price * 1e9

    total_gas_wei = gas_cost_wei + l1_gas_cost_wei

    try:
        from web3 import Web3
        w3 = None
        rpc_url = (
            settings.ARBITRUM_RPC_URL
            if chain_id == 42161
            else settings.ETHEREUM_RPC_URL
        )
        w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={"timeout": 10}))
        if w3 and w3.is_connected():
            eth_price_usd = _get_eth_price_usd()
        else:
            eth_price_usd = _get_eth_price_usd_fallback()
    except Exception:
        eth_price_usd = _get_eth_price_usd_fallback()

    gas_cost_usd = (total_gas_wei / 1e18) * eth_price_usd

    return {
        "gas_limit": gas_limit,
        "gas_price_gwei": gas_price_gwei,
        "gas_cost_wei": gas_cost_wei,
        "l1_gas_cost_wei": l1_gas_cost_wei,
        "total_gas_wei": total_gas_wei,
        "estimated_cost_usd": round(gas_cost_usd, 4),
        "eth_price_usd": eth_price_usd,
        "operation": operation,
        "timestamp": time.time(),
    }


def estimate_flashloan_gas_cost(
    chain_id: int = 42161,
    flashloan_amount_usd: float = 100000,
) -> dict:
    base = estimate_gas_cost(
        chain_id=chain_id,
        gas_limit=ARBITRUM_FLASHLOAN_GAS,
        operation="flashloan",
    )

    try:
        from web3 import Web3
        rpc_url = (
            settings.ARBITRUM_RPC_URL
            if chain_id == 42161
            else settings.ETHEREUM_RPC_URL
        )
        w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={"timeout": 10}))
        if w3 and w3.is_connected():
            eth_price_usd = _get_eth_price_usd()
        else:
            eth_price_usd = _get_eth_price_usd_fallback()
    except Exception:
        eth_price_usd = _get_eth_price_usd_fallback()

    return {
        "gas_limit": ARBITRUM_FLASHLOAN_GAS,
        "gas_price_gwei": base["gas_price_gwei"],
        "estimated_cost_usd": round(base["estimated_cost_usd"], 4),
        "flashloan_amount_usd": flashloan_amount_usd,
        "eth_price_usd": eth_price_usd,
        "operation": "flashloan",
        "timestamp": time.time(),
    }


def estimate_full_arb_gas_cost(
    chain_id: int = 42161,
    use_flashloan: bool = False,
) -> dict:
    if use_flashloan:
        return estimate_gas_cost(
            chain_id=chain_id,
            gas_limit=ARBITRUM_FLASHLOAN_GAS + ARBITRUM_SWAP_GAS,
            operation="flashloan_swap",
        )
    return estimate_gas_cost(
        chain_id=chain_id,
        gas_limit=ARBITRUM_SWAP_GAS * 2 + ARBITRUM_APPROVE_GAS,
        operation="full_arb",
    )


def _get_default_gas_limit(operation: str) -> int:
    limits = {
        "swap": ARBITRUM_SWAP_GAS,
        "approve": ARBITRUM_APPROVE_GAS,
        "flashloan": ARBITRUM_FLASHLOAN_GAS,
        "flashloan_swap": ARBITRUM_FLASHLOAN_GAS + ARBITRUM_SWAP_GAS,
        "full_arb": ARBITRUM_SWAP_GAS * 2 + ARBITRUM_APPROVE_GAS,
        "multicall": ARBITRUM_MULTICALL_GAS,
    }
    return limits.get(operation, ARBITRUM_SWAP_GAS)


def _get_eth_price_usd() -> float:
    try:
        import requests
        resp = requests.get(
            "https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd",
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        return float(data.get("ethereum", {}).get("usd", 0) or 0)
    except Exception:
        return _get_eth_price_usd_fallback()


def _get_eth_price_usd_fallback() -> float:
    return 3500.0


def get_arb_gas_estimate(
    to_address: str,
    data: str = "0x",
    value_wei: int = 0,
    chain_id: int = 42161,
) -> dict:
    gas_info = get_gas_price(chain_id)
    gas_price_gwei = gas_info.get("gas_price_gwei", settings.GAS_PRICE_GWEI)

    try:
        from web3 import Web3
        rpc_url = (
            settings.ARBITRUM_RPC_URL
            if chain_id == 42161
            else settings.ETHEREUM_RPC_URL
        )
        w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={"timeout": 10}))
        if w3 and w3.is_connected():
            estimated_gas = w3.eth.estimate_gas(
                {"from": w3.eth.accounts[0] if w3.eth.accounts else "0x0000000000000000000000000000000000000000", "to": to_address, "data": data, "value": value_wei}
            )
        else:
            estimated_gas = ARBITRUM_SWAP_GAS
    except Exception:
        estimated_gas = ARBITRUM_SWAP_GAS

    gas_price_wei = gas_price_gwei * 1e9
    gas_cost_wei = estimated_gas * gas_price_wei

    eth_price = _get_eth_price_usd()
    gas_cost_usd = (gas_cost_wei / 1e18) * eth_price

    return {
        "estimated_gas": estimated_gas,
        "gas_price_gwei": gas_price_gwei,
        "gas_cost_wei": gas_cost_wei,
        "estimated_cost_usd": round(gas_cost_usd, 4),
        "eth_price_usd": eth_price,
        "to_address": to_address,
        "timestamp": time.time(),
    }