#!/bin/bash
#
# Run script for Test Inbound Agent Server
#
# This script sets up and runs the lightweight test inbound agent server
# for manual testing without requiring Asterisk or other infrastructure.
#
# Usage:
#   ./scripts/run_test_inbound.sh [--port PORT] [--client]
#

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}Test Inbound Agent - Setup & Run${NC}"
echo -e "${BLUE}======================================${NC}"
echo ""

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Change to project directory
cd "$PROJECT_DIR"

# Check Python version
echo -e "${YELLOW}Checking Python version...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: python3 not found${NC}"
    echo "Please install Python 3.8 or higher"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo -e "${GREEN}✓ Python $PYTHON_VERSION found${NC}"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
    echo ""
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate
echo -e "${GREEN}✓ Virtual environment activated${NC}"
echo ""

# Install/upgrade websockets if needed
echo -e "${YELLOW}Checking dependencies...${NC}"
if ! python3 -c "import websockets" 2>/dev/null; then
    echo "Installing websockets library..."
    pip install websockets
    echo -e "${GREEN}✓ websockets installed${NC}"
else
    echo -e "${GREEN}✓ websockets already installed${NC}"
fi
echo ""

# Run the test server
echo -e "${GREEN}Starting test inbound agent server...${NC}"
echo ""

# Pass all arguments to the Python script
python3 tests/test_inbound_real_conversation.py "$@"
