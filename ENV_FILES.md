# Environment Files Guide

This document explains the environment file system used in the Linux ISO Torrent Updater.

## Overview

The project uses a multi-tier environment file system to support different deployment scenarios while keeping secrets secure.

## File Types

### Example Files (Templates - Committed to Git)

| File | Purpose | Contains |
|------|---------|----------|
| `.env.example` | Production template | Default values, placeholders |
| `.env.development.example` | Development template | Dev server settings, debug flags |
| `.env.local.example` | Local template | Instructions for local setup |

### Active Files (Never Committed - In .gitignore)

| File | Purpose | Priority | Commit? |
|------|---------|----------|---------|
| `.env` | Production config | Low | ❌ No |
| `.env.development` | Development config | Medium | ⚠️ Maybe* |
| `.env.local` | Personal config | **Highest** | ❌ **NEVER** |

\* `.env.development` can be committed if it contains no secrets (team-shared dev server addresses)

## Loading Priority

### Native Python Execution

Files are loaded in this order (later files override earlier):

```
1. .env                    (Base/Production)
   ↓ overridden by
2. .env.development        (Development)
   ↓ overridden by
3. .env.local              (Personal - Highest Priority)
   ↓ overridden by
4. System environment vars (CLI, shell exports)
```

### Docker Execution

Docker does NOT automatically load `.env` files from the filesystem. You must specify them:

```bash
# Single file
docker run --env-file .env.local ...

# docker-compose (uses .env by default)
docker-compose up

# docker-compose with multiple files
docker-compose --env-file .env --env-file .env.local up
```

## Use Cases

### Scenario 1: Developer Working Locally

```bash
# Setup
cp .env.development.example .env.development  # Team dev settings
cp .env.local.example .env.local              # Personal settings
nano .env.local                                # Add personal credentials

# Run
python linux_iso_torrent_updater.py           # Auto-loads all .env files
```

Result: Uses development server from `.env.development` but personal credentials from `.env.local`

### Scenario 2: Testing in Docker Locally

```bash
# Setup
cp .env.local.example .env.local
nano .env.local

# Run
docker run --rm --network host --env-file .env.local linux-iso-updater:latest
```

Result: Uses local configuration in Docker container

### Scenario 3: Production Deployment

```bash
# Setup
cp .env.example .env
nano .env  # Add production credentials

# Build and run
docker build -t linux-iso-updater:latest .
docker-compose up
```

Result: Uses production configuration

### Scenario 4: CI/CD Pipeline

```bash
# Use environment variables directly
docker run --rm \
  -e TRANSMISSION_HOST=transmission.prod.example.com \
  -e TRANSMISSION_PORT=9091 \
  -e TRANSMISSION_USER=$PROD_USER \
  -e TRANSMISSION_PASS=$PROD_PASS \
  linux-iso-updater:latest
```

Result: No `.env` files needed, all from environment

## File Contents

### .env.example (Production Template)

```bash
# Production Transmission settings
TRANSMISSION_HOST=localhost
TRANSMISSION_PORT=9091
TRANSMISSION_USER=your_username
TRANSMISSION_PASS=your_password
```

### .env.development.example (Development Template)

```bash
# Development Transmission server
TRANSMISSION_HOST=dev-transmission.local
TRANSMISSION_PORT=9091
TRANSMISSION_USER=dev_user
TRANSMISSION_PASS=dev_password

# Development flags
LOG_LEVEL=DEBUG
```

### .env.local.example (Local Template)

```bash
# Your personal Transmission instance
TRANSMISSION_HOST=localhost
TRANSMISSION_PORT=9091
TRANSMISSION_USER=myusername
TRANSMISSION_PASS=mypassword

# Personal settings
# LOG_LEVEL=INFO
```

## Best Practices

### ✅ DO

- Use `.env.local` for personal credentials
- Commit `.env.example`, `.env.development.example`, `.env.local.example`
- Document all variables in example files
- Keep secrets only in `.env.local`
- Use `.env.development` for shared dev server addresses
- Review `.gitignore` regularly

### ❌ DON'T

- Commit `.env.local` or `.env` with real credentials
- Put production secrets in `.env.development`
- Hardcode credentials in scripts
- Share `.env.local` files
- Remove files from `.gitignore`

## Security

### Committed Files (Safe)

These files contain NO secrets:
- `✅ .env.example` - Only placeholders
- `✅ .env.development.example` - Only placeholders
- `✅ .env.local.example` - Only placeholders

### Never Commit (Secrets)

These files may contain real credentials:
- `❌ .env` - May contain production secrets
- `❌ .env.local` - Contains personal secrets
- `❌ .env.*.local` - Any file matching this pattern

### If You Accidentally Commit Secrets

1. **Rotate the credentials immediately**
2. Remove from Git history:
   ```bash
   git filter-branch --force --index-filter \
     "git rm --cached --ignore-unmatch .env.local" \
     --prune-empty --tag-name-filter cat -- --all
   ```
3. Force push (if you have permission)
4. Notify your team

## Testing Configuration

Use the provided test script:

```bash
# Test which .env files are loaded
python test_env.py
```

Output shows:
- Which files exist
- Load order
- Final configuration values
- Validation results

## Troubleshooting

### .env Files Not Loading (Native)

```bash
# Check if python-dotenv is installed
pip list | grep python-dotenv

# Install if missing
pip install python-dotenv

# Verify files exist
ls -la .env*
```

### Docker Not Using .env Files

```bash
# .env files are NOT automatically mounted in Docker
# You must specify them:

# ❌ Wrong - .env.local inside container won't be found
docker run linux-iso-updater:latest

# ✅ Correct - pass environment variables
docker run --env-file .env.local linux-iso-updater:latest
```

### Configuration Not Taking Effect

Check the priority order:

```bash
# See what's loaded
python test_env.py

# Check specific file
cat .env.local

# Verify no typos in variable names
env | grep TRANSMISSION
```

### Wrong File Being Used

```bash
# Clear all .env files and start fresh
rm .env .env.development .env.local

# Copy only what you need
cp .env.local.example .env.local
nano .env.local

# Test
python test_env.py
```

## IDE Integration

### VS Code

Create `.vscode/settings.json`:
```json
{
    "python.envFile": "${workspaceFolder}/.env.local"
}
```

### PyCharm

1. Run → Edit Configurations
2. Environment → Environment variables
3. Enable "Load from file"
4. Select `.env.local`

## Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `TRANSMISSION_HOST` | Yes | `localhost` | Transmission server hostname |
| `TRANSMISSION_PORT` | Yes | `9091` | Transmission RPC port |
| `TRANSMISSION_USER` | Yes | - | Transmission username |
| `TRANSMISSION_PASS` | Yes | - | Transmission password |
| `LOG_LEVEL` | No | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |

## Quick Reference

```bash
# Setup for local development
cp .env.local.example .env.local
nano .env.local

# Test configuration
python test_env.py

# Run locally
python linux_iso_torrent_updater.py

# Run in Docker
docker run --rm --network host --env-file .env.local linux-iso-updater:latest

# Run with docker-compose
docker-compose up

# Check what's in git
git status --ignored
```

---

For more information:
- [DEVELOPMENT.md](DEVELOPMENT.md) - Development guide
- [README.md](README.md) - Main documentation
- [DOCKER.md](DOCKER.md) - Docker reference
