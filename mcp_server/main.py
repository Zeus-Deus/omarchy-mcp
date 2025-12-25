#!/usr/bin/env python3
"""
Omarchy MCP Server - Knowledge base for Omarchy/Arch/Hyprland
"""

import os
import json
from typing import Optional
import chromadb
from mcp.server.fastmcp import FastMCP
from sentence_transformers import SentenceTransformer

# Configuration
CHROMA_HOST = os.getenv("CHROMA_HOST", "chromadb")
CHROMA_PORT = int(os.getenv("CHROMA_PORT", "8000"))
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# Initialize MCP Server
mcp = FastMCP("omarchy-kb")

# Initialize embedding model
print(f"🔧 Loading embedding model: {EMBEDDING_MODEL}")
embedder = SentenceTransformer(EMBEDDING_MODEL)

# Connect to Chroma
print(f"🔌 Connecting to Chroma at {CHROMA_HOST}:{CHROMA_PORT}")
client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
collection = client.get_collection(name="omarchy_docs")

print(f"✅ Connected to collection with {collection.count()} documents")

# ============================================================================
# TOOL 1: Search Documentation
# ============================================================================

@mcp.tool()
def search_documentation(
    query: str,
    source_filter: Optional[str] = None,
    omarchy_version: Optional[str] = None,
    top_k: int = 5
) -> str:
    """
    Search Omarchy/Arch/Hyprland documentation using semantic similarity.
    
    This tool understands the MEANING of your question and finds relevant docs,
    even if they don't use the exact same words. Perfect for config questions,
    troubleshooting, and "how do I..." queries.
    
    Args:
        query: Your question or search query
               Examples:
               - "How do I add a CPU widget to waybar?"
               - "Where is the Hyprland config in Omarchy?"
               - "How to enable PipeWire audio?"
        
        source_filter: Filter by documentation source (optional)
                      - "omarchy": Only Omarchy-specific docs (RECOMMENDED for Omarchy questions)
                      - "hyprland": Hyprland window manager docs
                      - "arch": Base Arch Linux docs
                      Leave empty to search all sources (Omarchy gets priority)
        
        omarchy_version: Filter by Omarchy version (e.g., "3.2.3")
                        Leave empty for latest/any version
        
        top_k: Number of results to return (default: 5, max: 20)
    
    Returns:
        JSON array of matching documentation chunks with:
        - source: Where the doc came from (omarchy/hyprland/arch)
        - page: Documentation page name
        - section: Specific section within the page
        - content: The actual documentation text
        - confidence: Relevance score (0-1, higher is better)
        - priority: Source priority (1=Omarchy highest, 3=Arch lowest)
    
    Important: When Omarchy and Arch/Hyprland docs conflict, ALWAYS prefer 
    Omarchy docs (priority=1). Omarchy has custom configs that differ from 
    vanilla Arch/Hyprland.
    """
    
    # Generate query embedding
    query_embedding = embedder.encode(query).tolist()
    
    # Build filter
    where_filter = {}
    if source_filter:
        where_filter["source"] = source_filter
    if omarchy_version:
        where_filter["version"] = omarchy_version
    
    # Query Chroma
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(top_k, 20),
        where=where_filter if where_filter else None,
        include=["documents", "metadatas", "distances"]
    )
    
    # Format results
    formatted_results = []
    for doc, meta, distance in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0]
    ):
        formatted_results.append({
            "source": meta.get("source", "unknown"),
            "page": meta.get("page", ""),
            "section": meta.get("section", ""),
            "content": doc,
            "confidence": round(1 - distance, 3),
            "priority": meta.get("priority", 3),
            "version": meta.get("version", "any"),
            "tags": meta.get("tags", "").split(",") if meta.get("tags") else []
        })
    
    # Sort by priority first (Omarchy > Hyprland > Arch), then by confidence
    formatted_results.sort(key=lambda x: (x["priority"], -x["confidence"]))
    
    return json.dumps(formatted_results, indent=2)


# ============================================================================
# TOOL 2: Find Config File Locations
# ============================================================================

@mcp.tool()
def find_config_location(app_name: str, source: str = "omarchy") -> str:
    """
    Find exact file paths for configuration files in Omarchy/Arch/Hyprland.
    
    Omarchy often places configs in different locations than vanilla Arch,
    and uses modular config structures. This tool knows those differences.
    
    Args:
        app_name: Application name
                 Examples: "waybar", "hyprland", "kitty", "nvim", "mako"
        
        source: Which source to search (default: "omarchy")
               - "omarchy": Omarchy-specific paths (RECOMMENDED)
               - "hyprland": Hyprland default paths
               - "arch": Standard Arch Linux paths
    
    Returns:
        JSON with config file locations, paths, and Omarchy-specific notes
    
    Example:
        find_config_location("waybar", "omarchy")
        Returns: ~/.config/waybar/config.jsonc with notes about modular structure
    """
    
    # Search for config location info
    search_query = f"{app_name} configuration file path location"
    query_embedding = embedder.encode(search_query).tolist()
    
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=5,
        where={"source": source},
        include=["documents", "metadatas"]
    )
    
    # Extract location info
    locations = []
    for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
        # Look for paths in content (simple heuristic)
        if "~/" in doc or "/etc/" in doc or ".config" in doc:
            locations.append({
                "app": app_name,
                "source": source,
                "page": meta.get("page", ""),
                "section": meta.get("section", ""),
                "excerpt": doc[:500],  # First 500 chars
                "priority": meta.get("priority", 3)
            })
    
    if not locations:
        return json.dumps({
            "error": f"No config location found for {app_name} in {source}",
            "suggestion": f"Try search_documentation('{app_name} config') instead"
        })
    
    return json.dumps(locations, indent=2)


# ============================================================================
# TOOL 3: Compare Arch vs Omarchy
# ============================================================================

@mcp.tool()
def compare_omarchy_vs_arch(topic: str) -> str:
    """
    Compare how Omarchy differs from vanilla Arch/Hyprland for a specific topic.
    
    Useful when you want to understand what Omarchy changed or customized.
    
    Args:
        topic: What to compare
              Examples: "waybar config", "hyprland keybindings", "theme system"
    
    Returns:
        JSON with side-by-side comparison of Arch vs Omarchy approach
    """
    
    query_embedding = embedder.encode(topic).tolist()
    
    # Get Omarchy docs
    omarchy_results = collection.query(
        query_embeddings=[query_embedding],
        n_results=3,
        where={"source": "omarchy"},
        include=["documents", "metadatas"]
    )
    
    # Get Arch/Hyprland docs
    arch_results = collection.query(
        query_embeddings=[query_embedding],
        n_results=3,
        where={"source": {"$in": ["arch", "hyprland"]}},
        include=["documents", "metadatas"]
    )
    
    comparison = {
        "topic": topic,
        "omarchy_approach": [],
        "arch_hyprland_approach": []
    }
    
    for doc, meta in zip(omarchy_results["documents"][0], omarchy_results["metadatas"][0]):
        comparison["omarchy_approach"].append({
            "page": meta.get("page", ""),
            "excerpt": doc[:300]
        })
    
    for doc, meta in zip(arch_results["documents"][0], arch_results["metadatas"][0]):
        comparison["arch_hyprland_approach"].append({
            "source": meta.get("source", ""),
            "page": meta.get("page", ""),
            "excerpt": doc[:300]
        })
    
    return json.dumps(comparison, indent=2)


# ============================================================================
# SERVER INFO
# ============================================================================

@mcp.tool()
def get_server_info() -> str:
    """
    Get information about the Omarchy MCP knowledge base.
    
    Returns stats about the vector database, sources, and capabilities.
    """
    
    total_docs = collection.count()
    
    # Count by source
    omarchy_count = len(collection.get(where={"source": "omarchy"})["ids"])
    hyprland_count = len(collection.get(where={"source": "hyprland"})["ids"])
    arch_count = len(collection.get(where={"source": "arch"})["ids"])
    
    info = {
        "name": "Omarchy Knowledge Base MCP Server",
        "version": "1.0.0",
        "total_documents": total_docs,
        "sources": {
            "omarchy": {"count": omarchy_count, "priority": 1, "description": "Omarchy-specific documentation (highest priority)"},
            "hyprland": {"count": hyprland_count, "priority": 2, "description": "Hyprland window manager documentation"},
            "arch": {"count": arch_count, "priority": 3, "description": "Arch Linux base documentation"}
        },
        "capabilities": [
            "Semantic search across all documentation",
            "Config file location lookup",
            "Omarchy vs Arch comparison",
            "Version-aware queries (Omarchy versions)",
            "Priority-based results (Omarchy > Hyprland > Arch)"
        ],
        "embedding_model": EMBEDDING_MODEL
    }
    
    return json.dumps(info, indent=2)


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 OMARCHY MCP SERVER STARTING")
    print("=" * 60)
    print(f"📚 Knowledge base: {collection.count()} documents")
    print(f"🔧 Tools available: 4")
    print("=" * 60)
    mcp.run()
