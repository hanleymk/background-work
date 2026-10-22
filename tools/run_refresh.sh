#!/usr/bin/env bash
# Nightly wrapper: silent on success or no-op; on failure posts the error to Telegram topic "Cron system messages".
# Env overrides (for testing): REFRESH_CMD
cd "$(dirname "$0")/.."
OUT=$(${REFRESH_CMD:-/usr/bin/python3 tools/refresh.py} 2>&1); RC=$?
echo "$(date -Is) rc=$RC $OUT" >> refresh.log
[ $RC -eq 0 ] && exit 0
set -a; . /root/.hermes/.env 2>/dev/null; set +a
MSG="⚠️ markhanley.com nightly refresh FAILED (exit $RC). Site was not updated.
$(echo "$OUT" | tail -n 8 | cut -c1-300)"
curl -s -m 30 -o /dev/null -w "telegram:%{http_code}\n" "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
  --data-urlencode "chat_id=8835949688" --data-urlencode "message_thread_id=2535" --data-urlencode "text=$MSG" >> refresh.log
exit $RC
