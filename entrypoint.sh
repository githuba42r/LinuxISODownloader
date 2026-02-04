#!/bin/bash
# Docker entrypoint script for Linux ISO Torrent Updater
# Supports both CLI and web interface modes

set -e

# Check if the first argument is --web or web
if [ "$1" = "--web" ] || [ "$1" = "web" ]; then
    echo "Starting web interface..."
    shift  # Remove --web/web from arguments
    exec python /app/web_interface.py "$@"
else
    echo "Running CLI mode..."
    exec python /app/linux_iso_torrent_updater.py "$@"
fi
