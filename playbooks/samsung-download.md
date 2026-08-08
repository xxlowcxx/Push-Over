# Samsung Download mode — stock flash playbook

## Preconditions
- Device you own / are authorized to service
- Battery > 30%
- **Push Over data pull already done** if you needed files (flash usually wipes)
- Official firmware for **exact model** (SamFW / SamMobile / OEM — your source of truth)

## Host tools
- Heimdall (Linux): NOT installed
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
