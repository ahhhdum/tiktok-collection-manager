"""Script to download favorite TikTok videos."""

from pathlib import Path
import argparse

from scripts.download_videos import download_videos

def main():
    """Main entry point for downloading favorites."""
    parser = argparse.ArgumentParser(description="Download TikTok favorites from JSON file")
    parser.add_argument("favorites_file", type=Path, help="Path to the favorites JSON file")
    parser.add_argument("--limit", type=int, help="Limit the number of videos to download (for testing)")
    
    args = parser.parse_args()
    download_videos(args.favorites_file, "favorite", args.limit)

if __name__ == "__main__":
    main() 