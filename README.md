# Bilibili UP Update Tracker

监控 B 站 UP 主最新投稿，并通过 Email、通用 Webhook 或 Gotify 发送通知。支持 YAML、环境变量、命令行、Docker Compose 和 GitHub Actions。

## Docker Compose 快速开始

```bash
git clone https://github.com/Artistkisa/bilibili-up-update-tracker.git
cd bilibili-up-update-tracker
cp .env.example .env
```

编辑 `.env`，至少设置 UP 主列表并完整配置一个通知渠道：

```dotenv
TZ=Asia/Shanghai
CHECK_CRON=0 10 * * *
UP_USERS_JSON=[{"uid":68559,"name":"22和33"}]
NOTIFY_CHANNELS=email
EMAIL_SMTP_HOST=smtp.qq.com
EMAIL_SMTP_PORT=587
EMAIL_USER=your_email@qq.com
EMAIL_PASS=邮箱授权码
EMAIL_TO=recipient@example.com
```

启动并查看日志：

```bash
docker compose up -d --build
docker compose logs -f
```

数据保存到 `./data`，cron 日志保存到 `./logs`，容器默认自动重启。

## YAML 配置

```bash
cp config.example.yaml config.yaml
python src/monitor.py
```

配置结构：

```yaml
up_users:
  - uid: 68559
    name: 22和33

data_file: data/monitor_data.json

schedule:
  cron: "0 10 * * *"
  timezone: Asia/Shanghai

notifications:
  email:
    enabled: true
    smtp_host: smtp.qq.com
    smtp_port: 587
    username: your_email@qq.com
    password: 邮箱授权码
    recipients: [recipient@example.com]

  webhook:
    enabled: false
    url: https://example.com/webhook
    headers:
      Authorization: Bearer token
    timeout: 10

  gotify:
    enabled: false
    url: https://gotify.example.com
    token: application-token
    priority: 5
    timeout: 10
```

真正的 `config.yaml` 和 `.env` 已加入 `.gitignore`。不要把密码或 Token 写入示例文件或提交到 Git。

## 配置优先级与命令行

优先级为：

```text
命令行参数 > 环境变量 > config.yaml > 旧版 src/config.py > 内置默认值
```

命令行参数：

```bash
python src/monitor.py --config /path/config.yaml
python src/monitor.py --data-file /path/state.json
python src/monitor.py --up 68559:22和33 --up 403748305:BML制作指挥部
python src/monitor.py --notify webhook --notify gotify
```

敏感配置不提供命令行参数，避免进入 shell 历史。旧版 `src/config.py` 仅在没有新配置来源时兼容读取，并会显示弃用警告；计划在 v1.2 删除。

## 环境变量

| 分类 | 变量 |
| --- | --- |
| 基础 | `CONFIG_FILE`、`DATA_FILE`、`UP_USERS_JSON` |
| Docker 调度 | `CHECK_CRON`、`TZ` |
| 通知选择 | `NOTIFY_CHANNELS=email,webhook,gotify` |
| Email | `EMAIL_SMTP_HOST`、`EMAIL_SMTP_PORT`、`EMAIL_USER`、`EMAIL_PASS`、`EMAIL_TO` |
| Webhook | `WEBHOOK_URL`、`WEBHOOK_HEADERS_JSON`、`WEBHOOK_TIMEOUT` |
| Gotify | `GOTIFY_URL`、`GOTIFY_TOKEN`、`GOTIFY_PRIORITY`、`GOTIFY_TIMEOUT` |

`UP_USERS_JSON` 示例：

```json
[{"uid":68559,"name":"22和33"}]
```

## 通知行为

通用 Webhook 发送 `POST application/json`：

```json
{
  "event": "bilibili.video.updated",
  "checked_at": "2026-07-30T20:00:00+08:00",
  "updates": [
    {
      "uid": 68559,
      "up_name": "22和33",
      "bvid": "BV...",
      "title": "视频标题",
      "url": "https://www.bilibili.com/video/BV...",
      "published_at": "2026-07-30T19:00:00+08:00"
    }
  ]
}
```

同时启用多个渠道时，只有全部渠道成功才会确认更新。任一渠道失败，视频状态保持不变，并在下次检查时重试全部渠道。

## GitHub Actions

在仓库 Secrets 中配置：

- `UP_USERS_JSON`
- Email：`EMAIL_SMTP_HOST`、`EMAIL_SMTP_PORT`、`EMAIL_USER`、`EMAIL_PASS`、`EMAIL_TO`
- Webhook：`WEBHOOK_URL`、`WEBHOOK_HEADERS_JSON`
- Gotify：`GOTIFY_URL`、`GOTIFY_TOKEN`

在 Variables 中配置 `NOTIFY_CHANNELS`，例如 `email,gotify`。可选配置 `GOTIFY_PRIORITY`。

GitHub Actions 的计划任务使用 UTC，不能由运行时 `CHECK_CRON` 动态修改。要调整 Actions 执行时间，请编辑 `.github/workflows/monitor.yml` 中的 `schedule.cron`。

## 本机安装与测试

```bash
python -m pip install -r requirements.txt
python src/monitor.py
python -m unittest discover -s tests -v
```

要求 Python 3.11 或更高版本。

## License

[MIT](LICENSE)
