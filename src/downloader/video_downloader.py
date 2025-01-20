import json
import time
from pathlib import Path
from typing import Dict, Any, Optional, Literal
import yt_dlp
from ..utils.logger import (
    logger,
    load_download_history,
    save_download_history,
    load_video_metadata,
    save_video_metadata,
    YTDLLogger
)
from ..utils.config import (
    DOWNLOADS_DIR,
    LIKED_VIDEO_METADATA,
    FAVORITE_VIDEO_METADATA,
    check_disk_space
)
from ..utils.rate_limiter import RateLimitHandler
from ..utils.session_manager import SessionManager

class TikTokDownloader:
    def __init__(self, output_dir: Path, metadata_file: Path):
        """Initialize TikTok video downloader.
        
        Args:
            output_dir: Directory to save downloaded videos
            metadata_file: File to store video metadata
        """
        self.download_history = load_download_history()
        self.video_metadata = load_video_metadata(metadata_file)
        self.metadata_file = metadata_file
        self.rate_limiter = RateLimitHandler()
        self.session_manager = SessionManager()
        
        # Configure yt-dlp options with reduced verbosity
        self.ydl_opts = {
            'format': 'best',
            'outtmpl': str(output_dir / '%(id)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
            'verbose': False,
            'progress': True,
            'logger': YTDLLogger(),  # Use custom logger
            'progress_hooks': [self._progress_hook],  # Add progress hook
            **self.session_manager.get_yt_dlp_options()
        }

    def _extract_video_id(self, url: str) -> Optional[str]:
        """Extract video ID from TikTok URL."""
        try:
            # Handle tiktokv.com format
            if 'tiktokv.com' in url:
                return url.rstrip('/').split('/')[-1]
            # Handle regular tiktok.com format
            elif 'video/' in url:
                return url.split('video/')[1].split('?')[0]
            return url.split('/')[-1].split('?')[0]
        except Exception as e:
            logger.error(f"Failed to extract video ID from {url}: {e}")
            return None

    def _convert_to_web_url(self, url: str) -> str:
        """Convert tiktokv.com URL to regular tiktok.com URL format."""
        if 'tiktokv.com' in url:
            video_id = self._extract_video_id(url)
            return f"https://www.tiktok.com/@user/video/{video_id}"
        return url

    def _get_video_metadata(self, url: str) -> Optional[Dict[str, Any]]:
        """Extract metadata from TikTok video."""
        attempts = 0
        max_attempts = 3
        last_error = None

        while attempts < max_attempts:
            try:
                with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    filesize = info.get('filesize') or info.get('filesize_approx', 0)
                    
                    return {
                        'id': info.get('id'),
                        'title': info.get('title'),
                        'description': info.get('description'),
                        'uploader': info.get('uploader'),
                        'uploader_id': info.get('uploader_id'),
                        'timestamp': info.get('timestamp'),
                        'duration': info.get('duration'),
                        'view_count': info.get('view_count'),
                        'like_count': info.get('like_count'),
                        'comment_count': info.get('comment_count'),
                        'repost_count': info.get('repost_count'),
                        'tags': info.get('tags', []),
                        'filesize': filesize,
                    }
            except Exception as e:
                last_error = str(e)
                attempts += 1
                
                if "Cookie" in last_error or "permission" in last_error.lower():
                    logger.warning("Cookie/permission error detected, updating session...")
                    self.session_manager.rotate_user_agent()
                    self.ydl_opts.update(self.session_manager.get_yt_dlp_options())
                
                if attempts < max_attempts:
                    delay = 2 ** attempts  # Exponential backoff
                    logger.warning(f"Attempt {attempts}/{max_attempts} failed. Retrying in {delay}s... Error: {last_error}")
                    time.sleep(delay)
                else:
                    logger.error(f"Failed to extract metadata after {max_attempts} attempts. Last error: {last_error}")
        
        return None

    def download_video(self, url: str) -> bool:
        """Download a single video and its metadata."""
        video_id = self._extract_video_id(url)
        if not video_id:
            return False

        # Skip if already downloaded
        if video_id in self.download_history:
            logger.info(f"Video {video_id} already downloaded, skipping...")
            return True

        try:
            # Convert URL to web format for yt-dlp
            web_url = self._convert_to_web_url(url)
            logger.info(f"Converting {url} to {web_url}")

            # Get metadata first
            metadata = self._get_video_metadata(web_url)
            if not metadata:
                # Update rate limiter with content error
                self.rate_limiter.update(False, "NoneType metadata - likely slideshow or non-standard content")
                logger.warning(f"Skipping video {video_id} - non-standard content (possibly slideshow)")
                return False

            # Check if we have enough disk space
            filesize = metadata.get('filesize', 0)
            if not check_disk_space(filesize):
                logger.error(f"Not enough disk space for video {video_id} (size: {filesize / 1024 / 1024:.2f} MB). Stopping downloads.")
                return False

            # Configure download options
            download_opts = self.ydl_opts.copy()
            download_opts['extract_flat'] = False

            # Download video with retries
            success = False
            error_msg = ""
            max_download_attempts = 3
            
            for attempt in range(max_download_attempts):
                try:
                    with yt_dlp.YoutubeDL(download_opts) as ydl:
                        ydl.download([web_url])
                    success = True
                    break
                except Exception as e:
                    error_msg = str(e)
                    if "NoneType" in error_msg or "unsupported operand" in error_msg:
                        logger.warning(f"Skipping video {video_id} - non-standard content detected")
                        # Don't retry for content-related errors
                        break
                    if attempt < max_download_attempts - 1:
                        delay = 2 ** (attempt + 1)  # Exponential backoff
                        logger.warning(f"Download attempt {attempt + 1}/{max_download_attempts} failed. Retrying in {delay}s... Error: {error_msg}")
                        
                        if "Cookie" in error_msg or "permission" in error_msg.lower():
                            self.session_manager.rotate_user_agent()
                            download_opts.update(self.session_manager.get_yt_dlp_options())
                        
                        time.sleep(delay)

            # Update rate limiter and get delay for next download
            delay = self.rate_limiter.update(success, error_msg)
            
            if success:
                # Update history and metadata
                self.download_history.add(video_id)
                self.video_metadata[video_id] = metadata
                
                # Save to files
                save_download_history(self.download_history)
                save_video_metadata(self.video_metadata, self.metadata_file)

                logger.info(f"Successfully downloaded video {video_id} (size: {filesize / 1024 / 1024:.2f} MB)")
                
                # If we've had several successes, try reducing delay
                stats = self.rate_limiter.get_stats()
                if stats['success_count'] % 10 == 0:
                    self.session_manager.rotate_user_agent()
                    self.ydl_opts.update(self.session_manager.get_yt_dlp_options())
                
                return True
            return False

        except Exception as e:
            error_msg = str(e)
            # Check if this is a content-related error
            content_errors = ['NoneType', 'unsupported operand', 'slideshow', 'index out of range']
            if any(err in error_msg for err in content_errors):
                logger.warning(f"Skipping video {video_id} - content error: {error_msg}")
                self.rate_limiter.update(False, error_msg)
                return False
            
            logger.error(f"Failed to download {url}: {error_msg}")
            self.rate_limiter.update(False, error_msg)
            return False

    def process_videos(self, data_file: Path, video_type: Literal["liked", "favorite"], limit: int = None):
        """Process videos from the TikTok data export file.
        
        Args:
            data_file: Path to the TikTok data export JSON file
            video_type: Type of videos to process ("liked" or "favorite")
            limit: Optional limit on number of videos to process
        """
        type_config = {
            "liked": {
                "json_path": ["Activity", "Like List", "ItemFavoriteList"],
                "url_key": "link"
            },
            "favorite": {
                "json_path": ["Activity", "Favorite Videos", "FavoriteVideoList"],
                "url_key": "Link"
            }
        }[video_type]

        try:
            # Open file with UTF-8 encoding
            with open(data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Navigate JSON path to get videos
            current = data
            for key in type_config["json_path"]:
                current = current[key]
            videos = current

            if limit:
                videos = videos[:limit]
                logger.info(f"Testing with {limit} videos")

            # Pre-process all video IDs and filter out already downloaded ones
            video_map = {}
            for video in videos:
                url = video[type_config["url_key"]]
                video_id = self._extract_video_id(url)
                if video_id:
                    video_map[video_id] = video

            # Get list of videos to download (exclude already downloaded ones)
            videos_to_download = {
                vid_id: video 
                for vid_id, video in video_map.items() 
                if vid_id not in self.download_history
            }

            total_new_videos = len(videos_to_download)
            if total_new_videos == 0:
                logger.info("No new videos to download")
                return

            logger.info(f"Found {len(video_map)} total videos")
            logger.info(f"Skipping {len(self.download_history)} already downloaded videos")
            logger.info(f"Downloading {total_new_videos} new videos")

            # Process only new videos
            for i, (video_id, video) in enumerate(videos_to_download.items(), 1):
                try:
                    url = video[type_config["url_key"]]
                    logger.info(f"Processing new video {i}/{total_new_videos}: {url}")
                    
                    success = self.download_video(url)
                    if not success:
                        # If we hit disk space limit, stop processing
                        if "disk space" in logger.handlers[0].formatter.format(logger.handlers[0].buffer[-1]):
                            logger.info("Stopping downloads due to disk space limit")
                            break
                        # For other failures, continue to next video
                        continue
                    
                    # Use dynamic delay from rate limiter
                    delay = self.rate_limiter.get_stats()['current_delay']
                    time.sleep(delay)
                except Exception as e:
                    logger.error(f"Error processing video {video_id}: {e}")
                    continue  # Continue with next video even if this one fails

            # Log final statistics
            stats = self.rate_limiter.get_stats()
            logger.info("Download session completed. Statistics:")
            logger.info(f"Successful downloads: {stats['success_count']}")
            logger.info(f"Failed downloads: {stats['failure_count']}")
            logger.info(f"Rate limit hits: {stats['rate_limit_hits']}")

        except Exception as e:
            logger.error(f"Failed to process {video_type} videos: {e}")
            return

    # Keep existing methods for backward compatibility
    def process_favorite_videos(self, favorites_file: Path, limit: int = None):
        """Process videos from the favorites JSON file."""
        return self.process_videos(favorites_file, "favorite", limit)

    def process_liked_videos(self, liked_file: Path, limit: int = None):
        """Process videos from the liked videos JSON file."""
        return self.process_videos(liked_file, "liked", limit)

    def _progress_hook(self, d: Dict[str, Any]) -> None:
        """Handle download progress updates."""
        if d['status'] == 'downloading':
            # Only log progress at certain percentages
            if 'downloaded_bytes' in d and 'total_bytes' in d:
                progress = (d['downloaded_bytes'] / d['total_bytes']) * 100
                if progress % 25 == 0:  # Log at 0%, 25%, 50%, 75%, 100%
                    logger.info(f"Download progress: {progress:.1f}%") 