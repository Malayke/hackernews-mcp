#!/usr/bin/env python3
"""
Hacker News MCP Server
Provides tools to fetch HN comments and article content
"""

import asyncio
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
import mcp.server.stdio

# Import existing modules
from hn_parser import parse_hn_comments
from firecrawl_client import scrape_url, get_markdown, FirecrawlError

# Initialize server
server = Server("hackernews-mcp")


def format_comment_llm(comment: dict, indent: int = 0) -> str:
    """Format a single comment in compact LLM-optimized format"""
    prefix = "  " * indent
    lines = []
    
    # Determine comment type based on indent
    comment_type = "REPLY" if indent > 0 else "COMMENT"
    
    # Add compact header
    lines.append(f"{prefix}{comment_type} [{comment['author']} @ {comment['time']}] ID: {comment['id']}")
    
    # Add text directly without extra formatting
    text_lines = comment['text'].split('\n')
    for line in text_lines:
        lines.append(f"{prefix}{line}")
    
    # Add blank line only between top-level comments
    if indent == 0 and comment['replies']:
        lines.append("")
    
    # Recursively format replies
    for reply in comment['replies']:
        lines.append(format_comment_llm(reply, indent + 1))
    
    return '\n'.join(lines)


def format_hn_discussion(result: dict) -> str:
    """Format the complete HN discussion in LLM-optimized format"""
    story = result['story']
    lines = []
    
    # Story header
    lines.append(f"STORY: {story.get('title', 'N/A')}")
    lines.append(f"URL: {story.get('url', 'N/A')}")
    lines.append(f"AUTHOR: {story.get('author', 'N/A')} | POINTS: {story.get('points', 'N/A')} | TIME: {story.get('time', 'N/A')}")
    lines.append(f"TOTAL_COMMENTS: {result['total_comments']}")
    lines.append("")
    
    # Format all comments
    for i, comment in enumerate(result['comments'], 1):
        lines.append(f"COMMENT #{i}")
        lines.append(format_comment_llm(comment))
        lines.append("")
    
    return '\n'.join(lines)


def extract_item_id(hn_url: str) -> str:
    """Extract HN item ID from URL or return the ID directly"""
    if 'item?id=' in hn_url:
        # Extract from URL
        return hn_url.split('item?id=')[1].split('&')[0]
    else:
        # Assume it's already an ID
        return hn_url


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available tools"""
    return [
        types.Tool(
            name="get_hn_content",
            description="Get Hacker News comments and the content of the linked article. Provide a HN URL (e.g., https://news.ycombinator.com/item?id=46130187) or just the item ID (e.g., 46130187)",
            inputSchema={
                "type": "object",
                "properties": {
                    "hn_url": {
                        "type": "string",
                        "description": 'Hacker News item URL or ID (e.g., "https://news.ycombinator.com/item?id=46130187" or "46130187")'
                    }
                },
                "required": ["hn_url"]
            }
        )
    ]


@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Handle tool execution requests"""
    
    if name != "get_hn_content":
        raise ValueError(f"Unknown tool: {name}")
    
    if not arguments or "hn_url" not in arguments:
        raise ValueError("Missing required argument: hn_url")
    
    hn_url = arguments["hn_url"]
    
    try:
        # Extract item ID
        item_id = extract_item_id(hn_url)
        
        # Parse HN comments
        hn_result = parse_hn_comments(item_id)
        
        # Format HN discussion
        hn_discussion = format_hn_discussion(hn_result)
        
        # Get article URL
        article_url = hn_result['story'].get('url', '')
        article_content = ""
        
        # Fetch article content if URL exists and is external
        if article_url and not article_url.startswith('https://news.ycombinator.com'):
            try:
                # Use Firecrawl to scrape article
                scrape_result = scrape_url(
                    target_url=article_url,
                    only_main_content=True
                )
                article_content = get_markdown(scrape_result)
            except FirecrawlError as e:
                article_content = f"[Error fetching article content: {str(e)}]"
            except Exception as e:
                article_content = f"[Unexpected error fetching article: {str(e)}]"
        else:
            article_content = "[No external article URL - this is a text post or Ask HN]"
        
        # Combine results
        result_text = f"""# ARTICLE CONTENT

{article_content}

---

# HACKER NEWS DISCUSSION

{hn_discussion}"""
        
        return [
            types.TextContent(
                type="text",
                text=result_text
            )
        ]
        
    except Exception as e:
        return [
            types.TextContent(
                type="text",
                text=f"Error: {str(e)}"
            )
        ]


async def main():
    """Main entry point for the MCP server"""
    # Run the server using stdin/stdout streams
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="hackernews-mcp",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
