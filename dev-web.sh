#!/bin/bash
# Development script for running web interface with hot-reload
# This script runs the Flask development server with auto-reload enabled

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "${GREEN}=== Linux ISO Torrent Updater - Development Server ===${NC}\n"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Virtual environment not found. Creating...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}Virtual environment created.${NC}\n"
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate

# Check and install dependencies
echo -e "${YELLOW}Checking dependencies...${NC}"
if ! venv/bin/pip show flask >/dev/null 2>&1; then
    echo -e "${YELLOW}Installing dependencies from requirements.txt...${NC}"
    venv/bin/pip install -r requirements.txt
    echo -e "${GREEN}Dependencies installed.${NC}\n"
else
    echo -e "${GREEN}Dependencies already installed.${NC}\n"
fi

# Check for .env files
if [ -f ".env.local" ]; then
    echo -e "${GREEN}Found .env.local - will load configuration${NC}"
elif [ -f ".env.development" ]; then
    echo -e "${GREEN}Found .env.development - will load configuration${NC}"
elif [ -f ".env" ]; then
    echo -e "${GREEN}Found .env - will load configuration${NC}"
else
    echo -e "${RED}WARNING: No .env file found!${NC}"
    echo -e "${YELLOW}Create .env.local with your Transmission credentials:${NC}"
    echo "  TRANSMISSION_HOST=localhost"
    echo "  TRANSMISSION_PORT=9091"
    echo "  TRANSMISSION_USER=your_username"
    echo "  TRANSMISSION_PASS=your_password"
    echo ""
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Parse command line arguments
PORT=${PORT:-8084}
HOST=${HOST:-127.0.0.1}
SCHEDULE_TIME=${SCHEDULE_TIME:-disabled}
LOG_LEVEL=${LOG_LEVEL:-INFO}

while [[ $# -gt 0 ]]; do
    case $1 in
        --port|-p)
            PORT="$2"
            shift 2
            ;;
        --host|-h)
            HOST="$2"
            shift 2
            ;;
        --schedule-time|-s)
            SCHEDULE_TIME="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --port, -p PORT           Port to run on (default: 8084)"
            echo "  --host, -h HOST           Host to bind to (default: 127.0.0.1)"
            echo "  --schedule-time, -s TIME  Schedule time for auto-checks (default: disabled)"
            echo ""
            echo "Environment variables:"
            echo "  PORT                      Same as --port"
            echo "  HOST                      Same as --host"
            echo "  SCHEDULE_TIME             Same as --schedule-time"
            echo ""
            echo "Examples:"
            echo "  $0                                    # Run on default settings"
            echo "  $0 --port 8085                        # Run on port 8085"
            echo "  $0 --host 0.0.0.0 --port 8084         # Accessible from network"
            echo "  $0 --schedule-time 03:00              # Enable scheduling at 3am"
            echo "  PORT=8085 $0                          # Using environment variable"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

echo -e "${GREEN}Configuration:${NC}"
echo -e "  Host: ${YELLOW}$HOST${NC}"
echo -e "  Port: ${YELLOW}$PORT${NC}"
echo -e "  Schedule: ${YELLOW}$SCHEDULE_TIME${NC}"
echo -e "  Hot-reload: ${GREEN}ENABLED${NC}"
echo -e "  Debug mode: ${GREEN}ENABLED${NC}"
echo ""
echo -e "${GREEN}Starting development server...${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop${NC}"
echo ""
echo -e "${GREEN}Access the web interface at:${NC}"
if [ "$HOST" = "0.0.0.0" ]; then
    echo -e "  ${YELLOW}http://localhost:$PORT${NC}"
    echo -e "  ${YELLOW}http://$(hostname -I | awk '{print $1}'):$PORT${NC}"
else
    echo -e "  ${YELLOW}http://$HOST:$PORT${NC}"
fi
echo ""

# Set Flask environment variables for development
export FLASK_ENV=development
export FLASK_DEBUG=1

# Run the web interface with debug mode (enables auto-reload)
exec venv/bin/python web_interface.py \
    --host "$HOST" \
    --port "$PORT" \
    --schedule-time "$SCHEDULE_TIME" \
    --debug
