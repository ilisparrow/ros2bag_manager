#!/bin/bash

# Build Tauri application using Docker container
# This avoids installing system dependencies

echo "Building Tauri application in Docker container..."

# Build the Docker image
docker build -t tauri-builder -f Dockerfile.tauri-build .

# Run the build in the container and copy output
docker run --rm -v $(pwd):/app -v tauri-cache:/root/.cargo tauri-builder

echo ""
echo "Build complete! Packages are in:"
echo "  - src-tauri/target/release/bundle/deb/"
echo "  - src-tauri/target/release/bundle/appimage/"
