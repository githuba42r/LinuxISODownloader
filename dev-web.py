#!/usr/bin/env python3
"""
Development runner for the web interface with hot-reload support.
This script provides a simple way to run the web interface during development.
"""

import os
import sys
import subprocess
from pathlib import Path

# ANSI color codes
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
RED = '\033[0;31m'
BLUE = '\033[0;34m'
NC = '\033[0m'  # No Color

def print_colored(message, color=NC):
    """Print colored message."""
    print(f"{color}{message}{NC}")

def check_venv():
    """Check if running in virtual environment."""
    if sys.prefix == sys.base_prefix:
        print_colored("⚠️  Not running in virtual environment!", YELLOW)
        print_colored("Recommended: Run './dev-web.sh' instead for automatic venv setup", YELLOW)
        print()
        response = input("Continue without venv? (y/N): ")
        if response.lower() != 'y':
            sys.exit(1)
    else:
        print_colored("✓ Running in virtual environment", GREEN)

def check_dependencies():
    """Check if required packages are installed."""
    try:
        import flask
        import apscheduler
        import transmission_rpc
        print_colored("✓ Dependencies installed", GREEN)
        return True
    except ImportError as e:
        print_colored(f"✗ Missing dependency: {e}", RED)
        print_colored("Run: pip install -r requirements.txt", YELLOW)
        return False

def check_env_files():
    """Check for environment configuration files."""
    env_files = ['.env.local', '.env.development', '.env']
    found = False
    
    for env_file in env_files:
        if Path(env_file).exists():
            print_colored(f"✓ Found {env_file}", GREEN)
            found = True
            break
    
    if not found:
        print_colored("⚠️  No .env file found!", YELLOW)
        print_colored("Create .env.local with your Transmission credentials:", YELLOW)
        print("  TRANSMISSION_HOST=localhost")
        print("  TRANSMISSION_PORT=9091")
        print("  TRANSMISSION_USER=your_username")
        print("  TRANSMISSION_PASS=your_password")
        print()
    
    return found

def main():
    """Main entry point."""
    print_colored("=" * 60, BLUE)
    print_colored("  Linux ISO Torrent Updater - Development Server", BLUE)
    print_colored("=" * 60, BLUE)
    print()
    
    # Check environment
    check_venv()
    
    if not check_dependencies():
        sys.exit(1)
    
    check_env_files()
    
    # Get configuration from environment or defaults
    host = os.environ.get('HOST', '127.0.0.1')
    port = os.environ.get('PORT', '8084')
    schedule_time = os.environ.get('SCHEDULE_TIME', 'disabled')
    
    print()
    print_colored("Configuration:", GREEN)
    print(f"  Host:       {host}")
    print(f"  Port:       {port}")
    print(f"  Schedule:   {schedule_time}")
    print(f"  Debug:      ENABLED (hot-reload)")
    print()
    print_colored("Starting development server...", GREEN)
    print_colored("Press Ctrl+C to stop", YELLOW)
    print()
    
    if host == '0.0.0.0':
        print_colored("Access at:", BLUE)
        print(f"  http://localhost:{port}")
        # Try to get local IP
        try:
            import socket
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            print(f"  http://{local_ip}:{port}")
        except:
            pass
    else:
        print_colored(f"Access at: http://{host}:{port}", BLUE)
    
    print()
    print_colored("📝 Changes to Python/HTML/CSS/JS files will auto-reload!", GREEN)
    print()
    
    # Set Flask environment for development
    os.environ['FLASK_ENV'] = 'development'
    os.environ['FLASK_DEBUG'] = '1'
    
    # Build command
    cmd = [
        sys.executable,
        'web_interface.py',
        '--host', host,
        '--port', port,
        '--schedule-time', schedule_time,
        '--debug'
    ]
    
    # Run the web interface
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print()
        print_colored("✓ Development server stopped", GREEN)
        sys.exit(0)

if __name__ == '__main__':
    main()
