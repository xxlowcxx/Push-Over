from __future__ import annotations

import os
from pathlib import Path

_PKG = Path(__file__).resolve().parents[1]


def root() -> Path:
    return Path(os.environ.get("PUSHOVER_ROOT", _PKG)).expanduser().resolve()


ROOT = root()
DATA = Path(os.environ.get("PUSHOVER_DATA", ROOT / "data"))
QUARANTINE = DATA / "quarantine"
TRUSTED = DATA / "trusted"
LOGS = DATA / "logs"
CASES = DATA / "cases"
PLAYBOOKS = ROOT / "playbooks"
BURN_BOX_URL = os.environ.get("BURN_BOX_URL", "http://127.0.0.1:5000")
PHOENIX = Path(
    os.environ.get("PHOENIXWRAP_ROOT", Path.home() / "Projects/repos/PhoenixWrap")
)

for d in (DATA, QUARANTINE, TRUSTED, LOGS, CASES, PLAYBOOKS):
    d.mkdir(parents=True, exist_ok=True)
