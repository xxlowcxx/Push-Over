# Push Over

Multi-path Android wrap. Pull what the device allows, quarantine it, then follow a clean-OS playbook.

| | |
| --- | --- |
| What it is | Detect, pull, secure wrap, playbook. The Android pack inside Cooler is this same work. |
| What it is not | An FRP bypass. A Google-account skip. Phoenix, which keeps originals. Burn Box, which deletes them. |
| Status | The modes below are the current body. Code comes back in a later push. |
| Owner | LowC. Powered by Siren Logix. Toolaid. |

## Mission

Repush the code and finish the wrap. Owner and account paths stay proper.

## Modes

| Mode | When | What it does |
|------|------|----------------|
| `auto` | Default | Detect USB and pick the safest path |
| `owner` | You have the Google or OEM account | Checklist to clear FRP properly, then pull |
| `mtp` | Phone in MTP | Quarantine reachable files into the wrap vault |
| `adb` | Debugging authorized | Deeper pull via adb |
| `download` | Samsung Download or fastboot | Stock flash playbook. Expect a wipe. |

## Secure wrap

1. Quarantine copy under `data/quarantine/<case>/`
2. SHA-256 manifest
3. Optional PhoenixWrap rebirth, if it is installed
4. Optional Burn Box upload, if it is up
5. Case JSON and an audit log

## Quick start

```bash
cd ~/Projects/repos/Push-Over
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
./bin/pushover doctor
./bin/pushover detect
./bin/pushover auto --tech lowc --note "owned repair"
```

No FRP or Google-account skip. A flash uses the official playbook for a device you own. A full pull happens only when the device exposes the files.
