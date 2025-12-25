#!/usr/bin/env python3
"""
Clean Hyprland wiki markdown files.
Already in good format, just add metadata.
"""

import os
import json
from pathlib import Path

RAW_DIR = Path("data/raw/hyprland/hyprland-wiki/content")
OUTPUT_DIR = Path("data/processed/hyprland")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def clean_markdown_file(md_file):
    """Extract sections from Hyprland markdown."""
    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Get category from folder structure
    category = md_file.parent.name if md_file.parent.name != "content" else "General"
    page_title = md_file.stem.replace("-", " ").title()
    
    # Split by ## headers (sections)
    sections = []
    current_section = {"title": "Overview", "content": []}
    
    for line in content.split('\n'):
        if line.startswith('## '):
            # Save previous section
            if current_section["content"]:
                sections.append(current_section)
            # New section
            section_title = line.replace('##', '').strip()
            current_section = {"title": section_title, "content": []}
        else:
            if line.strip():
                current_section["content"].append(line)
    
    # Add last section
    if current_section["content"]:
        sections.append(current_section)
    
    return {
        "page": page_title,
        "category": category,
        "sections": sections
    }

def main():
    print("🧹 Cleaning Hyprland markdown files...")
    processed_count = 0
    
    for md_file in RAW_DIR.rglob("*.md"):
        try:
            result = clean_markdown_file(md_file)
            
            # Save as JSON with metadata
            page_name = result["page"].replace("/", "_").replace(" ", "_")
            output_file = OUTPUT_DIR / f"{page_name}.json"
            
            output_data = {
                "source": "hyprland",
                "page": result["page"],
                "category": result["category"],
                "version": "any",
                "sections": []
            }
            
            for section in result["sections"]:
                output_data["sections"].append({
                    "section": section["title"],
                    "content": "\n".join(section["content"]),
                    "priority": 2,  # Hyprland = priority 2
                    "tags": ["hyprland", result["category"].lower()]
                })
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            
            processed_count += 1
        
        except Exception as e:
            print(f"  ⚠️  Error processing {md_file.name}: {e}")
    
    print(f"✅ Cleaned {processed_count} Hyprland pages → {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
