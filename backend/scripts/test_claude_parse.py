"""Quick self-check for claude_engine JSON helpers (no API)."""
from __future__ import annotations

import os
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))
os.chdir(BACKEND)

from services.claude_engine import _parse_model_json, _strip_model_wrappers


def main() -> None:
    assert _parse_model_json('{"x": 1}')["x"] == 1
    assert _parse_model_json('pre\n{"x": 2}\n')["x"] == 2
    s = _strip_model_wrappers('<think>a</think>{"y": 3}')
    assert _parse_model_json(s)["y"] == 3
    print("parse helpers OK")


if __name__ == "__main__":
    main()
