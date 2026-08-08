"""ADB pull when debugging is authorized."""
from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

from pushover.audit import log
from pushover.wrap import Case, wrap_file

# Common user-accessible paths (no root required)
DEFAULT_PATHS = [
    "/sdcard/DCIM",
    "/sdcard/Pictures",
    "/sdcard/Download",
    "/sdcard/Documents",
    "/sdcard/Movies",
    "/sdcard/Music",
    "/sdcard/Android/media",
]


def _run(cmd: list[str], timeout: int = 300) -> tuple[int, str, str]:
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return p.returncode, p.stdout or "", p.stderr or ""
    except FileNotFoundError:
        return 127, "", "adb not found"
    except subprocess.TimeoutExpired:
        return 124, "", "timeout"


def pull_adb(
    case: Case,
    *,
    paths: list[str] | None = None,
    use_phoenix: bool = False,
    use_burn_box: bool = False,
) -> dict:
    if not shutil.which("adb"):
        return {"pulled": 0, "errors": ["adb not installed"]}

    paths = paths or DEFAULT_PATHS
    tmp = Path(tempfile.mkdtemp(prefix="pushover-adb-"))
    pulled = 0
    errors: list[str] = []

    for remote in paths:
        local = tmp / remote.lstrip("/")
        local.parent.mkdir(parents=True, exist_ok=True)
        code, out, err = _run(["adb", "pull", remote, str(local)])
        if code != 0:
            errors.append(f"{remote}: {err.strip() or out.strip() or 'fail'}")
            continue
        # walk pulled tree
        root = local if local.exists() else tmp
        for fp in root.rglob("*"):
            if not fp.is_file():
                continue
            try:
                rel = str(fp.relative_to(tmp))
                wrap_file(
                    case,
                    fp,
                    rel=rel,
                    source="adb",
                    use_phoenix=use_phoenix,
                    use_burn_box=use_burn_box,
                )
                pulled += 1
            except OSError as e:
                errors.append(str(e))

    log("adb_pull", f"pulled={pulled}", case=case.id)
    return {"pulled": pulled, "errors": errors[:30], "tmp": str(tmp)}
