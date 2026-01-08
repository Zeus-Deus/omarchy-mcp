#!/usr/bin/env python3
"""
Ingest processed documentation into Chroma vector database.
OPTIMIZED: Uses batch processing for 10x faster ingestion.
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
CHUNK_SIZE = 400
BATCH_SIZE = 256  # Process 256 chunks at a time (Sweet spot for CPU)

# Initialize
print(f"🔧 Initializing embedding model: {EMBEDDING_MODEL}")
embedder = SentenceTransformer(EMBEDDING_MODEL)

print(f"🔌 Connecting to Chroma at {CHROMA_HOST}:{CHROMA_PORT}")
client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)

collection = client.get_or_create_collection(
    name="omarchy_docs",
    metadata={"hnsw:space": "cosine"}
)

def chunk_text(text, chunk_size=CHUNK_SIZE):
    """Split text into chunks."""
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size):
        chunk = " ".join(words[i:i + chunk_size])
        if chunk.strip() and len(chunk.split()) > 20:
            chunks.append(chunk)
    return chunks

class BatchProcessor:
    def __init__(self, batch_size=BATCH_SIZE):
        self.batch_size = batch_size
        self.ids = []
        self.documents = []
        self.metadatas = []
        self.total_processed = 0

    def add(self, doc_id, document, metadata):
        self.ids.append(doc_id)
        self.documents.append(document)
        self.metadatas.append(metadata)
        
        if len(self.documents) >= self.batch_size:
            self.flush()

    def flush(self):
        if not self.documents:
            return
            
        # 1. Generate embeddings for the whole batch (Vectorized operation = FAST)
        embeddings = embedder.encode(self.documents).tolist()
        
        # 2. Upsert to Chroma in one network request
        collection.upsert(
            ids=self.ids,
            documents=self.documents,
            embeddings=embeddings,
            metadatas=self.metadatas
        )
        
        self.total_processed += len(self.documents)
        # Clear buffers
        self.ids = []
        self.documents = []
        self.metadatas = []

# Global batch processor
processor = BatchProcessor()

def ingest_source(source_name, source_dir):
    """Read files and add to batch processor."""
    print(f"\n📥 Queuing {source_name} documentation...")
    
    json_files = list(source_dir.glob("*.json"))
    if not json_files:
        print(f"  ⚠️  No JSON files found in {source_dir}")
        return
    
    # Just iterate and add to batch
    for json_file in tqdm(json_files, desc=f"  Reading {source_name}"):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            source = data.get("source", "unknown")
            page = data.get("page", json_file.stem)
            version = data.get("version", "any")
            priority = data.get("priority", 3)
            
            # Logic to extract content based on format
            contents_to_process = [] # list of (section_title, text_content, tags)
            
            if "sections" in data: # Arch/Hyprland format
                for section in data["sections"]:
                    contents_to_process.append((
                        section.get("section", ""),
                        section.get("content", ""),
                        section.get("tags", [])
                    ))
            elif "content" in data: # Omarchy format
                contents_to_process.append((
                    data.get("section", "general"),
                    data["content"],
                    data.get("tags", [])
                ))
            
            # Chunk and add
            for section, content, tags in contents_to_process:
                if not content or len(content.split()) < 20:
                    continue
                    
                chunks = chunk_text(content)
                for i, chunk in enumerate(chunks):
                    doc_id = f"{source}_{page}_{section}_{i}".replace(" ", "_").replace("/", "_")[:100]
                    
                    # ADD TO BATCH INSTEAD OF PROCESSING IMMEDIATELY
                    processor.add(
                        doc_id=doc_id,
                        document=chunk,
                        metadata={
                            "source": source,
                            "page": page,
                            "section": section,
                            "version": version,
                            "priority": priority,
                            "tags": ",".join(tags),
                            "chunk_index": i
                        }
                    )
                    
        except Exception as e:
            print(f"Error in {json_file}: {e}")

def process_releases():
    """Process release notes (already fast, but adding to batch consistency)."""
    print("\n📦 Queuing Omarchy release notes...")
    releases_dir = PROCESSED_DIR / "omarchy_releases"
    if not releases_dir.exists():
        return

    json_files = list(releases_dir.glob("*.json"))
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                chunks = json.load(f)
            for chunk in chunks:
                 # Check validity
                if not all(k in chunk for k in ["content", "version", "section_id"]): continue
                
                processor.add(
                    doc_id=f"release_{chunk['version']}_{chunk['section_id']}",
                    document=chunk["content"],
                    metadata={
                        "source": "omarchy_releases",
                        "version": chunk["version"],
                        "title": chunk.get("title", ""),
                        "url": chunk.get("url", ""),
                        "type": "release_note",
                        "priority": 1
                    }
                )
        except Exception:
            pass

def main():
    print("=" * 60)
    print("OMARCHY MCP - OPTIMIZED BATCH INGESTION")
    print("=" * 60)
    
    # 1. Queue everything
    if (PROCESSED_DIR / "archwiki").exists():
        ingest_source("ArchWiki", PROCESSED_DIR / "archwiki")
    
    if (PROCESSED_DIR / "hyprland").exists():
        ingest_source("Hyprland", PROCESSED_DIR / "hyprland")
        
    process_releases()
    
    if (PROCESSED_DIR / "omarchy").exists():
        ingest_source("Omarchy", PROCESSED_DIR / "omarchy")
    
    # 2. Final Flush (Process whatever is left in the buffer)
    print("\n🔄 Processing final batch...")
    processor.flush()
    
    print("\n" + "=" * 60)
    print(f"✅ INGESTION COMPLETE")
    print(f"📊 Total chunks vectorized: {processor.total_processed}")
    print("=" * 60)

if __name__ == "__main__":
    main()
