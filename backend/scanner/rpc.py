from __future__ import annotations

import time
from typing import Optional

from web3 import Web3

from config import settings


def get_web3(chain_id: int = 42161) -> Optional[Web3]:
    rpc_url = (
        settings.ARBITRUM_RPC_URL
        if chain_id == 42161
        else settings.ETHEREUM_RPC_URL
    )
    try:
        w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={"timeout": 10}))
        if w3.is_connected():
            return w3
    except Exception:
        pass
    return None


def get_block_number(chain_id: int = 42161) -> Optional[int]:
    w3 = get_web3(chain_id)
    if w3 is None:
        return None
    try:
        return w3.eth.block_number
    except Exception:
        return None


def get_gas_price(chain_id: int = 42161) -> dict:
    w3 = get_web3(chain_id)
    result = {
        "gas_price_gwei": 0,
        "base_fee_gwei": 0,
        "priority_fee_gwei": 0,
        "timestamp": time.time(),
    }
    if w3 is None:
        return result
    try:
        gas_price = w3.eth.gas_price
        result["gas_price_gwei"] = w3.from_wei(gas_price, "gwei")
        block = w3.eth.get_block("latest")
        base_fee = block.get("baseFeePerGas")
        if base_fee:
            result["base_fee_gwei"] = w3.from_wei(base_fee, "gwei")
            priority_fee = gas_price - base_fee
            result["priority_fee_gwei"] = w3.from_wei(max(priority_fee, 0), "gwei")
    except Exception:
        pass
    return result


def get_block_time(chain_id: int = 42161) -> float:
    w3 = get_web3(chain_id)
    if w3 is None:
        return 0
    try:
        latest = w3.eth.get_block("latest")
        prev = w3.eth.get_block(latest["number"] - 1)
        return float(latest["timestamp"] - prev["timestamp"])
    except Exception:
        return 0


def get_contract(abi: list, address: str, chain_id: int = 42161):
    w3 = get_web3(chain_id)
    if w3 is None:
        return None
    return w3.eth.contract(address=Web3.to_checksum_address(address), abi=abi)


def call_contract_method(contract, method_name: str, *args, **kwargs):
    try:
        method = getattr(contract.functions, method_name)(*args, **kwargs)
        return method.call()
    except Exception:
        return None


def get_token_balance(token_address: str, wallet_address: str, chain_id: int = 42161) -> Optional[int]:
    erc20_abi = [
        {
            "constant": True,
            "inputs": [{"name": "_owner", "type": "address"}],
            "name": "balanceOf",
            "outputs": [{"name": "balance", "type": "uint256"}],
            "type": "function",
        },
        {
            "constant": True,
            "inputs": [],
            "name": "decimals",
            "outputs": [{"name": "", "type": "uint8"}],
            "type": "function",
        },
    ]
    contract = get_contract(erc20_abi, token_address, chain_id)
    if contract is None:
        return None
    try:
        balance = contract.functions.balanceOf(wallet_address).call()
        decimals = contract.functions.decimals().call()
        return balance
    except Exception:
        return None


def get_token_price_from_pool(pool_address: str, chain_id: int = 42161) -> Optional[dict]:
    w3 = get_web3(chain_id)
    if w3 is None:
        return None

    pair_abi = [
        {
            "inputs": [],
            "name": "getReserves",
            "outputs": [
                {"name": "reserve0", "type": "uint112"},
                {"name": "reserve1", "type": "uint112"},
                {"name": "blockTimestampLast", "type": "uint32"},
            ],
            "stateMutability": "view",
            "type": "function",
        },
        {
            "inputs": [],
            "name": "token0",
            "outputs": [{"name": "", "type": "address"}],
            "stateMutability": "view",
            "type": "function",
        },
        {
            "inputs": [],
            "name": "token1",
            "outputs": [{"name": "", "type": "address"}],
            "stateMutability": "view",
            "type": "function",
        },
        {
            "inputs": [],
            "name": "fee",
            "outputs": [{"name": "", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function",
        },
    ]

    try:
        contract = w3.eth.contract(
            address=Web3.to_checksum_address(pool_address),
            abi=pair_abi,
        )
        reserves = contract.functions.getReserves().call()
        token0 = contract.functions.token0().call()
        token1 = contract.functions.token1().call()
        fee = contract.functions.fee().call()

        reserve0 = reserves[0]
        reserve1 = reserves[1]
        fee_rate = float(fee) / 1e6 if isinstance(fee, int) else 0.003

        price0_per_1 = float(reserve1) / float(reserve0) if reserve0 > 0 else 0
        price1_per_0 = float(reserve0) / float(reserve1) if reserve1 > 0 else 0

        return {
            "pool_address": pool_address,
            "token0": token0,
            "token1": token1,
            "reserve0": reserve0,
            "reserve1": reserve1,
            "fee_rate": fee_rate,
            "price_token0_per_token1": price0_per_1,
            "price_token1_per_token0": price1_per_0,
        }
    except Exception:
        return None