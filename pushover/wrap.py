"""Secure wrap — quarantine, hash, optional Phoenix + Burn Box."""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from pushover.audit import log
from pushover.paths import BURN_BOX_URL, CASES, PHOENIX, QUARANTINE, TRUSTED


@dataclass
class WrapItem:
    rel_path: str
    sha256: str
    size: int
    source: str
    phoenix: bool = False
    burn_box_id: int | None = None


@dataclass
class Case:
    id: str
    mode: str
    tech: str
    note: str
    ownership_note: str
    device_serial: str | None
    device_product: str | None
    created_at: float
    items: list[WrapItem] = field(default_factory=list)
    status: str = "open"
    notes: list[str] = field(default_factory=list)


def _case_id() -> str:
    return time.strftime("%Y%m%d-%H%M%S") + f"-{int(time.time() * 1000) % 100000:05d}"


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def new_case(
    mode: str,
    *,
    tech: str = "siren",
    note: str = "",
    ownership_note: str = "",
    serial: str | None = None,
    product: str | None = None,
) -> Case:
    c = Case(
        id=_case_id(),
        mode=mode,
        tech=tech,
        note=note,
        ownership_note=ownership_note or note,
        device_serial=serial,
        device_product=product,
        created_at=time.time(),
    )
    case_dir = QUARANTINE / c.id
    case_dir.mkdir(parents=True, exist_ok=True)
    save_case(c)
    log("case_created", c.id, mode=mode, tech=tech, serial=serial)
    return c


def case_dir(case: Case) -> Path:
    return QUARANTINE / case.id


def save_case(case: Case) -> Path:
    p = CASES / f"{case.id}.json"
    p.write_text(json.dumps(asdict(case), indent=2), encoding="utf-8")
    # also in quarantine folder
    (case_dir(case) / "CASE.json").write_text(
        json.dumps(asdict(case), indent=2), encoding="utf-8"
    )
    return p


def load_case(case_id: str) -> Case:
    p = CASES / f"{case_id}.json"
    raw = json.loads(p.read_text(encoding="utf-8"))
    items = [WrapItem(**i) for i in raw.pop("items", [])]
    return Case(items=items, **raw)


def wrap_file(
    case: Case,
    src: Path,
    *,
    rel: str | None = None,
    source: str = "mtp",
    use_phoenix: bool = False,
    use_burn_box: bool = False,
) -> WrapItem:
    """Copy one file into case quarantine and secure-wrap it."""
    src = src.resolve()
    if not src.is_file():
        raise FileNotFoundError(src)

    rel = rel or src.name
    dest = case_dir(case) / "files" / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)

    digest = _sha256(dest)
    item = WrapItem(
        rel_path=str(Path("files") / rel),
        sha256=digest,
        size=dest.stat().st_size,
        source=source,
    )

    if use_phoenix and PHOENIX.is_dir():
        phoenix_sh = PHOENIX / "phoenixwrap.sh"
        if phoenix_sh.is_file():
            try:
                subprocess.run(
                    [str(phoenix_sh), "run", str(dest), "--note", f"pushover:{case.id}"],
                    capture_output=True,
                    text=True,
                    timeout=120,
                    check=False,
                )
                item.phoenix = True
            except (OSError, subprocess.TimeoutExpired):
                case.notes.append(f"phoenix failed for {rel}")

    if use_burn_box:
        bb_id = _burn_box_upload(dest)
        if bb_id is not None:
            item.burn_box_id = bb_id

    case.items.append(item)
    save_case(case)
    log("wrap_file", rel, case=case.id, sha256=digest, size=item.size)
    return item


def _burn_box_upload(path: Path) -> int | None:
    try:
        import uuid

        boundary = uuid.uuid4().hex
        data = path.read_bytes()
        filename = path.name
        body = (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
            f"Content-Type: application/octet-stream\r\n\r\n"
        ).encode() + data + f"\r\n--{boundary}--\r\n".encode()
        req = urllib.request.Request(
            f"{BURN_BOX_URL.rstrip('/')}/api/files/upload",
            data=body,
            method="POST",
            headers={
                "Content-Type": f"multipart/form-data; boundary={boundary}",
            },
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = json.loads(resp.read().decode())
            return int(raw.get("id")) if raw.get("id") is not None else None
    except (urllib.error.URLError, urllib.error.HTTPError, OSError, ValueError, json.JSONDecodeError):
        return None


def seal_case(case: Case) -> Path:
    case.status = "sealed"
    manifest = {
        "pushover": "0.1.0",
        "law": "Secure wrap of device-accessible files only. No FRP bypass.",
        "case": asdict(case),
        "item_count": len(case.items),
        "sealed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    out = TRUSTED / f"{case.id}__manifest.json"
    out.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    save_case(case)
    log("case_sealed", case.id, items=len(case.items))
    return out
