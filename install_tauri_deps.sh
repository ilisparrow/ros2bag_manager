#!/bin/bash

# Install Tauri build dependencies for Ubuntu/Debian
# These are required to compile the Tauri application

echo "Installing Tauri build dependencies..."

sudo apt update
sudo apt install -y \
    libwebkit2gtk-4.1-dev \
    build-essential \
    curl \
    wget \
    file \
    libxdo-dev \
    libssl-dev \
    libayatana-appindicator3-dev \
    librsvg2-dev \
    libgtk-3-dev

echo "Dependencies installed successfully!"
echo "You can now run: cargo tauri build"
