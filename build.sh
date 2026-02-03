#!/bin/bash
# Build script for Linux ISO Torrent Updater Docker image

set -e

IMAGE_NAME="linux-iso-updater"
IMAGE_TAG="${1:-latest}"
FULL_IMAGE_NAME="${IMAGE_NAME}:${IMAGE_TAG}"

echo "Building Docker image: ${FULL_IMAGE_NAME}"

# Build the image
docker build -t "${FULL_IMAGE_NAME}" .

echo ""
echo "Build completed successfully!"
echo ""
echo "To run the container:"
echo "  docker run --rm --network host --env-file .env ${FULL_IMAGE_NAME}"
echo ""
echo "To test with docker-compose:"
echo "  docker-compose up"
echo ""
echo "To push to a registry (optional):"
echo "  docker tag ${FULL_IMAGE_NAME} your-registry/${FULL_IMAGE_NAME}"
echo "  docker push your-registry/${FULL_IMAGE_NAME}"
