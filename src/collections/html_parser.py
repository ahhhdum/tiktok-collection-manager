from pathlib import Path
from typing import Dict, List, TypedDict
import re
from bs4 import BeautifulSoup
from ..utils.logger import logger

class VideoMetadata(TypedDict):
    video_id: str
    creator: str
    description: str
    thumbnail_url: str

def parse_collection_videos_html(html_content: str) -> List[VideoMetadata]:
    """
    Parse video IDs and metadata from a collection page HTML content.
    Returns a list of video metadata dictionaries.
    """
    if not html_content.strip():
        logger.error("Empty HTML content provided")
        return []
        
    try:
        # Parse HTML with BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find all video items
        videos: List[VideoMetadata] = []
        video_items = soup.find_all('div', {'data-e2e': 'collection-item'})
        
        if not video_items:
            logger.error("No video items found in HTML. Check if the page structure has changed.")
            return []
            
        logger.info(f"Found {len(video_items)} video items to process")
        
        for idx, item in enumerate(video_items, 1):
            try:
                # Find the video link
                video_link = item.find('a', class_='css-1mdo0pl-AVideoContainer')
                if not video_link or not video_link.get('href'):
                    logger.warning(f"Video {idx}: Found video without link, skipping...")
                    continue
                
                # Extract video ID from URL
                video_url = video_link['href']
                video_id_match = re.search(r'/video/(\d+)', video_url)
                if not video_id_match:
                    logger.warning(f"Video {idx}: Could not extract video ID from URL: {video_url}")
                    continue
                
                video_id = video_id_match.group(1)
                
                # Get creator username
                creator_elem = item.find('p', {'data-e2e': 'collection-item-username'})
                creator = creator_elem.text if creator_elem else "unknown"
                if creator == "unknown":
                    logger.warning(f"Video {idx} ({video_id}): Could not find creator username")
                
                # Get video description from aria-label and img alt
                description_div = item.find('div', {'aria-label': True})
                img = item.find('img', {'alt': True})
                
                # Prefer aria-label description if available, fallback to img alt
                description = description_div['aria-label'] if description_div else (img['alt'] if img and img.get('alt') else "")
                if not description:
                    logger.warning(f"Video {idx} ({video_id}): No description found")
                
                # Get thumbnail URL
                thumbnail_url = img['src'] if img and img.get('src') else ""
                if not thumbnail_url:
                    logger.warning(f"Video {idx} ({video_id}): No thumbnail URL found")
                
                videos.append({
                    'video_id': video_id,
                    'creator': creator,
                    'description': description,
                    'thumbnail_url': thumbnail_url
                })
                
                logger.info(f"Successfully parsed video {idx}/{len(video_items)}: {video_id} by {creator}")
                
            except Exception as e:
                logger.error(f"Failed to parse video {idx}: {str(e)}")
                continue
        
        logger.info(f"Successfully parsed {len(videos)}/{len(video_items)} videos")
        return videos
    
    except Exception as e:
        logger.error(f"Failed to parse collection videos HTML: {str(e)}")
        return []

def parse_collections_html(html_file: Path) -> Dict[str, str]:
    """
    Parse collections from saved TikTok HTML content.
    Returns a dictionary of collection names and their URLs.
    """
    try:
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse HTML with BeautifulSoup
        soup = BeautifulSoup(content, 'html.parser')
        
        # Find all collection containers
        collections: Dict[str, str] = {}
        collection_items = soup.find_all('div', {'data-e2e': 'collection-list-item'})
        
        for item in collection_items:
            # Get collection name from img alt attribute
            name_img = item.find('img')
            if not name_img or not name_img.get('alt'):
                logger.warning("Found collection without name, skipping...")
                continue
            
            collection_name = name_img['alt']
            
            # Get collection URL from href
            link = item.find('a')
            if not link or not link.get('href'):
                logger.warning(f"No link found for collection '{collection_name}', skipping...")
                continue
            
            collection_url = f"https://www.tiktok.com{link['href']}"
            collections[collection_name] = collection_url
            
            logger.info(f"Found collection '{collection_name}' with URL: {collection_url}")
        
        return collections
    
    except Exception as e:
        logger.error(f"Failed to parse collections HTML: {e}")
        return {} 