# Ling Flash Arbitrage Scanner

Advanced real-time arbitrage opportunity scanner for the Arbitrum network. Discovers hundreds of cross-DEX, triangular, and multi-hop arbitrage opportunities using pool-derived pricing with slippage-aware profit calculation.

## Features

- **Real-time Pool Scanning**: Discovers and monitors DEX pools on Arbitrum via DexScreener data
- **BFS Token Discovery**: Breadth-first search from seed symbols to find connected token pairs
- **Cross-Pool Arbitrage**: Finds price discrepancies across pools for the same token pairs
- **Triangular Arbitrage**: Detects 3-hop and 4-hop cyclic arbitrage routes
- **Multi-Hop Arbitrage**: DFS cycle detection for up to 4-hop routes with real fees
- **Pool-Derived Pricing**: Prices computed from on-chain liquidity split (no stale aggregates)
- **Slippage-Aware Profit**: Constant-product model with impact estimation (`tradeSize / (2 × liquidity)`)
- **Sanity Filter**: Drops pools whose local price deviates >3× from token aggregate
- **Beautiful Web UI**: Glassmorphism dark theme, animated backgrounds, sortable tables, route chips, confidence bars, detail drawers, profit distribution chart

## Architecture

```
ling-flash-arbitrage-scanner/
├── backend/                  # Python FastAPI backend
│   ├── main.py              # FastAPI app entry point, routes, background scan
│   ├── config.py            # All tunable configuration parameters
│   ├── models/
│   │   └── schemas.py       # Pydantic data models (PoolInfo, etc.)
│   ├── scanner/
│   │   ├── dexscreener.py   # Async DexScreener client, BFS discovery, pool pricing
│   │   └── rpc.py           # RPC helpers
│   ├── arbitrage/
│   │   ├── engine.py        # Async scan engine, opportunity builder, sanity filter
│   │   └── router.py        # get_amount_out, cross-pool, triangular, multi-hop detection
│   ├── gas/
│   │   └── calculator.py    # L1+L2 gas cost estimation
│   ├── flashloan/
│   │   └── balancer.py      # Balancer V2 flash loan quotes
│   ├── scoring/
│   │   ├── confidence.py    # Multi-factor confidence scoring
│   │   └── competition.py   # Market competition scoring
│   └── requirements.txt     # Python dependencies
├── frontend/                 # React/Vite frontend
│   ├── src/
│   │   ├── App.tsx          # SPA with tabs, token map, dashboard layout
│   │   ├── main.tsx         # React entry point
│   │   ├── index.css        # Design system (glassmorphism, dark theme, animations)
│   │   ├── components/
│   │   │   ├── Dashboard.tsx        # Composed dashboard view
│   │   │   ├── SummaryCards.tsx     # Stat cards with gradient accents
│   │   │   ├── ProfitChart.tsx      # Canvas-based profit distribution histogram
│   │   │   ├── FilterBar.tsx        # Slider controls for filtering
│   │   │   ├── OpportunityTable.tsx # Sortable table with pagination
│   │   │   ├── OpportunityDetail.tsx# Slide-over detail drawer
│   │   │   ├── RouteChips.tsx       # Token map helper, route chip rendering
│   │   │   ├── NetworkPulse.tsx     # Network telemetry display
│   │   │   ├── ProfitBreakdown.tsx  # Per-leg profit breakdown
│   │   │   ├── FlashLoanInfo.tsx    # Flash loan details
│   │   │   ├── GasEstimate.tsx      # Gas cost display
│   │   │   ├── ScoreBadge.tsx       # Score visualization
│   │   │   ├── LoadingState.tsx     # Loading skeleton
│   │   │   ├── ErrorState.tsx       # Error display
│   │   │   ├── EmptyState.tsx       # Empty state with scan trigger
│   │   │   └── icons.tsx            # Inline SVG icon components
│   │   ├── hooks/
│   │   │   ├── useOpportunities.ts  # Data fetching with auto-refresh
│   │   │   ├── useScanner.ts        # Scan trigger hook
│   │   │   └── useWebSocket.ts      # WebSocket connection hook
│   │   ├── lib/
│   │   │   ├── api.ts         # API client
│   │   │   └── types.ts       # TypeScript interfaces
│   │   └── utils/
│   │       ├── format.ts      # Formatting helpers (USD, bps, %, risk, score)
│   │       └── colors.ts      # Color utilities
│   ├── index.html             # HTML entry point
│   ├── package.json           # Node dependencies
│   ├── tsconfig.json          # TypeScript config
│   └── vite.config.ts         # Vite config with proxy to backend
├── .env.example               # Environment variables template
├── start.sh                   # Quick-start script
└── README.md                  # This file
```

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+

### Backend

```bash
cd backend
pip install -r requirements.txt
python main.py
```

The API starts on `http://localhost:8000`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The dev UI runs on `http://localhost:5173` (proxies `/api` to `localhost:8000`).

### Production Build

```bash
cd frontend
npm run build
```

The built SPA is served from the backend at `http://localhost:8000/`.

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/healthz` | GET | Health check |
| `/api/scanner/summary` | GET | Scanner summary metrics |
| `/api/scanner/networks` | GET | Network telemetry |
| `/api/scanner/tokens` | GET | Tracked tokens |
| `/api/scanner/opportunities` | GET | Filtered opportunities (query params: `minProfitBps`, `minConfidence`, `limit`) |
| `/api/scanner/opportunities/:id` | GET | Opportunity detail by ID |
| `/api/scanner/scan` | POST | Trigger a manual scan (body: `min_profit_bps`, `min_confidence`, `limit`, etc.) |
| `/api/ws` | WS | WebSocket for real-time scan updates |

## Configuration

Key tunable parameters in `backend/config.py`:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `MAX_TOKENS_PER_SCAN` | 800 | Max tokens discovered via BFS |
| `OPPORTUNITY_MIN_PROFIT_BPS` | 0.5 | Minimum profit in basis points |
| `OPPORTUNITY_MIN_CONFIDENCE` | 0.01 | Minimum confidence score |
| `OPPORTUNITY_MAX_PROFIT_BPS_CAP` | 1000 | Cap to filter unrealistic profits |
| `OPPORTUNITY_MAX_PRICE_DEVIATION` | 3.0 | Max local price deviation from aggregate |
| `TRADE_SIZE_USD` | 250.0 | Trade size for profit calculation |

## Scoring System

### Confidence Score (0–100%)
- Liquidity depth (25%)
- Volume (20%)
- Spread/Profit (20%)
- Gas efficiency (15%)
- Token quality (10%)
- Pool stability (10%)

### Competition Score (0–100%)
- DEX competition (30%)
- Liquidity depth (25%)
- Spread attractiveness (20%)
- Pool maturity (15%)
- Volume consistency (10%)

## Accuracy

- **No stale price assumptions**: All pool prices are derived from on-chain liquidity split, not DexScreener's `priceNative`
- **Slippage-aware**: `get_amount_out()` uses constant-product approximation with impact estimation
- **Sanity filter**: Pools whose local price deviates >3× from the token aggregate are excluded
- **Real fees**: All arbitrage legs include DEX swap fees and flash loan fees

## License

MIT
