# Omarchy MCP Server

A Model Context Protocol (MCP) server providing semantic search over Omarchy, Arch Linux, and Hyprland documentation.

## Version Information

- **Omarchy:** v3.2.3 (pinned)
- **Omarchy Releases:** All versions up to v3.2.3 (44 releases, ~100 chunks)
- **Arch Wiki:** Latest (updated via script)
- **Hyprland Wiki:** Latest (updated via script)

**Note:** This server contains Omarchy v3.2.3 documentation. Some features may differ if you are on a different version.

## Prerequisites

- **Arch-based Linux system** (uses pacman for arch-wiki-docs)
- Docker and Docker Compose
- Git
- 10 GB free disk space
- Internet connection for initial setup

## Quick Start

### 1. Clone the Repository

```
git clone https://github.com/Zeus-Deus/omarchy-mcp.git
cd omarchy-mcp
```

### 2. Run Setup

```
chmod +x scripts/setup.sh
./scripts/setup.sh
```

**This will take approximately 3-4 minutes and will:**

- Restore Omarchy v3.2.3 docs from snapshot
- Download latest Arch Wiki and Hyprland documentation
- Build and start Docker containers
- Process and ingest all documentation into vector database
- Create 8,500+ searchable documentation chunks

### 3. Configure Cursor IDE

Create or edit `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "omarchy-kb": {
      "command": "docker",
      "args": [
        "exec",
        "-i",
        "omarchy-mcp-server",
        "python",
        "/app/mcp_server/main.py"
      ]
    }
  }
}
```

**Important:** Restart Cursor completely after adding the configuration.

### 4. Use in Cursor

1. Open Cursor IDE
2. Switch to **Agent mode** (click "Ask" dropdown in bottom-left, select "Agent")
3. In the chat, type queries like:

```
Use omarchy-kb to search for waybar configuration
```

Or:

```
How do I configure Hyprland keybindings in Omarchy?
```

Or:

```
Use omarchy-kb to tell me what's new in Omarchy version 3.2.0
```

## Available Tools

The MCP server provides these tools:

- **search_documentation** - Semantic search across all documentation
- **find_config_location** - Find configuration file paths for applications
- **compare_omarchy_vs_arch** - Compare Omarchy vs vanilla Arch/Hyprland implementations
- **get_server_info** - View server statistics and capabilities

## Documentation Sources

The knowledge base includes:

| Source           | Documents   | Priority    | Description                                           |
| ---------------- | ----------- | ----------- | ----------------------------------------------------- |
| Omarchy          | 65          | 1 (highest) | Omarchy-specific documentation and customizations     |
| Omarchy Releases | ~100 chunks | 1 (highest) | GitHub release notes with changelogs and new features |
| Hyprland         | 302         | 2           | Hyprland window manager documentation                 |
| Arch Wiki        | 2,493       | 3           | Base Arch Linux documentation                         |

**Priority System:** When conflicts occur, Omarchy documentation takes precedence over Hyprland and Arch.

## Updating Documentation

**Note:** Omarchy documentation and release notes remain at v3.2.3 (pinned version). To update Arch Wiki and Hyprland documentation, re-run the setup script or manually execute the download and processing scripts.

## Manual Operations

### Stop the Server

```
docker-compose down
```

### Start the Server

```
docker-compose up -d
```

### View Logs

```
docker logs -f omarchy-mcp-server
```

### Rebuild After Code Changes

```
docker-compose down
docker-compose build
docker-compose up -d
```

## Project Structure

```
omarchy-mcp/
├── data/
│   ├── snapshots/
│   │   └── omarchy-3.2.3-processed/ # Version snapshot (in Git)
│   ├── raw/ # Downloaded HTML (ignored)
│   └── processed/ # Cleaned JSON (ignored)
├── scripts/
│   ├── setup.sh # Initial setup script
│   ├── 1_download_archwiki.sh # Download Arch Wiki
│   ├── 2_download_hyprland.sh # Download Hyprland wiki
│   ├── 3_download_omarchy.sh # Download Omarchy manual
│   ├── 4_clean_archwiki.py # Clean Arch HTML to JSON
│   ├── 5_clean_hyprland.py # Clean Hyprland MD to JSON
│   ├── 6_clean_omarchy.py # Clean Omarchy HTML to JSON
│   ├── 7_ingest_to_chroma.py # Ingest to vector database
│   ├── 8_download_omarchy_releases.py # Download Omarchy releases (NEW!)
│   └── 9_clean_omarchy_releases.py # Clean releases to JSON (NEW!)
├── mcp_server/
│   └── main.py # MCP server implementation
├── docker-compose.yml # Docker services definition
├── Dockerfile # Container build instructions
├── requirements.txt # Python dependencies
└── README.md
```

## Troubleshooting

### Server Not Connecting in Cursor

- Ensure Docker containers are running: `docker ps`
- Check server logs: `docker logs omarchy-mcp-server`
- Verify you are in **Agent mode** in Cursor (not "Ask" mode)
- Restart Cursor completely after updating config

### No Results from Queries

- Verify vector database is populated:

```
docker exec omarchy-mcp-server python -c "
import chromadb
client = chromadb.HttpClient(host='chromadb', port=8000)
collection = client.get_collection('omarchy_docs')
print(f'Documents: {collection.count()}')
"
```

- Should show approximately 8,500+ documents

### Setup Script Fails

- Ensure Docker daemon is running: `systemctl status docker`
- Check available disk space: `df -h`
- Verify internet connection
- Try running steps manually from `scripts/setup.sh`

## Technical Details

- **Vector Database:** ChromaDB
- **Embedding Model:** all-MiniLM-L6-v2 (sentence-transformers)
- **Chunk Size:** 400 words per document chunk
- **Search Method:** Cosine similarity on embeddings
- **Protocol:** Model Context Protocol (MCP) via stdio

## Contributing

Issues and pull requests welcome at https://github.com/Zeus-Deus/omarchy-mcp

## License

GNU General Public License v3.0 (GPL-3.0)

See [LICENSE](LICENSE) for full license text.
