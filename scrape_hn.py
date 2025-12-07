import requests
from bs4 import BeautifulSoup
from typing import List, Dict


def scrape_hacker_news() -> List[Dict[str, str]]:
    """
    Scrape Hacker News front page for stories.
    
    Returns:
        List of dictionaries containing story information
    """
    url = "https://news.ycombinator.com/"
    
    # Make HTTP request
    response = requests.get(url)
    response.raise_for_status()
    
    # Parse HTML
    soup = BeautifulSoup(response.text, 'html.parser')
    
    stories = []
    
    # Find all story rows (they have class 'athing')
    story_rows = soup.find_all('tr', class_='athing')
    
    for story in story_rows:
        # Get the title link
        title_element = story.find('span', class_='titleline')
        if not title_element:
            continue
            
        link_element = title_element.find('a')
        if not link_element:
            continue
            
        title = link_element.text
        link = link_element.get('href', '')
        
        # Get the subtext row (contains points, user, time, comments)
        subtext_row = story.find_next_sibling('tr')
        if not subtext_row:
            continue
            
        subtext = subtext_row.find('td', class_='subtext')
        if not subtext:
            continue
        
        # Extract points
        points_element = subtext.find('span', class_='score')
        points = points_element.text if points_element else "0 points"
        
        # Extract time
        age_element = subtext.find('span', class_='age')
        time_posted = age_element.get('title', '') if age_element else "N/A"
        time_ago = age_element.text if age_element else "N/A"
        
        # Extract comment count
        comment_links = subtext.find_all('a')
        comments = "0 comments"
        for link_tag in comment_links:
            if 'item?id=' in link_tag.get('href', ''):
                comment_text = link_tag.text
                if 'comment' in comment_text:
                    comments = comment_text
                    break
        
        story_data = {
            'title': title,
            'link': link,
            'points': points,
            'comments': comments,
            'time_posted': time_posted,
            'time_ago': time_ago
        }
        
        stories.append(story_data)
    
    return stories


def main():
    """Main function to run the scraper and display results"""
    print("Fetching Hacker News stories...\n")
    
    try:
        stories = scrape_hacker_news()
        
        # Sort stories by points (high to low)
        def get_points(story):
            # Extract numeric value from "X points" string
            points_str = story['points'].split()[0]
            try:
                return int(points_str)
            except ValueError:
                return 0
        
        stories.sort(key=get_points, reverse=True)
        
        print(f"Found {len(stories)} stories (sorted by points):\n")
        print("=" * 100)
        
        for i, story in enumerate(stories, 1):
            print(f"\n{i}. {story['title']}")
            print(f"   Link: {story['link']}")
            print(f"   Points: {story['points']}")
            print(f"   Comments: {story['comments']}")
            print(f"   Time: {story['time_ago']} (posted: {story['time_posted']})")
            print("-" * 100)
    
    except requests.RequestException as e:
        print(f"Error fetching Hacker News: {e}")
    except Exception as e:
        print(f"Error parsing data: {e}")


if __name__ == "__main__":
    main()
