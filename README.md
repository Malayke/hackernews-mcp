# Hacker News Reader MCP Server

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A [Model Context Protocol](https://modelcontextprotocol.io) (MCP) server that fetches Hacker News discussions and article content. Optimized for LLM consumption with compact, token-efficient formatting.

## Features

✅ Fetch complete Hacker News discussion threads  
✅ Scrape linked article content in markdown format  
✅ LLM-optimized output (compact nested replies)  
✅ Accepts both HN URLs and item IDs  
✅ Handles edge cases (text posts, Ask HN, deleted comments)  
✅ Powered by Firecrawl for robust article extraction  

## Installation

### Using uvx from GitHub (Recommended)

```bash
uvx --from git+https://github.com/Malayke/hackernews-mcp.git hackernews-mcp
```

### Using uv pip

```bash
uv pip install git+https://github.com/Malayke/hackernews-mcp.git
```

### Using pip

```bash
pip install git+https://github.com/Malayke/hackernews-mcp.git
```

## Usage

### As an MCP Server

Add to your MCP settings configuration (e.g., in Claude Desktop or other MCP clients):

```json
{
  "mcpServers": {
    "hackernews-mcp": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/Malayke/hackernews-mcp.git",
        "hackernews-mcp"
      ],
      "env": {
        "FIRECRAWL_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

Or if you've installed it with pip/uv pip:

```json
{
  "mcpServers": {
    "hackernews-mcp": {
      "command": "hackernews-mcp",
      "env": {
        "FIRECRAWL_API_KEY": "your_api_key_here"
      }
    }
  }
}
```


### Environment Variables

Required:
- `FIRECRAWL_API_KEY` - Your [Firecrawl](https://firecrawl.dev/) API key

Create a `.env` file:
```bash
FIRECRAWL_API_KEY=your_api_key_here
```

### Available Tools

#### `get_hn_content`

Fetches Hacker News comments and the linked article content.

**Input:**
- `hn_url`: HN URL or item ID
  - Full URL: `https://news.ycombinator.com/item?id=46130187`
  - Just ID: `46130187`

**Output:** Combined markdown with:
1. **Article Content** - Scraped article in markdown format
2. **HN Discussion** - Formatted comment threads with metadata

**Example:**
```json
{
  "hn_url": "https://news.ycombinator.com/item?id=46130187"
}
```

## Output Format

The tool returns LLM-optimized content:

```
# ARTICLE CONTENT

[Article markdown content here...]

---

# HACKER NEWS DISCUSSION

STORY: Article Title
URL: https://example.com/article
AUTHOR: username | POINTS: 123 | TIME: 2 hours ago
TOTAL_COMMENTS: 45

COMMENT #1
COMMENT [author @ time] ID: 123456
Comment text here...
  REPLY [author2 @ time] ID: 123457
  Reply text here...
    REPLY [author3 @ time] ID: 123458
    Nested reply text...

COMMENT #2
...
```

## Development

### Local Setup

```bash
# Clone the repository
git clone https://github.com/Malayke/hackernews-mcp.git
cd hackernews-mcp

# Install dependencies with uv
uv sync

# Set up environment
echo "FIRECRAWL_API_KEY=your_api_key_here" > .env

# Run the server
uv run server.py
```

### Testing

```bash
# Test the MCP server
uv run python test_mcp_server.py
```

### Using in Development Mode

For local development with live changes:

```json
{
  "mcpServers": {
    "hackernews-mcp": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/path/to/hackernews-mcp",
        "python",
        "server.py"
      ],
      "env": {
        "FIRECRAWL_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

## Requirements

- Python 3.11+
- Firecrawl API key (for article scraping)

## Dependencies

- `mcp` - Model Context Protocol SDK
- `requests` - HTTP requests
- `beautifulsoup4` - HTML parsing
- `firecrawl-py` - Article content extraction
- `python-dotenv` - Environment variable management

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Links

- [Model Context Protocol](https://modelcontextprotocol.io)
- [Firecrawl](https://firecrawl.dev/)
- [Hacker News](https://news.ycombinator.com)

## Support

For issues, questions, or contributions, please visit the [GitHub repository](https://github.com/Malayke/hackernews-mcp).
