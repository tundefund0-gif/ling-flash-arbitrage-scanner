#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== Arbitrum Arbitrage Scanner ==="
echo ""

# Start backend
echo "Starting backend API server..."
cd "$SCRIPT_DIR/backend"
python3 main.py &
BACKEND_PID=$!

# Wait for backend to be ready
echo "Waiting for backend to start..."
for i in $(seq 1 30); do
  if curl -s http://localhost:8000/api/healthz > /dev/null 2>&1; then
    echo "Backend is ready!"
    break
  fi
  sleep 1
done

# Start frontend
echo "Starting frontend dev server..."
cd "$SCRIPT_DIR/frontend"
npm run dev &
FRONTEND_PID=$!

echo ""
echo "=== Scanner is running ==="
echo "Frontend: http://localhost:3000"
echo "API:      http://localhost:8000"
echo ""
echo "Press Ctrl+C to stop"

# Cleanup on exit
cleanup() {
  echo "Shutting down..."
  kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
  exit 0
}
trap cleanup SIGINT SIGTERM

wait
