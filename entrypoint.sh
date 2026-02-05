#!/bin/bash
# Docker entrypoint script for Linux ISO Torrent Updater
# Supports both CLI and web interface modes

set -e

# Priority order for web mode detection:
# 1. --web or web command-line argument (highest priority)
# 2. WEB_ENABLED environment variable
# 3. Default: CLI mode (lowest priority)

# Check if the first argument is --web or web
if [ "$1" = "--web" ] || [ "$1" = "web" ]; then
    echo "Starting web interface (via command-line flag)..."
    shift  # Remove --web/web from arguments
    exec python /app/web_interface.py "$@"
# Check WEB_ENABLED environment variable (case-insensitive)
elif [ "${WEB_ENABLED,,}" = "true" ] || [ "${WEB_ENABLED,,}" = "yes" ] || [ "${WEB_ENABLED}" = "1" ]; then
    echo "Starting web interface (via WEB_ENABLED environment variable)..."
    exec python /app/web_interface.py "$@"
else
    echo "Running CLI mode..."
    exec python /app/linux_iso_torrent_updater.py "$@"
fi
