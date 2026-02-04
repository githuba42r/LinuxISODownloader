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
from datetime import datetime, time as datetime_time
from pathlib import Path
from typing import Dict, List, Optional

from flask import Flask, render_template, jsonify, request
import transmission_rpc
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

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
scheduler: Optional[BackgroundScheduler] = None
scheduled_distros: List[str] = []

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
                    'percentDone': torrent.progress,
                    'rateDownload': torrent.rate_download,
                    'rateUpload': torrent.rate_upload,
                    'totalSize': torrent.total_size,
                    'downloadedEver': torrent.downloaded_ever,
                    'uploadRatio': torrent.upload_ratio,
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
                        'error': f'Unknown distribution: {distro}',
                        'status': 'error'
                    }
                    continue
                
                # Find the latest torrent
                torrent_url = finder.get_latest_torrent_url()
                
                if not torrent_url:
                    results[distro] = {
                        'success': False,
                        'error': 'No torrent found',
                        'status': 'error'
                    }
                    continue
                
                # Check if we already have this torrent in Transmission
                existing_torrent = manager.find_existing_torrent(distro)
                
                if existing_torrent:
                    # We have a torrent for this distro - download new torrent and compare
                    try:
                        import requests
                        import transmission_rpc
                        response = requests.get(torrent_url, timeout=30)
                        if response.status_code != 200:
                            results[distro] = {
                                'success': False,
                                'error': f'Failed to download torrent from {torrent_url}',
                                'status': 'error'
                            }
                            continue
                        
                        new_torrent_data = response.content
                        
                        # Try to add the torrent - Transmission will detect if it's a duplicate
                        try:
                            new_torrent = manager.client.add_torrent(new_torrent_data)
                            
                            # Check if it's the same torrent or a different one
                            if new_torrent.id != existing_torrent.id:
                                # Different torrent - update is available!
                                # Remove the newly added one (we only wanted to check)
                                manager.client.remove_torrent(new_torrent.id, delete_data=True)
                                
                                results[distro] = {
                                    'success': True,
                                    'url': torrent_url,
                                    'existing_torrent': existing_torrent.name,
                                    'new_torrent': new_torrent.name,
                                    'status': 'update_available',
                                    'message': f'Update available! Current: {existing_torrent.name}',
                                    'checked_at': datetime.now().isoformat()
                                }
                            else:
                                # Same torrent ID - already up to date
                                results[distro] = {
                                    'success': True,
                                    'url': torrent_url,
                                    'existing_torrent': existing_torrent.name,
                                    'status': 'up_to_date',
                                    'message': f'Already up to date: {existing_torrent.name}',
                                    'checked_at': datetime.now().isoformat()
                                }
                        
                        except transmission_rpc.error.TransmissionError as e:
                            if "duplicate" in str(e).lower():
                                # Duplicate error means same torrent - already up to date
                                results[distro] = {
                                    'success': True,
                                    'url': torrent_url,
                                    'existing_torrent': existing_torrent.name,
                                    'status': 'up_to_date',
                                    'message': f'Already up to date: {existing_torrent.name}',
                                    'checked_at': datetime.now().isoformat()
                                }
                            else:
                                raise
                    
                    except Exception as e:
                        logger.error(f"Error comparing torrents for {distro}: {e}")
                        results[distro] = {
                            'success': False,
                            'error': str(e),
                            'existing_torrent': existing_torrent.name,
                            'status': 'error'
                        }
                else:
                    # No existing torrent - this is a new one
                    results[distro] = {
                        'success': True,
                        'url': torrent_url,
                        'status': 'new',
                        'message': 'New torrent available (not currently in Transmission)',
                        'checked_at': datetime.now().isoformat()
                    }
                    
            except Exception as e:
                logger.error(f"Error checking {distro}: {e}")
                results[distro] = {
                    'success': False,
                    'error': str(e),
                    'status': 'error'
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


def scheduled_check():
    """Perform scheduled torrent update check."""
    global scheduled_distros
    
    logger.info(f"Running scheduled torrent check for: {', '.join(scheduled_distros)}")
    
    if not scheduled_distros:
        logger.warning("No distributions configured for scheduled checks")
        return
    
    try:
        # Run the actual update (not just check)
        for distro in scheduled_distros:
            try:
                logger.info(f"Scheduled update for {distro}...")
                manager.update_torrent(distro)
            except Exception as e:
                logger.error(f"Scheduled update failed for {distro}: {e}")
        
        logger.info("Scheduled torrent check completed")
    except Exception as e:
        logger.error(f"Error in scheduled check: {e}")


def setup_scheduler(schedule_time: str, distros: List[str]) -> bool:
    """
    Set up the background scheduler for automatic torrent checks.
    
    Args:
        schedule_time: Time in HH:MM format (24-hour) or 'disabled'
        distros: List of distributions to check
    
    Returns:
        True if scheduler was set up successfully
    """
    global scheduler, scheduled_distros
    
    # Disable scheduler if requested
    if schedule_time.lower() == 'disabled' or not schedule_time:
        logger.info("Automatic scheduling disabled")
        return True
    
    # Parse the time
    try:
        hour, minute = map(int, schedule_time.split(':'))
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError("Invalid time range")
    except (ValueError, AttributeError) as e:
        logger.error(f"Invalid schedule time format '{schedule_time}'. Use HH:MM (24-hour) or 'disabled'. Error: {e}")
        return False
    
    scheduled_distros = distros if distros else ['debian', 'ubuntu', 'arch', 'raspberrypi']
    
    # Create scheduler
    scheduler = BackgroundScheduler()
    
    # Add job to run daily at specified time
    scheduler.add_job(
        scheduled_check,
        trigger=CronTrigger(hour=hour, minute=minute),
        id='torrent_check',
        name=f'Daily torrent check at {schedule_time}',
        replace_existing=True
    )
    
    scheduler.start()
    logger.info(f"Scheduled automatic torrent checks daily at {schedule_time} for: {', '.join(scheduled_distros)}")
    
    return True


@app.route('/')
def index():
    """Main page."""
    return render_template('index.html')


@app.route('/api/status')
def api_status():
    """Get current status of all torrents and manager state."""
    torrents = get_torrent_status()
    
    # Determine manager status based on current state
    if check_in_progress:
        status = 'checking'
        status_text = 'Checking for updates...'
    elif not manager:
        status = 'error'
        status_text = 'Manager not initialized'
    else:
        # Check if any torrents are actively downloading
        downloading = any(t.get('percentDone', 1) < 1.0 for t in torrents)
        
        if downloading:
            status = 'downloading'
            status_text = 'Downloading torrents'
        else:
            # All torrents complete or seeding
            status = 'idle'
            status_text = 'All torrents up to date'
    
    # Get next scheduled check time
    next_check = None
    schedule_info = 'Disabled'
    
    if scheduler and scheduler.running:
        jobs = scheduler.get_jobs()
        if jobs:
            job = jobs[0]  # Get the torrent_check job
            next_run = job.next_run_time
            if next_run:
                next_check = next_run.isoformat()
                # Calculate time until next run
                from datetime import datetime
                now = datetime.now(next_run.tzinfo) if next_run.tzinfo else datetime.now()
                
                time_until = next_run - now
                total_seconds = time_until.total_seconds()
                
                if total_seconds < 0:
                    schedule_info = 'Running now...'
                elif total_seconds < 60:
                    schedule_info = 'Next check in <1m'
                else:
                    hours = int(total_seconds // 3600)
                    minutes = int((total_seconds % 3600) // 60)
                    
                    if hours >= 24:
                        days = hours // 24
                        remaining_hours = hours % 24
                        if remaining_hours > 0:
                            schedule_info = f'Next check in {days}d {remaining_hours}h'
                        else:
                            schedule_info = f'Next check in {days}d'
                    elif hours > 0:
                        schedule_info = f'Next check in {hours}h {minutes}m'
                    else:
                        schedule_info = f'Next check in {minutes}m'
    
    return jsonify({
        'status': status,
        'status_text': status_text,
        'schedule_info': schedule_info,
        'torrents': torrents,
        'last_check': last_check_time.isoformat() if last_check_time else None,
        'next_check': next_check,
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
    # Determine status string for frontend
    if check_in_progress:
        status = 'in_progress'
    elif last_check_results:
        status = 'completed'
    else:
        status = 'idle'
    
    # Transform results from dict to array format expected by frontend
    results_array = []
    if last_check_results:
        for distro, result in last_check_results.items():
            message = ''
            result_status = result.get('status', 'unknown')
            
            if result_status == 'error':
                message = f"Error: {result.get('error', 'Unknown error')}"
            elif result_status == 'new':
                message = f"New torrent available (not in Transmission yet)"
            elif result_status == 'up_to_date':
                existing = result.get('existing_torrent', 'unknown')
                message = f"Already up to date: {existing}"
            elif result_status == 'update_available':
                existing = result.get('existing_torrent', 'unknown')
                message = f"Update available! Current: {existing}"
            elif result.get('success'):
                message = f"Found torrent: {result.get('url', 'N/A')}"
            else:
                message = f"Error: {result.get('error', 'Unknown error')}"
            
            results_array.append({
                'distro': distro,
                'message': message,
                'success': result.get('success', False),
                'status': result_status,
                'url': result.get('url'),
                'existing_torrent': result.get('existing_torrent')
            })
    
    return jsonify({
        'status': status,
        'in_progress': check_in_progress,
        'last_check': last_check_time.isoformat() if last_check_time else None,
        'results': results_array
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


@app.route('/api/distros')
def api_distros():
    """Get list of available distributions."""
    distros = ['centos', 'debian', 'ubuntu', 'arch', 'raspberrypi']
    return jsonify({
        'distros': distros
    })


def main():
    """Main entry point for web interface."""
    import argparse
    import atexit
    
    parser = argparse.ArgumentParser(description='Linux ISO Torrent Updater - Web Interface')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=8084, help='Port to bind to (default: 8084)')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--log-file', '-l', help='Path to log file (default: console only)')
    parser.add_argument('--schedule-time', default=None, 
                        help='Time to run automatic checks in HH:MM format (24-hour), e.g., "02:00" for 2am. Use "disabled" to disable scheduling. (default: from env or 02:00)')
    parser.add_argument('--schedule-distros', default=None,
                        help='Comma-separated list of distributions for scheduled checks (default: from env or all)')
    
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
    
    # Configure scheduler
    schedule_time = args.schedule_time or os.environ.get('SCHEDULE_TIME', '02:00')
    schedule_distros_str = args.schedule_distros or os.environ.get('SCHEDULE_DISTROS', 'debian,ubuntu,arch,raspberrypi')
    
    if schedule_distros_str and schedule_distros_str.lower() != 'disabled':
        schedule_distros = [d.strip() for d in schedule_distros_str.split(',')]
    else:
        schedule_distros = []
    
    # Setup scheduler if enabled
    if schedule_time.lower() != 'disabled':
        if not setup_scheduler(schedule_time, schedule_distros):
            logger.warning("Failed to setup scheduler, continuing without automatic checks")
    else:
        logger.info("Automatic scheduling disabled")
    
    # Register cleanup on exit
    def cleanup():
        global scheduler
        if scheduler:
            logger.info("Shutting down scheduler...")
            scheduler.shutdown()
    
    atexit.register(cleanup)
    
    logger.info(f"Starting web interface on {args.host}:{args.port}")
    logger.info(f"Open http://localhost:{args.port} in your browser")
    
    # Run Flask app
    try:
        app.run(host=args.host, port=args.port, debug=args.debug, threaded=True)
    finally:
        cleanup()


if __name__ == '__main__':
    main()
