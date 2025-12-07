import sys
import argparse
from typing import Dict, Any, Optional
from parse_hn_comments import parse_hn_comments
from firecrawl import scrape_url, get_markdown, FirecrawlError


def get_hn_content(hn_url: str, api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Get both HN comments and the content of the linked URL.
    
    Args:
        hn_url: Hacker News item URL (e.g., 'https://news.ycombinator.com/item?id=46130187' or just '46130187')
        api_key: Optional Firecrawl API key (if None, reads from FIRECRAWL_API_KEY env var)
    
    Returns:
        Dictionary containing:
            - 'hn_comments': Dict with story info and comments from HN
            - 'url_content': String with markdown content from the linked URL
            - 'story_url': The actual URL that was scraped
    
    Raises:
        ValueError: If HN URL/ID is invalid
        FirecrawlError: If content scraping fails
        Exception: For other errors
    """
    # Extract item ID from URL or use directly if it's just an ID
    if 'item?id=' in hn_url:
        item_id = hn_url.split('item?id=')[1].split('&')[0]
    else:
        item_id = hn_url.strip()
    
    # Validate item ID
    if not item_id.isdigit():
        raise ValueError(f"Invalid HN item ID: {item_id}")
    
    print(f"Fetching HN comments for item {item_id}...")
    
    # Get HN comments
    hn_data = parse_hn_comments(item_id)
    
    # Extract the story URL
    story_url = hn_data.get('story', {}).get('url', '')
    
    if not story_url:
        return {
            'hn_comments': hn_data,
            'url_content': None,
            'story_url': None,
            'error': 'No URL found in the HN story (might be a text post)'
        }
    
    # Skip if it's a HN internal URL
    if story_url.startswith('https://news.ycombinator.com'):
        return {
            'hn_comments': hn_data,
            'url_content': None,
            'story_url': story_url,
            'error': 'Story links to HN itself (Ask HN, Show HN, etc.)'
        }
    
    print(f"Fetching content from: {story_url}")
    
    # Get URL content using Firecrawl
    try:
        content_data = scrape_url(
            target_url=story_url,
            api_key=api_key,
            only_main_content=True,
            formats=["markdown"]
        )
        url_content = get_markdown(content_data)
    except FirecrawlError as e:
        return {
            'hn_comments': hn_data,
            'url_content': None,
            'story_url': story_url,
            'error': f'Failed to fetch URL content: {str(e)}'
        }
    
    return {
        'hn_comments': hn_data,
        'url_content': url_content,
        'story_url': story_url
    }


def print_result(result: Dict[str, Any], compact: bool = False):
    """
    Pretty print the result.
    
    Args:
        result: Result dictionary from get_hn_content
        compact: Whether to use compact format (LLM-optimized)
    """
    hn_data = result['hn_comments']
    story = hn_data.get('story', {})
    
    if compact:
        # Compact LLM-optimized format
        print(f"STORY: {story.get('title', 'N/A')}")
        print(f"URL: {story.get('url', 'N/A')}")
        print(f"AUTHOR: {story.get('author', 'N/A')} | POINTS: {story.get('points', 'N/A')} | TIME: {story.get('time', 'N/A')}")
        print(f"TOTAL_COMMENTS: {hn_data.get('total_comments', 0)}")
        print()
        
        if result.get('error'):
            print(f"WARNING: {result['error']}")
            print()
        
        # Print comments
        from parse_hn_comments import print_comment_llm
        for i, comment in enumerate(hn_data.get('comments', []), 1):
            print(f"COMMENT #{i}")
            print_comment_llm(comment)
            print()
        
        # Print URL content
        if result.get('url_content'):
            print("=" * 80)
            print("URL CONTENT")
            print("=" * 80)
            print(result['url_content'])
    else:
        # Standard verbose format
        print("=" * 80)
        print("HACKER NEWS STORY")
        print("=" * 80)
        print(f"Title: {story.get('title', 'N/A')}")
        print(f"URL: {story.get('url', 'N/A')}")
        print(f"Author: {story.get('author', 'N/A')}")
        print(f"Points: {story.get('points', 'N/A')}")
        print(f"Time: {story.get('time', 'N/A')}")
        print(f"Total Comments: {hn_data.get('total_comments', 0)}")
        print("=" * 80)
        print()
        
        if result.get('error'):
            print(f"⚠️  Warning: {result['error']}")
            print()
        
        # Print comments
        from parse_hn_comments import print_comment
        print("COMMENTS")
        print("=" * 80)
        for i, comment in enumerate(hn_data.get('comments', []), 1):
            print(f"\n[Comment {i}]")
            print_comment(comment)
        
        # Print URL content
        if result.get('url_content'):
            print("\n" + "=" * 80)
            print("URL CONTENT")
            print("=" * 80)
            print(result['url_content'])
            print("\n" + "=" * 80)


def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(
        description='Get HN comments and URL content for a Hacker News post',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python hello.py 46130187
  python hello.py https://news.ycombinator.com/item?id=46130187
  python hello.py 46130187 --compact
  python hello.py 46130187 --api-key YOUR_API_KEY
        """
    )
    parser.add_argument('hn_url', help='HN item ID or full URL')
    parser.add_argument('--compact', action='store_true',
                        help='Use compact LLM-optimized output format')
    parser.add_argument('--api-key', help='Firecrawl API key (optional, can use env var)')
    
    args = parser.parse_args()
    
    try:
        result = get_hn_content(args.hn_url, api_key=args.api_key)
        print_result(result, compact=args.compact)
        
        # Exit with warning code if there was an error fetching URL content
        if result.get('error'):
            sys.exit(2)
        
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except FirecrawlError as e:
        print(f"Firecrawl Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
