#!/bin/bash
set -e

echo "🚀 Setting up Omarchy MCP Server (v3.3.1)..."

# Create directories
mkdir -p data/processed/omarchy
mkdir -p data/raw/archwiki
mkdir -p data/raw/hyprland
mkdir -p data/raw/omarchy
mkdir -p data/raw/omarchy_releases

# Restore Omarchy v3.3.1 from snapshot
if [ -d "data/snapshots/omarchy-3.3.1-processed" ]; then
    echo "📦 Restoring Omarchy v3.3.1 docs..."
    cp -r data/snapshots/omarchy-3.3.1-processed/* data/processed/omarchy/
    echo "✅ Omarchy v3.3.1 docs restored"
else
    echo "❌ Error: Omarchy v3.3.1 snapshot not found!"
    exit 1
fi

# Build and start containers
echo "🐳 Building Docker containers..."
docker-compose build

echo "🚀 Starting services..."
docker-compose up -d

echo "⏳ Waiting for ChromaDB to start..."
sleep 10

# Download and process Arch & Hyprland docs
echo "📥 Downloading Arch & Hyprland documentation..."
./scripts/1_download_archwiki.sh
docker exec omarchy-mcp-server bash scripts/2_download_hyprland.sh

echo "📥 Downloading Omarchy release notes..."
docker exec omarchy-mcp-server python scripts/8_download_omarchy_releases.py

echo "🧹 Cleaning documentation..."
docker exec omarchy-mcp-server python scripts/4_clean_archwiki.py
docker exec omarchy-mcp-server python scripts/5_clean_hyprland.py
docker exec omarchy-mcp-server python scripts/9_clean_omarchy_releases.py

# Ingest everything
echo "📊 Ingesting to vector database (this takes ~3-4 minutes)..."
docker exec omarchy-mcp-server python scripts/7_ingest_to_chroma.py

echo ""
echo "✅ Setup complete!"
echo ""
echo "Add to ~/.cursor/mcp.json:"
echo '{'
echo '  "mcpServers": {'
echo '    "omarchy-kb": {'
echo '      "command": "docker",'
echo '      "args": ["exec", "-i", "omarchy-mcp-server", "python", "/app/mcp_server/main.py"]'
echo '    }'
echo '  }'
echo '}'
