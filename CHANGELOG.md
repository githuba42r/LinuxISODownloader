# Changelog

All notable changes to the Linux ISO Torrent Updater project.

## [Unreleased]

### Added - Additional Distributions Support (2026-02-04)

- **9 New Linux Distributions**
  - Linux Mint (Cinnamon edition via LinuxTracker.org)
  - Fedora Workstation (official torrents)
  - Pop!_OS (LTS via LinuxTracker.org)
  - Rocky Linux (DVD via LinuxTracker.org)
  - AlmaLinux (DVD via LinuxTracker.org)
  - Manjaro (KDE edition via LinuxTracker.org)
  - elementary OS (stable via LinuxTracker.org)
  - Zorin OS (Core edition via LinuxTracker.org)
  - EndeavourOS (via LinuxTracker.org)
  - Total: 14 distributions now supported

- **Web Interface Enhancements**
  - Progress bar hover effects with lift animation and shadow
  - ETA (estimated time remaining) display for active downloads
  - Progress percentage tooltips on hover
  - Visual polish and improved UX

- **Bug Fixes**
  - Fixed torrent status showing "Unknown" by mapping status strings to integer codes
  - Fixed progress bars showing >100% by properly converting percentages
  - Fixed Rocky Linux finder (search query too specific)
  - Fixed Manjaro finder (removed incorrect x86_64 requirement)

- **Configuration Changes**
  - Renamed `SCHEDULE_DISTROS` to `SELECT_DISTROS` for clarity
  - Variable now controls default selections in web UI
  - Fixed global `scheduled_distros` initialization bug

### Added - Dry-Run Feature (2026-02-04)

- **Dry-run mode** (`--dry-run` / `-n` flag)
  - Preview actions without making changes to Transmission
  - See what torrents would be updated
  - Test configuration safely
  - No Transmission credentials required in dry-run mode
  
- **Distribution selection** (`--distro` / `-d` flag)
  - Update specific distribution only
  - Choices: centos, debian, ubuntu, arch, all
  - Useful for testing individual distributions

- **Command-line argument parsing**
  - argparse integration with help text
  - Examples in help output
  - Short and long option forms

### Added - Environment File Support (2026-02-04)

- **Multi-tier .env file loading**
  - `.env` - Base/production configuration
  - `.env.development` - Development overrides
  - `.env.local` - Personal/local overrides (highest priority)
  
- **python-dotenv integration**
  - Automatic loading of .env files
  - Priority-based override system
  - Logging of loaded files

- **Example environment files**
  - `.env.example` - Production template
  - `.env.development.example` - Development template
  - `.env.local.example` - Local template

- **Test utility** (`test_env.py`)
  - Validate environment configuration
  - Show which .env files are loaded
  - Display final configuration values
  - Mask passwords in output

### Documentation

- **DRY_RUN.md** - Complete dry-run mode guide
  - Usage examples
  - Use cases and workflows
  - Output interpretation
  - Best practices

- **DEVELOPMENT.md** - Development environment guide
  - Environment file setup
  - Development workflow
  - Testing strategies
  - IDE integration

- **ENV_FILES.md** - Environment files reference
  - File types and priorities
  - Security best practices
  - Troubleshooting guide
  - Configuration scenarios

### Changed

- Updated `linux_iso_torrent_updater.py`
  - Added `TransmissionTorrentManager` dry_run parameter
  - Modified connection logic to skip Transmission in dry-run
  - Enhanced logging with `[DRY-RUN]` prefixes
  - Added command-line argument parsing

- Updated `Dockerfile`
  - Modified ENTRYPOINT/CMD to support arguments
  - Copies .env files (except .env.local)
  - Removes accidental .env.local files

- Updated `docker-compose.yml`
  - Added command examples for dry-run
  - Documented distro selection options

- Updated `.gitignore`
  - Comprehensive Python patterns
  - Protects all .env.local variants
  - Includes IDE and testing artifacts

- Updated `.dockerignore`
  - Excludes .env.local from builds
  - Prevents secrets in images

- Updated `README.md`
  - Command-line options section
  - Dry-run mode documentation
  - Enhanced usage examples
  - Environment file loading priority

- Updated `DOCKER.md`
  - Dry-run examples with Docker
  - Command-line arguments table
  - Interactive debugging examples

## [1.0.0] - 2026-02-03

### Initial Release

- Automatic torrent detection for major Linux distributions
  - CentOS Stream 9
  - Debian (latest stable)
  - Ubuntu LTS
  - Arch Linux

- Transmission RPC integration
  - Add/remove torrents
  - Smart version detection
  - Duplicate handling

- Docker support
  - Dockerfile with Python venv
  - docker-compose.yml
  - Build script

- Systemd integration
  - Service unit file
  - Timer unit file
  - Daily execution by default

- Comprehensive documentation
  - README.md
  - DOCKER.md
  - PROJECT_STRUCTURE.md
  - SUMMARY.md

- Configuration options
  - JSON config file
  - Environment variables
  - Multiple config methods

---

## Version History

- **Unreleased** - Current development version
- **1.0.0** (2026-02-03) - Initial release

## Upgrade Notes

### From 1.0.0 to Current

No breaking changes. New features are fully backward compatible.

**Optional enhancements:**
- Install `python-dotenv` for .env file support: `pip install python-dotenv`
- Use `--dry-run` flag to test before running
- Create `.env.local` for personal configuration

**Docker users:**
- Rebuild image to get new features: `docker build -t linux-iso-updater:latest .`
- Add command arguments in docker-compose.yml or docker run

**Native users:**
- Update requirements: `pip install -r requirements.txt`
- Run with `--help` to see new options
