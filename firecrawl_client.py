import os
import sys
import requests
from dotenv import load_dotenv
from typing import Optional, Dict, Any, cast

load_dotenv()


class FirecrawlError(Exception):
    """Base exception for Firecrawl API errors"""
    pass


class FirecrawlAPIKeyError(FirecrawlError):
    """Raised when API key is missing or invalid"""
    pass


class FirecrawlConnectionError(FirecrawlError):
    """Raised when connection to API fails"""
    pass


class FirecrawlResponseError(FirecrawlError):
    """Raised when API returns an error or unexpected response"""
    pass


def scrape_url(
    target_url: str,
    api_key: Optional[str] = None,
    only_main_content: bool = False,
    max_age: int = 172800000,
    parsers: Optional[list] = None,
    formats: Optional[list] = None,
    timeout: int = 30
) -> Dict[str, Any]:
    """
    Scrape a URL using Firecrawl API.
    
    Args:
        target_url: The URL to scrape
        api_key: Firecrawl API key (if None, reads from FIRECRAWL_API_KEY env var)
        only_main_content: Whether to return only main content
        max_age: Maximum age of cached content in milliseconds
        parsers: List of parsers to use (default: ["pdf"])
        formats: List of output formats (default: ["markdown"])
        timeout: Request timeout in seconds
    
    Returns:
        Dict containing the API response data
    
    Raises:
        FirecrawlAPIKeyError: If API key is missing
        FirecrawlConnectionError: If connection fails
        FirecrawlResponseError: If API returns an error or unexpected response
    """
    # Get API key from parameter or environment
    if api_key is None:
        api_key = os.getenv('FIRECRAWL_API_KEY')
    
    if not api_key:
        raise FirecrawlAPIKeyError(
            "FIRECRAWL_API_KEY not found. Please set it in .env file or pass as parameter"
        )
    
    # Set defaults
    if parsers is None:
        parsers = ["pdf"]
    if formats is None:
        formats = ["markdown"]
    
    url = "https://api.firecrawl.dev/v2/scrape"
    
    payload = {
        "url": target_url,
        "onlyMainContent": only_main_content,
        "maxAge": max_age,
        "parsers": parsers,
        "formats": formats
    }
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    response: Optional[requests.Response] = None
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=timeout)
        response.raise_for_status()
        
        try:
            data = response.json()
        except ValueError as e:
            raise FirecrawlResponseError(
                f"Failed to parse JSON response: {e}\nResponse text: {response.text}"
            )
        
        return data
        
    except requests.exceptions.Timeout:
        raise FirecrawlConnectionError(f"Request timed out after {timeout} seconds")
    
    except requests.exceptions.ConnectionError as e:
        raise FirecrawlConnectionError(f"Failed to connect to the API: {e}")
    
    except requests.exceptions.HTTPError as e:
        # HTTPError is only raised by response.raise_for_status(), so response must exist
        assert response is not None
        error_msg = f"HTTP error occurred: {e}\nStatus code: {response.status_code}"
        try:
            error_data = response.json()
            error_msg += f"\nError details: {error_data}"
        except ValueError:
            error_msg += f"\nResponse text: {response.text}"
        raise FirecrawlResponseError(error_msg)
    
    except requests.exceptions.RequestException as e:
        raise FirecrawlConnectionError(f"Request error: {e}")


def get_markdown(data: Dict[str, Any]) -> str:
    """
    Extract markdown content from Firecrawl API response.
    
    Args:
        data: The response data from scrape_url()
    
    Returns:
        The markdown content as a string
    
    Raises:
        FirecrawlResponseError: If expected fields are missing
    """
    if 'data' not in data:
        raise FirecrawlResponseError(
            f"'data' field not found in response. Response: {data}"
        )
    
    if 'markdown' not in data['data']:
        available_fields = list(data['data'].keys())
        raise FirecrawlResponseError(
            f"'markdown' field not found in data. Available fields: {available_fields}"
        )
    
    return data['data']['markdown']


def main():
    """Main function for CLI usage"""
    try:
        # Scrape the URL
        data = scrape_url(
            target_url="https://snoutcover.com/billie-story",
            only_main_content=False
        )
        
        # Extract and print markdown
        markdown_content = get_markdown(data)
        print(markdown_content)
        
    except FirecrawlError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
