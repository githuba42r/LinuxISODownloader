#!/usr/bin/env python3
"""
Web Interface for Linux ISO Torrent Updater
Provides a web-based UI for managing torrent updates.
"""

import json
import logging
import os
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from flask import Flask, render_template, jsonify, request
import transmission_rpc
from dotenv import load_dotenv

# Import the torrent manager from the main script
sys.path.insert(0, str(Path(__file__).parent))
import linux_iso_torrent_updater
from linux_iso_torrent_updater import (
    TransmissionTorrentManager,
    load_dotenv_files,
    load_config,
    setup_logging
)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)

# Global variables
manager: Optional[TransmissionTorrentManager] = None
last_check_time: Optional[datetime] = None
last_check_results: Dict[str, Dict] = {}
check_in_progress = False
check_lock = threading.Lock()

# Setup logging
logger = setup_logging()
# Set logger in imported module so it can be used there
linux_iso_torrent_updater.logger = logger


def initialize_manager():
    """Initialize the torrent manager with configuration."""
    global manager
    
    try:
        config = load_config()
        
        if not config.get('username') or not config.get('password'):
            logger.error("Transmission credentials not configured!")
            return False
        
        manager = TransmissionTorrentManager(
            host=config['host'],
            port=config['port'],
            username=config['username'],
            password=config['password'],
            dry_run=False
        )
        
        logger.info("Torrent manager initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize manager: {e}")
        return False


def get_torrent_status() -> List[Dict]:
    """Get status of all torrents in Transmission."""
    if not manager or not manager.client:
        return []
    
    try:
        torrents = manager.client.get_torrents()
        result = []
        
        for torrent in torrents:
            # Check if this is one of our managed distros
            distro = None
            for distro_name, patterns in {
                'centos': ['centos', 'CentOS'],
                'debian': ['debian'],
                'ubuntu': ['ubuntu'],
                'arch': ['arch', 'archlinux'],
                'raspberrypi': ['raspios', 'raspberry', 'raspberrypi'],
            }.items():
                if any(pattern.lower() in torrent.name.lower() for pattern in patterns):
                    distro = distro_name
                    break
            
            if distro:
                result.append({
                    'id': torrent.id,
                    'name': torrent.name,
                    'distro': distro,
                    'status': torrent.status,
                    'progress': torrent.progress,
                    'download_rate': torrent.rate_download,
                    'upload_rate': torrent.rate_upload,
                    'size': torrent.total_size,
                    'eta': torrent.eta.seconds if torrent.eta else None,
                    'peers_connected': torrent.peers_connected,
                    'seeders': getattr(torrent, 'peers_sending_to_us', 0),
                })
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting torrent status: {e}")
        return []


def check_for_updates(distros: List[str]) -> Dict[str, Dict]:
    """Check for updates for specified distributions."""
    global last_check_time, last_check_results, check_in_progress
    
    if not manager:
        return {'error': 'Manager not initialized'}
    
    with check_lock:
        if check_in_progress:
            return {'error': 'Check already in progress'}
        check_in_progress = True
    
    try:
        results = {}
        
        for distro in distros:
            try:
                logger.info(f"Checking {distro}...")
                
                # Get the finder for this distro
                finder = manager.distro_finders.get(distro)
                if not finder:
                    results[distro] = {
                        'success': False,
                        'error': f'Unknown distribution: {distro}'
                    }
                    continue
                
                # Find the latest torrent
                torrent_url = finder.get_latest_torrent_url()
                
                if torrent_url:
                    results[distro] = {
                        'success': True,
                        'url': torrent_url,
                        'checked_at': datetime.now().isoformat()
                    }
                else:
                    results[distro] = {
                        'success': False,
                        'error': 'No torrent found'
                    }
                    
            except Exception as e:
                logger.error(f"Error checking {distro}: {e}")
                results[distro] = {
                    'success': False,
                    'error': str(e)
                }
        
        last_check_time = datetime.now()
        last_check_results = results
        
        return results
        
    finally:
        with check_lock:
            check_in_progress = False


def update_distro(distro: str) -> Dict:
    """Update a specific distribution."""
    if not manager:
        return {'success': False, 'error': 'Manager not initialized'}
    
    try:
        manager.update_torrent(distro)
        return {
            'success': True,
            'message': f'Successfully processed {distro} torrent'
        }
    except Exception as e:
        logger.error(f"Error updating {distro}: {e}")
        return {
            'success': False,
            'error': str(e)
        }


@app.route('/')
def index():
    """Main page."""
    return render_template('index.html')


@app.route('/api/status')
def api_status():
    """Get current status of all torrents."""
    torrents = get_torrent_status()
    
    return jsonify({
        'torrents': torrents,
        'last_check': last_check_time.isoformat() if last_check_time else None,
        'check_in_progress': check_in_progress,
        'available_distros': list(manager.distro_finders.keys()) if manager else []
    })


@app.route('/api/check', methods=['POST'])
def api_check():
    """Check for updates for specified distributions."""
    data = request.json
    distros = data.get('distros', list(manager.distro_finders.keys()) if manager else [])
    
    # Run check in background thread
    def run_check():
        check_for_updates(distros)
    
    thread = threading.Thread(target=run_check)
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'success': True,
        'message': 'Check started'
    })


@app.route('/api/check/status')
def api_check_status():
    """Get status of the last check."""
    return jsonify({
        'in_progress': check_in_progress,
        'last_check': last_check_time.isoformat() if last_check_time else None,
        'results': last_check_results
    })


@app.route('/api/update', methods=['POST'])
def api_update():
    """Update specified distributions."""
    data = request.json
    distros = data.get('distros', [])
    
    if not distros:
        return jsonify({
            'success': False,
            'error': 'No distributions specified'
        }), 400
    
    # Run updates in background thread
    def run_updates():
        for distro in distros:
            update_distro(distro)
    
    thread = threading.Thread(target=run_updates)
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'success': True,
        'message': f'Update started for {len(distros)} distribution(s)'
    })


@app.route('/api/config')
def api_config():
    """Get current configuration."""
    return jsonify({
        'available_distros': list(manager.distro_finders.keys()) if manager else [],
        'transmission_connected': manager is not None and manager.client is not None
    })


def main():
    """Main entry point for web interface."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Linux ISO Torrent Updater - Web Interface')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=8084, help='Port to bind to (default: 8084)')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--log-file', '-l', help='Path to log file (default: console only)')
    
    args = parser.parse_args()
    
    # Setup logging
    global logger
    logger = setup_logging(args.log_file)
    
    # Load environment files
    load_dotenv_files()
    
    # Initialize manager
    logger.info("Initializing torrent manager...")
    if not initialize_manager():
        logger.error("Failed to initialize torrent manager. Please check your configuration.")
        sys.exit(1)
    
    logger.info(f"Starting web interface on {args.host}:{args.port}")
    logger.info(f"Open http://localhost:{args.port} in your browser")
    
    # Run Flask app
    app.run(host=args.host, port=args.port, debug=args.debug, threaded=True)


if __name__ == '__main__':
    main()
