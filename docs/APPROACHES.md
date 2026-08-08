# Approaches Push Over services

1. **owner** — Sign into previous Google/OEM account on device → FRP satisfied → full pull + optional flash
2. **mtp** — MTP file tree pull → secure wrap
3. **adb** — Authorized debugging pull
4. **download** — Stock firmware flash playbook (wipe expected); account may still be required after
5. **auto** — Detect and route

All paths log a case. None skip FRP without the account.
