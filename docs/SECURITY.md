# Push Over security model

## Satisfies security
- No FRP / Google account circumvention module
- Explicit modes; flash requires `--confirm-flash`
- Case ID, tech ID, ownership note on runs
- SHA-256 of every pulled file
- Audit JSONL

## Satisfies user
- Pulls everything the device **allows** (MTP/ADB)
- Secure wrap vault (quarantine + manifest)
- Optional PhoenixWrap + Burn Box deposit
- Clear playbooks for clean OS reinstall after backup
- Owner mode walks proper account unlock first
