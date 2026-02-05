# Linux ISO Torrent Updater

A Python application that automatically manages torrent files for the latest Linux distribution ISO images on a Transmission server. It tracks 14 popular Linux distributions, automatically removing old torrents and adding new ones as they become available.

## Features

- **Web Interface**: User-friendly web UI for managing torrent updates (port 8084)
- **CLI Mode**: Command-line interface for automation and scripting
- Automatically detects the latest ISO torrents for 14 distributions:
  - **CentOS Stream 9** (via LinuxTracker.org)
  - **Debian** (latest stable DVD)
  - **Ubuntu** (latest LTS desktop)
  - **Arch Linux** (latest release)
  - **Raspberry Pi OS** (latest arm64 release)
  - **Linux Mint** (latest Cinnamon edition)
  - **Fedora Workstation** (latest official release)
  - **Pop!_OS** (latest LTS)
  - **Rocky Linux** (latest DVD)
  - **AlmaLinux** (latest DVD)
  - **Manjaro** (latest KDE edition)
  - **elementary OS** (latest stable)
  - **Zorin OS** (latest Core edition)
  - **EndeavourOS** (latest release)
- Removes old torrents and their files when updates are available
- Integrates with Transmission via RPC
- Runs periodically via systemd timer
- Comprehensive logging
- Docker support with multiple configuration methods

**Note:** CentOS Stream no longer provides official torrent files. This script uses LinuxTracker.org as a community source for CentOS torrents.

## Requirements

### Docker Installation (Recommended)
- Docker Engine 20.10+
- Docker Compose (optional, for easier management)
- Transmission daemon (running on host or another container)

### Native Installation
- Python 3.6+
- Transmission daemon
- Required Python packages:
  - `transmission-rpc`
  - `requests`
  - `beautifulsoup4`
  - `flask` (for web interface)
  - `python-dotenv`

## Quick Start

The application has **two run modes**: Web Interface (GUI) or CLI (command-line). You choose the mode when starting the application.

### Web Interface (Easiest)

The web interface provides a user-friendly way to manage your Linux ISO torrents:

```bash
# Using Docker (Recommended)
docker-compose up -d web-interface

# Or using native Python
python web_interface.py
```

Then open http://localhost:8084 in your browser to:
- Select which distributions to check for updates
- View current torrent status
- Trigger manual update checks
- Monitor download progress in real-time

The web interface can be enabled in three ways:
1. **Environment variable** (Docker/Portainer): Set `WEB_ENABLED=true`
2. **Command-line flag** (Docker/Native): Use `--web` flag
3. **Direct execution** (Native): Run `python web_interface.py`

### CLI Mode (For Automation)

For automated scripts or cron jobs:

```bash
# Using Docker
docker-compose run --rm linux-iso-updater --distros debian,ubuntu,arch

# Or using native Python
python linux_iso_torrent_updater.py --distros debian,ubuntu,arch
```

## Installation

You can run this application either using Docker (recommended) or as a native Python script.

## Docker Installation (Recommended)

### 1. Build the Docker Image

```bash
# Clone or navigate to the repository
cd LinuxTorentDownloader

# Build the Docker image
docker build -t linux-iso-updater:latest .
```

### 2. Configure Credentials

Create an environment file:

```bash
# Copy the example file
cp .env.example .env

# Edit with your credentials
nano .env
```

Edit the `.env` file with your Transmission credentials:

```bash
TRANSMISSION_HOST=localhost
TRANSMISSION_PORT=9091
TRANSMISSION_USER=your_username
TRANSMISSION_PASS=your_password

# Optional: Configure automatic scheduling (for web interface)
SCHEDULE_ENABLED=true                                    # Enable automatic checks
SCHEDULE_FREQUENCY=1d                                    # Check daily
SCHEDULE_TIME=02:00                                      # Check at 2am (for daily+ frequencies)
SELECT_DISTROS=debian,ubuntu,arch,raspberrypi            # Distros selected by default in web UI
```

### 3. Run the Application

You can run the application in two modes: **Web Interface** (GUI) or **CLI** (command-line).

#### Web Interface Mode (Recommended for Interactive Use)

Start the web interface to manage torrents through a browser:

```bash
# Using docker-compose (recommended)
docker-compose up -d web-interface

# Or using docker run directly
docker run -d \
  --name linux-iso-updater-web \
  -p 8084:8084 \
  --env-file .env \
  linux-iso-updater:latest --web

# Access at http://localhost:8084
```

The web interface provides:
- Real-time torrent status monitoring
- Interactive distro selection
- Manual update checking
- Auto-refresh every 5 seconds
- Progress tracking with visual indicators
- **Automatic scheduled checks** (default: daily at 2am local time)

#### CLI Mode (For Automation)

For one-time runs or scheduled automation:

```bash
# Using docker run
docker run --rm \
  --network host \
  --env-file .env \
  linux-iso-updater:latest

# Or using docker-compose
docker-compose run --rm linux-iso-updater

# With specific distros
docker-compose run --rm linux-iso-updater --distros debian,ubuntu,arch

# Dry-run mode (no changes)
docker-compose run --rm linux-iso-updater --dry-run
```

### 4. Portainer Setup (Alternative to Command Line)

If you're using Portainer to manage Docker containers:

1. **In Portainer:** Go to Stacks → Add stack
2. **Name:** `linux-iso-updater`
3. **Upload or paste** the `docker-compose.portainer.yml` file (or use the regular `docker-compose.yml`)
4. **Add environment variables:**
   - `WEB_ENABLED` = true
   - `TRANSMISSION_HOST` = your transmission host
   - `TRANSMISSION_PORT` = 9091
   - `TRANSMISSION_USER` = your username
   - `TRANSMISSION_PASS` = your password
   - `SCHEDULE_ENABLED` = true
   - `SCHEDULE_FREQUENCY` = 1d
   - `WEB_PORT` = 8084
5. **Deploy the stack**
6. **Access the web interface:** `http://your-server-ip:8084`

**Note:** A Portainer-optimized docker-compose file is available: `docker-compose.portainer.yml`

See [DOCKER.md](DOCKER.md#portainer-integration) for detailed Portainer documentation.

### 5. Install Systemd Units (Docker)

```bash
# Copy the systemd files
sudo cp linux-iso-updater.service /etc/systemd/system/
sudo cp linux-iso-updater.timer /etc/systemd/system/

# Copy credentials
sudo mkdir -p /etc/linux-iso-updater
sudo cp .env /etc/linux-iso-updater/credentials.env
sudo chmod 600 /etc/linux-iso-updater/credentials.env

# Reload systemd
sudo systemctl daemon-reload

# Enable and start the timer
sudo systemctl enable linux-iso-updater.timer
sudo systemctl start linux-iso-updater.timer
```

### 5. Verify Installation

```bash
# Check timer status
sudo systemctl status linux-iso-updater.timer

# View logs
sudo journalctl -u linux-iso-updater.service -f

# Manually trigger a run
sudo systemctl start linux-iso-updater.service
```

## Native Installation

### 1. Install Python Dependencies

It's recommended to use a virtual environment to avoid conflicts with system packages:

```bash
# Clone or navigate to the repository
cd LinuxTorentDownloader

# Create a virtual environment
python -m venv venv

# Activate the virtual environment
source venv/bin/activate

# Install dependencies
pip install transmission-rpc requests beautifulsoup4 python-dotenv flask
```

Or install system-wide:

```bash
pip3 install transmission-rpc requests beautifulsoup4 python-dotenv flask
```

Or using your system package manager:

```bash
# Debian/Ubuntu
sudo apt install python3-requests python3-bs4 python3-dotenv
pip3 install transmission-rpc

# Arch Linux
sudo pacman -S python-requests python-beautifulsoup4 python-dotenv
pip install transmission-rpc
```

### 2. Install the Script

```bash
# Copy the script to system location
sudo cp linux_iso_torrent_updater.py /usr/local/bin/
sudo chmod +x /usr/local/bin/linux_iso_torrent_updater.py
```

### 3. Configure Credentials

Choose one of the following methods:

#### Option A: Using Config File (Recommended)

```bash
# For user-level configuration
mkdir -p ~/.config/linux-iso-updater
cp config.json.example ~/.config/linux-iso-updater/config.json
nano ~/.config/linux-iso-updater/config.json

# For system-level configuration (when using systemd)
sudo mkdir -p /etc/linux-iso-updater
sudo cp credentials.env.example /etc/linux-iso-updater/credentials.env
sudo nano /etc/linux-iso-updater/credentials.env
sudo chmod 600 /etc/linux-iso-updater/credentials.env
```

#### Option B: Using Environment Variables

```bash
export TRANSMISSION_HOST=localhost
export TRANSMISSION_PORT=9091
export TRANSMISSION_USER=your_username
export TRANSMISSION_PASS=your_password
```

### 4. Logging Configuration (Optional)

By default, logs are output to the console only. You can optionally configure file logging in two ways:

#### Option A: Command-Line Argument

```bash
# Log to a specific file
python linux_iso_torrent_updater.py --log-file /var/log/linux-iso-updater.log

# Or use a user-writable location
python linux_iso_torrent_updater.py --log-file ~/logs/linux-iso-updater.log
```

#### Option B: Environment Variable

```bash
# Set LOG_FILE environment variable
export LOG_FILE=/var/log/linux-iso-updater.log
python linux_iso_torrent_updater.py

# Or inline
LOG_FILE=~/logs/iso-updater.log python linux_iso_torrent_updater.py
```

Note: The command-line `--log-file` argument takes precedence over the `LOG_FILE` environment variable.

### 5. Install Systemd Units (Native)

Note: For Docker installation, see the Docker Installation section above.

```bash
# Copy systemd files
sudo cp linux-iso-updater.service /etc/systemd/system/
sudo cp linux-iso-updater.timer /etc/systemd/system/

# Edit the service file to use native Python (not Docker)
sudo nano /etc/systemd/system/linux-iso-updater.service
# Change ExecStart to: /usr/bin/python3 /usr/local/bin/linux_iso_torrent_updater.py
# Set appropriate User/Group

# Reload systemd
sudo systemctl daemon-reload

# Enable and start the timer
sudo systemctl enable linux-iso-updater.timer
sudo systemctl start linux-iso-updater.timer
```

## Usage

This application can be used in two modes:

### Web Interface Mode

The web interface provides an easy-to-use GUI for managing your Linux ISO torrents:

```bash
# Using Docker (recommended)
docker-compose up -d web-interface

# Or native Python
python web_interface.py

# With custom host/port
python web_interface.py --host 0.0.0.0 --port 8084

# With debug mode (for development)
python web_interface.py --debug
```

Access the web interface at http://localhost:8084

**Web Interface Features:**
- Real-time torrent status with auto-refresh (5 seconds)
- Select distributions to check for updates
- View download progress, speeds, and ratios
- Manual update checking with progress tracking
- Responsive design for mobile devices
- Visual status indicators and progress bars with hover effects
- ETA (estimated time remaining) display for active downloads
- Progress percentage tooltips on hover
- **Automatic scheduled checks** - runs daily at configured time (default: 2am)

**Web Interface Command-Line Options:**

```bash
# Basic usage
python web_interface.py

# Custom host and port
python web_interface.py --host 0.0.0.0 --port 8084

# With debug mode
python web_interface.py --debug

# Configure automatic scheduling
python web_interface.py --schedule-enabled true --schedule-frequency 1d --schedule-time 02:00

# Disable automatic scheduling
python web_interface.py --schedule-enabled false

# Check every 8 hours
python web_interface.py --schedule-frequency 8h

# With log file
python web_interface.py --log-file ~/logs/web-interface.log
```

**Available web interface options:**
- `--host`: Host to bind to (default: 0.0.0.0)
- `--port`: Port to bind to (default: 8084)
- `--debug`: Enable Flask debug mode
- `--schedule-enabled`: Enable/disable automatic checks (true/false, default: true)
- `--schedule-frequency`: Frequency for automatic checks (1h/8h/1d/7d/14d/30d, default: 1d)
- `--schedule-time`: Time for automatic checks in HH:MM format (default: 02:00, only used for daily+ frequencies)
- `--select-distros`: Distributions selected by default in web UI (comma-separated)
- `--log-file`, `-l`: Path to log file (default: console only)

### Automatic Scheduling (Web Interface)

When running the web interface, you can configure automatic torrent checks:

**Via Environment Variables** (recommended):

```bash
# In .env file
WEB_ENABLED=true                                         # Enable web interface (default: false)
SCHEDULE_ENABLED=true                                    # Enable/disable automatic checks (default: true)
SCHEDULE_FREQUENCY=1d                                    # Check frequency (1h/8h/1d/7d/14d/30d)
SCHEDULE_TIME=02:00                                      # Time for daily+ checks (HH:MM format)
SELECT_DISTROS=debian,ubuntu,arch,raspberrypi            # Distros selected by default in web UI
```

**Important:** `SCHEDULE_ENABLED` only works when `WEB_ENABLED=true` (automatic checks require the web interface to run).

**Frequency Options:**
- `1h` - Check every hour
- `8h` - Check every 8 hours  
- `1d` - Check daily (default)
- `7d` - Check weekly
- `14d` - Check every 2 weeks
- `30d` - Check monthly

**Via Command Line:**

```bash
# Enable with hourly checks
python web_interface.py --schedule-enabled true --schedule-frequency 1h

# Enable with daily checks at 2am
python web_interface.py --schedule-enabled true --schedule-frequency 1d --schedule-time 02:00

# Disable automatic checks
python web_interface.py --schedule-enabled false
```

**Via Web UI:**

You can also enable/disable automatic checks and change the frequency directly in the web interface settings menu.

**Via Command-Line Arguments**:

```bash
python web_interface.py --schedule-time 14:30 --select-distros debian,ubuntu
```

**Via Docker Environment**:

```bash
docker run -d \
  -p 8084:8084 \
  --env-file .env \
  -e WEB_ENABLED=true \
  -e SCHEDULE_ENABLED=true \
  -e SCHEDULE_FREQUENCY=1d \
  -e SCHEDULE_TIME=02:00 \
  -e SELECT_DISTROS=debian,ubuntu,arch \
  linux-iso-updater:latest
```

**Configuration Options:**
- **Web Interface**: Set `WEB_ENABLED=true` to run web server (default: false)
- **Enable/Disable Scheduling**: Set `SCHEDULE_ENABLED=true` or `false` (default: true, requires WEB_ENABLED=true)
- **Frequency**: `1h`, `8h`, `1d`, `7d`, `14d`, `30d` (default: 1d)
- **Time**: `HH:MM` in 24-hour format for daily+ frequencies (default: 02:00)
- **Distributions**: Comma-separated list to select by default in web UI
- **Default distros**: debian,ubuntu,arch,centos,raspberrypi,mint,fedora,popos,rocky,alma,manjaro,elementary,zorin,endeavour

The scheduler runs in the background and automatically checks for new torrents based on the configured frequency.

### Command Line Options

The script supports several command-line options:

```bash
# If using virtual environment, activate it first
source venv/bin/activate

# Show help
python linux_iso_torrent_updater.py --help

# Normal run - update configured distributions
python linux_iso_torrent_updater.py

# Dry-run - show what would be done without making changes
python linux_iso_torrent_updater.py --dry-run

# Update specific distribution only (overrides config)
python linux_iso_torrent_updater.py --distro debian

# Update multiple distributions (overrides config)
python linux_iso_torrent_updater.py --distros debian,ubuntu

# Dry-run for specific distribution
python linux_iso_torrent_updater.py --dry-run --distro ubuntu

# Or use venv python directly without activating
venv/bin/python linux_iso_torrent_updater.py --dry-run

# With log file
python linux_iso_torrent_updater.py --log-file ~/logs/iso-updater.log

# Or via environment variable
LOG_FILE=~/logs/iso-updater.log python linux_iso_torrent_updater.py
```

**Available options:**
- `--dry-run`, `-n`: Show what would be done without making any changes to Transmission
- `--distro`, `-d <name>`: Update specific distribution (choices: centos, debian, ubuntu, arch, raspberrypi, mint, fedora, popos, rocky, alma, manjaro, elementary, zorin, endeavour) - overrides config
- `--distros <list>`: Comma-separated list of distributions - overrides config
- `--log-file`, `-l <path>`: Path to log file (default: console only)

### Configuring Which Distributions to Update

You can control which distributions are updated using three methods (in priority order):

#### 1. Command-Line Arguments (Highest Priority)

```bash
# Update only Debian
python linux_iso_torrent_updater.py --distro debian

# Update Debian and Ubuntu
python linux_iso_torrent_updater.py --distros debian,ubuntu

# Docker
docker run --rm --network host --env-file .env \
  linux-iso-updater:latest --distros debian,ubuntu
```

#### 2. Environment Variable

```bash
# Set in shell
export DISTROS=debian,ubuntu
python linux_iso_torrent_updater.py

# Or inline
DISTROS=debian,ubuntu python linux_iso_torrent_updater.py

# In .env file
echo "DISTROS=debian,ubuntu,arch" >> .env
```

#### 3. Configuration File

Edit `~/.config/linux-iso-updater/config.json`:

```json
{
  "host": "localhost",
  "port": 9091,
  "username": "myuser",
  "password": "mypass",
  "distros": ["debian", "ubuntu", "arch"]
}
```

#### 4. Default (All Distributions)

If none of the above are set, all distributions will be updated.

**Priority order:**
1. `--distro` or `--distros` command-line flags *(highest)*
2. `DISTROS` environment variable
3. `distros` in config.json
4. All distributions *(default)*

### Docker Usage

#### Manual Execution

Run the container manually:

```bash
# Normal run - using docker run
docker run --rm \
  --network host \
  -e TRANSMISSION_HOST=localhost \
  -e TRANSMISSION_PORT=9091 \
  -e TRANSMISSION_USER=myuser \
  -e TRANSMISSION_PASS=mypass \
  linux-iso-updater:latest

# With DISTROS configured
docker run --rm \
  --network host \
  -e TRANSMISSION_HOST=localhost \
  -e TRANSMISSION_PORT=9091 \
  -e TRANSMISSION_USER=myuser \
  -e TRANSMISSION_PASS=mypass \
  -e DISTROS=debian,ubuntu \
  linux-iso-updater:latest

# Dry-run mode
docker run --rm \
  --network host \
  --env-file .env \
  linux-iso-updater:latest --dry-run

# Update specific distro only (overrides DISTROS env var)
docker run --rm \
  --network host \
  --env-file .env \
  linux-iso-updater:latest --distro debian

# Dry-run for specific distro
docker run --rm \
  --network host \
  --env-file .env \
  linux-iso-updater:latest --dry-run --distro ubuntu

# Using docker-compose (edit docker-compose.yml to add command arguments)
docker-compose up
```

#### Passing Configuration to Docker Containers

Docker containers don't have access to your host's files by default. Here are the methods to pass configuration:

##### Method 1: Using --env-file (Recommended)

The `--env-file` flag reads environment variables from a file on your host:

```bash
# Create a .env file with your credentials (if you haven't already)
cat > .env <<EOF
TRANSMISSION_HOST=localhost
TRANSMISSION_PORT=9091
TRANSMISSION_USER=myuser
TRANSMISSION_PASS=mypass
DISTROS=debian,ubuntu,raspberrypi
EOF

# Run with --env-file
docker run --rm \
  --network host \
  --env-file .env \
  linux-iso-updater:latest --dry-run

# You can use any .env file location
docker run --rm \
  --network host \
  --env-file /etc/linux-iso-updater/credentials.env \
  linux-iso-updater:latest
```

##### Method 2: Using -e for Individual Variables

Pass environment variables individually:

```bash
docker run --rm \
  --network host \
  -e TRANSMISSION_HOST=localhost \
  -e TRANSMISSION_PORT=9091 \
  -e TRANSMISSION_USER=myuser \
  -e TRANSMISSION_PASS=mypass \
  -e DISTROS=debian,ubuntu \
  linux-iso-updater:latest --dry-run
```

##### Method 3: Using Volume Mounts for .env Files

Mount a .env file from your host into the container:

```bash
# Mount .env file to /app/.env inside container
docker run --rm \
  --network host \
  -v "$(pwd)/.env:/app/.env:ro" \
  linux-iso-updater:latest --dry-run

# The script will automatically load /app/.env if it exists
```

##### Method 4: Using Volume Mounts for config.json

If you prefer config.json over .env files:

```bash
# Create config file
mkdir -p ~/.config/linux-iso-updater
cat > ~/.config/linux-iso-updater/config.json <<EOF
{
  "host": "localhost",
  "port": 9091,
  "username": "myuser",
  "password": "mypass",
  "distros": ["debian", "ubuntu", "raspberrypi"]
}
EOF

# Mount config directory
docker run --rm \
  --network host \
  -v ~/.config/linux-iso-updater:/root/.config/linux-iso-updater:ro \
  linux-iso-updater:latest --dry-run
```

##### Method 5: Docker Compose with env_file

In `docker-compose.yml`:

```yaml
version: '3.8'
services:
  linux-iso-updater:
    image: linux-iso-updater:latest
    network_mode: host
    env_file:
      - .env                    # Loads .env from project directory
      # OR
      - /etc/linux-iso-updater/credentials.env  # System-wide config
    # Optional: Override or add environment variables
    environment:
      - DISTROS=debian,ubuntu
```

Then run:

```bash
docker-compose run --rm linux-iso-updater --dry-run
```

##### Method 6: Using LOG_FILE with Volume Mount

If you want to write logs to a file on the host:

```bash
# Create log directory on host
mkdir -p ~/logs

# Run with log file and volume mount
docker run --rm \
  --network host \
  --env-file .env \
  -v ~/logs:/logs \
  -e LOG_FILE=/logs/iso-updater.log \
  linux-iso-updater:latest --dry-run

# Or use --log-file argument
docker run --rm \
  --network host \
  --env-file .env \
  -v ~/logs:/logs \
  linux-iso-updater:latest --log-file /logs/iso-updater.log --dry-run
```

**Security Notes:**
- Never commit `.env` files with real credentials to version control
- Use `.env.local` for local development (it's gitignored)
- Set proper permissions: `chmod 600 .env`
- Use `:ro` (read-only) flag when mounting sensitive files
- For production, consider using Docker secrets or environment variables from your orchestration platform

**Priority Order in Docker:**
1. Command-line arguments (`--distro`, `--log-file`)
2. Environment variables from `-e` flags
3. Environment variables from `--env-file`
4. Mounted `.env` files inside container
5. Mounted `config.json` files
6. Default values

#### Rebuilding the Image

After making changes to the script:

```bash
# Rebuild the image
docker build -t linux-iso-updater:latest .

# Or with docker-compose
docker-compose build
```

### Native Usage

#### Manual Execution

Run the script manually to test:

```bash
# Normal run
/usr/local/bin/linux_iso_torrent_updater.py

# Dry-run mode
/usr/local/bin/linux_iso_torrent_updater.py --dry-run

# Update specific distro
/usr/local/bin/linux_iso_torrent_updater.py --distro debian

# Dry-run for specific distro
/usr/local/bin/linux_iso_torrent_updater.py --dry-run --distro ubuntu
```

Or with environment variables:

```bash
# Normal run
TRANSMISSION_USER=myuser TRANSMISSION_PASS=mypass python3 linux_iso_torrent_updater.py

# Dry-run mode
TRANSMISSION_USER=myuser TRANSMISSION_PASS=mypass python3 linux_iso_torrent_updater.py --dry-run
```

### Dry-Run Mode

Dry-run mode allows you to see what the script would do without making any actual changes to Transmission. This is useful for:

- Testing configuration before running for real
- Seeing what torrents would be updated
- Verifying torrent URLs are found correctly
- Debugging without affecting your downloads

**What happens in dry-run mode:**
- ✅ Finds and downloads torrent files from distribution websites
- ✅ Shows torrent URLs and metadata
- ✅ Reports what actions would be taken
- ❌ Does NOT connect to Transmission (credentials optional)
- ❌ Does NOT add new torrents
- ❌ Does NOT remove old torrents

**Example output:**
```
[DRY-RUN MODE: No changes will be made to Transmission]
Found Debian torrent: https://cdimage.debian.org/.../debian-12.0.0-amd64-DVD-1.iso.torrent
[DRY-RUN] Downloaded torrent (hash: 1a2b3c4d5e6f7g8h...)
[DRY-RUN] No existing debian torrent found
[DRY-RUN] Would add new torrent from https://...
```

### Systemd Timer (Both Docker and Native)

The timer runs automatically based on the configured schedule (default: daily at 3 AM).

Check timer status:

```bash
# View timer status
sudo systemctl status linux-iso-updater.timer

# List all timers
sudo systemctl list-timers

# View service logs
sudo journalctl -u linux-iso-updater.service -f

# Manually trigger the service
sudo systemctl start linux-iso-updater.service
```

### Customizing the Schedule

Edit `/etc/systemd/system/linux-iso-updater.timer` and modify the `OnCalendar` value:

```ini
# Daily at 3 AM
OnCalendar=daily

# Every 6 hours
OnCalendar=00/6:00:00

# Weekly on Sunday at 3 AM
OnCalendar=Sun *-*-* 03:00:00

# Every Monday and Friday at 2 AM
OnCalendar=Mon,Fri *-*-* 02:00:00
```

After editing, reload systemd:

```bash
sudo systemctl daemon-reload
sudo systemctl restart linux-iso-updater.timer
```

## Logging

### Default Behavior

By default, the script logs to **console only** (stdout). This is suitable for:
- Interactive use
- Docker containers (logs captured by Docker)
- systemd services (logs captured by journald)
- Debugging and testing

### File Logging (Optional)

To also log to a file, use one of these methods:

#### Command-Line Option

```bash
# Log to console AND file
python linux_iso_torrent_updater.py --log-file /path/to/logfile.log

# Examples
python linux_iso_torrent_updater.py --log-file /var/log/linux-iso-updater.log
python linux_iso_torrent_updater.py --log-file ~/logs/iso-updater.log
python linux_iso_torrent_updater.py -l /tmp/updater.log
```

#### Environment Variable

```bash
# Set LOG_FILE environment variable
export LOG_FILE=/var/log/linux-iso-updater.log
python linux_iso_torrent_updater.py

# Or add to .env file
echo "LOG_FILE=/var/log/linux-iso-updater.log" >> .env
```

**Note:** The `--log-file` command-line argument takes precedence over the `LOG_FILE` environment variable.

### Docker Logging

When run via Docker, logs are output to:
- Docker container logs (viewable with `docker logs`)
- systemd journal (when run via systemd)
- Optional log file (if LOG_FILE environment variable is set)

View logs:

```bash
# View Docker container logs
docker logs linux-iso-updater

# View systemd journal (when using systemd + Docker)
journalctl -u linux-iso-updater.service -f

# View logs from the last run
journalctl -u linux-iso-updater.service --since "1 hour ago"

# Follow docker-compose logs
docker-compose logs -f

# If using LOG_FILE environment variable, also check the log file
tail -f /path/to/logfile.log
```

### Native Logging

When running natively, logs are output to:
- Console (stdout) - always enabled
- Optional log file (if `--log-file` or `LOG_FILE` is set)
- systemd journal (when run via systemd)

View logs:

```bash
# Console output (default)
python linux_iso_torrent_updater.py --dry-run

# If using log file, view it
tail -f /path/to/logfile.log

# View systemd journal (when run via systemd)
journalctl -u linux-iso-updater.service -f

# View logs from the last run
journalctl -u linux-iso-updater.service --since "1 hour ago"
```

## Configuration

### Environment File Loading Priority

The script supports multiple `.env` files for different environments:

#### Native Python Execution
When running the script directly, it loads `.env` files in this order (highest priority last):

1. `.env` - Base configuration (can be committed)
2. `.env.development` - Development overrides (can be committed)
3. `.env.local` - Local overrides (**NEVER commit - contains secrets**)

Then checks:
4. Config file at `~/.config/linux-iso-updater/config.json`
5. Environment variables from `/etc/linux-iso-updater/credentials.env` (systemd)
6. System environment variables

#### Docker Execution
Docker uses environment variables in this order (highest priority first):

1. Variables passed via `docker run -e`
2. Variables from `--env-file` flag
3. Variables in docker-compose.yml environment section
4. Variables in `/etc/linux-iso-updater/credentials.env` (when using systemd)

### Setting Up Environment Files

#### For Development

```bash
# Copy and edit development config
cp .env.development.example .env.development
nano .env.development
```

#### For Local Testing

```bash
# Copy and edit local config (this file is gitignored)
cp .env.local.example .env.local
nano .env.local
```

#### For Production (Docker)

```bash
# Use the standard .env file
cp .env.example .env
nano .env
```

### Example Workflow

1. **Team shared settings** → `.env` or `.env.development` (committed)
2. **Personal local settings** → `.env.local` (never committed)
3. **Production/Docker** → `.env` or systemd credentials

### Transmission RPC Settings

#### Docker
The Docker container uses environment variables (in order of precedence):
1. Variables passed via `docker run -e` or `--env-file`
2. Variables in `.env` file (when using docker-compose)
3. Variables in `/etc/linux-iso-updater/credentials.env` (when using systemd)

#### Native
The script connects to Transmission using these settings (in order of precedence):
1. Environment variables from `.env.local` (if exists)
2. Environment variables from `.env.development` (if exists)
3. Environment variables from `.env` (if exists)
4. Config file at `~/.config/linux-iso-updater/config.json`
5. Environment variables from `/etc/linux-iso-updater/credentials.env` (systemd)
6. System environment variables (`TRANSMISSION_HOST`, `TRANSMISSION_PORT`, `TRANSMISSION_USER`, `TRANSMISSION_PASS`)

Default values:
- Host: `localhost`
- Port: `9091`
- Username: (required)
- Password: (required)

### Enabling Transmission RPC

Ensure Transmission RPC is enabled and configured:

```bash
# Edit Transmission settings
sudo systemctl stop transmission-daemon
sudo nano /etc/transmission-daemon/settings.json
```

Required settings:

```json
{
  "rpc-enabled": true,
  "rpc-port": 9091,
  "rpc-authentication-required": true,
  "rpc-username": "your_username",
  "rpc-password": "your_password",
  "rpc-whitelist-enabled": false
}
```

Restart Transmission:

```bash
sudo systemctl start transmission-daemon
```

## Troubleshooting

### Docker-Specific Issues

#### Container Cannot Connect to Transmission

Ensure you're using `--network host` to allow the container to access localhost:

```bash
# Check Transmission is accessible
curl http://localhost:9091/transmission/rpc

# Verify Docker container can access host network
docker run --rm --network host alpine ping -c 3 localhost
```

If using a custom Docker network or Transmission in another container:

```bash
# Use container name instead of localhost
docker run --rm \
  --network transmission-network \
  -e TRANSMISSION_HOST=transmission \
  -e TRANSMISSION_PORT=9091 \
  -e TRANSMISSION_USER=user \
  -e TRANSMISSION_PASS=pass \
  linux-iso-updater:latest
```

#### Image Build Failures

```bash
# Clean build without cache
docker build --no-cache -t linux-iso-updater:latest .

# Check disk space
docker system df
docker system prune -a
```

#### Container Exits Immediately

Check container logs:

```bash
# View logs from last run
docker logs linux-iso-updater

# Run container interactively for debugging
docker run -it --rm \
  --network host \
  --env-file .env \
  --entrypoint /bin/bash \
  linux-iso-updater:latest

# Then inside container, run manually:
python /app/linux_iso_torrent_updater.py
```

### Common Issues (Both Docker and Native)

#### Permission Denied

For native installation, ensure the script runs as the Transmission user:

```bash
# Check Transmission user
ps aux | grep transmission

# Update service file (native only)
sudo nano /etc/systemd/system/linux-iso-updater.service
# Set User= and Group= to match Transmission user
```

For Docker, the container runs as a non-root user but needs network access to reach Transmission.

#### Connection Refused

Check Transmission is running and RPC is enabled:

```bash
sudo systemctl status transmission-daemon
curl http://localhost:9091/transmission/rpc

# Check RPC credentials
transmission-remote localhost:9091 -n username:password -l
```

#### Torrent Not Found

The script searches for torrents from various sources:

**Torrent Sources:**
- **CentOS Stream 9**: LinuxTracker.org (community source)
- **Debian**: Official Debian CDImage servers
- **Ubuntu**: Official Ubuntu releases
- **Arch Linux**: Official Arch Linux servers
- **Raspberry Pi OS**: Official Raspberry Pi downloads
- **Linux Mint**: LinuxTracker.org (community mirror)
- **Fedora Workstation**: Official Fedora torrent servers
- **Pop!_OS**: LinuxTracker.org (community mirror)
- **Rocky Linux**: LinuxTracker.org (community mirror)
- **AlmaLinux**: LinuxTracker.org (community mirror)
- **Manjaro**: LinuxTracker.org (community mirror)
- **elementary OS**: LinuxTracker.org (community mirror)
- **Zorin OS**: LinuxTracker.org (community mirror)
- **EndeavourOS**: LinuxTracker.org (community mirror)

If a torrent cannot be found:

1. Check logs for specific errors
2. Verify the source is accessible (some distributions may temporarily remove torrents)
3. For CentOS, Mint, Pop!_OS, Rocky, AlmaLinux, Manjaro, elementary, Zorin, and EndeavourOS: LinuxTracker.org may be temporarily down or the page structure may have changed
4. Try the `--dry-run` flag to see what's happening without making changes

**CentOS Note:** CentOS Stream no longer provides official torrent files. This script uses LinuxTracker.org as a community-maintained source. If LinuxTracker is unavailable, CentOS torrents won't be found.

#### Testing Individual Distributions

Test a single distribution to isolate issues:

```bash
# Test with dry-run
python linux_iso_torrent_updater.py --dry-run --distro debian
python linux_iso_torrent_updater.py --dry-run --distro centos
python linux_iso_torrent_updater.py --dry-run --distro ubuntu
python linux_iso_torrent_updater.py --dry-run --distro arch
python linux_iso_torrent_updater.py --dry-run --distro raspberrypi
python linux_iso_torrent_updater.py --dry-run --distro mint
python linux_iso_torrent_updater.py --dry-run --distro fedora
python linux_iso_torrent_updater.py --dry-run --distro popos
python linux_iso_torrent_updater.py --dry-run --distro rocky
python linux_iso_torrent_updater.py --dry-run --distro alma
python linux_iso_torrent_updater.py --dry-run --distro manjaro
python linux_iso_torrent_updater.py --dry-run --distro elementary
python linux_iso_torrent_updater.py --dry-run --distro zorin
python linux_iso_torrent_updater.py --dry-run --distro endeavour
```

## Uninstallation

### Docker Installation

```bash
# Stop and disable timer
sudo systemctl stop linux-iso-updater.timer
sudo systemctl disable linux-iso-updater.timer

# Remove systemd files
sudo rm /etc/systemd/system/linux-iso-updater.{service,timer}

# Remove credentials
sudo rm -rf /etc/linux-iso-updater

# Remove Docker image
docker rmi linux-iso-updater:latest

# Reload systemd
sudo systemctl daemon-reload
```

### Native Installation

```bash
# Stop and disable timer
sudo systemctl stop linux-iso-updater.timer
sudo systemctl disable linux-iso-updater.timer

# Remove files
sudo rm /etc/systemd/system/linux-iso-updater.{service,timer}
sudo rm /usr/local/bin/linux_iso_torrent_updater.py
sudo rm -rf /etc/linux-iso-updater
sudo rm /var/log/linux-iso-updater.log

# Reload systemd
sudo systemctl daemon-reload
```

## Development

This project includes tools for easy development with hot-reload support.

### Quick Start for Developers

The easiest way to develop the web interface is using the provided development scripts:

```bash
# Make the script executable
chmod +x dev-web.sh

# Start development server with hot-reload on port 8099
./dev-web.sh

# With custom options
./dev-web.sh --port 8085 --host 0.0.0.0 --schedule-time 14:30
```

**Features:**
- Automatic reload when Python files change
- Flask debug mode with detailed error pages
- Runs on port 8099 by default (avoids conflict with Docker on 8084)
- Automatic virtual environment setup
- Dependency checking and installation
- Colored output for better visibility

### Development vs Production

| Aspect | Development (`./dev-web.sh`) | Production (Docker) |
|--------|------------------------------|---------------------|
| Port | 8099 | 8084 |
| Auto-reload | Yes | No |
| Debug mode | Enabled | Disabled |
| Performance | Slower (file monitoring) | Optimized |
| Error pages | Detailed with traceback | Simple messages |

### Making Changes

1. **Python code** (`web_interface.py`, `linux_iso_torrent_updater.py`):
   - Edit file → Server auto-restarts → Test in browser

2. **HTML templates** (`templates/index.html`):
   - Edit file → Refresh browser

3. **CSS/JavaScript** (`static/css/style.css`, `static/js/app.js`):
   - Edit file → Hard refresh browser (Ctrl+F5 or Cmd+Shift+R)

### Development Scripts

Two equivalent scripts are provided:

- **`dev-web.sh`** - Bash script (recommended for Linux/Mac)
- **`dev-web.py`** - Python script (cross-platform alternative)

Both provide the same functionality. The Bash script has slightly better terminal output formatting.

### Running Development and Production Simultaneously

You can run both at the same time on different ports:

```bash
# Terminal 1: Production via Docker on port 8084
docker-compose up web-interface

# Terminal 2: Development with hot-reload on port 8099
./dev-web.sh
```

### For More Details

See **[DEVELOPMENT.md](DEVELOPMENT.md)** for comprehensive development documentation including:
- Environment file configuration (`.env.local`, `.env.development`)
- IDE setup (VS Code, PyCharm)
- Troubleshooting development issues
- Adding new distributions
- Testing strategies
- Contributing guidelines

## Security Considerations

- Store credentials securely with restricted permissions (600)
- Docker containers run as non-root user (uid 1000) for security
- Use `--network host` carefully; consider Docker networks for better isolation
- The systemd service runs with Docker, which requires root or docker group access
- Consider using Docker secrets for production deployments
- Review and audit the script before running with elevated privileges
- Keep the Docker image updated with security patches

## Contributing

Feel free to submit issues, fork the repository, and create pull requests for any improvements.

## License

This project is provided as-is for educational and practical use.

## Disclaimer

This script downloads and seeds Linux distribution ISO files. Ensure you have:
- Sufficient disk space for multiple large ISO files
- Adequate bandwidth for seeding
- Permission from your network administrator if on a managed network

The script respects rate limiting and includes delays between requests to avoid overloading distribution servers.
