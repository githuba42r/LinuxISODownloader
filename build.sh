#!/bin/bash
# Build script for Linux ISO Torrent Updater Docker image

set -e

REGISTRY="ghcr.io/githuba42r"
IMAGE_NAME="linux-iso-updater"

# Read version from VERSION file if it exists, otherwise use argument or 'latest'
if [ -f "VERSION" ]; then
    VERSION=$(cat VERSION | tr -d '[:space:]')
    echo "Using version from VERSION file: ${VERSION}"
    IMAGE_TAG="${1:-${VERSION}}"
else
    IMAGE_TAG="${1:-latest}"
fi

LOCAL_IMAGE_NAME="${IMAGE_NAME}:${IMAGE_TAG}"
REGISTRY_IMAGE_NAME="${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"

echo "Building Docker image: ${LOCAL_IMAGE_NAME}"
echo ""

# Always build with version tag AND latest tag (unless IMAGE_TAG is already 'latest')
if [ "$IMAGE_TAG" != "latest" ]; then
    echo "Tagging as both ${IMAGE_TAG} and latest"
    docker build \
        -t "${LOCAL_IMAGE_NAME}" \
        -t "${REGISTRY_IMAGE_NAME}" \
        -t "${IMAGE_NAME}:latest" \
        -t "${REGISTRY}/${IMAGE_NAME}:latest" \
        .
else
    echo "Tagging as latest only"
    docker build \
        -t "${LOCAL_IMAGE_NAME}" \
        -t "${REGISTRY_IMAGE_NAME}" \
        .
fi

echo ""
echo "Build completed successfully!"
echo ""
echo "Images tagged:"
echo "  - ${LOCAL_IMAGE_NAME}"
echo "  - ${REGISTRY_IMAGE_NAME}"
if [ "$IMAGE_TAG" != "latest" ]; then
    echo "  - ${IMAGE_NAME}:latest"
    echo "  - ${REGISTRY}/${IMAGE_NAME}:latest"
fi
echo ""
echo "To run the container:"
echo "  docker run --rm --network host --env-file .env ${LOCAL_IMAGE_NAME}"
echo ""
echo "To test with docker-compose:"
echo "  docker-compose up"
echo ""
echo "To push to GitHub Container Registry:"
echo "  docker push ${REGISTRY_IMAGE_NAME}"
if [ "$IMAGE_TAG" != "latest" ]; then
    echo "  docker push ${REGISTRY}/${IMAGE_NAME}:latest"
fi
echo ""
echo "Note: Make sure you're logged in to GHCR first:"
echo "  echo \$GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin"
