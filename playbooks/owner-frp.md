# Owner FRP path (proper)

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
