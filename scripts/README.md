# Development Scripts

Utility scripts for Memoriai development.

## Documentation

### `serve-docs.py`
Serves MkDocs documentation locally for development.

```bash
python scripts/serve-docs.py
```

Features:
- Auto-installs MkDocs dependencies if needed
- Serves docs at http://127.0.0.1:8000
- Auto-reload on file changes
- Graceful shutdown with Ctrl+C

## Usage

From project root:

```bash
# Serve documentation
python scripts/serve-docs.py

# Or directly with MkDocs (if installed)
mkdocs serve
```