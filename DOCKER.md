# Docker Quick Reference

## Building the Image

```bash
# Build with default tag (latest)
./build.sh

# Build with custom tag
./build.sh v1.0

# Build manually
docker build -t linux-iso-updater:latest .
```

## Running the Container

### One-time Execution

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
| `--distro <name>` | `-d <name>` | Update specific distro (centos, debian, ubuntu, arch, all) |

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
