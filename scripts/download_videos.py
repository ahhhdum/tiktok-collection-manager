"""Script to download TikTok videos from data export."""

from pathlib import Path
import argparse
from typing import Literal

from src.downloader.video_downloader import TikTokDownloader
from src.utils.logger import logger
from src.utils.config import (
    LIKED_VIDEOS_DIR,
    FAVORITE_VIDEOS_DIR,
    LIKED_VIDEO_METADATA,
    FAVORITE_VIDEO_METADATA
)

def download_videos(data_file: Path, video_type: Literal["liked", "favorite"], limit: int = None) -> None:
    """Download videos from TikTok data export file."""
    if not data_file.exists():
        raise FileNotFoundError(f"Data file not found: {data_file}")
    
    # Always use separate directories and metadata files based on type
    if video_type == "liked":
        output_dir = LIKED_VIDEOS_DIR
        metadata_file = LIKED_VIDEO_METADATA
    else:  # favorite
        output_dir = FAVORITE_VIDEOS_DIR
        metadata_file = FAVORITE_VIDEO_METADATA
    
    # Initialize downloader with explicit metadata file
    downloader = TikTokDownloader(output_dir=output_dir, metadata_file=metadata_file)
    
    try:
        # Process videos using the unified method but with separate metadata
        downloader.process_videos(data_file, video_type, limit)
    except Exception as e:
        logger.error(f"Failed to process {video_type} videos: {e}")

def main():
    """Main entry point for downloading videos."""
    parser = argparse.ArgumentParser(description="Download TikTok videos from data export file")
    parser.add_argument("data_file", type=Path, help="Path to the TikTok data export JSON file")
    parser.add_argument("--type", type=str, choices=["liked", "favorite"], required=True,
                      help="Type of videos to download (liked or favorite)")
    parser.add_argument("--limit", type=int, help="Limit the number of videos to download (for testing)")
    
    args = parser.parse_args()
    download_videos(args.data_file, args.type, args.limit)

if __name__ == "__main__":
    main() 