#!/usr/bin/env python3
"""Convert release notes to searchable JSON chunks"""
import json
import re
import glob
from pathlib import Path

def clean_release_notes():
    # Find ANY release file instead of hardcoding the name
    input_dir = "/app/data/raw/omarchy_releases"
    files = glob.glob(f"{input_dir}/releases_up_to_*.json")
    
    if not files:
        print(f"❌ Error: No release file found in {input_dir}")
        return

    # Pick the most recent file found
    input_file = sorted(files)[-1]
    print(f"📂 Processing release file: {input_file}")

    output_dir = "/app/data/processed/omarchy_releases"
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    with open(input_file) as f:
        releases = json.load(f)
    
    processed_count = 0
    
    for release in releases:
        try:
            version = release.get("version", "unknown")
            if version == "unknown":
                continue
            
            body = release.get("body", "")
            if not body or not body.strip():
                # print(f"  ⚠️  Skipping v{version}: empty release notes")
                continue
            
            # Split release notes into sections
            sections = split_into_sections(body)
            chunks = []
            
            for i, section in enumerate(sections):
                content = section["content"].strip()
                # Relaxed limit: Accept shorter chunks (min 10 words) for changelogs
                if not content or len(content.split()) < 10:
                    continue
                
                chunks.append({
                    "version": version,
                    "section_id": i,
                    "title": section["title"],
                    "content": content,
                    "type": "release_note",
                    "url": release.get("html_url", ""),
                    "published": release.get("published_at", "")
                })
            
            if not chunks:
                continue
            
            # Save processed chunks
            output_file = f"{output_dir}/{version}.json"
            with open(output_file, "w") as f:
                json.dump(chunks, f, indent=2)
            
            print(f"✅ Processed v{version}: {len(chunks)} chunks")
            processed_count += 1
        
        except Exception as e:
            version = release.get("version", "unknown")
            print(f"  ⚠️  Error processing release {version}: {e}")
            continue

    print(f"🎉 Total releases processed: {processed_count}")

def split_into_sections(markdown):
    """Split markdown by ## headers"""
    sections = []
    current = {"title": "Overview", "content": ""}
    
    for line in markdown.split("\n"):
        if line.startswith("## "):
            if current["content"]:
                sections.append(current)
            current = {"title": line[3:].strip(), "content": ""}
        else:
            current["content"] += line + "\n"
    
    if current["content"]:
        sections.append(current)
    
    return sections

if __name__ == "__main__":
    clean_release_notes()
