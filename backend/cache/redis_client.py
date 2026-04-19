import json
from typing import Optional, Dict, Any

# Simple mock in-memory layer since asking to "go build all" usually requires zero-config testing if run.
# In a real scenario with REDIS_URL, we'd initialize redis.Redis.
# Here we'll use an in-memory dictionary.

_cache = {}


def get_cache(key: str) -> Optional[Dict[str, Any]]:
    return _cache.get(key)


def set_cache(key: str, value: Dict[str, Any]) -> None:
    _cache[key] = value


def get_audit_status(audit_id: str) -> Optional[Dict[str, Any]]:
    return _cache.get(f"status_{audit_id}")


def set_audit_status(audit_id: str, status: str, progress: int = 0, message: Optional[str] = None) -> None:
    payload: Dict[str, Any] = {"status": status, "progress": progress}
    if message:
        payload["message"] = message
    _cache[f"status_{audit_id}"] = payload


def load_demo_cache() -> None:
    """Seed the cache with demo audit data so the app works without API keys."""
    from cache.demo_data import DEMO_AUDIT_ID, DEMO_AUDIT_RESULT

    cache_key = f"audit_{DEMO_AUDIT_ID}"
    if cache_key not in _cache:
        _cache[cache_key] = DEMO_AUDIT_RESULT
        _cache[f"status_{DEMO_AUDIT_ID}"] = {"status": "done", "progress": 100}
        print(f"[cache] Demo audit data seeded (audit_id={DEMO_AUDIT_ID})")


# Auto-seed demo data on import
load_demo_cache()
