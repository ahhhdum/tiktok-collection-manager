# TikTok Collection Manager

A Python-based tool for managing TikTok video collections, downloading videos, and organizing them into categories.

## Setup

1. Install the package in development mode:
```bash
pip install -e .
```

2. Required Python packages (automatically installed):
- beautifulsoup4>=4.12.2
- requests>=2.31.0
- yt-dlp>=2023.12.30
- tqdm>=4.66.1
- python-dotenv>=1.0.0

## Input Data

The system uses your TikTok data export file:

1. Request your data from TikTok (Settings -> Privacy -> Request Data)
2. When received, extract the ZIP file
3. Place `user_data_tiktok.json` in the `data/` directory
   - This file contains both your liked and favorite videos

## Log Files

The system maintains several JSON files to track downloads and metadata:

### download_history.json
- A shared list of all downloaded video IDs
- Used to prevent downloading the same video twice, even across different sources (liked/favorites)
- Simple format: `["video_id1", "video_id2", ...]`
- Checked before any download attempt

### Metadata Files
The system maintains separate metadata files for organization:

- `liked_video_metadata.json`: Metadata for liked videos
- `favorite_video_metadata.json`: Metadata for favorite videos
- `collection_videos.json`: Metadata for collection videos

Each metadata file contains:
- Video ID and URL
- Title and description
- Creator information
- View/like/comment counts
- File size and duration
- Download timestamp
- Collection information (for collection videos)

## Collection Pages HTML Files

Currently, collection pages HTML files need to be manually saved:
1. Go to your TikTok profile and open each collection
2. Save the page HTML (right-click -> Save As -> Webpage, Complete)
3. Place the saved HTML files in `data/collection_pages/`
4. Each file should be named after its collection (e.g., "Travel.html", "Cooking.html")

Note: Future versions may automate this process using web automation tools.

## Project Structure

```
tiktok-save/
├── data/                      # Data storage directory
│   ├── collection_videos.json # Metadata for all videos in collections
│   ├── user_data_tiktok.json # TikTok data export file
│   └── collection_pages/      # HTML files of TikTok collection pages
├── downloads/                 # Downloaded video files
│   ├── collections/          # Organized videos by collection
│   ├── liked_videos/         # Videos from TikTok liked list
│   ├── favorite_videos/      # Videos from TikTok favorites
│   └── uncategorized/        # Newly downloaded videos
├── logs/                     # Log files directory
│   ├── download_history.json # Shared history of all downloaded video IDs
│   ├── liked_video_metadata.json    # Metadata for liked videos
│   └── favorite_video_metadata.json  # Metadata for favorite videos
├── src/                      # Source code
├── scripts/                  # Command-line scripts
├── tests/                    # Test files
└── requirements.txt          # Python package dependencies
```

## Complete Workflow

### 1. Download Videos from TikTok Export

You can download videos using the unified script or the individual scripts:

```bash
# Using the unified script (recommended):
python scripts/download_videos.py data/user_data_tiktok.json --type liked
python scripts/download_videos.py data/user_data_tiktok.json --type favorite

# Using individual scripts (same functionality):
python scripts/download_liked.py data/user_data_tiktok.json
python scripts/download_favorites.py data/user_data_tiktok.json

# Optional: Use --limit parameter for testing
python scripts/download_videos.py data/user_data_tiktok.json --type liked --limit 5
```

These scripts:
- Read the TikTok data export JSON file
- Download videos that haven't been downloaded before
- Save videos to their respective directories:
  - Liked videos go to `downloads/liked_videos/`
  - Favorite videos go to `downloads/favorite_videos/`
- Maintain separate metadata files:
  - Liked video metadata in `logs/liked_video_metadata.json`
  - Favorite video metadata in `logs/favorite_video_metadata.json`
- Handle rate limiting and retries
- Skip already downloaded videos

### 2. Process Collection Pages

Next, process the HTML collection pages to extract video metadata:

```bash
python scripts/process_collection_pages.py
```

This script:
- Reads HTML files from `data/collection_pages/`
- Extracts video metadata (ID, creator, description, etc.)
- Saves metadata to `data/collection_videos.json`
- Logs processing details with debug information
- Handles both video and photo content (skips photos)

Output:
- Creates/updates `data/collection_videos.json`
- Each video entry contains:
  - video_id
  - creator_name
  - creator_id
  - description
  - url
  - thumbnail_url
  - collection_name

### 3. Organize Downloads

Finally, organize the downloaded videos into their collection folders:

```bash
python scripts/organize_downloads.py
```

This script:
- Reads video metadata from `data/collection_videos.json`
- Creates collection directories under `downloads/collections/`
- Moves videos from `downloads/uncategorized/` to their respective collection folders
- Names are based on video IDs (e.g., "7455962360709238059.mp4")

## Debug Logging

All scripts include detailed debug logging that shows:
- Number of videos found in each collection
- Successfully parsed videos with IDs and creators
- Skipped items (e.g., photos)
- File operations (moves, creates)
- Download progress and retries

## Notes

- You need to export your TikTok data to get the `user_data_tiktok.json` file
- Collection pages HTML files must be manually saved from your TikTok profile (see "Collection Pages HTML Files" section)
- The scripts handle missing directories by creating them as needed
- Photos and non-video content are automatically skipped during processing
- Failed downloads are logged and can be retried
- The download script includes rate limiting to avoid TikTok restrictions
- Each type of video (liked/favorite) maintains its own metadata file for better organization
- Future improvements planned:
  - Automated collection page scraping
  - Better error handling for TikTok API changes
  - Support for additional TikTok data export formats 