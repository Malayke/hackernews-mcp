#!/usr/bin/env python3
"""
Test script for Hacker News MCP Server
Tests the server functionality without needing MCP client connection
"""

import sys
import asyncio
from server import (
    extract_item_id,
    format_comment_llm,
    format_hn_discussion,
    handle_list_tools,
    handle_call_tool
)


def test_extract_item_id():
    """Test item ID extraction from various inputs"""
    print("Testing extract_item_id...")
    
    test_cases = [
        ("https://news.ycombinator.com/item?id=42616867", "42616867"),
        ("https://news.ycombinator.com/item?id=12345&p=1", "12345"),
        ("42616867", "42616867"),
    ]
    
    for input_val, expected in test_cases:
        result = extract_item_id(input_val)
        status = "✓" if result == expected else "✗"
        print(f"  {status} Input: {input_val} -> {result} (expected: {expected})")
    
    print()


async def test_list_tools():
    """Test listing available tools"""
    print("Testing list_tools...")
    
    tools = await handle_list_tools()
    print(f"  ✓ Found {len(tools)} tool(s)")
    
    for tool in tools:
        print(f"    - {tool.name}: {tool.description}")
        print(f"      Required params: {tool.inputSchema.get('required', [])}")
    
    print()


async def test_get_hn_content_with_id():
    """Test get_hn_content tool with a HN item ID"""
    print("Testing get_hn_content with item ID...")
    
    # Using a well-known HN post (replace with a recent valid ID if needed)
    test_id = "42616867"  # A HN post ID
    
    try:
        result = await handle_call_tool(
            name="get_hn_content",
            arguments={"hn_url": test_id}
        )
        
        if result and len(result) > 0:
            content = result[0].text
            print(f"  ✓ Successfully fetched content for ID {test_id}")
            print(f"  ✓ Response length: {len(content)} characters")
            
            # Check for expected sections
            if "# ARTICLE CONTENT" in content:
                print("  ✓ Contains article content section")
            if "# HACKER NEWS DISCUSSION" in content:
                print("  ✓ Contains HN discussion section")
            if "STORY:" in content:
                print("  ✓ Contains story information")
            
            # Show a preview
            preview = content[:500] + "..." if len(content) > 500 else content
            print("\n  Preview of response:")
            print("  " + "-" * 60)
            for line in preview.split('\n')[:20]:
                print(f"  {line}")
            print("  " + "-" * 60)
        else:
            print("  ✗ No content returned")
            
    except Exception as e:
        print(f"  ✗ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print()


async def test_get_hn_content_with_url():
    """Test get_hn_content tool with a full HN URL"""
    print("Testing get_hn_content with full URL...")
    
    test_url = "https://news.ycombinator.com/item?id=42616867"
    
    try:
        result = await handle_call_tool(
            name="get_hn_content",
            arguments={"hn_url": test_url}
        )
        
        if result and len(result) > 0:
            content = result[0].text
            print(f"  ✓ Successfully fetched content for URL")
            print(f"  ✓ Response length: {len(content)} characters")
        else:
            print("  ✗ No content returned")
            
    except Exception as e:
        print(f"  ✗ Error: {e}")
    
    print()


async def test_error_handling():
    """Test error handling with invalid inputs"""
    print("Testing error handling...")
    
    # Test with invalid tool name
    try:
        await handle_call_tool(name="invalid_tool", arguments={})
        print("  ✗ Should have raised error for invalid tool")
    except ValueError as e:
        print(f"  ✓ Correctly raised error for invalid tool: {e}")
    
    # Test with missing argument
    try:
        await handle_call_tool(name="get_hn_content", arguments={})
        print("  ✗ Should have raised error for missing argument")
    except ValueError as e:
        print(f"  ✓ Correctly raised error for missing argument: {e}")
    
    print()


async def main():
    """Run all tests"""
    print("=" * 70)
    print("HACKER NEWS MCP SERVER - TEST SUITE")
    print("=" * 70)
    print()
    
    # Synchronous tests
    test_extract_item_id()
    
    # Async tests
    await test_list_tools()
    await test_get_hn_content_with_id()
    await test_get_hn_content_with_url()
    await test_error_handling()
    
    print("=" * 70)
    print("TEST SUITE COMPLETED")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
