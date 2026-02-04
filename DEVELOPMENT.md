# Development Guide

This guide explains how to set up and work with the Linux ISO Torrent Updater in a development environment.

## Environment Files

The project supports multiple environment files for different scenarios:

### File Priority (Native Execution)

When running the script natively, `.env` files are loaded in this order (later files override earlier ones):

1. `.env` - Base/production configuration (can be committed)
2. `.env.development` - Development-specific settings (can be committed)
3. `.env.local` - Personal local settings (**NEVER commit**)

### File Purpose

| File | Purpose | Commit? | Use Case |
|------|---------|---------|----------|
| `.env.example` | Template for production | ✅ Yes | Docker/production setup |
| `.env.development.example` | Template for development | ✅ Yes | Shared dev configuration |
| `.env.local.example` | Template for local | ✅ Yes | Personal setup guide |
| `.env` | Production config | ❌ No | Production/Docker |
| `.env.development` | Development config | ✅ Maybe | Team dev settings |
| `.env.local` | Local overrides | ❌ **NEVER** | Personal secrets |

## Development Setup

### 1. Clone and Install Dependencies

```bash
# Clone the repository
git clone <repository-url>
cd LinuxTorentDownloader

# Create a virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Set Up Development Environment

```bash
# Copy development environment template
cp .env.development.example .env.development

# Edit with development Transmission settings
nano .env.development
```

Example `.env.development`:
```bash
TRANSMISSION_HOST=localhost
TRANSMISSION_PORT=9091
TRANSMISSION_USER=dev_user
TRANSMISSION_PASS=dev_password
LOG_LEVEL=DEBUG
```

### 3. Set Up Local Overrides

```bash
# Copy local environment template
cp .env.local.example .env.local

# Edit with your personal settings
nano .env.local
```

Example `.env.local`:
```bash
TRANSMISSION_HOST=192.168.1.100
TRANSMISSION_PORT=9091
TRANSMISSION_USER=myusername
TRANSMISSION_PASS=mypassword
```

### 4. Verify Configuration

```bash
# Run the script to test
python linux_iso_torrent_updater.py

# Check which .env files were loaded (look at logs)
python linux_iso_torrent_updater.py 2>&1 | grep "Loaded environment"
```

## Development Workflow

### Running Locally

```bash
# With virtual environment
source venv/bin/activate
python linux_iso_torrent_updater.py

# Direct execution
./linux_iso_torrent_updater.py
```

### Testing with Docker

```bash
# Build the development image
docker build -t linux-iso-updater:dev .

# Run with .env.development
docker run --rm --network host \
  --env-file .env.development \
  linux-iso-updater:dev

# Run with .env.local (for personal testing)
docker run --rm --network host \
  --env-file .env.local \
  linux-iso-updater:dev
```

### Using docker-compose for Development

Create a `docker-compose.override.yml` for local development:

```yaml
version: '3.8'

services:
  linux-iso-updater:
    env_file:
      - .env.development
      - .env.local  # Override with local settings
    volumes:
      # Mount source for live development
      - ./linux_iso_torrent_updater.py:/app/linux_iso_torrent_updater.py:ro
```

Then run:
```bash
docker-compose -f docker-compose.yml -f docker-compose.override.yml up
```

## Testing Different Configurations

### Test with Different Transmission Instances

#### Development Server
`.env.development`:
```bash
TRANSMISSION_HOST=dev-server.local
TRANSMISSION_PORT=9091
```

#### Local Test Server
`.env.local`:
```bash
TRANSMISSION_HOST=localhost
TRANSMISSION_PORT=9092
```

#### Production Server (via .env)
`.env`:
```bash
TRANSMISSION_HOST=transmission.example.com
TRANSMISSION_PORT=9091
```

### Testing Specific Distributions

Modify the script temporarily to test one distribution:

```python
# In linux_iso_torrent_updater.py, main() function:
if __name__ == '__main__':
    # For testing specific distributions
    import sys
    if len(sys.argv) > 1:
        distro = sys.argv[1]
        manager.update_torrent(distro)
    else:
        manager.update_all_torrents()
```

Then run:
```bash
python linux_iso_torrent_updater.py debian
python linux_iso_torrent_updater.py ubuntu
```

## Debugging

### Enable Debug Logging

Add to your `.env.local`:
```bash
LOG_LEVEL=DEBUG
```

Then update the script to use it:
```python
# In linux_iso_torrent_updater.py
log_level = os.getenv('LOG_LEVEL', 'INFO')
logging.basicConfig(
    level=getattr(logging, log_level),
    # ... rest of config
)
```

### Check Environment Loading

```bash
# See which .env files are loaded
python linux_iso_torrent_updater.py 2>&1 | grep -E "Loaded|Loading"

# Print all environment variables
python -c "import os; from dotenv import load_dotenv; \
  load_dotenv('.env'); \
  load_dotenv('.env.development', override=True); \
  load_dotenv('.env.local', override=True); \
  print('HOST:', os.getenv('TRANSMISSION_HOST')); \
  print('PORT:', os.getenv('TRANSMISSION_PORT')); \
  print('USER:', os.getenv('TRANSMISSION_USER'))"
```

### Interactive Testing

```python
# Start Python interpreter
python

# Load environment
from dotenv import load_dotenv
load_dotenv('.env')
load_dotenv('.env.development', override=True)
load_dotenv('.env.local', override=True)

# Import and test
import os
from linux_iso_torrent_updater import TransmissionTorrentManager

config = {
    'host': os.getenv('TRANSMISSION_HOST'),
    'port': int(os.getenv('TRANSMISSION_PORT', '9091')),
    'username': os.getenv('TRANSMISSION_USER'),
    'password': os.getenv('TRANSMISSION_PASS')
}

manager = TransmissionTorrentManager(**config)
# Test individual functions
manager.update_torrent('debian')
```

## Best Practices

### 1. Never Commit Secrets

Always add sensitive files to `.gitignore`:
```gitignore
.env.local
.env.*.local
*.env.local
.env
config.json
credentials.env
```

### 2. Use .env.development for Team Settings

Share common development settings:
```bash
# .env.development (can be committed)
TRANSMISSION_HOST=dev.example.com
TRANSMISSION_PORT=9091
LOG_LEVEL=DEBUG
# Note: Use placeholder credentials
TRANSMISSION_USER=dev_user_placeholder
TRANSMISSION_PASS=see_env_local
```

### 3. Document Required Variables

In `.env.local.example`:
```bash
# REQUIRED: Your local Transmission credentials
TRANSMISSION_USER=your_username
TRANSMISSION_PASS=your_password

# OPTIONAL: Override development server
# TRANSMISSION_HOST=localhost
# TRANSMISSION_PORT=9091
```

### 4. Environment Validation

Add validation to catch configuration errors early:

```python
def validate_config(config):
    """Validate configuration is complete."""
    required = ['host', 'port', 'username', 'password']
    missing = [k for k in required if not config.get(k)]
    
    if missing:
        raise ValueError(f"Missing required config: {', '.join(missing)}")
    
    return config
```

## Common Development Tasks

### Add a New Distribution

1. Create a new finder class:
```python
class FedoraTorrentFinder(DistroTorrentFinder):
    def __init__(self):
        super().__init__("Fedora")
        self.base_url = "https://fedoraproject.org/..."
    
    def get_latest_torrent_url(self) -> Optional[str]:
        # Implementation
        pass
```

2. Register in `TransmissionTorrentManager`:
```python
self.distro_finders = {
    'centos': CentOSTorrentFinder(),
    'debian': DebianTorrentFinder(),
    'ubuntu': UbuntuTorrentFinder(),
    'arch': ArchTorrentFinder(),
    'fedora': FedoraTorrentFinder(),  # Add here
}
```

3. Test:
```bash
python linux_iso_torrent_updater.py fedora
```

### Update Dependencies

```bash
# Update requirements.txt
pip install --upgrade transmission-rpc requests beautifulsoup4 python-dotenv
pip freeze | grep -E "transmission-rpc|requests|beautifulsoup4|python-dotenv" > requirements.txt

# Rebuild Docker image
docker build -t linux-iso-updater:dev .
```

### Run Tests (if implemented)

```bash
# With pytest
pytest tests/

# With coverage
pytest --cov=linux_iso_torrent_updater tests/
```

## Troubleshooting Development Issues

### .env Files Not Loading

```bash
# Check if python-dotenv is installed
pip list | grep python-dotenv

# Verify file exists and is readable
ls -la .env*

# Check file permissions
chmod 644 .env.development
chmod 600 .env.local
```

### Configuration Priority Confusion

```bash
# Test configuration loading order
python -c "
from pathlib import Path
import os
from dotenv import load_dotenv

files = ['.env', '.env.development', '.env.local']
for f in files:
    if Path(f).exists():
        print(f'Loading: {f}')
        load_dotenv(f, override=True)

print(f'Final HOST: {os.getenv(\"TRANSMISSION_HOST\")}')
print(f'Final PORT: {os.getenv(\"TRANSMISSION_PORT\")}')
"
```

### Docker Environment Not Working

```bash
# Check what's in the container
docker run -it --rm --entrypoint /bin/bash linux-iso-updater:dev

# Inside container:
ls -la /app/
cat /app/.env 2>/dev/null || echo "No .env in container"
env | grep TRANSMISSION
```

## IDE Setup

### VS Code

Create `.vscode/launch.json`:
```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: Current File",
            "type": "python",
            "request": "launch",
            "program": "${file}",
            "console": "integratedTerminal",
            "envFile": "${workspaceFolder}/.env.local"
        }
    ]
}
```

### PyCharm

1. Go to Run → Edit Configurations
2. Add new Python configuration
3. Set environment file to `.env.local`
4. Enable "Load environment variables from file"

## Contributing

When contributing:

1. ✅ **DO** commit `.env.example`, `.env.development.example`, `.env.local.example`
2. ❌ **DON'T** commit `.env`, `.env.local`, or files with real credentials
3. ✅ **DO** document any new environment variables in example files
4. ✅ **DO** test with multiple environment configurations
5. ❌ **DON'T** hardcode credentials or server addresses

## Security Reminders

- 🔒 Always use `.env.local` for personal credentials
- 🔒 Review `.gitignore` before committing
- 🔒 Use `git status` to verify no sensitive files are staged
- 🔒 Consider using `git-secrets` or similar tools
- 🔒 Rotate credentials if accidentally committed

---

For more information, see:
- [README.md](README.md) - General documentation
- [DOCKER.md](DOCKER.md) - Docker-specific instructions
- [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) - Project layout
