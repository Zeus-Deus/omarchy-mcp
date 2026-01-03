#!/usr/bin/env python3
"""Convert release notes to searchable JSON chunks"""
import json
import re
from pathlib import Path

def clean_release_notes():
    input_file = "/app/data/raw/omarchy_releases/releases_up_to_3.2.3.json"
    output_dir = "/app/data/processed/omarchy_releases"
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    with open(input_file) as f:
        releases = json.load(f)
    
    for release in releases:
        try:
            version = release.get("version", "unknown")
            if version == "unknown":
                continue
            
            body = release.get("body", "")
            if not body or not body.strip():
                print(f"  ⚠️  Skipping v{version}: empty release notes")
                continue
            
            # Split release notes into sections
            sections = split_into_sections(body)
            chunks = []
            
            for i, section in enumerate(sections):
                content = section["content"].strip()
                # Skip sections with less than 20 words
                if not content or len(content.split()) < 20:
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
            
            # Only save if we have valid chunks
            if not chunks:
                print(f"  ⚠️  Skipping v{version}: no valid content")
                continue
            
            # Save processed chunks
            output_file = f"{output_dir}/{version}.json"
            with open(output_file, "w") as f:
                json.dump(chunks, f, indent=2)
            
            print(f"✅ Processed v{version}: {len(chunks)} chunks")
        
        except Exception as e:
            version = release.get("version", "unknown")
            print(f"  ⚠️  Error processing release {version}: {e}")
            continue

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
