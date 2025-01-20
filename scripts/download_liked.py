"""Script to download liked TikTok videos."""

from pathlib import Path
import argparse

from scripts.download_videos import download_videos

def main():
    """Main entry point for downloading liked videos."""
    parser = argparse.ArgumentParser(description="Download TikTok liked videos from JSON file")
    parser.add_argument("liked_file", type=Path, help="Path to the liked videos JSON file")
    parser.add_argument("--limit", type=int, help="Limit the number of videos to download (for testing)")
    
    args = parser.parse_args()
    download_videos(args.liked_file, "liked", args.limit)

if __name__ == "__main__":
    main() 