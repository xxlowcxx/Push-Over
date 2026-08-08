"""MTP pull — gvfs, jmtpfs, or free bus from KDE kiod then retry."""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from pushover.audit import log
from pushover.wrap import Case, wrap_file


def _run(cmd: list[str], timeout: int = 120) -> tuple[int, str, str]:
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return p.returncode, p.stdout or "", p.stderr or ""
    except FileNotFoundError:
        return 127, "", "not found"
    except subprocess.TimeoutExpired:
        return 124, "", "timeout"


def find_gvfs_mtp() -> Path | None:
    uid = os.getuid()
    base = Path(f"/run/user/{uid}/gvfs")
    if not base.is_dir():
        return None
    for p in base.iterdir():
        name = p.name.lower()
        if "mtp" in name or "samsung" in name or "android" in name:
            return p
    return None


def _walk_pull(
    case: Case,
    root: Path,
    *,
    source: str,
    use_phoenix: bool,
    use_burn_box: bool,
    max_files: int,
) -> tuple[int, list[str]]:
    pulled = 0
    errors: list[str] = []
    for fp in root.rglob("*"):
        if pulled >= max_files:
            errors.append(f"hit max_files={max_files}")
            break
        if not fp.is_file():
            continue
        # skip noise
        if any(part.startswith(".") and part not in (".", "..") for part in fp.parts[-2:]):
            if fp.name.startswith(".") and fp.stat().st_size == 0:
                continue
        try:
            rel = str(fp.relative_to(root))
            wrap_file(
                case,
                fp,
                rel=rel,
                source=source,
                use_phoenix=use_phoenix,
                use_burn_box=use_burn_box,
            )
            pulled += 1
        except OSError as e:
            errors.append(f"{fp}: {e}")
    return pulled, errors


def try_release_kiod() -> bool:
    """Best-effort: stop user kiod holding MTP so libmtp/jmtpfs can attach."""
    # kiod6 holds Samsung MTP on KDE — restart is invasive but owner-authorized for mission
    code, out, err = _run(["pgrep", "-u", str(os.getuid()), "-x", "kiod6"])
    if code != 0:
        code, out, err = _run(["pgrep", "-u", str(os.getuid()), "kiod"])
    if code != 0 or not out.strip():
        return False
    pids = out.split()
    for pid in pids:
        _run(["kill", "-TERM", pid])
    time.sleep(1.5)
    log("mtp_kiod_release", "sent TERM to kiod", pids=pids)
    return True


def pull_mtp(
    case: Case,
    *,
    use_phoenix: bool = False,
    use_burn_box: bool = False,
    max_files: int = 10000,
    release_kiod: bool = True,
) -> dict:
    """Pull reachable MTP files into secure wrap."""
    methods_tried: list[str] = []

    mounted = find_gvfs_mtp()
    if mounted:
        methods_tried.append("gvfs")
        log("mtp_pull", "using gvfs mount", path=str(mounted))
        pulled, errors = _walk_pull(
            case,
            mounted,
            source="mtp-gvfs",
            use_phoenix=use_phoenix,
            use_burn_box=use_burn_box,
            max_files=max_files,
        )
        return {
            "pulled": pulled,
            "method": "gvfs",
            "errors": errors[:20],
            "methods_tried": methods_tried,
        }

    if release_kiod:
        try_release_kiod()
        time.sleep(0.5)

    if shutil.which("jmtpfs"):
        methods_tried.append("jmtpfs")
        tmp = Path(tempfile.mkdtemp(prefix="pushover-mtp-"))
        code, out, err = _run(["jmtpfs", "-o", "allow_other", str(tmp)])
        # jmtpfs often returns 0 after fuse daemonize
        time.sleep(2)
        if any(tmp.iterdir()) or code == 0:
            try:
                pulled, errors = _walk_pull(
                    case,
                    tmp,
                    source="mtp-jmtpfs",
                    use_phoenix=use_phoenix,
                    use_burn_box=use_burn_box,
                    max_files=max_files,
                )
                return {
                    "pulled": pulled,
                    "method": "jmtpfs",
                    "errors": errors[:20],
                    "methods_tried": methods_tried,
                }
            finally:
                _run(["fusermount", "-u", str(tmp)])
                _run(["fusermount3", "-u", str(tmp)])

    # simple-mtpfs
    if shutil.which("simple-mtpfs"):
        methods_tried.append("simple-mtpfs")
        tmp = Path(tempfile.mkdtemp(prefix="pushover-smtp-"))
        code, out, err = _run(["simple-mtpfs", str(tmp)])
        time.sleep(1.5)
        if any(tmp.iterdir()) if tmp.exists() else False:
            try:
                pulled, errors = _walk_pull(
                    case,
                    tmp,
                    source="mtp-simple",
                    use_phoenix=use_phoenix,
                    use_burn_box=use_burn_box,
                    max_files=max_files,
                )
                return {
                    "pulled": pulled,
                    "method": "simple-mtpfs",
                    "errors": errors[:20],
                    "methods_tried": methods_tried,
                }
            finally:
                _run(["fusermount", "-u", str(tmp)])

    methods_tried.append("mtp-detect")
    code, out, err = _run(["mtp-detect"], timeout=10)
    msg = (
        "MTP not mounted. Unlock phone, set USB = File transfer, open once in Dolphin, "
        f"or install jmtpfs. Then: pushover mtp --case {case.id}"
    )
    case.notes.append(msg)
    log("mtp_pull_blocked", msg, mtp_detect=(out or "")[:500], err=(err or "")[:300])
    return {
        "pulled": 0,
        "method": "none",
        "errors": [msg],
        "methods_tried": methods_tried,
        "hint": "File transfer + unlock; optional: sudo pacman -S jmtpfs",
    }
