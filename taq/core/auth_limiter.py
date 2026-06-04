import time
from typing import Dict, Tuple, Optional
from fastapi import Request, HTTPException, status

class AuthRateLimiter:
    def __init__(self, limit: int = 5, window: int = 900):
        """
        Initialize the rate limiter.

        Args:
            limit: Maximum number of attempts allowed in the window period.
            window: Time window in seconds (default 15 minutes = 900 seconds).
        """
        self.limit = limit
        self.window = window
        # In a single instance, we can use a simple dict. In a multi-instance setup,
        # we would use a shared store like Redis.
        self.attempts: Dict[str, list] = {}

    def _clean_old_attempts(self, key: str, now: float) -> None:
        """Remove attempts older than the window."""
        if key in self.attempts:
            self.attempts[key] = [t for t in self.attempts[key] if now - t < self.window]
            # Remove the key if no attempts left
            if not self.attempts[key]:
                del self.attempts[key]

    def is_allowed(self, key: str) -> bool:
        """
        Check if the key is allowed to make an attempt.

        Args:
            key: Identifier for the rate limit (e.g., IP address or email).

        Returns:
            True if allowed, False if rate limit exceeded.
        """
        now = time.time()
        self._clean_old_attempts(key, now)

        if key not in self.attempts:
            self.attempts[key] = []

        if len(self.attempts[key]) >= self.limit:
            return False

        # Record this attempt
        self.attempts[key].append(now)
        return True

    def get_client_ip(self, request: Request) -> str:
        """
        Extract client IP from request, considering common proxy headers.
        Note: In production, ensure your proxy is trusted and properly configured.
        """
        # Check for common headers set by proxies/load balancers
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            # X-Forwarded-For can contain multiple IPs, the first is the client
            return forwarded.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # Fallback to the direct client host
        return request.client.host if request.client else "unknown"

# Create a singleton instance for use in the application
auth_rate_limiter = AuthRateLimiter()