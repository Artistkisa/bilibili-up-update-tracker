#!/bin/sh
set -eu

cron_expression=${CHECK_CRON:-"0 10 * * *"}
timezone=${TZ:-Asia/Shanghai}

field_count=$(printf '%s\n' "$cron_expression" | awk '{ print NF }')
if [ "$field_count" -ne 5 ] || printf '%s' "$cron_expression" | grep -q '[\r\n]'; then
    echo "Invalid CHECK_CRON: expected a five-field cron expression" >&2
    exit 2
fi

if [ ! -f "/usr/share/zoneinfo/$timezone" ]; then
    echo "Invalid TZ: timezone not found: $timezone" >&2
    exit 2
fi

ln -snf "/usr/share/zoneinfo/$timezone" /etc/localtime
printf '%s\n' "$timezone" > /etc/timezone

python3 - <<'PY'
import os
import shlex

names = (
    "CONFIG_FILE", "DATA_FILE", "UP_USERS_JSON", "CHECK_CRON", "TZ",
    "NOTIFY_CHANNELS", "EMAIL_SMTP_HOST", "EMAIL_SMTP_PORT", "EMAIL_USER",
    "EMAIL_PASS", "EMAIL_TO", "WEBHOOK_URL", "WEBHOOK_HEADERS_JSON",
    "WEBHOOK_TIMEOUT", "GOTIFY_URL", "GOTIFY_TOKEN", "GOTIFY_PRIORITY",
    "GOTIFY_TIMEOUT",
)
with open("/app/runtime.env", "w", encoding="utf-8") as output:
    for name in names:
        if name in os.environ:
            output.write(f"export {name}={shlex.quote(os.environ[name])}\n")
PY
chown root:appuser /app/runtime.env
chmod 640 /app/runtime.env

printf '%s cd /app/src && . /app/runtime.env && /usr/local/bin/python3 monitor.py >> /app/logs/cron.log 2>&1\n' \
    "$cron_expression" | crontab -u appuser -

touch /app/logs/cron.log
chown appuser:appuser /app/logs/cron.log

echo "Tracker scheduled with '$cron_expression' in timezone '$timezone'"
cron
exec tail -F /app/logs/cron.log
