# Dry-Run Mode Guide

This guide explains how to use the dry-run feature to test the Linux ISO Torrent Updater without making any changes to your Transmission server.

## What is Dry-Run Mode?

Dry-run mode allows you to preview what the script would do without actually making any changes to Transmission. It's a safe way to:

- Test your configuration
- See what torrents would be updated
- Verify torrent URLs are found correctly
- Debug issues without affecting downloads
- Understand the script's behavior before running it for real

## How It Works

### What Dry-Run DOES:

✅ Searches distribution websites for latest torrent files  
✅ Downloads torrent metadata (to check versions)  
✅ Shows torrent URLs and hashes  
✅ Displays what actions would be taken  
✅ Reports existing torrents (if Transmission credentials provided)  
✅ Logs all operations with `[DRY-RUN]` prefix  

### What Dry-Run DOES NOT Do:

❌ Connect to Transmission (credentials optional in dry-run)  
❌ Add new torrents  
❌ Remove old torrents  
❌ Delete any files  
❌ Modify Transmission in any way  

## Usage Examples

### Native Python

```bash
# Dry-run for all distributions
python3 linux_iso_torrent_updater.py --dry-run

# Dry-run for specific distribution
python3 linux_iso_torrent_updater.py --dry-run --distro debian

# Short form
python3 linux_iso_torrent_updater.py -n -d ubuntu

# With environment variables
TRANSMISSION_USER=test TRANSMISSION_PASS=test \
  python3 linux_iso_torrent_updater.py --dry-run
```

### Docker

```bash
# Dry-run using docker run
docker run --rm --network host --env-file .env \
  linux-iso-updater:latest --dry-run

# Dry-run for specific distro
docker run --rm --network host --env-file .env \
  linux-iso-updater:latest --dry-run --distro arch

# Without credentials (OK for dry-run)
docker run --rm --network host \
  -e TRANSMISSION_HOST=localhost \
  -e TRANSMISSION_PORT=9091 \
  -e TRANSMISSION_USER=dummy \
  -e TRANSMISSION_PASS=dummy \
  linux-iso-updater:latest --dry-run
```

### Docker Compose

Edit `docker-compose.yml`:

```yaml
services:
  linux-iso-updater:
    # ... other settings ...
    command: ["--dry-run"]
```

Then run:

```bash
docker-compose up
```

## Example Output

### Dry-Run with No Existing Torrents

```
INFO - DRY-RUN MODE: No changes will be made to Transmission
INFO - Checking debian torrent...
INFO - Found Debian torrent: https://cdimage.debian.org/debian-cd/current/amd64/bt-dvd/debian-12.0.0-amd64-DVD-1.iso.torrent
INFO - [DRY-RUN] Found latest debian torrent URL: https://...
INFO - [DRY-RUN] Would search for existing debian torrent
INFO - [DRY-RUN] Downloaded torrent (hash: a1b2c3d4e5f6g7h8...)
INFO - [DRY-RUN] No existing debian torrent found
INFO - [DRY-RUN] Would add new torrent from https://cdimage.debian.org/...
INFO - [DRY-RUN] Torrent hash: a1b2c3d4e5f6g7h8...
```

### Dry-Run with Existing Torrents

```
INFO - DRY-RUN MODE: No changes will be made to Transmission
INFO - Checking ubuntu torrent...
INFO - Found Ubuntu torrent: https://releases.ubuntu.com/24.04/ubuntu-24.04-desktop-amd64.iso.torrent
INFO - [DRY-RUN] Found latest ubuntu torrent URL: https://...
INFO - Found existing ubuntu torrent: ubuntu-24.04-desktop-amd64.iso (ID: 42)
INFO - [DRY-RUN] Downloaded torrent (hash: 9z8y7x6w5v4u3t2s...)
INFO - [DRY-RUN] Existing ubuntu torrent found: ubuntu-24.04-desktop-amd64.iso
INFO - [DRY-RUN] Would check if new torrent is different
INFO - [DRY-RUN] Actions that would be taken:
INFO - [DRY-RUN]   1. Add new torrent from https://releases.ubuntu.com/...
INFO - [DRY-RUN]   2. If different, remove old torrent: ubuntu-24.04-desktop-amd64.iso (ID: 42)
INFO - [DRY-RUN]   3. Delete old torrent data
```

## Use Cases

### 1. Testing Configuration

Before running the script for the first time:

```bash
# Test if credentials work (optional in dry-run)
python3 linux_iso_torrent_updater.py --dry-run

# Check output for any errors
# Verify torrent URLs are found
# Confirm expected distributions are processed
```

### 2. Verifying Torrent URLs

Check if distribution websites are accessible and torrents exist:

```bash
# Try each distribution
python3 linux_iso_torrent_updater.py --dry-run --distro centos
python3 linux_iso_torrent_updater.py --dry-run --distro debian
python3 linux_iso_torrent_updater.py --dry-run --distro ubuntu
python3 linux_iso_torrent_updater.py --dry-run --distro arch
```

### 3. Debugging Issues

If the script isn't working as expected:

```bash
# Run in dry-run to see detailed output
python3 linux_iso_torrent_updater.py --dry-run 2>&1 | tee dry-run.log

# Review the log file
less dry-run.log

# Look for errors or unexpected behavior
grep ERROR dry-run.log
grep WARNING dry-run.log
```

### 4. Scheduled Dry-Run Tests

Set up a cron job or systemd timer to run dry-run periodically:

```bash
# Create a test timer that runs dry-run daily
sudo nano /etc/systemd/system/linux-iso-updater-test.service
```

```ini
[Unit]
Description=Linux ISO Torrent Updater (Dry-Run Test)

[Service]
Type=oneshot
ExecStart=/usr/bin/docker run --rm \
  --network host \
  --env-file /etc/linux-iso-updater/credentials.env \
  linux-iso-updater:latest --dry-run
```

### 5. Pre-deployment Validation

Before deploying to production:

```bash
# Test in staging environment
docker run --rm --network host \
  -e TRANSMISSION_HOST=staging-transmission.local \
  -e TRANSMISSION_USER=staging_user \
  -e TRANSMISSION_PASS=staging_pass \
  linux-iso-updater:latest --dry-run

# Verify expected behavior
# Then deploy to production without --dry-run
```

## Interpreting Dry-Run Output

### Success Indicators

Look for these patterns in the output:

```
✓ "DRY-RUN MODE: No changes will be made"
✓ "Found [distro] torrent: [URL]"
✓ "Downloaded torrent (hash: ...)"
✓ "[DRY-RUN] Would add/remove torrent"
```

### Warning Signs

Watch out for these issues:

```
⚠ "Could not find latest torrent for [distro]"
⚠ "Failed to download torrent from [URL]"
⚠ "Error finding existing torrent"
⚠ "Connection refused" (if checking existing torrents)
```

### Common Error Messages

| Error | Meaning | Solution |
|-------|---------|----------|
| `Could not find latest torrent` | Website structure changed | Update finder class |
| `Failed to download torrent` | Network issue or URL invalid | Check internet connection |
| `Connection refused` | Transmission not accessible | Check Transmission is running |
| `Authentication failed` | Wrong credentials | Verify username/password |

## Dry-Run vs Normal Mode Comparison

| Action | Dry-Run Mode | Normal Mode |
|--------|--------------|-------------|
| Search websites | ✅ Yes | ✅ Yes |
| Download torrents | ✅ Yes (metadata) | ✅ Yes |
| Connect to Transmission | ❌ No | ✅ Yes |
| Check existing torrents | ⚠️ Optional | ✅ Yes |
| Add new torrents | ❌ No | ✅ Yes |
| Remove old torrents | ❌ No | ✅ Yes |
| Requires credentials | ⚠️ Optional | ✅ Required |

## Best Practices

### 1. Always Dry-Run First

When making changes to the script or configuration:

```bash
# Test changes in dry-run mode first
python3 linux_iso_torrent_updater.py --dry-run

# If successful, run for real
python3 linux_iso_torrent_updater.py
```

### 2. Use Dry-Run in CI/CD

Include dry-run checks in your pipeline:

```yaml
# .github/workflows/test.yml
- name: Test Script
  run: |
    docker build -t linux-iso-updater:test .
    docker run --rm linux-iso-updater:test --dry-run
```

### 3. Document Dry-Run Results

Save dry-run output for troubleshooting:

```bash
# Run dry-run and save output
python3 linux_iso_torrent_updater.py --dry-run 2>&1 | \
  tee "dry-run-$(date +%Y%m%d-%H%M%S).log"
```

### 4. Combine with Specific Distributions

Test one distribution at a time:

```bash
# Test each distribution separately
for distro in centos debian ubuntu arch; do
  echo "Testing $distro..."
  python3 linux_iso_torrent_updater.py --dry-run --distro $distro
done
```

### 5. Use in Development

Keep dry-run as default during development:

```bash
# Add alias in ~/.bashrc
alias iso-updater-test='python3 /path/to/linux_iso_torrent_updater.py --dry-run'
alias iso-updater-run='python3 /path/to/linux_iso_torrent_updater.py'
```

## Troubleshooting Dry-Run

### Dry-Run Doesn't Show Existing Torrents

If you want to see what torrents would be replaced:

```bash
# Provide valid Transmission credentials
TRANSMISSION_USER=realuser TRANSMISSION_PASS=realpass \
  python3 linux_iso_torrent_updater.py --dry-run
```

Or just accept that existing torrents won't be checked:

```bash
# Dry-run without checking existing (uses dummy credentials)
python3 linux_iso_torrent_updater.py --dry-run
```

### Getting Connection Errors in Dry-Run

This is normal - dry-run doesn't require Transmission access:

```
WARNING - Transmission credentials not configured (OK for dry-run)
```

To suppress these warnings, provide dummy credentials:

```bash
TRANSMISSION_USER=test TRANSMISSION_PASS=test \
  python3 linux_iso_torrent_updater.py --dry-run
```

### Dry-Run Exits with Error

If dry-run exits with non-zero status:

```bash
# Check the error message
python3 linux_iso_torrent_updater.py --dry-run
echo "Exit code: $?"

# Run with verbose logging
LOG_LEVEL=DEBUG python3 linux_iso_torrent_updater.py --dry-run
```

## Integration Examples

### With Makefile

```makefile
.PHONY: dry-run run

dry-run:
	docker run --rm --network host --env-file .env \
		linux-iso-updater:latest --dry-run

run:
	docker run --rm --network host --env-file .env \
		linux-iso-updater:latest
```

### With Shell Script

```bash
#!/bin/bash
# update-isos.sh

set -e

echo "Running dry-run first..."
python3 linux_iso_torrent_updater.py --dry-run

read -p "Proceed with actual update? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Running update..."
    python3 linux_iso_torrent_updater.py
else
    echo "Cancelled."
    exit 1
fi
```

### With systemd (Test Service)

```ini
# /etc/systemd/system/linux-iso-updater-test.service
[Unit]
Description=Linux ISO Torrent Updater Test (Dry-Run)
After=network-online.target

[Service]
Type=oneshot
ExecStart=/usr/local/bin/linux_iso_torrent_updater.py --dry-run
```

## Summary

Dry-run mode is an essential feature for:

- 🧪 **Testing**: Verify configuration and behavior
- 🔍 **Debugging**: Identify issues without risk
- 📋 **Planning**: See what would happen before committing
- 🛡️ **Safety**: No accidental changes to production

**Always use dry-run when:**
- Running the script for the first time
- Testing configuration changes
- Debugging issues
- Validating in new environments
- You're unsure what will happen

**Example workflow:**
```bash
# 1. Test with dry-run
./linux_iso_torrent_updater.py --dry-run

# 2. Review output
# 3. If everything looks good, run for real
./linux_iso_torrent_updater.py
```

---

For more information:
- [README.md](README.md) - Main documentation
- [DOCKER.md](DOCKER.md) - Docker usage
- [DEVELOPMENT.md](DEVELOPMENT.md) - Development guide
