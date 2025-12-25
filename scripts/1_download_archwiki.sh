#!/bin/bash
set -e

echo "📥 Installing arch-wiki-docs..."
sudo pacman -S --noconfirm arch-wiki-docs

echo "📂 Copying Arch Wiki files..."
mkdir -p data/raw/archwiki
cp -r /usr/share/doc/arch-wiki/html data/raw/archwiki/

echo "✅ Arch Wiki files ready at data/raw/archwiki/"

