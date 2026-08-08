"""USB / ADB detection — observe only, no bypass."""
from __future__ import annotations

import re
import shutil
import subprocess
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class DeviceSnapshot:
    mode: str = "none"  # none|mtp|download|adb|adb_unauthorized|unknown
    lsusb_lines: list[str] = field(default_factory=list)
    serial: str | None = None
    product: str | None = None
    vid_pid: str | None = None
    adb_state: str | None = None
    notes: list[str] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _run(cmd: list[str], timeout: int = 15) -> tuple[int, str, str]:
    env = None
    # Prefer user-local platform-tools (homebase install)
    home_adb = Path.home() / ".local" / "bin"
    tools_adb = Path.home() / "Projects" / "homebase" / "tools" / "platform-tools"
    path = os.environ.get("PATH", "")
    extras = []
    if home_adb.is_dir():
        extras.append(str(home_adb))
    if tools_adb.is_dir():
        extras.append(str(tools_adb))
    if extras:
        import os as _os

        env = {**_os.environ, "PATH": os.pathsep.join(extras + [path])}
    try:
        p = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout, env=env
        )
        return p.returncode, p.stdout or "", p.stderr or ""
    except FileNotFoundError:
        return 127, "", "not found"
    except subprocess.TimeoutExpired:
        return 124, "", "timeout"


def detect() -> DeviceSnapshot:
    snap = DeviceSnapshot()
    _, out, _ = _run(["lsusb"])
    lines = [ln for ln in out.splitlines() if ln.strip()]
    snap.lsusb_lines = lines

    samsung = [
        ln
        for ln in lines
        if re.search(r"04e8:", ln, re.I) or "Samsung" in ln
    ]

    for ln in samsung:
        m = re.search(r"ID\s+([0-9a-fA-F]{4}):([0-9a-fA-F]{4})", ln)
        if m:
            snap.vid_pid = f"{m.group(1)}:{m.group(2)}".lower()
        low = ln.lower()
        if "685d" in low or "download" in low:
            snap.mode = "download"
            snap.product = snap.product or "Samsung Download/Gadget"
            snap.notes.append("Download mode — stock flash playbook; expect wipe")
        elif "6860" in low or "mtp" in low:
            if snap.mode != "download":
                snap.mode = "mtp"
            snap.product = snap.product or "Samsung MTP"
            snap.notes.append("MTP — can quarantine reachable files")
        else:
            if snap.mode == "none":
                snap.mode = "unknown"
            snap.notes.append(f"Samsung: {ln}")

    for ln in lines:
        if re.search(r"05ac:", ln, re.I) or "Apple" in ln:
            snap.notes.append(
                "Apple device on bus — use iOS tools (idevice/restore), not Push Over Android"
            )

    # sysfs serial
    try:
        for d in Path("/sys/bus/usb/devices").iterdir():
            vid_p = d / "idVendor"
            if not vid_p.exists():
                continue
            if vid_p.read_text().strip() != "04e8":
                continue
            if (d / "serial").exists():
                snap.serial = (d / "serial").read_text().strip() or snap.serial
            if (d / "product").exists():
                snap.product = (d / "product").read_text().strip() or snap.product
    except OSError:
        pass

    if shutil.which("adb"):
        _run(["adb", "start-server"])
        _, out, _ = _run(["adb", "devices", "-l"])
        snap.raw["adb_devices"] = out
        for ln in out.splitlines()[1:]:
            ln = ln.strip()
            if not ln:
                continue
            parts = ln.split()
            if len(parts) < 2:
                continue
            serial, state = parts[0], parts[1]
            snap.serial = snap.serial or serial
            snap.adb_state = state
            if state == "device":
                snap.mode = "adb"
                snap.notes.append("ADB authorized — deep pull available")
            elif state == "unauthorized":
                if snap.mode in ("none", "unknown", "mtp"):
                    snap.mode = "adb_unauthorized"
                snap.notes.append("ADB unauthorized — allow debugging on phone")
    else:
        snap.notes.append("adb not installed — MTP/download paths only")

    if snap.mode == "none":
        snap.notes.append("No Android device detected on USB")

    snap.notes.append(
        "FRP policy: Push Over never skips Google/OEM account. "
        "Use mode 'owner' after signing in, or flash then sign in properly."
    )
    return snap
