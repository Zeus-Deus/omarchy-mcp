#!/bin/bash
set -e

# ============================================================
# Omarchy MCP Server - Version Upgrade Script
# ============================================================
# This script automates upgrading the MCP server to a new 
# Omarchy version. It updates version references and runs 
# the full data pipeline.
# ============================================================

show_usage() {
    echo "Usage: $0 <new_version>"
    echo ""
    echo "Example:"
    echo "  $0 3.4.0    # Upgrade to v3.4.0"
    echo ""
    echo "This script will:"
    echo "  1. Update version references in source files"
    echo "  2. Download fresh Omarchy documentation"
    echo "  3. Process manual pages and release notes"
    echo "  4. Ingest everything into ChromaDB"
    echo "  5. Create a new snapshot"
    exit 1
}

# Check for version argument
if [ $# -ne 1 ]; then
    show_usage
fi

NEW_VERSION="$1"

# Validate version format (simple check)
if ! [[ "$NEW_VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "❌ Error: Version must be in format like 3.4.0"
    exit 1
fi

echo "============================================================"
echo "🔄 UPGRADING OMARCHY MCP SERVER TO v$NEW_VERSION"
echo "============================================================"

# Current directory (project root - script is in scripts/)
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# ============================================================
# STEP 1: Update version references in source files
# ============================================================
echo ""
echo "📝 Step 1: Updating version references..."

# Update scripts/8_download_omarchy_releases.py (function definition)
sed -i "s|max_version=\"[0-9.]*\"|max_version=\"$NEW_VERSION\"|g" scripts/8_download_omarchy_releases.py
# Update scripts/8_download_omarchy_releases.py (function call at bottom)
sed -i "s|download_releases(\"[0-9.]*\")|download_releases(\"$NEW_VERSION\")|g" scripts/8_download_omarchy_releases.py
echo "  ✅ Updated scripts/8_download_omarchy_releases.py"

# Update scripts/6_clean_omarchy.py
sed -i "s|\"version\": \"[0-9.]*\"|\"version\": \"$NEW_VERSION\"|g" scripts/6_clean_omarchy.py
echo "  ✅ Updated scripts/6_clean_omarchy.py"

# Update scripts/create_snapshot.sh
sed -i "s|VERSION=\"[0-9.]*\"|VERSION=\"$NEW_VERSION\"|g" scripts/create_snapshot.sh
echo "  ✅ Updated scripts/create_snapshot.sh"

# Update scripts/setup.sh (display message)
sed -i "s|Setting up Omarchy MCP Server (v[0-9.]*)|Setting up Omarchy MCP Server (v$NEW_VERSION)|g" scripts/setup.sh
echo "  ✅ Updated scripts/setup.sh"

# Update README.md
sed -i "s|Omarchy: v[0-9.]* (pinned)|Omarchy: v$NEW_VERSION (pinned)|g" README.md
sed -i "s|Omarchy Releases: All versions up to v[0-9.]*|Omarchy Releases: All versions up to v$NEW_VERSION|g" README.md
sed -i "s|Restore Omarchy v[0-9.]* docs from snapshot|Restore Omarchy v$NEW_VERSION docs from snapshot|g" README.md
sed -i "s|documentation and release notes remain at v[0-9.]* (pinned)|documentation and release notes remain at v$NEW_VERSION (pinned)|g" README.md
sed -i "s|omarchy-[0-9.]*-processed|omarchy-$NEW_VERSION-processed|g" README.md
echo "  ✅ Updated README.md"

# ============================================================
# STEP 2: Download fresh Omarchy documentation
# ============================================================
echo ""
echo "📥 Step 2: Downloading fresh Omarchy documentation..."
./scripts/3_download_omarchy.sh

# ============================================================
# STEP 3: Process documentation inside Docker container
# ============================================================
echo ""
echo "🧹 Step 3: Processing documentation..."

# Ensure containers are running
if ! docker-compose ps | grep -q "Up"; then
    echo "  ⚠️  Containers not running, starting them..."
    docker-compose up -d
    sleep 10
fi

# Process manual pages
echo "  📄 Processing Omarchy manual..."
docker exec omarchy-mcp-server python scripts/6_clean_omarchy.py

# Download and process release notes
echo "  📦 Downloading release notes..."
docker exec omarchy-mcp-server python scripts/8_download_omarchy_releases.py

echo "  📦 Processing release notes..."
docker exec omarchy-mcp-server python scripts/9_clean_omarchy_releases.py

# ============================================================
# STEP 4: Ingest to ChromaDB
# ============================================================
echo ""
echo "📊 Step 4: Ingesting to vector database..."
docker exec omarchy-mcp-server python scripts/7_ingest_to_chroma.py

# ============================================================
# STEP 5: Create snapshot
# ============================================================
echo ""
echo "📸 Step 5: Creating snapshot..."
./scripts/create_snapshot.sh

# ============================================================
# DONE!
# ============================================================
echo ""
echo "============================================================"
echo "✅ UPGRADE COMPLETE!"
echo "============================================================"
echo ""
echo "Summary of changes:"
echo "  • Updated to Omarchy v$NEW_VERSION"
echo "  • Created snapshot: data/snapshots/omarchy-$NEW_VERSION-processed/"
echo "  • Updated README.md"
echo ""
echo "To commit the changes:"
echo "  git add data/snapshots/omarchy-$NEW_VERSION-processed/"
echo "  git add scripts/8_download_omarchy_releases.py"
echo "  git add scripts/6_clean_omarchy.py"
echo "  git add scripts/create_snapshot.sh"
echo "  git add scripts/setup.sh"
echo "  git add README.md"
echo "  git commit -m \"feat: update to Omarchy v$NEW_VERSION\""
echo ""
