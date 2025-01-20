import time
from typing import List, Dict, Any
from .logger import logger
from .config import (
    INITIAL_DELAY,
    MIN_DELAY,
    MAX_DELAY,
    RATE_LIMIT_WINDOW,
    MAX_FAILURES_BEFORE_BACKOFF,
    SUCCESS_STREAK_THRESHOLD,
    TARGET_HOURLY_RATE
)

class RateLimitHandler:
    def __init__(self):
        self.failures: List[float] = []  # timestamps of failures
        self.current_delay = INITIAL_DELAY
        self.consecutive_failures = 0
        self.consecutive_successes = 0
        self.hourly_downloads: List[float] = []  # timestamps of successful downloads
        self.session_stats: Dict[str, int] = {
            'success_count': 0,
            'failure_count': 0,
            'rate_limit_hits': 0
        }
    
    def _get_hourly_rate(self) -> int:
        """Calculate downloads in the last hour."""
        now = time.time()
        hour_ago = now - 3600
        self.hourly_downloads = [t for t in self.hourly_downloads if t > hour_ago]
        
        # Don't report rate warnings until we have enough samples
        if len(self.hourly_downloads) < 5:
            return TARGET_HOURLY_RATE  # Pretend we're on target during warmup
            
        # If we've been running less than 15 minutes, scale up the rate
        if (now - min(self.hourly_downloads)) < 900:  # 15 minutes
            current_rate = len(self.hourly_downloads)
            # Extrapolate the rate to hourly
            return int(current_rate * (3600 / (now - min(self.hourly_downloads))))
            
        return len(self.hourly_downloads)
    
    def update(self, success: bool, error_message: str = '') -> float:
        """Update rate limiter state and get next delay time.
        
        Args:
            success: Whether the last request was successful
            error_message: Error message if request failed
            
        Returns:
            float: Number of seconds to wait before next request
        """
        now = time.time()
        
        # Clean up old failures outside the window
        self.failures = [f for f in self.failures if now - f < RATE_LIMIT_WINDOW]
        
        if not success:
            self.failures.append(now)
            self.session_stats['failure_count'] += 1
            self.consecutive_failures += 1
            self.consecutive_successes = 0
            
            # Check if error suggests rate limiting
            rate_limit_indicators = [
                'too many requests',
                '429',
                'rate limit',
                'blocked',
                'timeout'
            ]
            
            # Check if error is content-related (not a rate limit issue)
            content_related_errors = [
                'NoneType',
                'unsupported operand',
                'slideshow',
                'index out of range'
            ]
            
            if any(indicator in error_message.lower() for indicator in rate_limit_indicators):
                self.session_stats['rate_limit_hits'] += 1
                # Aggressive backoff for rate limits
                self.current_delay = min(self.current_delay * 2, MAX_DELAY)
                logger.warning(f"Rate limit detected. Increasing delay to {self.current_delay}s")
            elif any(err in error_message for err in content_related_errors):
                # Don't increase delay for content-related errors
                logger.info("Content-related error detected. Maintaining current delay.")
                self.consecutive_failures = 0  # Reset failure count since it's not a rate issue
            else:
                # Progressive backoff based on consecutive failures
                multiplier = min(self.consecutive_failures, 3)
                self.current_delay = min(self.current_delay * (1 + 0.5 * multiplier), MAX_DELAY)
                logger.warning(f"Failure #{self.consecutive_failures}. Increasing delay to {self.current_delay}s")
        else:
            self.session_stats['success_count'] += 1
            self.consecutive_successes += 1
            self.consecutive_failures = 0
            self.hourly_downloads.append(now)
            
            hourly_rate = self._get_hourly_rate()
            
            # Only adjust rates if we have enough data
            if len(self.hourly_downloads) >= 5:
                # If we're ahead of schedule, be more conservative
                if hourly_rate > TARGET_HOURLY_RATE:
                    reduction_factor = 0.05  # 5% reduction
                else:
                    # More aggressive reduction if we're behind schedule
                    reduction_factor = 0.15 if self.consecutive_successes >= SUCCESS_STREAK_THRESHOLD else 0.05
                
                # Reduce delay if we're having sustained success
                if self.consecutive_successes >= SUCCESS_STREAK_THRESHOLD:
                    self.current_delay = max(
                        MIN_DELAY,
                        self.current_delay * (1 - reduction_factor)
                    )
                    logger.info(f"Success streak: {self.consecutive_successes}. Reducing delay to {self.current_delay}s")
                
                if hourly_rate < TARGET_HOURLY_RATE * 0.8:  # More than 20% behind schedule
                    logger.warning(f"Behind target rate ({hourly_rate}/{TARGET_HOURLY_RATE} downloads/hour). Adjusting strategy.")
        
        return self.current_delay
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current session statistics."""
        return {
            **self.session_stats,
            'current_delay': self.current_delay,
            'recent_failures': len(self.failures),
            'consecutive_successes': self.consecutive_successes,
            'consecutive_failures': self.consecutive_failures,
            'hourly_rate': self._get_hourly_rate()
        } 