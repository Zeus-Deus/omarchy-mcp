#!/usr/bin/env python3
"""
Clean ArchWiki HTML files and convert to structured markdown.
Only processes English pages, extracts sections, adds metadata.
"""

import os
import json
from pathlib import Path
from bs4 import BeautifulSoup
import re

RAW_DIR = Path("data/raw/archwiki/html/en")
OUTPUT_DIR = Path("data/processed/archwiki")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def clean_html_to_markdown(html_file):
    """Extract clean text from ArchWiki HTML page."""
    with open(html_file, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'lxml')
    
    # Remove navigation, footer, sidebar
    for unwanted in soup.select('.mw-navigation, .mw-footer, #toc, .printfooter'):
        unwanted.decompose()
    
    # Get page title
    title_tag = soup.select_one('h1.firstHeading')
    title = title_tag.get_text().strip() if title_tag else html_file.stem
    
    # Get main content
    content = soup.select_one('#mw-content-text')
    if not content:
        return None
    
    # Extract sections (split by h2 headers)
    sections = []
    current_section = {"title": "Introduction", "content": []}
    
    for element in content.children:
        if element.name == 'h2':
            # Save previous section
            if current_section["content"]:
                sections.append(current_section)
            # Start new section
            headline = element.select_one('.mw-headline')
            section_title = headline.get_text().strip() if headline else element.get_text().strip()
            current_section = {"title": section_title, "content": []}
        elif element.name in ['p', 'ul', 'ol', 'pre', 'div']:
            text = element.get_text().strip()
            if text:
                current_section["content"].append(text)
    
    # Add last section
    if current_section["content"]:
        sections.append(current_section)
    
    return {
        "page": title,
        "sections": sections
    }

def main():
    print("🧹 Cleaning ArchWiki HTML files...")
    processed_count = 0
    
    # Process all HTML files in en/ directory
    for html_file in RAW_DIR.rglob("*.html"):
        try:
            result = clean_html_to_markdown(html_file)
            if not result:
                continue
            
            # Save as JSON with metadata
            page_name = result["page"].replace("/", "_").replace(" ", "_")
            output_file = OUTPUT_DIR / f"{page_name}.json"
            
            # Add metadata
            output_data = {
                "source": "arch",
                "page": result["page"],
                "version": "any",
                "sections": []
            }
            
            # Each section becomes a separate document chunk
            for section in result["sections"]:
                output_data["sections"].append({
                    "section": section["title"],
                    "content": "\n\n".join(section["content"]),
                    "priority": 3,  # Arch = priority 3 (lowest)
                    "tags": ["arch", result["page"].lower().replace(" ", "-")]
                })
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            
            processed_count += 1
            if processed_count % 10 == 0:
                print(f"  Processed {processed_count} pages...")
        
        except Exception as e:
            print(f"  ⚠️  Error processing {html_file.name}: {e}")
    
    print(f"✅ Cleaned {processed_count} ArchWiki pages → {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
