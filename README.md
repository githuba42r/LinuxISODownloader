# Linux ISO Torrent Updater

A Python script that automatically manages torrent files for the latest Linux distribution ISO images on a Transmission server. It tracks CentOS Stream, Debian, Ubuntu, and Arch Linux releases, removing old torrents and adding new ones as they become available.

## Features

- Automatically detects the latest ISO torrents for:
  - CentOS Stream 9
  - Debian (latest stable DVD)
  - Ubuntu (latest LTS desktop)
  - Arch Linux (latest release)
- Removes old torrents and their files when updates are available
- Integrates with Transmission via RPC
- Runs periodically via systemd timer
- Comprehensive logging

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
```

### 3. Test the Docker Container

```bash
# Using docker run
docker run --rm \
  --network host \
  --env-file .env \
  linux-iso-updater:latest

# Or using docker-compose
docker-compose up
```

### 4. Install Systemd Units (Docker)

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

```bash
pip3 install transmission-rpc requests beautifulsoup4
```

Or using your system package manager:

```bash
# Debian/Ubuntu
sudo apt install python3-requests python3-bs4
pip3 install transmission-rpc

# Arch Linux
sudo pacman -S python-requests python-beautifulsoup4
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

### 4. Set Up Logging

```bash
# Create log file with appropriate permissions
sudo touch /var/log/linux-iso-updater.log
sudo chown debian-transmission:debian-transmission /var/log/linux-iso-updater.log
```

Note: Replace `debian-transmission` with your Transmission user. Common alternatives:
- Debian/Ubuntu: `debian-transmission`
- Arch Linux: `transmission`
- Generic: check with `ps aux | grep transmission`

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

### Docker Usage

#### Manual Execution

Run the container manually:

```bash
# Using docker run
docker run --rm \
  --network host \
  -e TRANSMISSION_HOST=localhost \
  -e TRANSMISSION_PORT=9091 \
  -e TRANSMISSION_USER=myuser \
  -e TRANSMISSION_PASS=mypass \
  linux-iso-updater:latest

# Using environment file
docker run --rm \
  --network host \
  --env-file .env \
  linux-iso-updater:latest

# Using docker-compose
docker-compose up
```

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
/usr/local/bin/linux_iso_torrent_updater.py
```

Or with environment variables:

```bash
TRANSMISSION_USER=myuser TRANSMISSION_PASS=mypass python3 linux_iso_torrent_updater.py
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

### Docker Logging

When run via Docker, logs are output to:
- Docker container logs (viewable with `docker logs`)
- systemd journal (when run via systemd)

View logs:

```bash
# View container logs (if running)
docker logs linux-iso-updater

# View systemd journal (when using systemd + Docker)
journalctl -u linux-iso-updater.service -f

# View logs from the last run
journalctl -u linux-iso-updater.service --since "1 hour ago"

# Follow docker-compose logs
docker-compose logs -f
```

### Native Logging

Logs are written to:
- `/var/log/linux-iso-updater.log` (file)
- systemd journal (when run via systemd)

View logs:

```bash
# View log file
tail -f /var/log/linux-iso-updater.log

# View systemd journal
journalctl -u linux-iso-updater.service -f

# View logs from the last run
journalctl -u linux-iso-updater.service --since "1 hour ago"
```

## Configuration

### Transmission RPC Settings

#### Docker
The Docker container uses environment variables (in order of precedence):
1. Variables passed via `docker run -e` or `--env-file`
2. Variables in `.env` file (when using docker-compose)
3. Variables in `/etc/linux-iso-updater/credentials.env` (when using systemd)

#### Native
The script connects to Transmission using these settings (in order of precedence):
1. Config file at `~/.config/linux-iso-updater/config.json`
2. Environment variables from `/etc/linux-iso-updater/credentials.env` (systemd)
3. Environment variables (`TRANSMISSION_HOST`, `TRANSMISSION_PORT`, `TRANSMISSION_USER`, `TRANSMISSION_PASS`)

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

The script searches for torrents on official distribution websites. If links change:

1. Check logs for specific errors
2. Verify the distribution still provides torrent files
3. Update the finder classes in the script if needed
4. Rebuild Docker image if using Docker

#### Testing Individual Distributions

You can modify the script temporarily to test one distribution:

```python
# In main(), replace:
manager.update_all_torrents()

# With:
manager.update_torrent('debian')  # or 'ubuntu', 'centos', 'arch'
```

Then rebuild the Docker image or run the native script.

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
