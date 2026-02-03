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
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
import transmission_rpc

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/linux-iso-updater.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class DistroTorrentFinder:
    """Base class for finding distribution torrent URLs."""
    
    def __init__(self, name: str):
        self.name = name
        
    def get_latest_torrent_url(self) -> Optional[str]:
        """Get the URL of the latest torrent file."""
        raise NotImplementedError


class CentOSTorrentFinder(DistroTorrentFinder):
    """Find latest CentOS Stream torrent."""
    
    def __init__(self):
        super().__init__("CentOS")
        self.base_url = "https://www.centos.org/download/"
        
    def get_latest_torrent_url(self) -> Optional[str]:
        try:
            # CentOS Stream 9 is the current version
            # Look for torrent on the official mirror
            torrent_url = "https://mirrors.centos.org/mirrorlist?path=/9-stream/BaseOS/x86_64/iso/CentOS-Stream-9-latest-x86_64-dvd1.iso.torrent&redirect=1&protocol=https"
            
            response = requests.get(torrent_url, timeout=30, allow_redirects=True)
            if response.status_code == 200 and b'.torrent' in response.content[:1000]:
                logger.info(f"Found CentOS torrent: {response.url}")
                return response.url
            
            # Fallback: Try direct mirror
            mirror_url = "https://mirror.stream.centos.org/9-stream/BaseOS/x86_64/iso/CentOS-Stream-9-latest-x86_64-dvd1.iso.torrent"
            response = requests.head(mirror_url, timeout=30)
            if response.status_code == 200:
                logger.info(f"Found CentOS torrent: {mirror_url}")
                return mirror_url
                
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


class TransmissionTorrentManager:
    """Manage torrents in Transmission."""
    
    def __init__(self, host: str, port: int, username: str, password: str):
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
        try:
            torrents = self.client.get_torrents()
            name_patterns = {
                'centos': ['centos', 'CentOS'],
                'debian': ['debian'],
                'ubuntu': ['ubuntu'],
                'arch': ['arch', 'archlinux'],
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
            
            # If we have an existing torrent, check if it's the same
            if existing_torrent:
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


def load_config() -> Dict:
    """Load configuration from file or environment variables."""
    config_file = os.path.expanduser('~/.config/linux-iso-updater/config.json')
    
    # Try to load from config file
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load config file: {e}")
    
    # Fall back to environment variables
    return {
        'host': os.getenv('TRANSMISSION_HOST', 'localhost'),
        'port': int(os.getenv('TRANSMISSION_PORT', '9091')),
        'username': os.getenv('TRANSMISSION_USER', ''),
        'password': os.getenv('TRANSMISSION_PASS', ''),
    }


def main():
    """Main entry point."""
    try:
        config = load_config()
        
        if not config.get('username') or not config.get('password'):
            logger.error("Transmission credentials not configured!")
            logger.error("Set TRANSMISSION_USER and TRANSMISSION_PASS environment variables")
            logger.error(f"or create config file at ~/.config/linux-iso-updater/config.json")
            sys.exit(1)
        
        manager = TransmissionTorrentManager(
            host=config['host'],
            port=config['port'],
            username=config['username'],
            password=config['password']
        )
        
        manager.update_all_torrents()
        
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
