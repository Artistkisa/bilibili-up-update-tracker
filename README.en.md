# Bilibili UP Update Tracker

> Automatically track new Bilibili uploads and notify through Email, Webhook, or Gotify.

Configure it once and let it check multiple UP creators on a schedule. New uploads produce a summary containing the title, URL, publish time, duration, and play count.

[中文](README.md) · [YAML example](config.example.yaml) · [Environment example](.env.example)

## Highlights

- Monitor multiple UP creators
- Email, generic Webhook, and Gotify notifications
- Docker Compose and Docker CLI deployment
- Serverless scheduling with GitHub Actions
- Direct Python, Linux/macOS cron, and Windows Task Scheduler support
- YAML, environment-variable, and CLI configuration
- Configurable Docker cron schedule and timezone
- Persistent state with no historical notifications on first run
- Updates are committed only after every enabled channel succeeds

## Choose a deployment method

| Method | Best for | Scheduling | Persistence |
| --- | --- | --- | --- |
| Docker Compose (recommended) | NAS, VPS, home server | Built-in cron | Host volumes |
| Docker CLI | Existing container workflows | Built-in cron | Manual volumes |
| GitHub Actions | Users without a server | Actions schedule | Actions cache |
| Direct Python | Testing and custom integrations | External scheduler | Local file |
| System cron / Task Scheduler | Long-running non-Docker installs | Operating system | Local file |

## Five-minute Docker Compose setup

```bash
git clone https://github.com/Artistkisa/bilibili-up-update-tracker.git
cd bilibili-up-update-tracker
cp .env.example .env
```

Edit `.env` with at least one UP creator and one complete notification channel:

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

Start the service:

```bash
docker compose up -d --build
docker compose logs -f
```

State is stored in `./data`, logs in `./logs`, and the container restarts automatically.

## Other deployment methods

### Docker CLI

```bash
docker build -t bilibili-up-update-tracker .
docker run -d \
  --name bilibili-up-tracker \
  --restart unless-stopped \
  --env-file .env \
  -v "$(pwd)/data:/app/data" \
  -v "$(pwd)/logs:/app/logs" \
  bilibili-up-update-tracker
```

### GitHub Actions

Fork the repository and add `UP_USERS_JSON` plus the credentials for your selected notification channels as repository Secrets. Add `NOTIFY_CHANNELS` as a repository Variable, for example `email,gotify`, then run **Actions → Monitor Bilibili UP → Run workflow**.

GitHub Actions schedules use UTC. The default `0 2 * * *` runs at 10:00 in UTC+8. Edit `.github/workflows/monitor.yml` to change it; runtime `CHECK_CRON` does not modify the Actions schedule.

### Direct Python

```bash
python -m pip install -r requirements.txt
cp config.example.yaml config.yaml
python src/monitor.py
```

Direct execution checks once. Use system cron, Task Scheduler, or another automation tool for recurring checks.

### Linux/macOS cron

```cron
0 * * * * cd /path/to/bilibili-up-update-tracker && /usr/bin/python3 src/monitor.py >> logs/cron.log 2>&1
```

### Windows Task Scheduler

Create a basic task that runs Python with `D:\path\to\project\src\monitor.py` as the argument and the project directory as “Start in.”

## Configuration

Copy [config.example.yaml](config.example.yaml) to `config.yaml`, or use [.env.example](.env.example). Real `.env` and `config.yaml` files are ignored by Git.

Configuration precedence:

```text
CLI arguments > environment variables > config.yaml > legacy src/config.py > defaults
```

CLI examples:

```bash
python src/monitor.py --config /path/config.yaml
python src/monitor.py --data-file /path/state.json
python src/monitor.py --up 68559:creator-name --up 403748305:BML
python src/monitor.py --notify webhook --notify gotify
```

Secrets intentionally have no CLI flags, keeping them out of shell history.

| Area | Environment variables |
| --- | --- |
| Base | `CONFIG_FILE`, `DATA_FILE`, `UP_USERS_JSON` |
| Docker schedule | `CHECK_CRON`, `TZ` |
| Channels | `NOTIFY_CHANNELS` |
| Email | `EMAIL_SMTP_HOST`, `EMAIL_SMTP_PORT`, `EMAIL_USER`, `EMAIL_PASS`, `EMAIL_TO` |
| Webhook | `WEBHOOK_URL`, `WEBHOOK_HEADERS_JSON`, `WEBHOOK_TIMEOUT` |
| Gotify | `GOTIFY_URL`, `GOTIFY_TOKEN`, `GOTIFY_PRIORITY`, `GOTIFY_TIMEOUT` |

## Notification channels

The generic Webhook receives an `application/json` POST containing `event`, `checked_at`, and an `updates` array with UID, creator name, BVID, title, URL, and publish time. Custom headers such as `Authorization` are supported.

For Gotify, create an Application and configure its server URL, application Token, and optional priority.

Enable several channels with:

```dotenv
NOTIFY_CHANNELS=email,webhook,gotify
```

An upload is marked as notified only when every enabled channel succeeds. A failure retries all channels during the next check, preventing permanent missed notifications at the cost of possible duplicates on channels that already succeeded.

## Upgrading from v1.0

1. Move the UP list to `config.yaml` or `UP_USERS_JSON`.
2. Move email settings to YAML or environment variables.
3. Docker users should adopt `compose.yaml` and `.env`.
4. Preserve the existing `data/monitor_data.json` file.

v1.1 reads legacy `src/config.py` only when no new configuration source exists and emits a deprecation warning. Legacy support is scheduled for removal in v1.2.

## FAQ

**Why is there no notification on the first run?**

The first run records the current latest uploads as a baseline, avoiding historical notifications.

**How do I change the interval?**

Use `CHECK_CRON` for Docker, edit the workflow UTC cron for GitHub Actions, or configure your operating-system scheduler.

**Where is state stored?**

The default is `data/monitor_data.json`; Compose maps it to the host `./data` directory.

**How do I inspect errors?**

Use `docker compose logs -f`, or run the Python command directly to see per-channel errors.

## Development

```bash
python -m unittest discover -s tests -v
python -m compileall -q src tests
docker compose config
docker compose build
```

Issues and pull requests are welcome.

## License

[MIT](LICENSE)
