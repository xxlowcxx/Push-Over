# Push Over

**Toolaid · Owner LowC · Powered by Siren Logix**

> Multi-path Android service: detect → pull what the device allows → **secure wrap** → clean-OS playbook.
> **Not an FRP bypass.** Owner/account paths stay proper.

## Modes

| Mode | When | What it does |
|------|------|----------------|
| `auto` | Default | Detect USB and pick safest path |
| `owner` | You have Google/OEM account | Checklist to clear FRP properly, then pull |
| `mtp` | Phone in MTP | Quarantine reachable files into wrap vault |
| `adb` | Debugging authorized | Deeper pull via adb |
| `download` | Samsung Download / fastboot | Stock flash **playbook** (expect wipe) |

## Secure wrap

Pulled files get:

1. Quarantine copy under `data/quarantine/<case>/`
2. SHA-256 manifest
3. Optional **PhoenixWrap** rebirth (if installed)
4. Optional **Burn Box** upload (if `:5000` is up)
5. Case JSON + audit log

## Quick start

```bash
cd ~/Projects/repos/Push-Over
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
./bin/pushover doctor
./bin/pushover detect
./bin/pushover auto --tech lowc --note "owned repair"
```

## Hard line

No FRP/Google account skip. Flash = official playbooks for **owned** devices. Full pull only when the device **exposes** files.
