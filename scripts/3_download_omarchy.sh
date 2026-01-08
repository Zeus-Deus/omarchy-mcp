#!/bin/bash
set -e

echo "📥 Downloading Omarchy documentation..."

# Ensure target directory exists
mkdir -p data/raw/omarchy
cd data/raw/omarchy

# Mirror the manual (full offline copy)
if [ ! -d "learn.omacom.io" ]; then
    echo "Downloading Omarchy manual..."
    wget -mkEpnp https://learn.omacom.io/2/the-omarchy-manual/
    echo "✅ Manual downloaded"
fi

# Mirror the main website
if [ ! -d "omarchy.org" ]; then
    echo "Downloading Omarchy website..."
    wget -mkEpnp https://omarchy.org/
    echo "✅ Website downloaded"
fi

# Download releases page (for changelog parsing)
if [ ! -f "releases.html" ]; then
    echo "Downloading releases page..."
    wget -O releases.html https://github.com/basecamp/omarchy/releases
    echo "✅ Releases page downloaded"
fi

# Clone the repo (configs, scripts, extra docs)
if [ ! -d "omarchy-repo" ]; then
    echo "Cloning Omarchy repository..."
    git clone https://github.com/basecamp/omarchy.git omarchy-repo
    echo "✅ Repository cloned"
else
    echo "⚠️  Repository exists, pulling updates..."
    cd omarchy-repo
    git pull
    cd ..
fi

echo "✅ All Omarchy docs downloaded to data/raw/omarchy/"
