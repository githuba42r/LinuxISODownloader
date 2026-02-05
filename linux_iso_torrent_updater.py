#!/usr/bin/env python3
"""
Linux ISO Torrent Updater for Transmission
Manages torrents for the latest CentOS, Debian, Ubuntu, and Arch Linux ISO images.
"""

import json
import logging
import os
import sys
import time
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
import transmission_rpc
from dotenv import load_dotenv

# Import version
try:
    from __version__ import __version__
except ImportError:
    __version__ = "unknown"

# Logger will be configured in main() after parsing command-line arguments
logger = None

def setup_logging(log_file: Optional[str] = None):
    """
    Setup logging with console output and optional file logging.
    
    Args:
        log_file: Optional path to log file. If None, only logs to console.
    """
    handlers = [logging.StreamHandler(sys.stdout)]
    
    if log_file:
        try:
            # Expand user path and create parent directory if needed
            log_path = Path(log_file).expanduser()
            log_path.parent.mkdir(parents=True, exist_ok=True)
            handlers.append(logging.FileHandler(log_path))
            print(f"Logging to file: {log_path}", file=sys.stderr)
        except (PermissionError, OSError) as e:
            print(f"Warning: Could not write to log file {log_file}: {e}", file=sys.stderr)
            print("Continuing with console-only logging", file=sys.stderr)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=handlers,
        force=True  # Allow reconfiguration
    )
    
    return logging.getLogger(__name__)


class DistroTorrentFinder:
    """Base class for finding distribution torrent URLs."""
    
    def __init__(self, name: str):
        self.name = name
        
    def get_latest_torrent_url(self) -> Optional[str]:
        """Get the URL of the latest torrent file."""
        raise NotImplementedError


class CentOSTorrentFinder(DistroTorrentFinder):
    """Find latest CentOS Stream torrent from LinuxTracker.org."""
    
    def __init__(self):
        super().__init__("CentOS")
        # CentOS no longer provides official torrents, use LinuxTracker as source
        self.base_url = "https://linuxtracker.org/index.php?page=torrents&search=centos+stream+9&order=3&by=2"
        
    def get_latest_torrent_url(self) -> Optional[str]:
        try:
            # Note: CentOS official mirrors no longer provide .torrent files
            # We use LinuxTracker.org as a community source for CentOS torrents
            
            response = requests.get(self.base_url, timeout=30)
            if response.status_code != 200:
                logger.warning("Could not access LinuxTracker for CentOS torrents")
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for CentOS Stream 9 x86_64 DVD torrent (most recent)
            # Find all torrent detail links
            for link in soup.find_all('a', href=True):
                href = str(link['href'])
                title = str(link.get('title', ''))
                
                # Look for x86_64 DVD1 torrents for Stream 9
                if ('CentOS-Stream-9' in title and 
                    'x86_64-dvd1.iso' in title and
                    'torrent-details' in href):
                    
                    # Extract the torrent ID from the details link
                    if 'id=' in href:
                        torrent_id = href.split('id=')[1].split('&')[0]
                        # Construct download URL (use download.php, not downloadcheck)
                        torrent_url = f"https://linuxtracker.org/download.php?id={torrent_id}"
                        logger.info(f"Found CentOS torrent on LinuxTracker: {title}")
                        return torrent_url
                        
        except Exception as e:
            logger.error(f"Error finding CentOS torrent: {e}")
        
        return None


class DebianTorrentFinder(DistroTorrentFinder):
    """Find latest Debian torrent."""
    
    def __init__(self):
        super().__init__("Debian")
        self.base_url = "https://cdimage.debian.org/debian-cd/current/amd64/bt-dvd/"
        
    def get_latest_torrent_url(self) -> Optional[str]:
        try:
            response = requests.get(self.base_url, timeout=30)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find the first DVD torrent (debian-XX.X.X-amd64-DVD-1.iso.torrent)
            for link in soup.find_all('a', href=True):
                href = str(link['href'])
                if href.endswith('.torrent') and 'DVD-1' in href and 'amd64' in href:
                    torrent_url = urljoin(self.base_url, href)
                    logger.info(f"Found Debian torrent: {torrent_url}")
                    return torrent_url
                    
        except Exception as e:
            logger.error(f"Error finding Debian torrent: {e}")
        
        return None


class UbuntuTorrentFinder(DistroTorrentFinder):
    """Find latest Ubuntu LTS torrent."""
    
    def __init__(self):
        super().__init__("Ubuntu")
        self.base_url = "https://releases.ubuntu.com/"
        
    def get_latest_torrent_url(self) -> Optional[str]:
        try:
            # Try to find the latest LTS version
            response = requests.get(self.base_url, timeout=30)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for LTS releases (e.g., 24.04, 22.04)
            lts_versions = []
            for link in soup.find_all('a', href=True):
                href = str(link['href'])
                if href.endswith('/') and any(char.isdigit() for char in href):
                    # Extract version number
                    version = href.strip('/')
                    if '.' in version:
                        lts_versions.append(version)
            
            # Sort to get latest (assuming higher version numbers are newer)
            lts_versions = sorted(lts_versions, reverse=True)
            
            for version in lts_versions:
                try:
                    version_url = urljoin(self.base_url, f"{version}/")
                    response = requests.get(version_url, timeout=30)
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Find desktop torrent
                    for link in soup.find_all('a', href=True):
                        href = str(link['href'])
                        if href.endswith('.torrent') and 'desktop-amd64' in href:
                            torrent_url = urljoin(version_url, href)
                            logger.info(f"Found Ubuntu torrent: {torrent_url}")
                            return torrent_url
                except Exception:
                    continue
                    
        except Exception as e:
            logger.error(f"Error finding Ubuntu torrent: {e}")
        
        return None


class ArchTorrentFinder(DistroTorrentFinder):
    """Find latest Arch Linux torrent."""
    
    def __init__(self):
        super().__init__("Arch")
        self.base_url = "https://archlinux.org/releng/releases/"
        
    def get_latest_torrent_url(self) -> Optional[str]:
        try:
            response = requests.get(self.base_url, timeout=30)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find the latest release torrent link
            for link in soup.find_all('a', href=True):
                href = str(link['href'])
                if 'torrent' in href.lower() and 'magnet' not in href.lower():
                    # Construct full URL if relative
                    if not href.startswith('http'):
                        torrent_url = urljoin(self.base_url, href)
                    else:
                        torrent_url = href
                    logger.info(f"Found Arch torrent: {torrent_url}")
                    return torrent_url
            
            # Fallback: Try direct magnet2torrent approach or archlinux.org/download page
            download_page = "https://archlinux.org/download/"
            response = requests.get(download_page, timeout=30)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            for link in soup.find_all('a', href=True):
                href = str(link['href'])
                if href.endswith('.torrent'):
                    torrent_url = href if href.startswith('http') else urljoin(download_page, href)
                    logger.info(f"Found Arch torrent: {torrent_url}")
                    return torrent_url
                    
        except Exception as e:
            logger.error(f"Error finding Arch torrent: {e}")
        
        return None


class RaspberryPiOSTorrentFinder(DistroTorrentFinder):
    """Find latest Raspberry Pi OS torrent."""
    
    def __init__(self):
        super().__init__("Raspberry Pi OS")
        self.base_url = "https://downloads.raspberrypi.com/raspios_arm64/images/"
        
    def get_latest_torrent_url(self) -> Optional[str]:
        try:
            # Get the list of available versions
            response = requests.get(self.base_url, timeout=30)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find all version directories (format: raspios_arm64-YYYY-MM-DD)
            versions = []
            for link in soup.find_all('a', href=True):
                href = str(link['href'])
                if href.startswith('raspios_arm64-') and href.endswith('/'):
                    versions.append(href.strip('/'))
            
            if not versions:
                logger.warning("No Raspberry Pi OS versions found")
                return None
            
            # Sort versions to get the latest (they're in YYYY-MM-DD format)
            latest_version = sorted(versions)[-1]
            version_url = urljoin(self.base_url, f"{latest_version}/")
            
            # Get the torrent from the version directory
            response = requests.get(version_url, timeout=30)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for the standard arm64 torrent (not lite, not full)
            for link in soup.find_all('a', href=True):
                href = str(link['href'])
                if (href.endswith('.torrent') and 
                    'arm64' in href and 
                    'lite' not in href and 
                    'full' not in href):
                    torrent_url = urljoin(version_url, href)
                    logger.info(f"Found Raspberry Pi OS torrent: {torrent_url}")
                    return torrent_url
                    
        except Exception as e:
            logger.error(f"Error finding Raspberry Pi OS torrent: {e}")
        
        return None


class LinuxMintTorrentFinder(DistroTorrentFinder):
    """Find latest Linux Mint torrent from LinuxTracker.org."""
    
    def __init__(self):
        super().__init__("Linux Mint")
        self.base_url = "https://linuxtracker.org/index.php?page=torrents&search=mint+cinnamon&order=3&by=2"
        
    def get_latest_torrent_url(self) -> Optional[str]:
        try:
            response = requests.get(self.base_url, timeout=30)
            if response.status_code != 200:
                logger.warning("Could not access LinuxTracker for Linux Mint torrents")
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for Linux Mint Cinnamon x86_64 torrent (most popular edition)
            for link in soup.find_all('a', href=True):
                href = str(link['href'])
                title = str(link.get('title', ''))
                
                # Look for Cinnamon edition (flagship), excluding beta releases
                if ('linuxmint' in title.lower() and 
                    'cinnamon' in title.lower() and
                    ('64bit' in title.lower() or '64-bit' in title.lower()) and
                    'beta' not in title.lower() and
                    'torrent-details' in href):
                    
                    if 'id=' in href:
                        torrent_id = href.split('id=')[1].split('&')[0]
                        torrent_url = f"https://linuxtracker.org/download.php?id={torrent_id}"
                        logger.info(f"Found Linux Mint torrent: {torrent_url}")
                        return torrent_url
                        
        except Exception as e:
            logger.error(f"Error finding Linux Mint torrent: {e}")
        
        return None


class FedoraTorrentFinder(DistroTorrentFinder):
    """Find latest Fedora Workstation torrent."""
    
    def __init__(self):
        super().__init__("Fedora")
        self.base_url = "https://torrent.fedoraproject.org/"
        
    def get_latest_torrent_url(self) -> Optional[str]:
        try:
            response = requests.get(self.base_url, timeout=30)
            if response.status_code != 200:
                logger.warning("Could not access Fedora torrent server")
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find the latest Fedora Workstation Live x86_64 torrent
            # Look for links with 'Workstation' and 'x86_64' in the filename
            latest_version = None
            latest_url = None
            
            for link in soup.find_all('a', href=True):
                href = str(link['href'])
                
                if ('Fedora-Workstation-Live-x86_64' in href and 
                    href.endswith('.torrent')):
                    
                    # Extract version number (e.g., Fedora-Workstation-Live-x86_64-43.torrent)
                    try:
                        version = int(href.split('-')[-1].replace('.torrent', ''))
                        if latest_version is None or version > latest_version:
                            latest_version = version
                            latest_url = urljoin(self.base_url, href)
                    except ValueError:
                        continue
            
            if latest_url:
                logger.info(f"Found Fedora Workstation torrent: {latest_url}")
                return latest_url
                        
        except Exception as e:
            logger.error(f"Error finding Fedora torrent: {e}")
        
        return None


class PopOSTorrentFinder(DistroTorrentFinder):
    """Find latest Pop!_OS torrent from LinuxTracker.org."""
    
    def __init__(self):
        super().__init__("Pop!_OS")
        self.base_url = "https://linuxtracker.org/index.php?page=torrents&search=pop+os&order=3&by=2"
        
    def get_latest_torrent_url(self) -> Optional[str]:
        try:
            response = requests.get(self.base_url, timeout=30)
            if response.status_code != 200:
                logger.warning("Could not access LinuxTracker for Pop!_OS torrents")
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for Pop!_OS AMD64/Intel torrent
            for link in soup.find_all('a', href=True):
                href = str(link['href'])
                title = str(link.get('title', ''))
                
                if ('pop' in title.lower() and 
                    ('amd64' in title.lower() or 'intel' in title.lower()) and
                    'torrent-details' in href):
                    
                    if 'id=' in href:
                        torrent_id = href.split('id=')[1].split('&')[0]
                        torrent_url = f"https://linuxtracker.org/download.php?id={torrent_id}"
                        logger.info(f"Found Pop!_OS torrent: {torrent_url}")
                        return torrent_url
                        
        except Exception as e:
            logger.error(f"Error finding Pop!_OS torrent: {e}")
        
        return None


class RockyLinuxTorrentFinder(DistroTorrentFinder):
    """Find latest Rocky Linux torrent from LinuxTracker.org."""
    
    def __init__(self):
        super().__init__("Rocky Linux")
        self.base_url = "https://linuxtracker.org/index.php?page=torrents&search=rocky&order=3&by=2"
        
    def get_latest_torrent_url(self) -> Optional[str]:
        try:
            response = requests.get(self.base_url, timeout=30)
            if response.status_code != 200:
                logger.warning("Could not access LinuxTracker for Rocky Linux torrents")
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for Rocky x86_64 DVD torrent (format: Rocky-10.1-x86_64-dvd1)
            for link in soup.find_all('a', href=True):
                href = str(link['href'])
                title = str(link.get('title', ''))
                
                if ('rocky' in title.lower() and 
                    'x86_64' in title.lower() and
                    'dvd' in title.lower() and
                    'torrent-details' in href):
                    
                    if 'id=' in href:
                        torrent_id = href.split('id=')[1].split('&')[0]
                        torrent_url = f"https://linuxtracker.org/download.php?id={torrent_id}"
                        logger.info(f"Found Rocky Linux torrent: {torrent_url}")
                        return torrent_url
                        
        except Exception as e:
            logger.error(f"Error finding Rocky Linux torrent: {e}")
        
        return None


class AlmaLinuxTorrentFinder(DistroTorrentFinder):
    """Find latest AlmaLinux torrent from LinuxTracker.org."""
    
    def __init__(self):
        super().__init__("AlmaLinux")
        self.base_url = "https://linuxtracker.org/index.php?page=torrents&search=almalinux&order=3&by=2"
        
    def get_latest_torrent_url(self) -> Optional[str]:
        try:
            response = requests.get(self.base_url, timeout=30)
            if response.status_code != 200:
                logger.warning("Could not access LinuxTracker for AlmaLinux torrents")
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for AlmaLinux x86_64 DVD torrent
            for link in soup.find_all('a', href=True):
                href = str(link['href'])
                title = str(link.get('title', ''))
                
                if ('almalinux' in title.lower() and 
                    'x86_64' in title.lower() and
                    ('dvd' in title.lower() or 'dvd1' in title.lower()) and
                    'torrent-details' in href):
                    
                    if 'id=' in href:
                        torrent_id = href.split('id=')[1].split('&')[0]
                        torrent_url = f"https://linuxtracker.org/download.php?id={torrent_id}"
                        logger.info(f"Found AlmaLinux torrent: {torrent_url}")
                        return torrent_url
                        
        except Exception as e:
            logger.error(f"Error finding AlmaLinux torrent: {e}")
        
        return None


class ManjaroTorrentFinder(DistroTorrentFinder):
    """Find latest Manjaro torrent from LinuxTracker.org."""
    
    def __init__(self):
        super().__init__("Manjaro")
        self.base_url = "https://linuxtracker.org/index.php?page=torrents&search=manjaro+kde&order=3&by=2"
        
    def get_latest_torrent_url(self) -> Optional[str]:
        try:
            response = requests.get(self.base_url, timeout=30)
            if response.status_code != 200:
                logger.warning("Could not access LinuxTracker for Manjaro torrents")
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for Manjaro KDE torrent (most popular edition)
            # Note: Manjaro ISOs don't include architecture in the name
            for link in soup.find_all('a', href=True):
                href = str(link['href'])
                title = str(link.get('title', ''))
                
                if ('manjaro' in title.lower() and 
                    'kde' in title.lower() and
                    'minimal' not in title.lower() and
                    'rc' not in title.lower() and
                    'torrent-details' in href):
                    
                    if 'id=' in href:
                        torrent_id = href.split('id=')[1].split('&')[0]
                        torrent_url = f"https://linuxtracker.org/download.php?id={torrent_id}"
                        logger.info(f"Found Manjaro torrent: {torrent_url}")
                        return torrent_url
                        
        except Exception as e:
            logger.error(f"Error finding Manjaro torrent: {e}")
        
        return None


class ElementaryOSTorrentFinder(DistroTorrentFinder):
    """Find latest elementary OS torrent from LinuxTracker.org."""
    
    def __init__(self):
        super().__init__("elementary OS")
        self.base_url = "https://linuxtracker.org/index.php?page=torrents&search=elementary&order=3&by=2"
        
    def get_latest_torrent_url(self) -> Optional[str]:
        try:
            response = requests.get(self.base_url, timeout=30)
            if response.status_code != 200:
                logger.warning("Could not access LinuxTracker for elementary OS torrents")
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for elementary OS torrent
            for link in soup.find_all('a', href=True):
                href = str(link['href'])
                title = str(link.get('title', ''))
                
                if ('elementary' in title.lower() and 
                    'torrent-details' in href and
                    'beta' not in title.lower()):
                    
                    if 'id=' in href:
                        torrent_id = href.split('id=')[1].split('&')[0]
                        torrent_url = f"https://linuxtracker.org/download.php?id={torrent_id}"
                        logger.info(f"Found elementary OS torrent: {torrent_url}")
                        return torrent_url
                        
        except Exception as e:
            logger.error(f"Error finding elementary OS torrent: {e}")
        
        return None


class ZorinOSTorrentFinder(DistroTorrentFinder):
    """Find latest Zorin OS torrent from LinuxTracker.org."""
    
    def __init__(self):
        super().__init__("Zorin OS")
        self.base_url = "https://linuxtracker.org/index.php?page=torrents&search=zorin&order=3&by=2"
        
    def get_latest_torrent_url(self) -> Optional[str]:
        try:
            response = requests.get(self.base_url, timeout=30)
            if response.status_code != 200:
                logger.warning("Could not access LinuxTracker for Zorin OS torrents")
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for Zorin OS Core torrent (free edition)
            for link in soup.find_all('a', href=True):
                href = str(link['href'])
                title = str(link.get('title', ''))
                
                if ('zorin' in title.lower() and 
                    'core' in title.lower() and
                    '64' in title.lower() and
                    'torrent-details' in href):
                    
                    if 'id=' in href:
                        torrent_id = href.split('id=')[1].split('&')[0]
                        torrent_url = f"https://linuxtracker.org/download.php?id={torrent_id}"
                        logger.info(f"Found Zorin OS torrent: {torrent_url}")
                        return torrent_url
                        
        except Exception as e:
            logger.error(f"Error finding Zorin OS torrent: {e}")
        
        return None


class EndeavourOSTorrentFinder(DistroTorrentFinder):
    """Find latest EndeavourOS torrent from LinuxTracker.org."""
    
    def __init__(self):
        super().__init__("EndeavourOS")
        self.base_url = "https://linuxtracker.org/index.php?page=torrents&search=endeavouros&order=3&by=2"
        
    def get_latest_torrent_url(self) -> Optional[str]:
        try:
            response = requests.get(self.base_url, timeout=30)
            if response.status_code != 200:
                logger.warning("Could not access LinuxTracker for EndeavourOS torrents")
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for EndeavourOS torrent
            for link in soup.find_all('a', href=True):
                href = str(link['href'])
                title = str(link.get('title', ''))
                
                if ('endeavour' in title.lower() and 
                    'torrent-details' in href):
                    
                    if 'id=' in href:
                        torrent_id = href.split('id=')[1].split('&')[0]
                        torrent_url = f"https://linuxtracker.org/download.php?id={torrent_id}"
                        logger.info(f"Found EndeavourOS torrent: {torrent_url}")
                        return torrent_url
                        
        except Exception as e:
            logger.error(f"Error finding EndeavourOS torrent: {e}")
        
        return None


class TransmissionTorrentManager:
    """Manage torrents in Transmission."""
    
    def __init__(self, host: str, port: int, username: str, password: str, dry_run: bool = False):
        self.dry_run = dry_run
        if dry_run:
            logger.info("DRY-RUN MODE: No changes will be made to Transmission")
            self.client = None
        else:
            self.client = transmission_rpc.Client(
                host=host,
                port=port,
                username=username,
                password=password
            )
        self.distro_finders = {
            'centos': CentOSTorrentFinder(),
            'debian': DebianTorrentFinder(),
            'ubuntu': UbuntuTorrentFinder(),
            'arch': ArchTorrentFinder(),
            'raspberrypi': RaspberryPiOSTorrentFinder(),
            'linuxmint': LinuxMintTorrentFinder(),
            'fedora': FedoraTorrentFinder(),
            'popos': PopOSTorrentFinder(),
            'rocky': RockyLinuxTorrentFinder(),
            'alma': AlmaLinuxTorrentFinder(),
            'manjaro': ManjaroTorrentFinder(),
            'elementary': ElementaryOSTorrentFinder(),
            'zorin': ZorinOSTorrentFinder(),
            'endeavour': EndeavourOSTorrentFinder(),
        }
        
    def get_torrent_hash(self, torrent_url: str) -> Optional[str]:
        """Download torrent file and compute its hash for identification."""
        try:
            response = requests.get(torrent_url, timeout=30)
            if response.status_code == 200:
                return hashlib.sha256(response.content).hexdigest()
        except Exception as e:
            logger.error(f"Error computing torrent hash for {torrent_url}: {e}")
        return None
    
    def find_existing_torrent(self, distro_name: str) -> Optional[transmission_rpc.Torrent]:
        """Find existing torrent for a distribution by name pattern."""
        if self.dry_run:
            logger.info(f"[DRY-RUN] Would search for existing {distro_name} torrent")
            return None
            
        try:
            torrents = self.client.get_torrents()
            name_patterns = {
                'centos': ['centos', 'CentOS'],
                'debian': ['debian'],
                'ubuntu': ['ubuntu'],
                'arch': ['arch', 'archlinux'],
                'raspberrypi': ['raspios', 'raspberry', 'raspberrypi'],
                'linuxmint': ['linuxmint', 'mint'],
                'fedora': ['fedora'],
                'popos': ['pop-os', 'pop_os', 'popos'],
                'rocky': ['rocky'],
                'alma': ['alma', 'almalinux'],
                'manjaro': ['manjaro'],
                'elementary': ['elementary'],
                'zorin': ['zorin'],
                'endeavour': ['endeavour', 'endeavouros'],
            }
            
            patterns = name_patterns.get(distro_name.lower(), [distro_name])
            
            for torrent in torrents:
                torrent_name_lower = torrent.name.lower()
                if any(pattern.lower() in torrent_name_lower for pattern in patterns):
                    logger.info(f"Found existing {distro_name} torrent: {torrent.name} (ID: {torrent.id})")
                    return torrent
                    
        except Exception as e:
            logger.error(f"Error finding existing torrent for {distro_name}: {e}")
        
        return None
    
    def update_torrent(self, distro_name: str):
        """Update torrent for a specific distribution."""
        logger.info(f"Checking {distro_name} torrent...")
        
        # Get the latest torrent URL
        finder = self.distro_finders.get(distro_name.lower())
        if not finder:
            logger.error(f"No finder configured for {distro_name}")
            return
        
        latest_url = finder.get_latest_torrent_url()
        if not latest_url:
            logger.warning(f"Could not find latest torrent for {distro_name}")
            return
        
        if self.dry_run:
            logger.info(f"[DRY-RUN] Found latest {distro_name} torrent URL: {latest_url}")
        
        # Check if we already have this torrent
        existing_torrent = self.find_existing_torrent(distro_name)
        
        # Download the new torrent file to check if it's different
        try:
            response = requests.get(latest_url, timeout=30)
            if response.status_code != 200:
                logger.error(f"Failed to download torrent from {latest_url}")
                return
            
            new_torrent_data = response.content
            new_hash = hashlib.sha256(new_torrent_data).hexdigest()
            
            if self.dry_run:
                logger.info(f"[DRY-RUN] Downloaded torrent (hash: {new_hash[:16]}...)")
            
            # If we have an existing torrent, check if it's the same
            if existing_torrent:
                if self.dry_run:
                    logger.info(f"[DRY-RUN] Existing {distro_name} torrent found: {existing_torrent.name}")
                    logger.info(f"[DRY-RUN] Would check if new torrent is different")
                    logger.info(f"[DRY-RUN] Actions that would be taken:")
                    logger.info(f"[DRY-RUN]   1. Add new torrent from {latest_url}")
                    logger.info(f"[DRY-RUN]   2. If different, remove old torrent: {existing_torrent.name} (ID: {existing_torrent.id})")
                    logger.info(f"[DRY-RUN]   3. Delete old torrent data")
                    return
                
                # We can't directly compare hashes, so we'll compare by checking
                # if adding the "new" torrent would be a duplicate
                logger.info(f"Existing {distro_name} torrent found, checking if update is needed...")
                
                # Add the new torrent (Transmission will detect duplicates)
                try:
                    new_torrent = self.client.add_torrent(new_torrent_data)
                    
                    # If we get here and it's a different torrent ID, remove the old one
                    if new_torrent.id != existing_torrent.id:
                        logger.info(f"New version detected for {distro_name}, removing old torrent...")
                        self.client.remove_torrent(existing_torrent.id, delete_data=True)
                        logger.info(f"Successfully updated {distro_name} torrent")
                    else:
                        logger.info(f"{distro_name} torrent is already up to date")
                        
                except transmission_rpc.error.TransmissionError as e:
                    if "duplicate" in str(e).lower():
                        logger.info(f"{distro_name} torrent is already up to date")
                    else:
                        raise
            else:
                # No existing torrent, just add it
                if self.dry_run:
                    logger.info(f"[DRY-RUN] No existing {distro_name} torrent found")
                    logger.info(f"[DRY-RUN] Would add new torrent from {latest_url}")
                    logger.info(f"[DRY-RUN] Torrent hash: {new_hash[:16]}...")
                    return
                
                logger.info(f"Adding new {distro_name} torrent...")
                self.client.add_torrent(new_torrent_data)
                logger.info(f"Successfully added {distro_name} torrent")
                
        except Exception as e:
            logger.error(f"Error updating {distro_name} torrent: {e}")
    
    def update_all_torrents(self):
        """Update all distribution torrents."""
        logger.info("Starting torrent update check...")
        
        for distro_name in self.distro_finders.keys():
            try:
                self.update_torrent(distro_name)
                time.sleep(2)  # Be nice to the servers
            except Exception as e:
                logger.error(f"Failed to update {distro_name}: {e}")
                continue
        
        logger.info("Torrent update check completed")


def load_dotenv_files():
    """
    Load environment variables from .env files in priority order.
    
    Priority (highest to lowest):
    1. .env.local (local overrides, never commit)
    2. .env.development (development settings)
    3. .env (default/production settings)
    
    Each file overrides the previous one.
    """
    # Determine the base directory (where the script is located)
    script_dir = Path(__file__).parent.resolve()
    
    # List of env files to load in order (lowest to highest priority)
    env_files = [
        script_dir / '.env',
        script_dir / '.env.development',
        script_dir / '.env.local',
    ]
    
    loaded_files = []
    for env_file in env_files:
        if env_file.exists():
            load_dotenv(env_file, override=True)
            loaded_files.append(str(env_file))
            if logger:
                logger.debug(f"Loaded environment from: {env_file}")
    
    if loaded_files and logger:
        logger.info(f"Loaded {len(loaded_files)} .env file(s): {', '.join([Path(f).name for f in loaded_files])}")
    
    return loaded_files


def load_config() -> Dict:
    """Load configuration from file or environment variables."""
    # First, load .env files (if they exist)
    load_dotenv_files()
    
    config_file = os.path.expanduser('~/.config/linux-iso-updater/config.json')
    
    # Try to load from config file
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                logger.info(f"Loading config from: {config_file}")
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load config file: {e}")
    
    # Fall back to environment variables (including those from .env files)
    logger.info("Loading config from environment variables")
    
    # Parse distros from environment variable
    distros_env = os.getenv('DISTROS', '')
    distros = []
    if distros_env:
        # Support comma-separated list: "debian,ubuntu" or "debian, ubuntu"
        distros = [d.strip() for d in distros_env.split(',') if d.strip()]
    
    config = {
        'host': os.getenv('TRANSMISSION_HOST', 'localhost'),
        'port': int(os.getenv('TRANSMISSION_PORT', '9091')),
        'username': os.getenv('TRANSMISSION_USER', ''),
        'password': os.getenv('TRANSMISSION_PASS', ''),
    }
    
    if distros:
        config['distros'] = distros
    
    return config


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Linux ISO Torrent Updater for Transmission',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Normal run - update all configured torrents
  %(prog)s
  
  # Dry-run - show what would be done
  %(prog)s --dry-run
  
  # Update specific distribution only (overrides config)
  %(prog)s --distro debian
  
  # Update multiple distributions (overrides config)
  %(prog)s --distros debian,ubuntu
  
  # Dry-run for specific distribution
  %(prog)s --dry-run --distro ubuntu
  
  # Log to file
  %(prog)s --log-file /var/log/linux-iso-updater.log

Environment Variables:
  DISTROS - Comma-separated list of distributions to update
            (e.g., "debian,ubuntu,arch,raspberrypi")
  LOG_FILE - Path to log file (default: console only)
  TRANSMISSION_HOST - Transmission server hostname
  TRANSMISSION_PORT - Transmission RPC port
  TRANSMISSION_USER - Transmission username
  TRANSMISSION_PASS - Transmission password
        """
    )
    parser.add_argument(
        '--version', '-v',
        action='version',
        version=f'%(prog)s {__version__}',
        help='Show version number and exit'
    )
    parser.add_argument(
        '--dry-run', '-n',
        action='store_true',
        help='Show what would be done without making any changes'
    )
    parser.add_argument(
        '--distro', '-d',
        choices=['centos', 'debian', 'ubuntu', 'arch', 'raspberrypi'],
        help='Update specific distribution only (overrides config/env)'
    )
    parser.add_argument(
        '--distros',
        help='Comma-separated list of distributions (overrides config/env). Example: debian,ubuntu,arch,raspberrypi'
    )
    parser.add_argument(
        '--log-file', '-l',
        help='Path to log file (default: console only). Can also be set via LOG_FILE environment variable.'
    )
    
    args = parser.parse_args()
    
    # Setup logging after parsing arguments
    log_file = args.log_file or os.getenv('LOG_FILE')
    global logger
    logger = setup_logging(log_file)
    
    try:
        config = load_config()
        
        if not config.get('username') or not config.get('password'):
            if args.dry_run:
                logger.warning("Transmission credentials not configured (OK for dry-run)")
                config['username'] = 'dummy_user'
                config['password'] = 'dummy_pass'
            else:
                logger.error("Transmission credentials not configured!")
                logger.error("Set TRANSMISSION_USER and TRANSMISSION_PASS environment variables")
                logger.error(f"or create config file at ~/.config/linux-iso-updater/config.json")
                sys.exit(1)
        
        manager = TransmissionTorrentManager(
            host=config['host'],
            port=config['port'],
            username=config['username'],
            password=config['password'],
            dry_run=args.dry_run
        )
        
        # Determine which distributions to update
        # Priority: command-line args > config file/env variable > all distributions
        distros_to_update = []
        
        if args.distro:
            # Single distro from command line (highest priority)
            distros_to_update = [args.distro]
            logger.info(f"Command-line override: updating {args.distro} only")
        elif args.distros:
            # Multiple distros from command line
            distros_to_update = [d.strip() for d in args.distros.split(',') if d.strip()]
            # Validate distros
            valid_distros = list(manager.distro_finders.keys())
            invalid = [d for d in distros_to_update if d not in valid_distros]
            if invalid:
                logger.error(f"Invalid distributions: {', '.join(invalid)}")
                logger.error(f"Valid choices: {', '.join(valid_distros)}")
                sys.exit(1)
            logger.info(f"Command-line override: updating {', '.join(distros_to_update)}")
        elif 'distros' in config and config['distros']:
            # Distros from config file or environment variable
            distros_to_update = config['distros']
            # Validate distros
            valid_distros = list(manager.distro_finders.keys())
            invalid = [d for d in distros_to_update if d not in valid_distros]
            if invalid:
                logger.warning(f"Invalid distributions in config: {', '.join(invalid)} (skipping)")
                distros_to_update = [d for d in distros_to_update if d in valid_distros]
            
            if not distros_to_update:
                logger.error("No valid distributions configured")
                sys.exit(1)
            logger.info(f"Config/environment: updating {', '.join(distros_to_update)}")
        else:
            # No distros specified, update all
            distros_to_update = list(manager.distro_finders.keys())
            logger.info(f"No distros configured, updating all: {', '.join(distros_to_update)}")
        
        # Update the specified distributions
        if len(distros_to_update) == 1:
            manager.update_torrent(distros_to_update[0])
        else:
            for distro in distros_to_update:
                try:
                    manager.update_torrent(distro)
                    time.sleep(2)  # Be nice to the servers
                except Exception as e:
                    logger.error(f"Failed to update {distro}: {e}")
                    continue
            logger.info("Torrent update check completed")
        
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
