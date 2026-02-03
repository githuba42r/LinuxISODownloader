# Project Structure

```
LinuxTorentDownloader/
├── linux_iso_torrent_updater.py    # Main Python script
├── Dockerfile                       # Docker image definition
├── docker-compose.yml              # Docker Compose configuration
├── .dockerignore                   # Files to exclude from Docker build
├── build.sh                        # Helper script to build Docker image
├── requirements.txt                # Python dependencies
├── linux-iso-updater.service       # Systemd service unit (Docker-enabled)
├── linux-iso-updater.timer         # Systemd timer unit
├── config.json.example             # Example config for native installation
├── credentials.env.example         # Example credentials for systemd
├── .env.example                    # Example environment file for Docker
├── README.md                       # Main documentation
└── DOCKER.md                       # Docker quick reference guide
```

## File Descriptions

### Core Application

- **linux_iso_torrent_updater.py**
  - Main Python script that manages Linux ISO torrents
  - Supports CentOS, Debian, Ubuntu, and Arch Linux
  - Uses Transmission RPC to add/remove torrents
  - Can be run standalone or in Docker

### Docker Files

- **Dockerfile**
  - Multi-stage build with Python virtual environment
  - Runs as non-root user (uid 1000)
  - Based on python:3.11-slim
  - Includes health check

- **docker-compose.yml**
  - Simplified Docker container management
  - Uses host network mode for localhost Transmission access
  - Configurable via environment variables or .env file
  - Includes resource limits

- **.dockerignore**
  - Excludes unnecessary files from Docker image
  - Reduces image size and build time

- **build.sh**
  - Convenience script to build Docker image
  - Supports custom image tags
  - Shows usage examples after build

- **.env.example**
  - Template for Docker environment variables
  - Copy to `.env` and edit for your setup

### Systemd Files

- **linux-iso-updater.service**
  - Systemd service unit for Docker execution
  - Runs as oneshot service
  - Loads credentials from `/etc/linux-iso-updater/credentials.env`
  - Can be adapted for native Python execution

- **linux-iso-updater.timer**
  - Systemd timer for periodic execution
  - Default: Daily at 3:00 AM
  - Includes randomized delay
  - Persistent across reboots

### Configuration Examples

- **config.json.example**
  - JSON configuration for native installation
  - Copy to `~/.config/linux-iso-updater/config.json`

- **credentials.env.example**
  - Environment variables for systemd service
  - Copy to `/etc/linux-iso-updater/credentials.env`

### Dependencies

- **requirements.txt**
  - Python package dependencies
  - transmission-rpc, requests, beautifulsoup4

### Documentation

- **README.md**
  - Complete documentation
  - Installation instructions for Docker and native
  - Configuration guide
  - Troubleshooting section

- **DOCKER.md**
  - Docker-specific quick reference
  - Common commands and workflows
  - Troubleshooting Docker issues
  - Advanced configurations

## Installation Paths

### Docker Installation

```
/etc/linux-iso-updater/credentials.env    # Credentials (optional)
/etc/systemd/system/linux-iso-updater.service
/etc/systemd/system/linux-iso-updater.timer
```

### Native Installation

```
/usr/local/bin/linux_iso_torrent_updater.py
/etc/linux-iso-updater/credentials.env     # System-wide config
~/.config/linux-iso-updater/config.json    # User config
/var/log/linux-iso-updater.log             # Log file
/etc/systemd/system/linux-iso-updater.service
/etc/systemd/system/linux-iso-updater.timer
```

## Quick Start

### Docker

```bash
# 1. Build image
./build.sh

# 2. Configure
cp .env.example .env
nano .env

# 3. Test run
docker-compose up

# 4. Install systemd timer
sudo cp linux-iso-updater.{service,timer} /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now linux-iso-updater.timer
```

### Native

```bash
# 1. Install dependencies
pip3 install -r requirements.txt

# 2. Configure
mkdir -p ~/.config/linux-iso-updater
cp config.json.example ~/.config/linux-iso-updater/config.json
nano ~/.config/linux-iso-updater/config.json

# 3. Test run
python3 linux_iso_torrent_updater.py

# 4. Install as service
sudo cp linux_iso_torrent_updater.py /usr/local/bin/
sudo chmod +x /usr/local/bin/linux_iso_torrent_updater.py
sudo cp linux-iso-updater.{service,timer} /etc/systemd/system/
# Edit service file to use native Python
sudo systemctl daemon-reload
sudo systemctl enable --now linux-iso-updater.timer
```

## Workflow

1. **Timer triggers** → Systemd timer activates based on schedule
2. **Service starts** → Either launches Docker container or runs Python script
3. **Script executes** → Checks for latest ISO torrents from distribution sites
4. **Compares versions** → Identifies if new torrents are available
5. **Updates torrents** → Removes old torrents, adds new ones via Transmission RPC
6. **Logs results** → Outputs to systemd journal and/or log file
7. **Service exits** → Oneshot service completes until next timer trigger

## Customization

### Adding New Distributions

Edit `linux_iso_torrent_updater.py`:

1. Create a new `DistroTorrentFinder` subclass
2. Implement `get_latest_torrent_url()` method
3. Add to `distro_finders` dict in `TransmissionTorrentManager.__init__()`
4. Rebuild Docker image if using Docker

### Changing Schedule

Edit `linux-iso-updater.timer`:

1. Modify `OnCalendar=` directive
2. Reload systemd: `sudo systemctl daemon-reload`
3. Restart timer: `sudo systemctl restart linux-iso-updater.timer`

### Custom Logging

Edit `linux_iso_torrent_updater.py`:

1. Modify `logging.basicConfig()` settings
2. Change log file path, format, or level
3. Rebuild Docker image if using Docker
