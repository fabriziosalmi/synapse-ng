#!/bin/bash
# launch_dashboard.sh - Quick launcher for Organism Consciousness Dashboard

set -e

# Colors
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${CYAN}"
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                                                                ║"
echo "║     🧬  ORGANISM CONSCIOUSNESS DASHBOARD  🧬                  ║"
echo "║                                                                ║"
echo "║     Synapse-NG Real-Time Monitoring Interface                 ║"
echo "║                                                                ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Check if we're in the right directory
if [ ! -f "dashboard_ui/index.html" ]; then
    echo -e "${YELLOW}⚠️  Please run this script from the synapse-ng root directory${NC}"
    exit 1
fi

echo -e "${GREEN}[1/3]${NC} Checking prerequisites..."

# Check if node is running
if curl -s http://localhost:8000/state > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Synapse-NG node detected at http://localhost:8000"
else
    echo -e "${YELLOW}⚠️${NC}  No node detected at http://localhost:8000"
    echo "      You can still launch the dashboard and connect manually"
fi

echo ""
echo -e "${GREEN}[2/3]${NC} Choosing HTTP server..."

# Try to find an HTTP server
if command -v python3 &> /dev/null; then
    echo -e "${GREEN}✓${NC} Using Python 3 HTTP server"
    HTTP_SERVER="python3 -m http.server"
    PORT=15000
elif command -v python &> /dev/null; then
    echo -e "${GREEN}✓${NC} Using Python HTTP server"
    HTTP_SERVER="python -m SimpleHTTPServer"
    PORT=15000
elif command -v npx &> /dev/null; then
    echo -e "${GREEN}✓${NC} Using Node.js HTTP server"
    HTTP_SERVER="npx http-server"
    PORT=15000
else
    echo -e "${YELLOW}⚠️${NC}  No HTTP server found"
    echo ""
    echo "Options:"
    echo "  1. Install Python: https://python.org"
    echo "  2. Install Node.js: https://nodejs.org"
    echo "  3. Open dashboard_ui/index.html directly in your browser"
    exit 1
fi

echo ""
echo -e "${GREEN}[3/3]${NC} Launching dashboard..."
echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Dashboard URL:${NC} http://localhost:${PORT}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Change to dashboard directory and start server
cd dashboard_ui

# Try to open browser automatically
sleep 2
if command -v open &> /dev/null; then
    open "http://localhost:${PORT}" &
elif command -v xdg-open &> /dev/null; then
    xdg-open "http://localhost:${PORT}" &
elif command -v start &> /dev/null; then
    start "http://localhost:${PORT}" &
fi

# Start the server
$HTTP_SERVER $PORT
