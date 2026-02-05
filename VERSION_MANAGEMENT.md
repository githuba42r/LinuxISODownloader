# Version Management

This document explains how to manage version numbers for the Linux ISO Torrent Updater.

## Version Files

The project tracks the version in two files:

1. **`VERSION`** - Plain text file with the version number (e.g., `v1.0.0`)
2. **`__version__.py`** - Python module that exports `__version__` variable

Both files must be kept in sync.

## Version Format

We use [Semantic Versioning](https://semver.org/):

```
vMAJOR.MINOR.PATCH

Examples:
  v1.0.0 - Initial release
  v1.0.1 - Patch (bug fix)
  v1.1.0 - Minor (new feature, backward compatible)
  v2.0.0 - Major (breaking change)
```

## Bumping the Version

### Using the Bump Script (Recommended)

The bump script supports npm-style version commands:

#### Automatic Version Bumping

```bash
# Patch version (bug fixes) - v1.0.0 → v1.0.1
./bump-version.sh patch

# Minor version (new features) - v1.0.0 → v1.1.0
./bump-version.sh minor

# Major version (breaking changes) - v1.0.0 → v2.0.0
./bump-version.sh major
```

#### Pre-release Versions

```bash
# Pre-patch (next patch as pre-release) - v1.0.0 → v1.0.1-alpha.0
./bump-version.sh prepatch

# Pre-minor (next minor as pre-release) - v1.0.0 → v1.1.0-alpha.0
./bump-version.sh preminor

# Pre-major (next major as pre-release) - v1.0.0 → v2.0.0-alpha.0
./bump-version.sh premajor

# Prerelease (bump prerelease number) - v1.0.1-alpha.0 → v1.0.1-alpha.1
./bump-version.sh prerelease
```

#### Custom Pre-release Identifiers

```bash
# Use 'beta' instead of 'alpha' - v1.0.0 → v1.0.1-beta.0
./bump-version.sh prepatch --preid=beta

# Use 'rc' (release candidate) - v1.0.0 → v1.1.0-rc.0
./bump-version.sh preminor --preid=rc
```

#### Explicit Version

```bash
# Set exact version
./bump-version.sh v1.5.0
./bump-version.sh v2.0.0-beta.3
```

The script will:
1. **Check for uncommitted changes** - Ensures git working directory is clean
2. **Parse the current version** from VERSION file
3. **Calculate the new version** based on the command
4. **Check for existing tags** - Prevents duplicate version tags
5. **Show the version change** and ask for confirmation
6. **Update both files** - VERSION and __version__.py
7. **Create a git commit** - Automatically commits the version files
8. **Create a git tag** - Creates an annotated tag with the new version
9. **Show next steps** for pushing and building Docker images

**Important**: The script requires a clean git working directory (no uncommitted changes).

### Version Bump Examples

| Current Version | Command | New Version |
|----------------|---------|-------------|
| v1.0.0 | `patch` | v1.0.1 |
| v1.0.0 | `minor` | v1.1.0 |
| v1.0.0 | `major` | v2.0.0 |
| v1.0.0 | `prepatch` | v1.0.1-alpha.0 |
| v1.0.0 | `prepatch --preid=beta` | v1.0.1-beta.0 |
| v1.0.1-alpha.0 | `prerelease` | v1.0.1-alpha.1 |
| v1.0.1-alpha.2 | `patch` | v1.0.1 (removes prerelease) |
| v1.0.0 | `v1.5.0` | v1.5.0 (explicit) |

### Manual Method

If you prefer to update manually:

```bash
# 1. Update VERSION file
echo "v1.0.1" > VERSION

# 2. Update __version__.py
cat > __version__.py << 'EOF'
"""Version information for Linux ISO Torrent Updater."""

__version__ = "v1.0.1"
EOF

# 3. Verify
cat VERSION
cat __version__.py
```

## Release Workflow

Complete workflow for creating a new release:

### 1. Ensure Clean Git State

```bash
# Check for uncommitted changes
git status

# Commit any pending work
git add .
git commit -m "Your changes"
```

The bump script will check for uncommitted changes and abort if found.

### 2. Update the Version

```bash
# Using automatic bump (recommended)
./bump-version.sh patch

# Or explicit version
./bump-version.sh v1.0.1
```

The script automatically:
- Updates VERSION and __version__.py
- Creates a git commit
- Creates a git tag

### 3. Update the Changelog (Optional)

If you maintain a CHANGELOG.md, update it before running the bump script:

```markdown
## [v1.0.1] - 2026-02-05

### Added
- New feature X
- New feature Y

### Fixed
- Bug fix A
- Bug fix B

### Changed
- Improvement C
```

Then commit the changelog before bumping:
```bash
git add CHANGELOG.md
git commit -m "Update changelog for v1.0.1"
./bump-version.sh patch
```

### 4. Push to Remote

```bash
# Push the commit and tag together
git push origin main
git push origin v1.0.1

# Or push all tags at once
git push origin main --tags
```

### 5. Build Docker Images

The build script automatically uses the version from the `VERSION` file:

```bash
# Build with version from VERSION file
./build.sh

# This creates:
#   - linux-iso-updater:v1.0.1
#   - linux-iso-updater:latest
#   - ghcr.io/githuba42r/linux-iso-updater:v1.0.1
#   - ghcr.io/githuba42r/linux-iso-updater:latest
```

Or build with a specific version:

```bash
# Build with custom tag
./build.sh v1.0.1
```

### 6. Push to Container Registry

```bash
# Login to GitHub Container Registry
echo $GITHUB_TOKEN | docker login ghcr.io -u YOUR_USERNAME --password-stdin

# Push versioned image
docker push ghcr.io/githuba42r/linux-iso-updater:v1.0.1

# Push latest tag
docker push ghcr.io/githuba42r/linux-iso-updater:latest
```

### 7. Create GitHub Release (Optional)

If using GitHub:

1. Go to your repository on GitHub
2. Click "Releases" → "Create a new release"
3. Select the tag `v1.0.1`
4. Add release notes (copy from CHANGELOG.md)
5. Attach any binaries if needed
6. Publish release

Or use GitHub CLI:

```bash
gh release create v1.0.1 \
  --title "Release v1.0.1" \
  --notes "See CHANGELOG.md for details"
```

## Version Checking

Users can check the version using the `--version` flag:

```bash
# CLI tool
python linux_iso_torrent_updater.py --version

# Web interface
python web_interface.py --version

# Docker
docker run --rm linux-iso-updater:latest --version
```

## Best Practices

### When to Bump

- **Patch (v1.0.X)**: Bug fixes, minor improvements, documentation updates
- **Minor (v1.X.0)**: New features that don't break existing functionality
- **Major (vX.0.0)**: Breaking changes, major refactors, API changes

### Version Synchronization

Always keep these in sync:
- ✅ `VERSION` file
- ✅ `__version__.py` file
- ✅ Git tag
- ✅ Docker image tag
- ✅ CHANGELOG.md (if maintained)

### Pre-release Versions

The script supports pre-release versions with automatic incrementing:

```bash
# Create first alpha pre-release - v1.0.0 → v1.0.1-alpha.0
./bump-version.sh prepatch

# Increment pre-release - v1.0.1-alpha.0 → v1.0.1-alpha.1
./bump-version.sh prerelease

# Continue incrementing - v1.0.1-alpha.1 → v1.0.1-alpha.2
./bump-version.sh prerelease

# Release the final version - v1.0.1-alpha.2 → v1.0.1
./bump-version.sh patch
```

**Common pre-release identifiers:**
- `alpha` - Early development, unstable
- `beta` - Feature complete, testing phase
- `rc` - Release candidate, final testing

**Example workflow:**
```bash
./bump-version.sh prepatch --preid=beta    # v1.0.0 → v1.0.1-beta.0
./bump-version.sh prerelease               # v1.0.1-beta.0 → v1.0.1-beta.1
./bump-version.sh prerelease               # v1.0.1-beta.1 → v1.0.1-beta.2
./bump-version.sh patch                    # v1.0.1-beta.2 → v1.0.1 (final)
```

## Troubleshooting

### Version Mismatch

If `VERSION` and `__version__.py` are out of sync:

```bash
# Check both files
cat VERSION
grep __version__ __version__.py

# Fix using bump-version.sh
./bump-version.sh v1.0.1
```

### Docker Image Not Using Correct Version

The `build.sh` script reads from `VERSION` file. If it's not working:

```bash
# Verify VERSION file exists and is readable
cat VERSION

# Build with explicit version
./build.sh v1.0.1

# Check built image
docker images | grep linux-iso-updater
```

### Git Tag Already Exists

If you need to move a tag:

```bash
# Delete local tag
git tag -d v1.0.1

# Delete remote tag
git push origin :refs/tags/v1.0.1

# Create new tag
git tag -a v1.0.1 -m "Release v1.0.1"
git push origin v1.0.1
```

## Automation (Optional)

You can automate version bumping in CI/CD:

### GitHub Actions Example

```yaml
name: Release

on:
  push:
    tags:
      - 'v*'

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Get version from tag
        id: version
        run: echo "VERSION=${GITHUB_REF#refs/tags/}" >> $GITHUB_OUTPUT
      
      - name: Build Docker image
        run: ./build.sh ${{ steps.version.outputs.VERSION }}
      
      - name: Login to GHCR
        run: echo "${{ secrets.GITHUB_TOKEN }}" | docker login ghcr.io -u ${{ github.actor }} --password-stdin
      
      - name: Push images
        run: |
          docker push ghcr.io/githuba42r/linux-iso-updater:${{ steps.version.outputs.VERSION }}
          docker push ghcr.io/githuba42r/linux-iso-updater:latest
```

## Quick Reference

```bash
# Check current version
cat VERSION

# Automatic version bumping (recommended)
./bump-version.sh patch     # Bug fixes: v1.0.0 → v1.0.1
./bump-version.sh minor     # New features: v1.0.0 → v1.1.0
./bump-version.sh major     # Breaking changes: v1.0.0 → v2.0.0

# Pre-release versions
./bump-version.sh prepatch  # v1.0.0 → v1.0.1-alpha.0
./bump-version.sh prerelease # v1.0.1-alpha.0 → v1.0.1-alpha.1

# Or explicit version
./bump-version.sh v1.5.0

# Commit and tag
git add VERSION __version__.py
git commit -m "Bump version to v1.0.1"
git tag -a v1.0.1 -m "Release v1.0.1"
git push origin main v1.0.1

# Build and push Docker
./build.sh
docker push ghcr.io/githuba42r/linux-iso-updater:v1.0.1
docker push ghcr.io/githuba42r/linux-iso-updater:latest
```
