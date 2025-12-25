#!/usr/bin/env python3
"""
Ingest processed documentation into Chroma vector database.
Chunks content, generates embeddings, stores with metadata.
"""

import os
import json
from pathlib import Path
import chromadb
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

# Configuration
PROCESSED_DIR = Path("data/processed")
CHROMA_HOST = os.getenv("CHROMA_HOST", "chromadb")
CHROMA_PORT = int(os.getenv("CHROMA_PORT", "8000"))
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
CHUNK_SIZE = 400  # words per chunk

# Initialize
print(f"🔧 Initializing embedding model: {EMBEDDING_MODEL}")
embedder = SentenceTransformer(EMBEDDING_MODEL)

print(f"🔌 Connecting to Chroma at {CHROMA_HOST}:{CHROMA_PORT}")
client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)

# Create or get collection
collection = client.get_or_create_collection(
    name="omarchy_docs",
    metadata={"hnsw:space": "cosine"}
)

def chunk_text(text, chunk_size=CHUNK_SIZE):
    """Split text into chunks of approximately chunk_size words."""
    words = text.split()
    chunks = []
    
    for i in range(0, len(words), chunk_size):
        chunk = " ".join(words[i:i + chunk_size])
        if chunk.strip() and len(chunk.split()) > 20:  # Min 20 words
            chunks.append(chunk)
    
    return chunks

def ingest_source(source_name, source_dir):
    """Ingest all JSON files from a source directory."""
    print(f"\n📥 Ingesting {source_name} documentation...")
    
    json_files = list(source_dir.glob("*.json"))
    if not json_files:
        print(f"  ⚠️  No JSON files found in {source_dir}")
        return 0
    
    total_chunks = 0
    
    for json_file in tqdm(json_files, desc=f"  Processing {source_name}"):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            source = data.get("source", "unknown")
            page = data.get("page", json_file.stem)
            version = data.get("version", "any")
            priority = data.get("priority", 3)
            
            # Handle different JSON structures
            if "sections" in data:
                # ArchWiki / Hyprland format
                for section in data["sections"]:
                    section_title = section.get("section", "")
                    content = section.get("content", "")
                    
                    if not content or len(content.split()) < 20:
                        continue
                    
                    # Chunk the content
                    chunks = chunk_text(content)
                    
                    for i, chunk in enumerate(chunks):
                        doc_id = f"{source}_{page}_{section_title}_{i}".replace(" ", "_").replace("/", "_")[:100]
                        
                        # Generate embedding
                        embedding = embedder.encode(chunk).tolist()
                        
                        # Store in Chroma
                        collection.upsert(
                            ids=[doc_id],
                            documents=[chunk],
                            embeddings=[embedding],
                            metadatas=[{
                                "source": source,
                                "page": page,
                                "section": section_title,
                                "version": version,
                                "priority": priority,
                                "tags": ",".join(section.get("tags", [])),
                                "chunk_index": i
                            }]
                        )
                        
                        total_chunks += 1
            
            elif "content" in data:
                # Omarchy format (direct content)
                content = data["content"]
                section = data.get("section", "general")
                
                if not content or len(content.split()) < 20:
                    continue
                
                chunks = chunk_text(content)
                
                for i, chunk in enumerate(chunks):
                    doc_id = f"{source}_{page}_{section}_{i}".replace(" ", "_").replace("/", "_")[:100]
                    
                    embedding = embedder.encode(chunk).tolist()
                    
                    collection.upsert(
                        ids=[doc_id],
                        documents=[chunk],
                        embeddings=[embedding],
                        metadatas=[{
                            "source": source,
                            "page": page,
                            "section": section,
                            "version": version,
                            "priority": priority,
                            "tags": ",".join(data.get("tags", [])),
                            "chunk_index": i
                        }]
                    )
                    
                    total_chunks += 1
        
        except Exception as e:
            print(f"\n  ⚠️  Error processing {json_file.name}: {e}")
    
    return total_chunks

def main():
    print("=" * 60)
    print("OMARCHY MCP - VECTOR DATABASE INGESTION")
    print("=" * 60)
    
    # Ingest each source
    total = 0
    
    # Priority 3: Arch (base knowledge)
    if (PROCESSED_DIR / "archwiki").exists():
        total += ingest_source("ArchWiki", PROCESSED_DIR / "archwiki")
    
    # Priority 2: Hyprland (window manager specific)
    if (PROCESSED_DIR / "hyprland").exists():
        total += ingest_source("Hyprland", PROCESSED_DIR / "hyprland")
    
    # Priority 1: Omarchy (highest priority, overrides others)
    if (PROCESSED_DIR / "omarchy").exists():
        total += ingest_source("Omarchy", PROCESSED_DIR / "omarchy")
    
    print("\n" + "=" * 60)
    print(f"✅ INGESTION COMPLETE")
    print(f"📊 Total chunks vectorized: {total}")
    print(f"💾 Chroma collection: omarchy_docs")
    print("=" * 60)
    
    # Verify
    count = collection.count()
    print(f"\n🔍 Verification: {count} documents in database")

if __name__ == "__main__":
    main()
