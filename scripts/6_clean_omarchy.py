#!/usr/bin/env python3
"""
Clean Omarchy documentation (manual + website + releases).
Highest priority source.
"""

import os
import json
from pathlib import Path
from bs4 import BeautifulSoup

MANUAL_DIR = Path("data/raw/omarchy/learn.omacom.io/2/the-omarchy-manual")
RELEASES_FILE = Path("data/raw/omarchy/releases.html")
REPO_DIR = Path("data/raw/omarchy/omarchy-repo")
OUTPUT_DIR = Path("data/processed/omarchy")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def clean_manual_page(html_file):
    """Extract content from Omarchy manual page."""
    with open(html_file, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'lxml')
    
    # Get title
    title_tag = soup.select_one('h1') or soup.select_one('title')
    title = title_tag.get_text().strip() if title_tag else html_file.stem
    
    # Get main content
    content_div = soup.select_one('article') or soup.select_one('main') or soup.select_one('body')
    if not content_div:
        return None
    
    # Extract paragraphs
    paragraphs = []
    for p in content_div.find_all(['p', 'li', 'code', 'pre']):
        text = p.get_text().strip()
        if text and len(text) > 20:  # Filter out tiny fragments
            paragraphs.append(text)
    
    return {
        "title": title,
        "content": "\n\n".join(paragraphs)
    }

def parse_releases():
    """Extract release notes from GitHub releases page."""
    with open(RELEASES_FILE, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'lxml')
    
    releases = []
    for release_div in soup.select('[data-test-selector="release-card"]'):
        version_tag = release_div.select_one('h2 a')
        version = version_tag.get_text().strip() if version_tag else "Unknown"
        
        body = release_div.select_one('.markdown-body')
        content = body.get_text().strip() if body else ""
        
        if version and content:
            releases.append({
                "version": version,
                "content": content
            })
    
    return releases

def main():
    print("🧹 Cleaning Omarchy documentation...")
    
    # 1. Process manual pages
    manual_count = 0
    for html_file in MANUAL_DIR.rglob("*.html"):
        try:
            result = clean_manual_page(html_file)
            if not result:
                continue
            
            page_name = html_file.stem
            output_file = OUTPUT_DIR / f"manual_{page_name}.json"
            
            output_data = {
                "source": "omarchy",
                "section": "manual",
                "page": result["title"],
                "version": "3.2.3",  # Update this to current version
                "priority": 1,  # Omarchy = highest priority
                "tags": ["omarchy", "manual"],
                "content": result["content"]
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            
            manual_count += 1
        except Exception as e:
            print(f"  ⚠️  Error processing {html_file.name}: {e}")
    
    print(f"  ✅ Processed {manual_count} manual pages")
    
    # 2. Process releases
    try:
        releases = parse_releases()
        for i, release in enumerate(releases):
            output_file = OUTPUT_DIR / f"release_{i:03d}.json"
            
            output_data = {
                "source": "omarchy",
                "section": "release_notes",
                "version": release["version"],
                "priority": 1,
                "tags": ["omarchy", "releases", "changelog"],
                "content": release["content"]
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"  ✅ Processed {len(releases)} release notes")
    except Exception as e:
        print(f"  ⚠️  Error processing releases: {e}")
    
    print(f"✅ All Omarchy docs cleaned → {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
