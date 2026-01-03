#!/usr/bin/env python3
"""Download Omarchy GitHub release notes up to specified version"""
import requests
import json
import os
from packaging import version

def download_releases(max_version="3.2.3"):
    """Download all release notes up to max_version"""
    
    output_dir = "/app/data/raw/omarchy_releases"
    os.makedirs(output_dir, exist_ok=True)
    
    # Fetch all releases from GitHub API
    url = "https://api.github.com/repos/basecamp/omarchy/releases"
    try:
        response = requests.get(url, params={"per_page": 100}, timeout=10)
        response.raise_for_status()
        releases = response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching releases: {e}")
        return 0
    
    max_ver = version.parse(max_version)
    collected = []
    
    for release in releases:
        tag = release["tag_name"].lstrip("v")
        
        # Only include releases up to max_version
        try:
            rel_ver = version.parse(tag)
            if rel_ver <= max_ver:
                collected.append({
                    "version": tag,
                    "name": release["name"],
                    "published_at": release["published_at"],
                    "body": release.get("body") or "",  # Markdown content
                    "html_url": release["html_url"]
                })
        except (ValueError, KeyError) as e:
            print(f"  ⚠️  Skipping invalid tag '{tag}': {e}")
            continue
    
    # Save as JSON
    output_file = f"{output_dir}/releases_up_to_{max_version}.json"
    with open(output_file, "w") as f:
        json.dump(collected, f, indent=2)
    
    print(f"✅ Downloaded {len(collected)} releases up to v{max_version}")
    print(f"📁 Saved to: {output_file}")
    return len(collected)

if __name__ == "__main__":
    download_releases("3.2.3")
