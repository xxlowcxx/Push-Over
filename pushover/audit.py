from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from pushover.paths import LOGS


def log(kind: str, message: str, **payload: Any) -> Path:
    day = time.strftime("%Y-%m-%d")
    path = LOGS / f"audit-{day}.jsonl"
    rec = {
        "ts": time.time(),
        "iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "kind": kind,
        "message": message,
        "payload": payload,
    }
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, default=str))
        f.write("\n")
    return path
