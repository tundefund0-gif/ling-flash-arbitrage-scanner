from __future__ import annotations

import asyncio
import os
import time
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from config import settings
from models.schemas import ScanRequest, ScanResponse
from arbitrage.engine import scan_opportunities

app = FastAPI(
    title="Arbitrum Arbitrage Scanner",
    description="Advanced real-time arbitrage opportunity scanner for Arbitrum",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_scan_state = {
    "last_scan": None,
    "last_opportunities": [],
    "last_summary": None,
    "last_networks": [],
    "is_scanning": False,
    "scan_interval": settings.SCAN_INTERVAL_SECONDS,
    "ws_clients": set(),
}


@app.get("/api/healthz")
async def health_check():
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "chain": "arbitrum",
        "chain_id": 42161,
    }


@app.get("/api/scanner/summary")
async def get_scanner_summary():
    state = _scan_state
    if state["last_summary"] is None:
        return {
            "total_opportunities": 0,
            "total_profit_usd": 0,
            "avg_profit_bps": 0,
            "best_profit_usd": 0,
            "best_profit_bps": 0,
            "pools_scanned": 0,
            "tokens_scanned": 0,
            "chains_active": ["arbitrum"],
            "scan_latency_ms": 0,
            "last_scan_at": None,
            "gas_price_gwei": settings.GAS_PRICE_GWEI,
            "arb_gas_price_gwei": settings.GAS_PRICE_GWEI,
        }
    return state["last_summary"]


@app.get("/api/scanner/networks")
async def get_networks():
    state = _scan_state
    if state["last_networks"]:
        return state["last_networks"]
    return [
        {
            "chain_id": 42161,
            "chain_name": "Arbitrum",
            "block_number": 0,
            "gas_price_gwei": settings.GAS_PRICE_GWEI,
            "base_fee_gwei": settings.GAS_PRICE_GWEI,
            "priority_fee_gwei": 0,
            "block_time_seconds": 0.25,
            "pools_scanned": 0,
            "tokens_tracked": 0,
            "last_update_at": datetime.utcnow().isoformat(),
        }
    ]


@app.get("/api/scanner/tokens")
async def get_tracked_tokens(
    chain: int = Query(42161, description="Chain ID"),
    limit: int = Query(50, ge=1, le=200),
):
    from scanner.dexscreener import discover_top_tokens_async
    tokens = await discover_top_tokens_async(chain, limit)
    return {
        "chain_id": chain,
        "count": len(tokens),
        "tokens": [t.model_dump() for t in tokens],
    }


@app.get("/api/scanner/opportunities")
async def get_opportunities(
    chain: int = Query(42161, description="Chain ID"),
    token: Optional[str] = Query(None, description="Token symbol filter"),
    minProfitBps: int = Query(0, description="Minimum profit in basis points"),
    limit: int = Query(500, ge=1, le=2000),
    minConfidence: float = Query(0.01, ge=0, le=1),
):
    state = _scan_state

    if state["last_opportunities"] and not token:
        results = state["last_opportunities"]
    else:
        scan_result = await scan_opportunities(
            chains=[chain],
            min_profit_bps=minProfitBps,
            min_confidence=minConfidence,
            limit=limit,
        )
        results = scan_result["opportunities"]
        state["last_opportunities"] = results
        state["last_summary"] = scan_result["summary"]
        state["last_networks"] = scan_result["networks"]

    if token:
        results = [
            o
            for o in results
            if o.token_in_symbol.lower() == token.lower()
            or o.token_out_symbol.lower() == token.lower()
        ]

    if chain != 42161:
        results = [o for o in results if o.chain_id == chain]

    return {
        "success": True,
        "opportunities": [o.model_dump() for o in results[:limit]],
        "total": len(results),
        "filtered": len(results),
        "limit": limit,
    }


@app.get("/api/scanner/opportunities/{opp_id}")
async def get_opportunity_detail(opp_id: str):
    state = _scan_state
    for opp in state["last_opportunities"]:
        if opp.id == opp_id:
            return {"success": True, "opportunity": opp.model_dump()}
    return JSONResponse(status_code=404, content={"error": "Opportunity not found"})


@app.post("/api/scanner/scan")
async def trigger_scan(request: ScanRequest):
    print(f"DEBUG: request.tokens = {request.tokens}")
    print(f"DEBUG: request.chains = {request.chains}")
    print(f"DEBUG: request.min_profit_bps = {request.min_profit_bps}")
    state = _scan_state
    state["is_scanning"] = True

    try:
        scan_result = await scan_opportunities(
            chains=request.chains,
            token_addresses=request.tokens,
            min_profit_bps=request.min_profit_bps,
            min_confidence=request.min_confidence,
            max_gas_cost_usd=request.max_gas_cost_usd,
            include_flashloan=request.include_flashloan,
            limit=request.limit,
        )

        state["last_opportunities"] = scan_result["opportunities"]
        state["last_summary"] = scan_result["summary"]
        state["last_networks"] = scan_result["networks"]
        state["last_scan"] = scan_result["scanned_at"]

        return ScanResponse(
            success=True,
            opportunities=scan_result["opportunities"],
            summary=scan_result["summary"],
            networks=scan_result["networks"],
            scanned_at=scan_result["scanned_at"],
            scan_duration_ms=scan_result["scan_duration_ms"],
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "success": False},
        )
    finally:
        state["is_scanning"] = False


@app.websocket("/api/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    _scan_state["ws_clients"].add(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        _scan_state["ws_clients"].discard(websocket)


async def broadcast_scan_update(data: dict):
    disconnected = set()
    for client in _scan_state["ws_clients"]:
        try:
            await client.send_text(str(data))
        except Exception:
            disconnected.add(client)
    for client in disconnected:
        _scan_state["ws_clients"].discard(client)


@app.on_event("startup")
async def startup_event():
    # Start background scan loop after a short delay to not block startup
    asyncio.create_task(_delayed_background_scan())


async def _delayed_background_scan():
    await asyncio.sleep(5)  # Wait for startup to complete
    while True:
        try:
            scan_result = await scan_opportunities(
                chains=[settings.ARBITRUM_CHAIN_ID],
                min_profit_bps=settings.OPPORTUNITY_MIN_PROFIT_BPS,
                min_confidence=settings.OPPORTUNITY_MIN_CONFIDENCE,
                include_flashloan=True,
                limit=1000,
            )
            _scan_state["last_opportunities"] = scan_result["opportunities"]
            _scan_state["last_summary"] = scan_result["summary"]
            _scan_state["last_networks"] = scan_result["networks"]
            _scan_state["last_scan"] = scan_result["scanned_at"]

            await broadcast_scan_update(
                {
                    "type": "scan_update",
                    "opportunities_count": len(scan_result["opportunities"]),
                    "summary": scan_result["summary"],
                    "scanned_at": scan_result["scanned_at"].isoformat(),
                }
            )
        except Exception:
            pass

        await asyncio.sleep(settings.SCAN_INTERVAL_SECONDS)


FRONTEND_DIST = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend", "dist")
if os.path.isdir(FRONTEND_DIST):
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        if full_path.startswith("api") or full_path.startswith("ws"):
            return JSONResponse(status_code=404, content={"error": "not found"})
        candidate = os.path.join(FRONTEND_DIST, full_path)
        if os.path.isfile(candidate):
            return FileResponse(candidate)
        return FileResponse(os.path.join(FRONTEND_DIST, "index.html"))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=False,
    )