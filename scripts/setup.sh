#!/bin/bash
set -e

echo "🚀 Setting up Omarchy MCP Server (v3.4.2)..."

# Create directories
mkdir -p data/processed/omarchy
mkdir -p data/processed/omarchy_releases
mkdir -p data/raw/archwiki
mkdir -p data/raw/hyprland
mkdir -p data/raw/omarchy
mkdir -p data/raw/omarchy_releases

# Restore Omarchy from committed snapshot if available. The snapshot preserves
# the exact docs of the pinned version even if the upstream website drifts
# later. Arch + Hyprland are always re-downloaded fresh further down.
PINNED_VERSION=$(grep -E '^VERSION=' scripts/create_snapshot.sh | cut -d'"' -f2)
SNAPSHOT_DIR="data/snapshots/omarchy-${PINNED_VERSION}-processed"
RESTORED_FROM_SNAPSHOT=false

if [ -d "$SNAPSHOT_DIR" ]; then
    echo "📦 Restoring Omarchy v${PINNED_VERSION} docs from snapshot..."
    cp "$SNAPSHOT_DIR"/manual_*.json data/processed/omarchy/ 2>/dev/null || true
    for f in "$SNAPSHOT_DIR"/[0-9]*.json; do
        [ -e "$f" ] && cp "$f" data/processed/omarchy_releases/
    done
    manual_count=$(ls data/processed/omarchy/manual_*.json 2>/dev/null | wc -l)
    release_count=$(ls data/processed/omarchy_releases/*.json 2>/dev/null | wc -l)
    echo "  ✅ Restored $manual_count manual pages + $release_count release-note files"
    RESTORED_FROM_SNAPSHOT=true
else
    echo "⚠️  No snapshot at $SNAPSHOT_DIR — downloading Omarchy docs live"
    echo "📥 Downloading Omarchy documentation..."
    ./scripts/3_download_omarchy.sh
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

echo "🧹 Cleaning Arch & Hyprland documentation..."
docker exec omarchy-mcp-server python scripts/4_clean_archwiki.py
docker exec omarchy-mcp-server python scripts/5_clean_hyprland.py

if [ "$RESTORED_FROM_SNAPSHOT" = false ]; then
    echo "📥 Downloading Omarchy release notes..."
    docker exec omarchy-mcp-server python scripts/8_download_omarchy_releases.py
    echo "🧹 Cleaning Omarchy documentation..."
    docker exec omarchy-mcp-server python scripts/6_clean_omarchy.py
    docker exec omarchy-mcp-server python scripts/9_clean_omarchy_releases.py
fi

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
