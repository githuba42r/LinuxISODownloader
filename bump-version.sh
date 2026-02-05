#!/bin/bash
# Version bump script for Linux ISO Torrent Updater
# Supports npm-style version commands: major, minor, patch, premajor, preminor, prepatch, prerelease

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if git is available
if ! command -v git &> /dev/null; then
    echo -e "${RED}Error: git is not installed${NC}"
    exit 1
fi

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo -e "${RED}Error: Not in a git repository${NC}"
    exit 1
fi

# Check for uncommitted changes
if ! git diff-index --quiet HEAD -- 2>/dev/null; then
    echo -e "${RED}Error: You have uncommitted changes${NC}"
    echo ""
    echo "Please commit or stash your changes before bumping the version:"
    echo "  git status"
    echo ""
    git status --short
    echo ""
    exit 1
fi

# Check if there are untracked files that should be committed
UNTRACKED=$(git ls-files --others --exclude-standard)
if [ -n "$UNTRACKED" ]; then
    echo -e "${YELLOW}Warning: You have untracked files:${NC}"
    echo "$UNTRACKED"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborted."
        exit 1
    fi
fi

# Get current version
CURRENT_VERSION=$(cat VERSION | tr -d '[:space:]')
echo -e "${BLUE}Current version: $CURRENT_VERSION${NC}"

# Parse current version (remove 'v' prefix if present)
VERSION_NO_V="${CURRENT_VERSION#v}"

# Extract version components and prerelease info
if [[ "$VERSION_NO_V" =~ ^([0-9]+)\.([0-9]+)\.([0-9]+)(-([a-zA-Z0-9]+)\.?([0-9]+)?)?$ ]]; then
    MAJOR="${BASH_REMATCH[1]}"
    MINOR="${BASH_REMATCH[2]}"
    PATCH="${BASH_REMATCH[3]}"
    PRERELEASE_TYPE="${BASH_REMATCH[5]}"
    PRERELEASE_NUM="${BASH_REMATCH[6]:-0}"
else
    echo -e "${RED}Error: Cannot parse current version: $CURRENT_VERSION${NC}"
    exit 1
fi

# Function to show usage
show_usage() {
    echo ""
    echo "Usage: ./bump-version.sh <version_type|version>"
    echo ""
    echo "Version types (like npm version):"
    echo "  major           Bump major version (X.0.0)"
    echo "  minor           Bump minor version (x.Y.0)"
    echo "  patch           Bump patch version (x.y.Z)"
    echo "  premajor        Bump to next major pre-release (X.0.0-alpha.0)"
    echo "  preminor        Bump to next minor pre-release (x.Y.0-alpha.0)"
    echo "  prepatch        Bump to next patch pre-release (x.y.Z-alpha.0)"
    echo "  prerelease      Bump pre-release version (x.y.z-alpha.N)"
    echo ""
    echo "Or specify exact version:"
    echo "  ./bump-version.sh v1.2.3           # Exact version"
    echo "  ./bump-version.sh v2.0.0-beta.1    # Pre-release version"
    echo ""
    echo "Examples:"
    echo "  ./bump-version.sh patch            # v1.0.0 → v1.0.1"
    echo "  ./bump-version.sh minor            # v1.0.1 → v1.1.0"
    echo "  ./bump-version.sh major            # v1.1.0 → v2.0.0"
    echo "  ./bump-version.sh prepatch         # v1.0.0 → v1.0.1-alpha.0"
    echo "  ./bump-version.sh prerelease       # v1.0.1-alpha.0 → v1.0.1-alpha.1"
    echo "  ./bump-version.sh v1.5.0           # Explicit version"
    echo ""
    echo "Pre-release identifiers: alpha, beta, rc"
    echo "You can also use: --preid=<identifier> to specify pre-release type"
    echo "  ./bump-version.sh prepatch --preid=beta    # v1.0.0 → v1.0.1-beta.0"
    echo ""
    echo "Note: This script will automatically commit and tag the version bump."
    echo ""
}

# Check if version type provided
if [ -z "$1" ]; then
    show_usage
    exit 1
fi

VERSION_TYPE="$1"

# Check for --preid option
PREID="alpha"
if [ -n "$2" ] && [[ "$2" =~ ^--preid=(.+)$ ]]; then
    PREID="${BASH_REMATCH[1]}"
fi

# Calculate new version based on type
case "$VERSION_TYPE" in
    major)
        NEW_MAJOR=$((MAJOR + 1))
        NEW_MINOR=0
        NEW_PATCH=0
        NEW_VERSION="v${NEW_MAJOR}.${NEW_MINOR}.${NEW_PATCH}"
        ;;
    
    minor)
        NEW_MAJOR=$MAJOR
        NEW_MINOR=$((MINOR + 1))
        NEW_PATCH=0
        NEW_VERSION="v${NEW_MAJOR}.${NEW_MINOR}.${NEW_PATCH}"
        ;;
    
    patch)
        NEW_MAJOR=$MAJOR
        NEW_MINOR=$MINOR
        NEW_PATCH=$((PATCH + 1))
        NEW_VERSION="v${NEW_MAJOR}.${NEW_MINOR}.${NEW_PATCH}"
        ;;
    
    premajor)
        NEW_MAJOR=$((MAJOR + 1))
        NEW_MINOR=0
        NEW_PATCH=0
        NEW_VERSION="v${NEW_MAJOR}.${NEW_MINOR}.${NEW_PATCH}-${PREID}.0"
        ;;
    
    preminor)
        NEW_MAJOR=$MAJOR
        NEW_MINOR=$((MINOR + 1))
        NEW_PATCH=0
        NEW_VERSION="v${NEW_MAJOR}.${NEW_MINOR}.${NEW_PATCH}-${PREID}.0"
        ;;
    
    prepatch)
        NEW_MAJOR=$MAJOR
        NEW_MINOR=$MINOR
        NEW_PATCH=$((PATCH + 1))
        NEW_VERSION="v${NEW_MAJOR}.${NEW_MINOR}.${NEW_PATCH}-${PREID}.0"
        ;;
    
    prerelease)
        if [ -n "$PRERELEASE_TYPE" ]; then
            # Already a prerelease, increment the number
            NEW_PRERELEASE_NUM=$((PRERELEASE_NUM + 1))
            NEW_VERSION="v${MAJOR}.${MINOR}.${PATCH}-${PRERELEASE_TYPE}.${NEW_PRERELEASE_NUM}"
        else
            # Not a prerelease, create first prerelease for current version
            NEW_VERSION="v${MAJOR}.${MINOR}.${PATCH}-${PREID}.0"
        fi
        ;;
    
    v[0-9]*|[0-9]*)
        # Explicit version provided
        NEW_VERSION="$VERSION_TYPE"
        
        # Validate version format
        if [[ ! "$NEW_VERSION" =~ ^v?[0-9]+\.[0-9]+\.[0-9]+(-[a-zA-Z0-9]+(\.[0-9]+)?)?$ ]]; then
            echo -e "${RED}Error: Invalid version format. Use vX.Y.Z or X.Y.Z (e.g., v1.0.1, v1.0.0-alpha.1)${NC}"
            show_usage
            exit 1
        fi
        
        # Ensure version starts with 'v'
        if [[ ! "$NEW_VERSION" =~ ^v ]]; then
            NEW_VERSION="v$NEW_VERSION"
        fi
        ;;
    
    *)
        echo -e "${RED}Error: Unknown version type: $VERSION_TYPE${NC}"
        show_usage
        exit 1
        ;;
esac

echo -e "${GREEN}New version: $NEW_VERSION${NC}"
echo ""

# Check if tag already exists
if git rev-parse "$NEW_VERSION" >/dev/null 2>&1; then
    echo -e "${RED}Error: Git tag $NEW_VERSION already exists${NC}"
    echo ""
    echo "To remove the existing tag:"
    echo "  git tag -d $NEW_VERSION"
    echo "  git push origin :refs/tags/$NEW_VERSION  # If pushed to remote"
    echo ""
    exit 1
fi

# Confirm
read -p "Bump version from $CURRENT_VERSION to $NEW_VERSION and create git commit + tag? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 1
fi

echo ""
echo "Updating version files..."

# Update VERSION file
echo "$NEW_VERSION" > VERSION
echo "✓ Updated VERSION file"

# Update __version__.py
cat > __version__.py << EOF
"""Version information for Linux ISO Torrent Updater."""

__version__ = "$NEW_VERSION"
EOF
echo "✓ Updated __version__.py"

echo ""
echo "Creating git commit..."

# Stage the version files
git add VERSION __version__.py

# Commit the changes
COMMIT_MESSAGE="Bump version to $NEW_VERSION"
git commit -m "$COMMIT_MESSAGE"
echo -e "${GREEN}✓ Created commit: $COMMIT_MESSAGE${NC}"

echo ""
echo "Creating git tag..."

# Create annotated tag
git tag -a "$NEW_VERSION" -m "Release $NEW_VERSION"
echo -e "${GREEN}✓ Created tag: $NEW_VERSION${NC}"

echo ""
echo -e "${GREEN}Version bumped successfully to $NEW_VERSION${NC}"
echo ""
echo "Next steps:"
echo "  1. Review the commit and tag:"
echo "     git log -1"
echo "     git show $NEW_VERSION"
echo ""
echo "  2. Push to remote:"
echo "     git push origin main"
echo "     git push origin $NEW_VERSION"
echo ""
echo "  3. Build Docker image:"
echo "     ./build.sh"
echo ""
echo "  4. Push to registry:"
echo "     docker push ghcr.io/githuba42r/linux-iso-updater:$NEW_VERSION"
echo "     docker push ghcr.io/githuba42r/linux-iso-updater:latest"
echo ""
echo -e "${YELLOW}Note: Changes have been committed and tagged locally. Don't forget to push!${NC}"
