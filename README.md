# zbmath-mcp

MCP server for [zbMath Open](https://zbmath.org) — the world's most comprehensive reviewed database of mathematical literature.

This server exposes the [zbMath Open REST API](https://api.zbmath.org/v1/) as [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) tools, enabling AI assistants such as Claude to search and retrieve mathematical publications, author profiles, and software entries directly.

## Tools

| Tool | Description |
|------|-------------|
| `search_documents` | Free-text search across 4.5 M+ zbMath documents |
| `get_document` | Fetch full metadata for a document by its zbMath ID |
| `structured_search` | Field-filtered search (author, title, MSC code, year range, journal) |
| `get_author` | Fetch an author profile by zbMath author ID |
| `get_software` | Fetch a software / swMath entry by its numeric ID |

## Requirements

- Python 3.11+
- [`uv`](https://docs.astral.sh/uv/) (recommended) or `pip`

## Installation

### Using uv (recommended)

```bash
uv tool install zbmath-mcp
```

### Using pip

```bash
pip install zbmath-mcp
```

### From source

```bash
git clone https://github.com/iwaokimura/zbmath-mcp.git
cd zbmath-mcp
pip install .
```

## Usage

### Running the server

```bash
zbmath-mcp
```

Or directly with Python:

```bash
python server.py
```

The server communicates over **stdio** using the MCP protocol.

### Connecting with Claude Desktop

Add the following to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "zbmath": {
      "command": "zbmath-mcp"
    }
  }
}
```

Or if running from source:

```json
{
  "mcpServers": {
    "zbmath": {
      "command": "python",
      "args": ["/path/to/zbmath-mcp/server.py"]
    }
  }
}
```

### Connecting with Claude Code (CLI)

```bash
claude mcp add zbmath -- zbmath-mcp
```

## Example interactions

Once connected, you can ask an AI assistant:

- *"Search zbMath for papers on the Langlands program from the last 5 years."*
- *"Get the zbMath document with ID 7192477."*
- *"Find all papers by Euler in zbMath."*
- *"Search for papers in MSC class 11 (Number Theory) published between 2000 and 2010."*
- *"Look up the software entry for Macaulay2 on swMath."*

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/
```

## License

MIT — see [LICENSE](LICENSE).
