#!/usr/bin/env python3
"""
Simple MCP client tester - validates the server works.
"""

import json
import sys
import os

# Add project root to Python path so we can import mcp_server
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp_server.main import (
    search_documentation,
    find_config_location,
    compare_omarchy_vs_arch,
    get_server_info
)

def test_server_info():
    """Test 1: Get server info"""
    print("\n" + "="*60)
    print("TEST 1: Server Info")
    print("="*60)
    
    result = get_server_info()
    data = json.loads(result)
    
    print(f"✅ Server: {data['name']}")
    print(f"✅ Total docs: {data['total_documents']}")
    print(f"✅ Sources:")
    for source, info in data['sources'].items():
        print(f"   - {source}: {info['count']} docs (priority {info['priority']})")
    print(f"✅ Model: {data['embedding_model']}")

def test_search_documentation():
    """Test 2: Search documentation"""
    print("\n" + "="*60)
    print("TEST 2: Search Documentation")
    print("="*60)
    
    queries = [
        "How do I configure waybar in Omarchy?",
        "Hyprland keybindings",
        "Enable PipeWire audio"
    ]
    
    for query in queries:
        print(f"\n🔍 Query: {query}")
        result = search_documentation(query=query, top_k=3)
        data = json.loads(result)
        
        if data:
            print(f"   ✅ Found {len(data)} results")
            for i, doc in enumerate(data[:2], 1):
                print(f"   {i}. [{doc['source']}] {doc['page']} → {doc['section']}")
                print(f"      Confidence: {doc['confidence']}, Priority: {doc['priority']}")
                print(f"      Excerpt: {doc['content'][:100]}...")
        else:
            print("   ⚠️ No results")

def test_find_config():
    """Test 3: Find config location"""
    print("\n" + "="*60)
    print("TEST 3: Find Config Location")
    print("="*60)
    
    apps = ["waybar", "hyprland", "kitty"]
    
    for app in apps:
        print(f"\n📁 App: {app}")
        result = find_config_location(app_name=app, source="omarchy")
        data = json.loads(result)
        
        if isinstance(data, list) and data:
            print(f"   ✅ Found {len(data)} config locations")
            for loc in data[:2]:
                print(f"   - {loc['page']} → {loc['section']}")
        elif "error" in data:
            print(f"   ⚠️ {data['error']}")

def test_comparison():
    """Test 4: Compare Omarchy vs Arch"""
    print("\n" + "="*60)
    print("TEST 4: Compare Omarchy vs Arch")
    print("="*60)
    
    topic = "waybar configuration"
    print(f"\n⚖️  Topic: {topic}")
    
    result = compare_omarchy_vs_arch(topic=topic)
    data = json.loads(result)
    
    print(f"\n   Omarchy approach: {len(data['omarchy_approach'])} docs")
    for doc in data['omarchy_approach'][:1]:
        print(f"   - {doc['page']}")
        print(f"     {doc['excerpt'][:100]}...")
    
    print(f"\n   Arch/Hyprland approach: {len(data['arch_hyprland_approach'])} docs")
    for doc in data['arch_hyprland_approach'][:1]:
        print(f"   - [{doc['source']}] {doc['page']}")

def main():
    print("\n" + "🧪 " + "="*58)
    print("   OMARCHY MCP SERVER - FUNCTIONALITY TEST")
    print("=" + "="*58)
    
    try:
        test_server_info()
        test_search_documentation()
        test_find_config()
        test_comparison()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED - MCP SERVER IS WORKING!")
        print("="*60 + "\n")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
