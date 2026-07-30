# Bilibili UP Update Tracker

Monitor new Bilibili uploads and notify through Email, a generic Webhook, or Gotify. Configuration is available through YAML, environment variables, CLI arguments, Docker Compose, and GitHub Actions.

## Docker Compose quick start

```bash
git clone https://github.com/Artistkisa/bilibili-up-update-tracker.git
cd bilibili-up-update-tracker
cp .env.example .env
```

Edit `.env` and configure the UP users plus at least one complete notification channel:

```dotenv
TZ=Asia/Shanghai
CHECK_CRON=0 10 * * *
UP_USERS_JSON=[{"uid":68559,"name":"22 and 33"}]
NOTIFY_CHANNELS=email
EMAIL_SMTP_HOST=smtp.qq.com
EMAIL_SMTP_PORT=587
EMAIL_USER=your_email@qq.com
EMAIL_PASS=replace_with_authorization_code
EMAIL_TO=recipient@example.com
```

```bash
docker compose up -d --build
docker compose logs -f
```

State is persisted in `./data`, cron logs in `./logs`, and the container uses `restart: unless-stopped`.

## YAML configuration

```bash
cp config.example.yaml config.yaml
python src/monitor.py
```

See [config.example.yaml](config.example.yaml) for Email, Webhook, Gotify, schedule, timezone, UP user, and data-file settings. Real `.env` and `config.yaml` files are ignored by Git.

Configuration precedence is:

```text
CLI arguments > environment variables > config.yaml > legacy src/config.py > defaults
```

CLI examples:

```bash
python src/monitor.py --config /path/config.yaml
python src/monitor.py --data-file /path/state.json
python src/monitor.py --up 68559:22-and-33 --up 403748305:BML
python src/monitor.py --notify webhook --notify gotify
```

Secrets intentionally have no CLI flags to keep them out of shell history. Legacy `src/config.py` is read only when no new configuration source exists, emits a deprecation warning, and is scheduled for removal in v1.2.

## Environment variables

| Area | Variables |
| --- | --- |
| Base | `CONFIG_FILE`, `DATA_FILE`, `UP_USERS_JSON` |
| Docker schedule | `CHECK_CRON`, `TZ` |
| Channel selection | `NOTIFY_CHANNELS=email,webhook,gotify` |
| Email | `EMAIL_SMTP_HOST`, `EMAIL_SMTP_PORT`, `EMAIL_USER`, `EMAIL_PASS`, `EMAIL_TO` |
| Webhook | `WEBHOOK_URL`, `WEBHOOK_HEADERS_JSON`, `WEBHOOK_TIMEOUT` |
| Gotify | `GOTIFY_URL`, `GOTIFY_TOKEN`, `GOTIFY_PRIORITY`, `GOTIFY_TIMEOUT` |

## Notification behavior

The generic Webhook receives an `application/json` POST containing the event name, check time, and an `updates` array with UID, UP name, BVID, title, URL, and publish time. Custom headers such as `Authorization` can be supplied with YAML or `WEBHOOK_HEADERS_JSON`.

When several channels are enabled, an update is committed only after every channel succeeds. If one fails, the old state remains and all enabled channels are retried on the next check.

## GitHub Actions

Configure `UP_USERS_JSON` and the selected channel credentials as repository Secrets. Set the repository Variable `NOTIFY_CHANNELS`, for example `email,gotify`.

GitHub Actions schedules use UTC and cannot be changed by runtime `CHECK_CRON`. Edit `schedule.cron` in `.github/workflows/monitor.yml` to change the Actions schedule.

## Local installation and tests

```bash
python -m pip install -r requirements.txt
python src/monitor.py
python -m unittest discover -s tests -v
```

Python 3.11 or later is required.

## License

[MIT](LICENSE)
