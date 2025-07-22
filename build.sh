#!/bin/bash
# build-backend.sh - Docker build script for Flask backend with attestations

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Parse arguments
PUSH=false
NO_CACHE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --push)
            PUSH=true
            shift
            ;;
        --no-cache)
            NO_CACHE=true
            shift
            ;;
        --help)
            echo "Usage: $0 [options]"
            echo "Options:"
            echo "  --push         Push to Docker Hub after build"
            echo "  --no-cache     Build without cache"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Get version from VERSION file
VERSION=$(cat VERSION)
echo -e "${GREEN}Building backend version: $VERSION${NC}"

# Docker image details
DOCKER_HUB_ORG="watkinslabs"
IMAGE_NAME="temuragi_backend"

# Check for docker buildx
if ! docker buildx version > /dev/null 2>&1; then
    echo -e "${RED}Docker buildx not found. Please install docker buildx plugin.${NC}"
    exit 1
fi

# Setup buildx builder
BUILDER_NAME="temuragi-builder"
if ! docker buildx ls | grep -q "^${BUILDER_NAME}"; then
    echo -e "${BLUE}Creating buildx builder: ${BUILDER_NAME}${NC}"
    docker buildx create --name ${BUILDER_NAME} --driver docker-container --bootstrap
fi

# Use the builder
docker buildx use ${BUILDER_NAME}

# Build arguments
BUILD_ARGS=""
if [ "$NO_CACHE" = true ]; then
    BUILD_ARGS="--no-cache"
fi

# Platform args - x86_64 only
PLATFORMS="linux/amd64"

# Build backend image with attestations
echo -e "${BLUE}Building Flask backend image with attestations: $DOCKER_HUB_ORG/$IMAGE_NAME:$VERSION${NC}"

if [ "$PUSH" = true ]; then
    # Login check
    if ! docker info 2>/dev/null | grep -q "Username"; then
        echo -e "${YELLOW}Not logged into Docker Hub. Please run: docker login${NC}"
        exit 1
    fi
    
    # Build and push in one command with buildx
    docker buildx build $BUILD_ARGS \
        --platform ${PLATFORMS} \
        --provenance=true \
        --sbom=true \
        --build-arg VERSION=$VERSION \
        -f Dockerfile \
        -t $DOCKER_HUB_ORG/$IMAGE_NAME:$VERSION \
        -t $DOCKER_HUB_ORG/$IMAGE_NAME:latest \
        --push \
        .
    
    echo -e "${GREEN}Built and pushed successfully with attestations!${NC}"
else
    # Build locally without push (single platform)
    docker buildx build $BUILD_ARGS \
        --provenance=true \
        --sbom=true \
        --build-arg VERSION=$VERSION \
        -f Dockerfile \
        -t $DOCKER_HUB_ORG/$IMAGE_NAME:$VERSION \
        -t $DOCKER_HUB_ORG/$IMAGE_NAME:latest \
        .
    
    echo -e "${BLUE}Build complete. Use --push to push to Docker Hub${NC}"
fi

# Summary
echo -e "${GREEN}Build complete! Version $VERSION${NC}"
echo "Image built: $DOCKER_HUB_ORG/$IMAGE_NAME:$VERSION"
echo ""
echo "To inspect attestations:"
echo "  docker buildx imagetools inspect $DOCKER_HUB_ORG/$IMAGE_NAME:$VERSION --format '{{ json .SBOM }}'"
echo "  docker buildx imagetools inspect $DOCKER_HUB_ORG/$IMAGE_NAME:$VERSION --format '{{ json .Provenance }}'"
echo ""
echo "To run locally:"
echo "  docker run -p 5000:5000 -e DATABASE_URL=postgresql://user:pass@host/db $DOCKER_HUB_ORG/$IMAGE_NAME:$VERSION"