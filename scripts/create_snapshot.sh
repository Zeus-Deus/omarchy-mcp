#!/bin/bash
set -e

VERSION="3.3.3"
SNAPSHOT_DIR="data/snapshots/omarchy-${VERSION}-processed"

echo "📸 Creating snapshot for Omarchy v${VERSION}..."

# 1. Ensure the target directory exists
if [ -d "$SNAPSHOT_DIR" ]; then
    echo "⚠️  Snapshot directory $SNAPSHOT_DIR already exists. Overwriting..."
    rm -rf "$SNAPSHOT_DIR"
fi
mkdir -p "$SNAPSHOT_DIR"

# 2. Copy the processed manual pages
# script 6 outputs to data/processed/omarchy
if [ -d "data/processed/omarchy" ]; then
    echo "📦 Copying manual pages..."
    cp data/processed/omarchy/*.json "$SNAPSHOT_DIR/"
else
    echo "❌ Error: data/processed/omarchy not found. Did you run setup.sh?"
    exit 1
fi

# 3. Copy the processed release notes
# script 9 outputs to data/processed/omarchy_releases
if [ -d "data/processed/omarchy_releases" ]; then
    echo "📦 Copying release notes..."
    # We copy them into the same snapshot folder for simplicity, or keep structure?
    # Looking at previous snapshots, they seem flat. Let's copy them in.
    cp data/processed/omarchy_releases/*.json "$SNAPSHOT_DIR/" 2>/dev/null || echo "   (No separate release note files found, skipping)"
fi

echo ""
echo "✅ Snapshot saved to: $SNAPSHOT_DIR"
echo "👉 You can now commit this directory to git:"
echo "   git add $SNAPSHOT_DIR"
echo "   git commit -m \"Add documentation snapshot for v${VERSION}\""
