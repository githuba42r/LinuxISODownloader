# Docker Quick Reference

## Building the Image

```bash
# Build with default tag (latest)
./build.sh

# Build with custom tag
./build.sh v1.0

# Build manually
docker build -t linux-iso-updater:latest .

# Build with GitHub Container Registry tag
docker build -t ghcr.io/githuba42r/linux-iso-updater:latest .
```

## Running the Container

### Web Interface

The web interface provides a GUI for managing torrent updates and runs on **port 8084** by default.

```bash
# Run web interface with host network
docker run --rm --network host --env-file .env \
  linux-iso-updater:latest --web

# Run web interface with port mapping (alternative to host network)
docker run --rm -p 8084:8084 --env-file .env \
  linux-iso-updater:latest --web

# Access the web interface
# Open http://localhost:8084 in your browser

# Run web interface with custom port
docker run --rm -p 8090:8084 --env-file .env \
  -e WEB_PORT=8090 \
  linux-iso-updater:latest --web --port 8090

# Run web interface with docker-compose
docker-compose up web-interface

# Run web interface in background
docker-compose up -d web-interface

# View web interface logs
docker-compose logs -f web-interface
```

**Web Interface Features:**
- View status of all tracked distributions
- Manually trigger updates for specific distributions
- Configure automatic scheduling (frequency: 1h, 8h, 1d, 7d, 14d, 30d)
- Enable/disable automatic checks
- View real-time update logs
- Monitor next scheduled check time

**Port Configuration:**
- Default port: **8084**
- Environment variable: `WEB_PORT=8084` (in docker-compose.yml)
- Command line: `--port 8090` (to use a different port)
- Network mode: Use `--network host` for direct access, or `-p 8084:8084` for port mapping

### CLI Mode

### CLI Mode

For one-time command-line execution without the web interface:

```bash
# Normal run - using environment file
docker run --rm --network host --env-file .env linux-iso-updater:latest

# Dry-run mode - see what would be done
docker run --rm --network host --env-file .env linux-iso-updater:latest --dry-run

# Update specific distribution only
docker run --rm --network host --env-file .env linux-iso-updater:latest --distro debian

# Dry-run for specific distribution
docker run --rm --network host --env-file .env linux-iso-updater:latest --dry-run --distro ubuntu

# Using individual environment variables
docker run --rm --network host \
  -e TRANSMISSION_HOST=localhost \
  -e TRANSMISSION_PORT=9091 \
  -e TRANSMISSION_USER=myuser \
  -e TRANSMISSION_PASS=mypass \
  linux-iso-updater:latest

# Using docker-compose
docker-compose up
```

### Command Line Arguments

The container accepts the same arguments as the Python script:

| Argument | Short | Description |
|----------|-------|-------------|
| `--dry-run` | `-n` | Show what would be done without making changes |
| `--distro <name>` | `-d <name>` | Update specific distro (centos, debian, ubuntu, arch, raspberrypi, mint, fedora, popos, rocky, alma, manjaro, elementary, zorin, endeavour, all) |

**Examples:**

```bash
# Dry-run for all distributions
docker run --rm --network host --env-file .env linux-iso-updater:latest --dry-run

# Show help
docker run --rm linux-iso-updater:latest --help

# Update only Ubuntu, dry-run mode
docker run --rm --network host --env-file .env \
  linux-iso-updater:latest --dry-run --distro ubuntu
```

### Interactive Debugging

```bash
# Open a shell in the container
docker run -it --rm --network host --env-file .env \
  --entrypoint /bin/bash \
  linux-iso-updater:latest

# Inside the container, run the script manually:
python /app/linux_iso_torrent_updater.py --dry-run
python /app/linux_iso_torrent_updater.py --distro debian
```

## Portainer Integration

### Running in Portainer

Portainer provides a web UI for managing Docker containers, making it easy to deploy and manage the Linux ISO Updater.

#### Method 1: Using Docker Compose Stack (Recommended)

1. **In Portainer, go to:** Stacks → Add stack
2. **Name your stack:** `linux-iso-updater`
3. **Paste the docker-compose.yml content** or use the Web editor
4. **Add environment variables** in the "Environment variables" section:
   ```
   TRANSMISSION_HOST=your-transmission-host
   TRANSMISSION_PORT=9091
   TRANSMISSION_USER=your-username
   TRANSMISSION_PASS=your-password
   SCHEDULE_ENABLED=true
   SCHEDULE_FREQUENCY=1d
   SCHEDULE_TIME=02:00
   SELECT_DISTROS=debian,ubuntu,arch,fedora,mint,rocky
   WEB_PORT=8084
   ```
5. **Deploy the stack**

#### Method 2: Using .env File Upload

1. **Create your .env file locally** with your credentials:
   ```bash
   TRANSMISSION_HOST=localhost
   TRANSMISSION_PORT=9091
   TRANSMISSION_USER=your-username
   TRANSMISSION_PASS=your-password
   SCHEDULE_ENABLED=true
   SCHEDULE_FREQUENCY=1d
   SCHEDULE_TIME=02:00
   SELECT_DISTROS=debian,ubuntu,arch
   ```

2. **In Portainer:**
   - Go to: Stacks → Add stack
   - Upload your docker-compose.yml
   - Under "Upload a .env file", upload your .env file
   - Deploy the stack

#### Method 3: Using Portainer Environment Variables

**Docker Compose for Portainer:**

```yaml
version: '3.8'

services:
  web-interface:
    image: ghcr.io/githuba42r/linux-iso-updater:latest
    container_name: linux-iso-updater-web
    ports:
      - "${WEB_PORT:-8084}:8084"
    environment:
      - TRANSMISSION_HOST=${TRANSMISSION_HOST:-localhost}
      - TRANSMISSION_PORT=${TRANSMISSION_PORT:-9091}
      - TRANSMISSION_USER=${TRANSMISSION_USER}
      - TRANSMISSION_PASS=${TRANSMISSION_PASS}
      - SCHEDULE_ENABLED=${SCHEDULE_ENABLED:-true}
      - SCHEDULE_FREQUENCY=${SCHEDULE_FREQUENCY:-1d}
      - SCHEDULE_TIME=${SCHEDULE_TIME:-02:00}
      - SELECT_DISTROS=${SELECT_DISTROS:-debian,ubuntu,arch,fedora,mint,rocky}
    restart: unless-stopped
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 256M
```

**Then in Portainer's Stack environment variables, add:**
- `TRANSMISSION_HOST` = `your-transmission-host`
- `TRANSMISSION_PORT` = `9091`
- `TRANSMISSION_USER` = `your-username`
- `TRANSMISSION_PASS` = `your-password`
- `SCHEDULE_ENABLED` = `true`
- `SCHEDULE_FREQUENCY` = `1d`
- `SCHEDULE_TIME` = `02:00`
- `WEB_PORT` = `8084`

### Accessing the Web Interface in Portainer

After deployment:
1. Go to **Containers** in Portainer
2. Find `linux-iso-updater-web`
3. Click on the port **8084** link (if published)
4. Or access directly: `http://your-server-ip:8084`

### Managing the Container in Portainer

**View Logs:**
1. Go to Containers → linux-iso-updater-web
2. Click "Logs" tab
3. Enable "Auto-refresh" for real-time logs

**Restart Container:**
1. Go to Containers → linux-iso-updater-web
2. Click "Restart" button

**Update Container:**
1. Go to Stacks → linux-iso-updater
2. Click "Editor"
3. Click "Pull and redeploy"
4. Or use "Update the stack" to change configuration

**Environment Variables:**
1. Go to Stacks → linux-iso-updater
2. Click "Editor"
3. Modify environment variables
4. Click "Update the stack"

### Portainer Tips

**Network Mode:**
- If Transmission is on the same Docker host, use `network_mode: host` in your compose file
- If Transmission is in another container, use a shared network or set `TRANSMISSION_HOST` to the container name

**Accessing Local Transmission:**
```yaml
services:
  web-interface:
    # For local Transmission, use host network
    network_mode: host
    # OR
    # Use bridge network and set TRANSMISSION_HOST to host.docker.internal
    extra_hosts:
      - "host.docker.internal:host-gateway"
    environment:
      - TRANSMISSION_HOST=host.docker.internal
```

**Volume Persistence (optional):**
```yaml
services:
  web-interface:
    volumes:
      # Persist logs
      - ./logs:/logs
    environment:
      - LOG_FILE=/logs/updater.log
```

**Scheduled Updates in Portainer:**
1. Enable automatic scheduling in the web interface (port 8084)
2. Or use Portainer's webhook feature for external triggering
3. The container will handle scheduling internally based on `SCHEDULE_FREQUENCY`

### Portainer Webhook Integration

To trigger updates via Portainer webhooks:

1. **Enable webhook in Portainer:**
   - Go to Containers → linux-iso-updater-web
   - Click "Duplicate/Edit"
   - Scroll to "Webhook"
   - Enable webhook and copy the URL

2. **Trigger updates externally:**
   ```bash
   # Restart container via webhook (triggers check on startup)
   curl -X POST https://your-portainer-url/api/webhooks/your-webhook-id
   ```

### Troubleshooting in Portainer

**Container won't start:**
1. Check logs in Portainer: Containers → linux-iso-updater-web → Logs
2. Verify environment variables are set correctly
3. Check that Transmission is accessible from the container

**Can't access web interface:**
1. Verify port 8084 is published: Containers → linux-iso-updater-web → "Published Ports"
2. Check firewall rules on your server
3. Try accessing via server IP: `http://server-ip:8084`

**Transmission connection failed:**
1. Check `TRANSMISSION_HOST` - use container name if Transmission is in Docker
2. Check `TRANSMISSION_PORT` - default is 9091
3. Verify credentials are correct
4. Check network mode (host vs bridge)

## Systemd Integration

### Setup

```bash
# 1. Build the image
./build.sh

# 2. Create credentials file
sudo mkdir -p /etc/linux-iso-updater
sudo cp .env.example /etc/linux-iso-updater/credentials.env
sudo nano /etc/linux-iso-updater/credentials.env
sudo chmod 600 /etc/linux-iso-updater/credentials.env

# 3. Install systemd units
sudo cp linux-iso-updater.service /etc/systemd/system/
sudo cp linux-iso-updater.timer /etc/systemd/system/
sudo systemctl daemon-reload

# 4. Enable and start
sudo systemctl enable linux-iso-updater.timer
sudo systemctl start linux-iso-updater.timer
```

### Management

```bash
# Check timer status
sudo systemctl status linux-iso-updater.timer
sudo systemctl list-timers | grep linux-iso

# Check service status
sudo systemctl status linux-iso-updater.service

# View logs
sudo journalctl -u linux-iso-updater.service -f
sudo journalctl -u linux-iso-updater.service --since "1 hour ago"

# Manually trigger
sudo systemctl start linux-iso-updater.service

# Stop timer
sudo systemctl stop linux-iso-updater.timer

# Disable timer
sudo systemctl disable linux-iso-updater.timer
```

## Docker Compose

### Basic Usage

```bash
# Run once
docker-compose up

# Run in background (not recommended for one-shot tasks)
docker-compose up -d

# View logs
docker-compose logs -f

# Rebuild and run
docker-compose up --build

# Stop and remove containers
docker-compose down
```

### Environment Configuration

Docker containers are isolated and don't have access to host files by default. Here's how to pass configuration:

#### Using --env-file (Recommended)

Create a `.env` file and pass it to the container:

```bash
# Create .env file
cat > .env <<EOF
TRANSMISSION_HOST=localhost
TRANSMISSION_PORT=9091
TRANSMISSION_USER=myuser
TRANSMISSION_PASS=mypass
DISTROS=debian,ubuntu,raspberrypi
LOG_FILE=/logs/iso-updater.log
EOF

# Secure the file
chmod 600 .env

# Run with env file
docker run --rm --network host --env-file .env \
  linux-iso-updater:latest --dry-run
```

#### Using Individual Environment Variables

```bash
docker run --rm --network host \
  -e TRANSMISSION_HOST=localhost \
  -e TRANSMISSION_PORT=9091 \
  -e TRANSMISSION_USER=myuser \
  -e TRANSMISSION_PASS=mypass \
  -e DISTROS=debian,ubuntu \
  linux-iso-updater:latest --dry-run
```

#### Mounting .env Files into the Container

Mount a .env file from host into the container:

```bash
# The script will automatically load .env files from /app/
docker run --rm --network host \
  -v "$(pwd)/.env:/app/.env:ro" \
  linux-iso-updater:latest --dry-run

# Mount .env.local for local overrides
docker run --rm --network host \
  -v "$(pwd)/.env:/app/.env:ro" \
  -v "$(pwd)/.env.local:/app/.env.local:ro" \
  linux-iso-updater:latest --dry-run
```

#### Mounting config.json

Use JSON configuration instead of .env:

```bash
# Create config.json
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

# Mount config directory into container
docker run --rm --network host \
  -v ~/.config/linux-iso-updater:/root/.config/linux-iso-updater:ro \
  linux-iso-updater:latest --dry-run
```

#### Logging to Host Filesystem

Write logs to a file on your host:

```bash
# Create log directory
mkdir -p ~/logs

# Method 1: Using LOG_FILE environment variable
docker run --rm --network host \
  --env-file .env \
  -e LOG_FILE=/logs/iso-updater.log \
  -v ~/logs:/logs \
  linux-iso-updater:latest

# Method 2: Using --log-file argument
docker run --rm --network host \
  --env-file .env \
  -v ~/logs:/logs \
  linux-iso-updater:latest --log-file /logs/iso-updater.log --dry-run

# View logs on host
tail -f ~/logs/iso-updater.log
```

#### Docker Compose Configuration

**Option 1: Using env_file in docker-compose.yml**

```yaml
version: '3.8'
services:
  linux-iso-updater:
    image: linux-iso-updater:latest
    network_mode: host
    env_file:
      - .env
    # Optional: override specific variables
    environment:
      - DISTROS=debian,ubuntu,raspberrypi
```

**Option 2: Using volumes for .env files**

```yaml
version: '3.8'
services:
  linux-iso-updater:
    image: linux-iso-updater:latest
    network_mode: host
    volumes:
      - ./.env:/app/.env:ro
      - ./.env.local:/app/.env.local:ro
```

**Option 3: Using volumes for config.json**

```yaml
version: '3.8'
services:
  linux-iso-updater:
    image: linux-iso-updater:latest
    network_mode: host
    volumes:
      - ~/.config/linux-iso-updater:/root/.config/linux-iso-updater:ro
```

**Option 4: With logging to host**

```yaml
version: '3.8'
services:
  linux-iso-updater:
    image: linux-iso-updater:latest
    network_mode: host
    env_file:
      - .env
    environment:
      - LOG_FILE=/logs/iso-updater.log
    volumes:
      - ./logs:/logs
    command: ["--dry-run"]
```

#### Configuration Priority

When multiple configuration sources are present:

1. **Command-line arguments** (highest priority)
   - `--distro debian`
   - `--log-file /logs/file.log`

2. **Environment variables from `-e`**
   - `docker run -e DISTROS=debian`

3. **Environment variables from `--env-file`**
   - `docker run --env-file .env`

4. **Mounted `.env` files in container**
   - Priority: `.env.local` → `.env.development` → `.env`

5. **Mounted `config.json`**
   - `~/.config/linux-iso-updater/config.json`

6. **Default values** (lowest priority)

#### Security Best Practices

```bash
# ✅ DO: Use read-only mounts for sensitive files
docker run --rm --network host \
  -v "$(pwd)/.env:/app/.env:ro" \
  linux-iso-updater:latest

# ✅ DO: Restrict file permissions
chmod 600 .env
chmod 600 ~/.config/linux-iso-updater/config.json

# ✅ DO: Use a separate credentials file for Docker
cp .env.example .env.docker
nano .env.docker
docker run --rm --network host --env-file .env.docker linux-iso-updater:latest

# ❌ DON'T: Commit .env files with real credentials
# ❌ DON'T: Use world-readable permissions
# ❌ DON'T: Include credentials in docker-compose.yml
```

#### Complete Example: Production Setup

```bash
# 1. Create secure credentials file
sudo mkdir -p /etc/linux-iso-updater
sudo cat > /etc/linux-iso-updater/credentials.env <<EOF
TRANSMISSION_HOST=localhost
TRANSMISSION_PORT=9091
TRANSMISSION_USER=transmission_user
TRANSMISSION_PASS=secure_password_here
DISTROS=debian,ubuntu,arch,raspberrypi
EOF
sudo chmod 600 /etc/linux-iso-updater/credentials.env
sudo chown root:root /etc/linux-iso-updater/credentials.env

# 2. Create log directory
sudo mkdir -p /var/log/linux-iso-updater
sudo chmod 755 /var/log/linux-iso-updater

# 3. Test with dry-run
sudo docker run --rm \
  --network host \
  --env-file /etc/linux-iso-updater/credentials.env \
  -v /var/log/linux-iso-updater:/logs \
  -e LOG_FILE=/logs/updater.log \
  linux-iso-updater:latest --dry-run

# 4. Run for real
sudo docker run --rm \
  --network host \
  --env-file /etc/linux-iso-updater/credentials.env \
  -v /var/log/linux-iso-updater:/logs \
  -e LOG_FILE=/logs/updater.log \
  linux-iso-updater:latest

# 5. Check logs
sudo tail -f /var/log/linux-iso-updater/updater.log
```

### Environment Configuration

The project supports multiple `.env` files for different environments:

#### For Development

```bash
# Use development configuration
cp .env.development.example .env.development
nano .env.development

# Run with development settings
docker run --rm --network host --env-file .env.development linux-iso-updater:latest
```

#### For Local Testing

```bash
# Create local configuration (never committed)
cp .env.local.example .env.local
nano .env.local

# Run with local settings
docker run --rm --network host --env-file .env.local linux-iso-updater:latest
```

#### For Production/Docker Compose

```bash
# Use standard .env file
cp .env.example .env
nano .env

# Run with docker-compose (automatically uses .env)
docker-compose up
```

#### Environment File Priority

When using docker-compose, you can specify multiple env files:

```yaml
# docker-compose.override.yml
services:
  linux-iso-updater:
    env_file:
      - .env                # Base configuration
      - .env.development    # Development overrides
      - .env.local          # Local overrides (highest priority)
```

**Note:** The Python script automatically loads `.env`, `.env.development`, and `.env.local` files when running natively, but Docker requires explicit `--env-file` or `env_file` configuration.

## Maintenance

### Update the Image

```bash
# After modifying the Python script
./build.sh

# Restart systemd service (if using)
sudo systemctl restart linux-iso-updater.service
```

### View Container Logs

```bash
# List recent containers
docker ps -a | grep linux-iso-updater

# View logs from last run
docker logs linux-iso-updater

# View systemd logs
sudo journalctl -u linux-iso-updater.service -n 50
```

### Cleanup

```bash
# Remove old images
docker rmi linux-iso-updater:latest

# Clean up Docker system
docker system prune -a

# Remove stopped containers
docker container prune
```

## Troubleshooting

### Check if Image Exists

```bash
docker images | grep linux-iso-updater
```

### Test Container Network Access

```bash
# Test if container can reach Transmission
docker run --rm --network host alpine ping -c 3 localhost

# Test HTTP access to Transmission RPC
docker run --rm --network host curlimages/curl:latest \
  curl -v http://localhost:9091/transmission/rpc
```

### Inspect Container

```bash
# View container details
docker inspect linux-iso-updater

# Check container environment
docker run --rm --network host --env-file .env \
  linux-iso-updater:latest env
```

### Common Issues

1. **"Cannot connect to Docker daemon"**
   ```bash
   sudo systemctl start docker
   sudo usermod -aG docker $USER
   # Log out and back in
   ```

2. **"Permission denied" accessing .env**
   ```bash
   chmod 644 .env
   ```

3. **Container exits immediately**
   ```bash
   # Check logs
   docker logs linux-iso-updater
   
   # Run interactively to see errors
   docker run -it --rm --network host --env-file .env \
     linux-iso-updater:latest
   ```

4. **Cannot connect to Transmission**
   ```bash
   # Verify Transmission is running
   curl http://localhost:9091/transmission/rpc
   
   # Check if using correct network mode
   # Use --network host for localhost access
   ```

## Advanced Configuration

### Custom Network

If Transmission is in a Docker container:

```bash
# Create a network
docker network create transmission-network

# Run Transmission (example)
docker run -d --name transmission \
  --network transmission-network \
  linuxserver/transmission

# Run updater with custom network
docker run --rm \
  --network transmission-network \
  -e TRANSMISSION_HOST=transmission \
  -e TRANSMISSION_PORT=9091 \
  -e TRANSMISSION_USER=admin \
  -e TRANSMISSION_PASS=password \
  linux-iso-updater:latest
```

### Resource Limits

```bash
# Limit CPU and memory
docker run --rm --network host --env-file .env \
  --cpus="1.0" \
  --memory="512m" \
  linux-iso-updater:latest
```

### Pushing to Registry

```bash
# Tag for your registry
docker tag linux-iso-updater:latest myregistry.com/linux-iso-updater:latest

# Login to registry
docker login myregistry.com

# Push
docker push myregistry.com/linux-iso-updater:latest

# Update systemd service to use registry image
sudo nano /etc/systemd/system/linux-iso-updater.service
# Change image name to myregistry.com/linux-iso-updater:latest
```
