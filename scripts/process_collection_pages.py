"""Script to download and process TikTok collection pages."""

import json
import re
from pathlib import Path
import argparse
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from bs4 import BeautifulSoup
import logging

from src.utils.logger import logger
from src.utils.config import COLLECTIONS_DATA
from src.collections.html_parser import VideoMetadata

# Set logging level to DEBUG
logger.setLevel(logging.DEBUG)

@dataclass
class CollectionVideo:
    """Represents a video in a collection with its metadata."""
    video_id: str
    creator: str
    creator_id: str
    description: str
    url: str
    thumbnail_url: str
    collection_name: str

def sanitize_filename(name: str) -> str:
    """Convert a collection name to a valid filename."""
    # Replace invalid filename characters with underscores
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', name)
    return f"{sanitized}.html"

def save_collection_page(collection_name: str, html_content: str) -> Path:
    """Save collection page HTML to a file."""
    # Create the collection pages directory if it doesn't exist
    output_dir = Path("data/collection_pages")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create sanitized filename
    filename = sanitize_filename(collection_name)
    output_path = output_dir / filename
    
    # Save the HTML content
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    logger.info(f"Saved collection page for '{collection_name}' to {output_path}")
    return output_path

def parse_collection_page(html_content: str, collection_name: str) -> List[CollectionVideo]:
    """Parse videos and their metadata from a collection page."""
    videos: List[CollectionVideo] = []
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Find all video items in the collection
    logger.debug(f"Parsing collection page: {collection_name}")
    video_items = soup.find_all('div', {'data-e2e': 'collection-item'})
    logger.debug(f"Found {len(video_items)} video items in {collection_name}")
    
    for item in video_items:
        try:
            # Get video link and ID
            video_link = item.find('a', class_='css-1mdo0pl-AVideoContainer')
            if not video_link or not video_link.get('href'):
                logger.debug(f"No video link found in item: {item}")
                continue
            
            video_url = video_link['href']
            if not video_url.startswith('http'):
                video_url = f"https://www.tiktok.com{video_url}"
            
            video_id_match = re.search(r'/video/(\d+)', video_url)
            if not video_id_match:
                logger.debug(f"Could not extract video ID from URL: {video_url}")
                continue
            
            video_id = video_id_match.group(1)
            logger.debug(f"Found video ID: {video_id}")
            
            # Get creator info
            creator_elem = item.find('p', {'data-e2e': 'collection-item-username'})
            creator = creator_elem.text if creator_elem else "unknown"
            
            # Get creator ID from their profile link
            creator_link = item.find('a', {'data-e2e': 'collection-item-avatar'})
            creator_id = "unknown"
            if creator_link and creator_link.get('href'):
                creator_id_match = re.search(r'/@([^?]+)', creator_link['href'])
                if creator_id_match:
                    creator_id = creator_id_match.group(1)
            
            # Get video description and thumbnail
            img = item.find('img', {'alt': True})
            description = img['alt'] if img and img.get('alt') else ""
            thumbnail_url = img['src'] if img and img.get('src') else ""
            
            # Create video object
            video = CollectionVideo(
                video_id=video_id,
                creator=creator,
                creator_id=creator_id,
                description=description,
                url=video_url,
                thumbnail_url=thumbnail_url,
                collection_name=collection_name
            )
            videos.append(video)
            logger.debug(f"Successfully parsed video {video_id} by {creator}")
            
        except Exception as e:
            logger.error(f"Failed to parse video in collection '{collection_name}': {e}")
            continue
    
    return videos

def process_collection_page(html_file: Path) -> List[CollectionVideo]:
    """Parse videos and their metadata from a collection page."""
    try:
        # Get collection name from filename
        collection_name = html_file.stem
        logger.debug(f"Processing collection page: {collection_name}")
        
        # Read HTML content
        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                html_content = f.read()
        except Exception as e:
            logger.error(f"Failed to read HTML file {html_file}: {str(e)}")
            return []
            
        if not html_content.strip():
            logger.error(f"Empty HTML content in file {html_file}")
            return []
            
        # Parse videos from HTML
        videos = parse_collection_page(html_content, collection_name)
        if not videos:
            logger.error(f"No videos found in collection '{collection_name}' ({html_file})")
            return []
            
        logger.info(f"Found {len(videos)} videos in collection '{collection_name}'")
        return videos
        
    except Exception as e:
        logger.error(f"Failed to process collection page {html_file}: {str(e)}")
        return []

def save_video_metadata(videos: List[CollectionVideo], output_file: Optional[Path] = None) -> None:
    """Save video metadata to a JSON file."""
    if output_file is None:
        output_file = Path("data/collection_videos.json")
    
    # Convert to dictionary format
    video_data = {
        video.video_id: asdict(video)
        for video in videos
    }
    
    # Save to file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(video_data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Saved metadata for {len(videos)} videos to {output_file}")

def main():
    """Process TikTok collection pages and save video metadata."""
    parser = argparse.ArgumentParser(description="Process TikTok collection pages")
    parser.add_argument('--input-dir', type=Path, default=Path('data/collection_pages'),
                      help='Directory containing collection HTML files')
    parser.add_argument('--input-file', type=Path,
                      help='Single HTML file to process')
    args = parser.parse_args()
    
    try:
        # Process single file or directory
        if args.input_file:
            if not args.input_file.exists():
                logger.error(f"Input file not found: {args.input_file}")
                return
            html_files = [args.input_file]
        else:
            if not args.input_dir.exists():
                logger.error(f"Input directory not found: {args.input_dir}")
                return
            html_files = list(args.input_dir.glob('*.html'))
            
        if not html_files:
            logger.error("No HTML files found to process")
            return
            
        logger.info(f"Found {len(html_files)} collection pages to process")
        
        # Process each HTML file
        all_videos = []
        for html_file in html_files:
            try:
                videos = process_collection_page(html_file)
                all_videos.extend(videos)
            except Exception as e:
                logger.error(f"Failed to process {html_file}: {str(e)}")
                continue
            
        if not all_videos:
            logger.error("No videos found in any collection")
            return
            
        # Save video metadata to JSON
        output_file = COLLECTIONS_DATA
        try:
            save_video_metadata(all_videos, output_file)
        except Exception as e:
            logger.error(f"Failed to save video metadata to {output_file}: {str(e)}")
            
    except Exception as e:
        logger.error(f"Script failed: {str(e)}")

if __name__ == '__main__':
    main() 