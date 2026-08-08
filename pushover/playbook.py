"""Clean OS flash playbooks — official paths only, confirm required."""
from __future__ import annotations

import shutil
from pathlib import Path

from pushover.paths import PLAYBOOKS


def samsung_download_playbook() -> str:
    heimdall = "installed" if shutil.which("heimdall") else "NOT installed"
    return f"""# Samsung Download mode — stock flash playbook

## Preconditions
- Device you own / are authorized to service
- Battery > 30%
- **Push Over data pull already done** if you needed files (flash usually wipes)
- Official firmware for **exact model** (SamFW / SamMobile / OEM — your source of truth)

## Host tools
- Heimdall (Linux): {heimdall}
- Odin (Windows ChaosForge host) — optional alternate

## Steps
1. Boot Download mode (model-specific: often Vol Down + Power, or Vol Down + Bixby + Power)
2. Confirm PC sees `04e8:685d` or similar (pushover detect → mode download)
3. `heimdall detect` (if installed)
4. Flash **stock** AP/BL/CP/CSC per OEM instructions for that model
5. First boot may show FRP / Google account — sign in with **previous account** (proper path)
6. Set new screen lock; return to Push Over owner/mtp for any post-setup backup

## Security
- This is **not** an FRP skip
- Wrong firmware can soft-brick — match model/CSC carefully
- Log case ID in your work order

## After flash
```bash
pushover detect
pushover owner --tech YOU --note "post-flash setup with Google account"
```
"""


def write_playbooks() -> list[Path]:
    PLAYBOOKS.mkdir(parents=True, exist_ok=True)
    paths = []
    p = PLAYBOOKS / "samsung-download.md"
    p.write_text(samsung_download_playbook(), encoding="utf-8")
    paths.append(p)
    p2 = PLAYBOOKS / "owner-frp.md"
    p2.write_text(
        """# Owner FRP path (proper)

1. On device setup screen: connect Wi‑Fi
2. Sign in with **previous Google account** (or OEM account if required)
3. Complete setup; set new PIN/biometrics
4. Enable USB File transfer and/or USB debugging if you want deeper pulls
5. Run:
   ```bash
   pushover mtp --tech YOU --note "post-owner unlock pull"
   # or
   pushover adb --tech YOU --note "post-owner unlock pull"
   ```

No bypass — this is the legitimate free-path.
""",
        encoding="utf-8",
    )
    paths.append(p2)
    return paths
