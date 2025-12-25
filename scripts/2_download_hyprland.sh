#!/bin/bash
set -e

echo "📥 Downloading Hyprland wiki..."

cd data/raw/hyprland

# Clone the official Hyprland wiki repo
if [ ! -d "hyprland-wiki" ]; then
    git clone https://github.com/hyprwm/hyprland-wiki.git
    echo "✅ Hyprland wiki cloned"
else
    echo "⚠️  Hyprland wiki already exists, pulling updates..."
    cd hyprland-wiki
    git pull
    cd ..
fi

echo "✅ Hyprland wiki ready at data/raw/hyprland/hyprland-wiki"
