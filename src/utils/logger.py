import json
import logging
from pathlib import Path
from typing import Dict, Any
from .config import (
    DOWNLOAD_HISTORY, 
    LIKED_VIDEO_METADATA
)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    encoding='utf-8'
)
logger = logging.getLogger(__name__)

class YTDLLogger:
    """Custom logger for yt-dlp to control verbosity."""
    def debug(self, msg):
        # Ignore debug messages
        pass

    def info(self, msg):
        # Only log download progress
        if "Downloading" in msg or "100%" in msg:
            logger.info(msg)

    def warning(self, msg):
        # Log all warnings
        logger.warning(msg)

    def error(self, msg):
        # Log all errors
        logger.error(msg)

def load_download_history() -> set:
    """Load the download history from JSON file."""
    if DOWNLOAD_HISTORY.exists():
        with open(DOWNLOAD_HISTORY, 'r', encoding='utf-8') as f:
            return set(json.load(f))
    return set()

def save_download_history(history: set) -> None:
    """Save the download history to JSON file."""
    with open(DOWNLOAD_HISTORY, 'w', encoding='utf-8') as f:
        json.dump(list(history), f)

def load_video_metadata(metadata_file: Path) -> Dict[str, Any]:
    """Load video metadata from JSON file."""
    try:
        if metadata_file.exists():
            with open(metadata_file, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load video metadata from {metadata_file}: {e}")
    return {}

def save_video_metadata(metadata: Dict[str, Any], metadata_file: Path) -> None:
    """Save video metadata to JSON file."""
    try:
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Failed to save video metadata to {metadata_file}: {e}") 