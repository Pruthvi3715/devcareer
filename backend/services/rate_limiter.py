"""
Sliding-window rate limiter for the chat API.
In-memory implementation (same zero-config pattern as redis_client.py).

Limits:
- Per-user: 20 messages/minute, 100 messages/hour
- Global: 60 messages/minute across all users
"""
from __future__ import annotations

import time
from collections import defaultdict
from threading import Lock
from typing import Tuple

_lock = Lock()

# {key: [timestamp, timestamp, ...]}
_windows: dict[str, list[float]] = defaultdict(list)


def _prune(key: str, window_seconds: float) -> None:
    """Remove expired timestamps from a window."""
    cutoff = time.time() - window_seconds
    _windows[key] = [t for t in _windows[key] if t > cutoff]


def check_rate_limit(
    user_id: str,
) -> Tuple[bool, int, str]:
    """
    Check all rate limit tiers for a user.

    Returns:
        (allowed, retry_after_seconds, reason)
    """
    now = time.time()

    with _lock:
        # --- Per-user: 20/minute ---
        user_min_key = f"user_min:{user_id}"
        _prune(user_min_key, 60.0)
        if len(_windows[user_min_key]) >= 20:
            oldest = _windows[user_min_key][0]
            retry = int(60.0 - (now - oldest)) + 1
            return False, max(1, retry), "Per-user limit: 20 messages per minute"

        # --- Per-user: 100/hour ---
        user_hr_key = f"user_hr:{user_id}"
        _prune(user_hr_key, 3600.0)
        if len(_windows[user_hr_key]) >= 100:
            oldest = _windows[user_hr_key][0]
            retry = int(3600.0 - (now - oldest)) + 1
            return False, max(1, retry), "Per-user limit: 100 messages per hour"

        # --- Global: 60/minute ---
        global_key = "global_min"
        _prune(global_key, 60.0)
        if len(_windows[global_key]) >= 60:
            oldest = _windows[global_key][0]
            retry = int(60.0 - (now - oldest)) + 1
            return False, max(1, retry), "Global limit: 60 messages per minute"

        # Record the request
        _windows[user_min_key].append(now)
        _windows[user_hr_key].append(now)
        _windows[global_key].append(now)

        return True, 0, ""


def get_remaining(user_id: str) -> dict:
    """Get remaining quota for a user (for response headers)."""
    with _lock:
        user_min_key = f"user_min:{user_id}"
        _prune(user_min_key, 60.0)
        user_hr_key = f"user_hr:{user_id}"
        _prune(user_hr_key, 3600.0)
        global_key = "global_min"
        _prune(global_key, 60.0)

        return {
            "per_minute": max(0, 20 - len(_windows[user_min_key])),
            "per_hour": max(0, 100 - len(_windows[user_hr_key])),
            "global_minute": max(0, 60 - len(_windows[global_key])),
        }
