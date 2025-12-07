import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import sys
import argparse


class HNComment:
    """Represents a Hacker News comment with its metadata and replies"""
    
    def __init__(self, comment_id: str, author: str, time: str, text: str, 
                 indent_level: int = 0, parent_id: Optional[str] = None):
        self.comment_id = comment_id
        self.author = author
        self.time = time
        self.text = text
        self.indent_level = indent_level
        self.parent_id = parent_id
        self.replies: List[HNComment] = []
    
    def to_dict(self) -> Dict:
        """Convert comment to dictionary format"""
        return {
            'id': self.comment_id,
            'author': self.author,
            'time': self.time,
            'text': self.text,
            'indent_level': self.indent_level,
            'parent_id': self.parent_id,
            'replies': [reply.to_dict() for reply in self.replies]
        }
    
    def __repr__(self) -> str:
        indent = "  " * self.indent_level
        return f"{indent}[{self.author}] {self.time}\n{indent}{self.text[:100]}..."


def parse_hn_comments(item_id: str) -> Dict:
    """
    Parse comments from a Hacker News item page.
    
    Args:
        item_id: The Hacker News item ID (e.g., '46130187')
    
    Returns:
        Dictionary containing story info and list of comments
    """
    url = f"https://news.ycombinator.com/item?id={item_id}"
    
    # Make HTTP request
    response = requests.get(url)
    response.raise_for_status()
    
    # Parse HTML
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Extract story information
    story_info = extract_story_info(soup)
    
    # Extract all comments
    comments = extract_comments(soup)
    
    return {
        'story': story_info,
        'comments': comments,
        'total_comments': len(comments)
    }


def extract_story_info(soup: BeautifulSoup) -> Dict:
    """Extract story title and metadata"""
    story_info = {}
    
    # Get title
    title_element = soup.find('span', class_='titleline')
    if title_element:
        link_element = title_element.find('a')
        if link_element:
            story_info['title'] = link_element.text
            story_info['url'] = link_element.get('href', '')
    
    # Get metadata (points, author, time)
    subtext = soup.find('td', class_='subtext')
    if subtext:
        # Points
        score_element = subtext.find('span', class_='score')
        story_info['points'] = score_element.text if score_element else 'N/A'
        
        # Author
        author_element = subtext.find('a', class_='hnuser')
        story_info['author'] = author_element.text if author_element else 'N/A'
        
        # Time
        age_element = subtext.find('span', class_='age')
        if age_element:
            story_info['time'] = age_element.get('title', age_element.text)
    
    return story_info


def extract_comments(soup: BeautifulSoup) -> List[Dict]:
    """
    Extract all comments from the page, maintaining hierarchy.
    
    Returns:
        List of comment dictionaries with nested replies
    """
    comments = []
    comment_tree = {}  # Store all comments by ID for building hierarchy
    
    # Find all comment rows
    comment_rows = soup.find_all('tr', class_='athing comtr')
    
    for row in comment_rows:
        comment_id = row.get('id', '')
        
        # Get indent level (determines nesting)
        indent_element = row.find('td', class_='ind')
        indent_level = 0
        if indent_element:
            indent_img = indent_element.find('img')
            if indent_img and indent_img.get('width'):
                # Width is indent_level * 40
                indent_level = int(indent_img.get('width', 0)) // 40
        
        # Get comment metadata
        comment_head = row.find('div', class_='commtext')
        if not comment_head:
            continue
        
        # Get author
        author_element = row.find('a', class_='hnuser')
        author = author_element.text if author_element else '[deleted]'
        
        # Get time
        age_element = row.find('span', class_='age')
        time = age_element.get('title', age_element.text) if age_element else 'N/A'
        
        # Get comment text
        text_element = row.find('div', class_='commtext')
        if text_element:
            # Replace truncated URLs with full URLs from href attributes
            for link in text_element.find_all('a'):
                href = link.get('href', '')
                if href and href.startswith('http'):
                    # Replace the link text with the full URL
                    link.string = href
            
            # Remove the reply link and other UI elements
            for span in text_element.find_all('span', class_='reply'):
                span.decompose()
            text = text_element.get_text(separator='\n', strip=True)
        else:
            text = '[deleted]'
        
        # Create comment object
        comment = HNComment(
            comment_id=comment_id,
            author=author,
            time=time,
            text=text,
            indent_level=indent_level
        )
        
        # Store in tree
        comment_tree[comment_id] = comment
        
        # If it's a top-level comment (indent 0), add to main list
        if indent_level == 0:
            comments.append(comment.to_dict())
    
    # Build nested structure
    comments_with_nesting = build_nested_structure(comment_rows, soup)
    
    return comments_with_nesting


def build_nested_structure(comment_rows, soup: BeautifulSoup) -> List[Dict]:
    """
    Build a nested comment structure with replies properly organized.
    """
    all_comments = []
    comment_stack = []  # Stack to track parent comments at each level
    
    for row in comment_rows:
        comment_id = row.get('id', '')
        
        # Get indent level
        indent_element = row.find('td', class_='ind')
        indent_level = 0
        if indent_element:
            indent_img = indent_element.find('img')
            if indent_img and indent_img.get('width'):
                indent_level = int(indent_img.get('width', 0)) // 40
        
        # Get author
        author_element = row.find('a', class_='hnuser')
        author = author_element.text if author_element else '[deleted]'
        
        # Get time
        age_element = row.find('span', class_='age')
        time = age_element.get('title', age_element.text) if age_element else 'N/A'
        
        # Get comment text
        text_element = row.find('div', class_='commtext')
        if text_element:
            # Replace truncated URLs with full URLs from href attributes
            for link in text_element.find_all('a'):
                href = link.get('href', '')
                if href and href.startswith('http'):
                    # Replace the link text with the full URL
                    link.string = href
            
            for span in text_element.find_all('span', class_='reply'):
                span.decompose()
            text = text_element.get_text(separator='\n', strip=True)
        else:
            text = '[deleted]'
        
        # Create comment dict
        comment = {
            'id': comment_id,
            'author': author,
            'time': time,
            'text': text,
            'indent_level': indent_level,
            'replies': []
        }
        
        # Adjust stack to current indent level
        comment_stack = comment_stack[:indent_level]
        
        # Add comment to appropriate location
        if indent_level == 0:
            # Top-level comment
            all_comments.append(comment)
            comment_stack = [comment]
        else:
            # Reply to parent
            if comment_stack:
                parent = comment_stack[-1]
                parent['replies'].append(comment)
                comment_stack.append(comment)
    
    return all_comments


def print_comment(comment: Dict, indent: int = 0):
    """Pretty print a comment with proper indentation"""
    prefix = "  " * indent
    print(f"{prefix}{'─' * 60}")
    print(f"{prefix}Author: {comment['author']}")
    print(f"{prefix}Time: {comment['time']}")
    print(f"{prefix}ID: {comment['id']}")
    print(f"{prefix}Text:")
    
    # Print text with indentation
    text_lines = comment['text'].split('\n')
    for line in text_lines:
        print(f"{prefix}  {line}")
    
    # Print replies
    if comment['replies']:
        print(f"{prefix}Replies: {len(comment['replies'])}")
        for reply in comment['replies']:
            print_comment(reply, indent + 1)


def print_comment_llm(comment: Dict, indent: int = 0):
    """Print comment in compact LLM-optimized format"""
    prefix = "  " * indent
    
    # Determine comment type based on indent
    comment_type = "REPLY" if indent > 0 else "COMMENT"
    
    # Print compact header
    print(f"{prefix}{comment_type} [{comment['author']} @ {comment['time']}] ID: {comment['id']}")
    
    # Print text directly without extra formatting
    text_lines = comment['text'].split('\n')
    for line in text_lines:
        print(f"{prefix}{line}")
    
    # Print blank line only between top-level comments
    if indent == 0 and comment['replies']:
        print()
    
    # Recursively print replies
    for reply in comment['replies']:
        print_comment_llm(reply, indent + 1)


def main():
    """Main function to parse and display comments"""
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description='Parse comments from Hacker News items',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python parse_hn_comments.py 46130187
  python parse_hn_comments.py https://news.ycombinator.com/item?id=46130187
  python parse_hn_comments.py 46130187 --llm
        """
    )
    parser.add_argument('item_id', help='HN item ID or full URL')
    parser.add_argument('--llm', action='store_true', 
                        help='Output in compact LLM-optimized format (saves tokens)')
    
    args = parser.parse_args()
    
    # Extract item ID from argument
    arg = args.item_id
    if 'item?id=' in arg:
        # Extract from URL
        item_id = arg.split('item?id=')[1].split('&')[0]
    else:
        item_id = arg
    
    if not args.llm:
        print(f"Fetching comments for item {item_id}...\n")
    
    try:
        result = parse_hn_comments(item_id)
        story = result['story']
        
        if args.llm:
            # LLM-optimized compact format
            print(f"STORY: {story.get('title', 'N/A')}")
            print(f"URL: {story.get('url', 'N/A')}")
            print(f"AUTHOR: {story.get('author', 'N/A')} | POINTS: {story.get('points', 'N/A')} | TIME: {story.get('time', 'N/A')}")
            print(f"TOTAL_COMMENTS: {result['total_comments']}")
            print()
            
            # Print comments in compact format
            for i, comment in enumerate(result['comments'], 1):
                print(f"COMMENT #{i}")
                print_comment_llm(comment)
                print()
        else:
            # Standard verbose format
            print("=" * 80)
            print("STORY INFORMATION")
            print("=" * 80)
            print(f"Title: {story.get('title', 'N/A')}")
            print(f"URL: {story.get('url', 'N/A')}")
            print(f"Author: {story.get('author', 'N/A')}")
            print(f"Points: {story.get('points', 'N/A')}")
            print(f"Time: {story.get('time', 'N/A')}")
            print(f"\nTotal Comments: {result['total_comments']}")
            print("=" * 80)
            print()
            
            # Display comments
            print("COMMENTS")
            print("=" * 80)
            for i, comment in enumerate(result['comments'], 1):
                print(f"\n[Comment {i}]")
                print_comment(comment)
            
            print("\n" + "=" * 80)
            print(f"Successfully parsed {result['total_comments']} comments!")
        
    except requests.RequestException as e:
        print(f"Error fetching Hacker News item: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error parsing comments: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
