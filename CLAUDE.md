# background-work (markhanley.com)
Mark's on-screen background-actor log. Static site in docs/ on GitHub Pages (hanleymk/background-work, main, /docs), domain markhanley.com (Hover DNS -> GitHub Pages IPs, CNAME www).
Source of truth: Google Sheet 1H3u_c0_rE7Vxt1WqkbqcQuB-eNFzDuPJRuxSoZt0L5o (text in A:F, screenshots are embedded images in cols F+).
Refresh: `/usr/bin/python3 tools/refresh.py` (system python has Google libs; Pillow is only in the Hermes venv, called by tools/resize.py). Nightly 3:30am via Hermes cron job "Background Work Site Refresh" (no_agent, script ~/.hermes/scripts/background-work-refresh.sh): silent on success/no-op, posts an ERROR block to Telegram topic "Cron system messages" on failure. Pushes only if changed.
Rules: rows below "Not Yet Released" are ignored. No episode => Film; episode => TV. Chicago Fire/Med/PD get their own pills. 05/14/22 typo mapped in DATE_FIX; TV dates before 2010 are hidden + warned.
Images are named by content hash (docs/img/<hash>_t.jpg / _l.jpg); unused ones are deleted on refresh. Abort guard if sheet looks truncated.
Google token needs drive.readonly (Drive API export is too large; script uses docs.google.com export URL with the bearer token).
