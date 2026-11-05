# Push Over

Multi-path Android wrap. Pull what the device allows, quarantine it, then follow a clean-OS playbook.

| | |
| --- | --- |
| What it is | Detect, pull, secure wrap, playbook. The Android pack inside Cooler is this same work. |
| What it is not | An FRP bypass. A Google-account skip. |
| Phoenix | If Phoenix is in the path, the original file stays. Phoenix does not delete the source. |
| Burn Box | If Burn Box is in the path, Burn Box deletes its own original after the safe copy. That rule is Burn Box's, not Phoenix's. |
| Status | The modes below are the current body. Code comes back in a later push. |
| Owner | LowC. Powered by Siren Logix. Toolaid. |

## Mission

Repush the code and finish the wrap. Owner and account paths stay proper. There is no FRP bypass in this project.

## Modes

| Mode | When | What it does |
|------|------|----------------|
| `auto` | Default | Detect USB and pick the safest path the device already allows |
| `owner` | You have the Google or OEM account | Use that account path, then pull. Do not skip the account. |
| `mtp` | Phone in MTP | Quarantine reachable files into the wrap vault |
| `adb` | Debugging already authorized by the owner | Deeper pull via adb |
| `download` | Samsung Download or fastboot, owned device | Official stock playbook. Expect a wipe. |

## Secure wrap

1. Quarantine copy under `data/quarantine/<case>/`
2. SHA-256 manifest
3. Optional PhoenixWrap step. The original stays.
4. Optional Burn Box upload. Burn Box's own rule deletes the file it took.
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
