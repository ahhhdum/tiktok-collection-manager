import os
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DOWNLOADS_DIR = BASE_DIR / "downloads"
LOGS_DIR = BASE_DIR / "logs"
DATA_DIR = BASE_DIR / "data"  # Add data directory for input files

# Create necessary directories
DOWNLOADS_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)

# Download history file
DOWNLOAD_HISTORY = LOGS_DIR / "download_history.json"
FAILED_DOWNLOADS = LOGS_DIR / "failed_downloads.json"
DOWNLOAD_PROGRESS = LOGS_DIR / "download_progress.json"
SPECIAL_CASES = LOGS_DIR / "special_cases.json"  # For slideshows and other non-standard content

# Collection management
COLLECTIONS_DIR = DOWNLOADS_DIR / "collections"
UNCATEGORIZED_DIR = DOWNLOADS_DIR / "uncategorized"
LIKED_VIDEOS_DIR = DOWNLOADS_DIR / "liked_videos"  
FAVORITE_VIDEOS_DIR = DOWNLOADS_DIR / "favorite_videos" 

# Create collection directories
COLLECTIONS_DIR.mkdir(exist_ok=True)
UNCATEGORIZED_DIR.mkdir(exist_ok=True)
LIKED_VIDEOS_DIR.mkdir(exist_ok=True)  # Create liked videos directory
FAVORITE_VIDEOS_DIR.mkdir(exist_ok=True)  # Create favorite videos directory

# Video metadata files
LIKED_VIDEO_METADATA = LOGS_DIR / "liked_video_metadata.json"
FAVORITE_VIDEO_METADATA = LOGS_DIR / "favorite_video_metadata.json"

# Input data files
USER_DATA_FILE = DATA_DIR / "user_data_tiktok.json"  # Default location for TikTok data export

# Default video format
VIDEO_FORMAT = "mp4"

# Rate limiting
MAX_CONCURRENT_DOWNLOADS = 1
INITIAL_DELAY = 4  
MIN_DELAY = 2  
MAX_DELAY = 30  # maximum delay allowed
MAX_RETRIES = 3
RETRY_BACKOFF_FACTOR = 5
RATE_LIMIT_WINDOW = 300  # 5 minutes in seconds
MAX_FAILURES_BEFORE_BACKOFF = 3
SUCCESS_STREAK_THRESHOLD = 3  # Reduced from 5 since downloads are working well
TARGET_HOURLY_RATE = 80  # target number of videos per hour

# Additional rate limiting parameters
WARMUP_PERIOD = 10  # minimum number of downloads before rate optimization
RATE_CHECK_INTERVAL = 900  # 15 minutes - minimum time before checking rates

# Disk space management (in bytes)
MAX_DOWNLOADS_SIZE = 500 * 1024 * 1024 * 1024  # 500GB in bytes
FILE_SIZE_TOLERANCE = 0.1  # 10% tolerance for file size verification

def get_directory_size(directory: Path) -> int:
    """Calculate total size of a directory in bytes."""
    total_size = 0
    for dirpath, _, filenames in os.walk(directory):
        for filename in filenames:
            file_path = Path(dirpath) / filename
            if not file_path.is_symlink():  # Skip symbolic links
                total_size += file_path.stat().st_size
    return total_size

def check_disk_space(file_size: int) -> bool:
    """Check if adding file_size would exceed MAX_DOWNLOADS_SIZE."""
    current_size = get_directory_size(DOWNLOADS_DIR)
    return (current_size + file_size) <= MAX_DOWNLOADS_SIZE

def format_size(size_bytes: int) -> str:
    """Format bytes into human readable string."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.2f} TB" 