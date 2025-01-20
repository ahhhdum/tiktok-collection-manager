"""Script to organize downloaded videos into their respective collection folders."""

import json
import shutil
from pathlib import Path
from typing import Dict, Set

from src.utils.logger import logger

def load_collection_data() -> Dict[str, str]:
    """Load the collection data and return a mapping of video_id to collection_name."""
    collection_file = Path("data/collection_videos.json")
    if not collection_file.exists():
        raise FileNotFoundError("Collection data file not found")
    
    with open(collection_file, 'r', encoding='utf-8') as f:
        collection_data = json.load(f)
    
    # Create video_id to collection_name mapping
    return {video_id: data['collection_name'] 
            for video_id, data in collection_data.items()}

def setup_collection_dirs(collection_names: Set[str]) -> Dict[str, Path]:
    """Create collection directories if they don't exist."""
    collections_dir = Path("downloads/collections")
    collections_dir.mkdir(exist_ok=True)
    
    collection_paths = {}
    for name in collection_names:
        # Sanitize collection name for use as directory name
        safe_name = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' 
                           for c in name)
        collection_dir = collections_dir / safe_name
        collection_dir.mkdir(exist_ok=True)
        collection_paths[name] = collection_dir
    
    return collection_paths

def organize_videos():
    """Organize downloaded videos into their respective collection folders."""
    # Load collection data
    try:
        video_collections = load_collection_data()
    except FileNotFoundError as e:
        logger.error(f"Failed to load collection data: {e}")
        return
    
    # Setup collection directories
    collection_paths = setup_collection_dirs(set(video_collections.values()))
    
    # Setup uncategorized directory
    uncategorized_dir = Path("downloads/uncategorized")
    if not uncategorized_dir.exists():
        logger.error("Uncategorized directory not found")
        return
        
    # Track video movements
    moved_to_collections = 0
    moved_to_uncategorized = 0
    
    # Process each video file
    for video_file in uncategorized_dir.glob("*.mp4"):
        video_id = video_file.stem
        
        # Check if video belongs to a collection
        if video_id in video_collections:
            collection_name = video_collections[video_id]
            target_dir = collection_paths[collection_name]
            
            # Move to collection
            try:
                shutil.move(str(video_file), str(target_dir / video_file.name))
                moved_to_collections += 1
                logger.info(f"Moved {video_file.name} to collection '{collection_name}'")
            except Exception as e:
                logger.error(f"Failed to move {video_file.name}: {e}")
    
    logger.info("Organization complete:")
    logger.info(f"- {moved_to_collections} videos moved to collections")
    logger.info(f"- {moved_to_uncategorized} videos moved to uncategorized")

if __name__ == "__main__":
    organize_videos() 