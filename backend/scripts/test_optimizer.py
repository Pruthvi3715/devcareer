"""Tests for token_optimizer and claude_engine retry logic."""
import sys, os, time, textwrap
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from services import token_optimizer

SAMPLE_PYTHON = textwrap.dedent('''\
    """Module docstring to remove."""
    import os
    import json
    import os
    # comment
    def hello(name: str) -> str:
        """Docstring."""
        # inline comment
        return f"Hello, {name}"
    class Greeter:
        """Class docstring."""
        def greet(self):
            """Method docstring."""
            print("hi")
''')

def test_strips_docstrings():
    r = token_optimizer.compress_python(SAMPLE_PYTHON)
    assert '"""Module docstring' not in r
    assert '"""Docstring."""' not in r
    print("[PASS] Docstrings stripped")

def test_dedup_imports():
    r = token_optimizer.compress_python(SAMPLE_PYTHON)
    lines = [l.strip() for l in r.splitlines() if l.strip().startswith("import os")]
    assert len(lines) <= 1, f"Dupes: {lines}"
    print("[PASS] Imports deduplicated")

def test_reduces_size():
    r = token_optimizer.compress_python(SAMPLE_PYTHON)
    s = token_optimizer.compression_stats(SAMPLE_PYTHON, r)
    print(f"  {s['original_chars']} -> {s['compressed_chars']} ({s['reduction_pct']}%)")
    assert s["reduction_pct"] > 20
    print("[PASS] Good compression")

def test_preserves_logic():
    r = token_optimizer.compress_python(SAMPLE_PYTHON)
    assert "hello" in r and "Greeter" in r and "print" in r
    print("[PASS] Logic preserved")

def test_invalid_syntax():
    r = token_optimizer.compress_python("def broken(\n  not valid")
    assert len(r) > 0
    print("[PASS] Bad syntax handled")

def test_budget():
    files = [{"path": "main.py", "content": "x=1\n"*5000, "line_count": 5000, "is_entry_point": True, "is_test": False}]
    r = token_optimizer.optimize_code_review_payload(files, max_tokens=1000)
    total = sum(len(f["content"]) for f in r)
    assert total <= 1000 * 4 + 200
    print(f"[PASS] Budget: {total} chars")

def test_entry_point_priority():
    files = [
        {"path": "test.py", "content": "t", "line_count": 100, "is_entry_point": False, "is_test": True},
        {"path": "main.py", "content": "m", "line_count": 50, "is_entry_point": True, "is_test": False},
    ]
    r = token_optimizer.optimize_code_review_payload(files, max_tokens=100000)
    assert r[0]["path"] == "main.py"
    print("[PASS] Entry points first")

def test_skip_empty():
    files = [
        {"path": "empty.py", "content": "", "line_count": 0, "is_entry_point": False, "is_test": False},
        {"path": "real.py", "content": "x=1", "line_count": 1, "is_entry_point": False, "is_test": False},
    ]
    r = token_optimizer.optimize_code_review_payload(files, max_tokens=100000)
    assert all(f["path"] != "empty.py" for f in r)
    print("[PASS] Empty skipped")

def test_rate_tracker():
    from services.claude_engine import _record_request, _requests_in_window, _request_log, _request_log_lock
    with _request_log_lock:
        _request_log.clear()
    for _ in range(5):
        _record_request()
    assert _requests_in_window() == 5
    print("[PASS] Rate tracker works")

def test_cooldown_no_block():
    from services.claude_engine import _proactive_cooldown, _request_log, _request_log_lock
    with _request_log_lock:
        _request_log.clear()
    t = time.time()
    _proactive_cooldown()
    assert time.time() - t < 0.5
    print("[PASS] No false cooldown")

def test_stats():
    s = token_optimizer.compression_stats("x"*1000, "x"*400)
    assert s["reduction_pct"] == 60.0
    print("[PASS] Stats correct")

if __name__ == "__main__":
    tests = [test_strips_docstrings, test_dedup_imports, test_reduces_size,
             test_preserves_logic, test_invalid_syntax, test_budget,
             test_entry_point_priority, test_skip_empty, test_rate_tracker,
             test_cooldown_no_block, test_stats]
    p = f = 0
    for t in tests:
        try:
            print(f"\n>> {t.__name__}")
            t()
            p += 1
        except Exception as e:
            f += 1
            print(f"[FAIL] {t.__name__}: {e}")
    print(f"\n{'='*50}\n{p} passed, {f} failed")
    sys.exit(1 if f else 0)
