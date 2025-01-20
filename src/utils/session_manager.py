import json
from pathlib import Path
from typing import Dict, Any, Optional
from .logger import logger
from .config import LOGS_DIR

class SessionManager:
    def __init__(self):
        self.cookies_file = LOGS_DIR / 'cookies.txt'
        self.session_file = LOGS_DIR / 'session_data.json'
        self.session_data: Dict[str, Any] = self._load_session_data()
        
    def _load_session_data(self) -> Dict[str, Any]:
        """Load session data from file."""
        if self.session_file.exists():
            try:
                with open(self.session_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load session data: {e}")
        return {
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'headers': {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'TE': 'trailers'
            },
            'cookies': {}
        }
    
    def _save_session_data(self):
        """Save session data to file."""
        try:
            with open(self.session_file, 'w', encoding='utf-8') as f:
                json.dump(self.session_data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save session data: {e}")
    
    def get_yt_dlp_options(self) -> Dict[str, Any]:
        """Get yt-dlp options with session data."""
        options = {
            'user_agent': self.session_data['user_agent'],
            'headers': self.session_data['headers'],
            'socket_timeout': 30,
            'retries': 3,
            'http_chunk_size': 10485760,  # 10MB
            'extractor_retries': 3,
            'file_access_retries': 3,
            'fragment_retries': 3,
            'skip_unavailable_fragments': True,
            'keep_fragments': False,
            'buffersize': 1024,
            'no_check_certificates': True,  # Add this if SSL issues occur
        }

        # Only try to use cookies if the file exists
        if self.cookies_file.exists():
            options.update({
                'cookiefile': str(self.cookies_file),
                'cookiesfrombrowser': None  # Disable browser cookies to avoid permission issues
            })
        
        return options
    
    def update_session(self, response_headers: Optional[Dict[str, str]] = None):
        """Update session data from response headers."""
        if response_headers:
            # Update any relevant headers or cookies
            if 'set-cookie' in response_headers:
                self.session_data['cookies'].update(self._parse_cookies(response_headers['set-cookie']))
            
            # Store other useful headers
            useful_headers = ['x-ratelimit-remaining', 'x-ratelimit-reset']
            for header in useful_headers:
                if header in response_headers:
                    self.session_data['headers'][header] = response_headers[header]
            
            self._save_session_data()
    
    def _parse_cookies(self, cookie_header: str) -> Dict[str, str]:
        """Parse cookie header into dictionary."""
        cookies = {}
        for cookie in cookie_header.split(';'):
            if '=' in cookie:
                name, value = cookie.strip().split('=', 1)
                cookies[name] = value
        return cookies
    
    def rotate_user_agent(self):
        """Rotate user agent to avoid detection."""
        user_agents = [
            # Windows Chrome
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            # Windows Firefox
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            # Windows Edge
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
            # Mobile Chrome
            'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36'
        ]
        current_index = user_agents.index(self.session_data['user_agent']) if self.session_data['user_agent'] in user_agents else -1
        next_index = (current_index + 1) % len(user_agents)
        self.session_data['user_agent'] = user_agents[next_index]
        logger.info(f"Rotated user agent to: {self.session_data['user_agent']}")
        self._save_session_data() 