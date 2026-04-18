# omarchy-mcp

MCP server exposing semantic search over **Omarchy** (pinned), **Arch Wiki** (rolling), and **Hyprland** (rolling) docs to IDEs (Cursor, OpenCode, Claude Code).

Stack: ChromaDB + sentence-transformers (`all-MiniLM-L6-v2`), 400-word chunks, cosine similarity, MCP over stdio. Runs as two Docker services: `omarchy-mcp-server` and `chromadb`.

## Version pinning model

The user keeps the server pinned to whatever Omarchy version their system is on. The single source of truth for the pinned version is `VERSION=` in `scripts/create_snapshot.sh` (also baked into `scripts/8_download_omarchy_releases.py`). Arch wiki and Hyprland are always fetched latest.

Each bumped version is preserved in `data/snapshots/omarchy-<version>-processed/` — **this directory IS committed to git** (unlike `data/raw/` and `data/processed/` which are gitignored). The snapshot is a flat dir of `manual_*.json` (manual pages) and `<version>.json` files (release-note chunks).

## Two entrypoints

- `scripts/upgrade.sh <version>` — bump to new Omarchy version. Seds version refs into source files, wipes stale raw Omarchy data, freshly downloads Omarchy + Arch + Hyprland, processes everything, ingests to Chroma, writes a new snapshot. User commits the snapshot dir after.
- `scripts/setup.sh` — bootstrap on a fresh machine. Reads `PINNED_VERSION` from `create_snapshot.sh` and **restores Omarchy from the committed snapshot** (skipping scripts 3/6/8/9). Arch + Hyprland download fresh. Then ingest. Falls through to live download if no snapshot exists.

## Numbered scripts (data pipeline)

`1_download_archwiki.sh` (pacman) → `2_download_hyprland.sh` (git) → `3_download_omarchy.sh` (wget mirror + git clone) → `4_clean_archwiki.py` → `5_clean_hyprland.py` → `6_clean_omarchy.py` → `7_ingest_to_chroma.py` → `8_download_omarchy_releases.py` (GitHub API, capped at `max_version`) → `9_clean_omarchy_releases.py`.

`create_snapshot.sh` copies `data/processed/omarchy/` + `data/processed/omarchy_releases/` into `data/snapshots/omarchy-<version>-processed/`.

## MCP tools exposed

`search_documentation`, `find_config_location`, `compare_omarchy_vs_arch`, `get_server_info`. Implementation in `mcp_server/main.py`.

## Gotchas

- Don't add existence-guards around downloads in `3_download_omarchy.sh` reasoning — `upgrade.sh` pre-wipes `learn.omacom.io`, `omarchy.org`, `releases.html` specifically because the guards would otherwise skip re-fetch.
- `setup.sh` is the only path that restores from snapshot. `upgrade.sh` never touches snapshots of past versions.
- README Quick Start mentions restoring from snapshot — that's setup.sh's behavior, not upgrade.sh's.
- Arch wiki `cp -r` into existing `data/raw/archwiki/html/` merges (old pages can linger). Known minor issue.
