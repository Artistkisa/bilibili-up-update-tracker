# Bilibili UP Update Tracker

[![Monitor](https://github.com/Artistkisa/bilibili-up-update-tracker/actions/workflows/monitor.yml/badge.svg)](https://github.com/Artistkisa/bilibili-up-update-tracker/actions/workflows/monitor.yml)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-supported-2496ED?logo=docker&logoColor=white)](Dockerfile)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/Artistkisa/bilibili-up-update-tracker?style=social)](https://github.com/Artistkisa/bilibili-up-update-tracker/stargazers)

> 自动追踪 B 站 UP 主的新投稿，并通过 Email、Webhook 或 Gotify 通知你。

无需一直打开 B 站，也不用手动刷新动态。配置一次后，程序会按计划检查多个 UP 主；发现新视频时发送包含标题、链接、发布时间、时长和播放量的汇总通知。

[English](README.en.md) · [配置示例](config.example.yaml) · [环境变量示例](.env.example) · [更新日志](CHANGELOG.md) · [参与贡献](CONTRIBUTING.md)

## 为什么用它？

- 📺 同时监控多个 UP 主
- 📣 支持 Email、通用 Webhook、Gotify
- 🐳 支持 Docker Compose 和 Docker CLI
- ☁️ 支持 GitHub Actions，无需自己的服务器
- 💻 支持本机运行、Linux/macOS cron 和 Windows 任务计划
- ⚙️ 支持 YAML、环境变量和命令行参数
- 🕐 Docker 中可自定义 cron 表达式和时区
- 💾 状态持久化，首次运行只建立基线，不发送旧视频
- 🔁 多渠道全部成功后才确认更新，失败会在下次检查时重试

## 通知效果

### 📧 Email

检测到新视频后，你会收到一封汇总邮件。一次检查发现多个 UP 主更新时，会合并到同一封邮件中：

```text
📺 B站 UP 主更新汇总
===================================

📅 检查时间：2026-02-17 22:18:00 CST
📊 本次更新：2 个
👥 监控 UP 主：5 个

1. 【22和33】
   📹 人生列车 Life Train【2026拜年纪单品】
   🔗 https://www.bilibili.com/video/BV1xxxxx
   🕐 发布时间：2026-01-28 20:00
   ⏱️ 时长：04:32
   👁️ 播放量：125万

2. 【黄霄雲】
   📹 【孙楠×黄霄雲】2026辽宁春晚《万家灯火共团圆》
   🔗 https://www.bilibili.com/video/BV1yyyyy
   🕐 发布时间：2026-01-27 19:30
   ⏱️ 时长：03:45
   👁️ 播放量：89万
```

### 🔗 Webhook

Webhook 会收到结构化 JSON，可用于接入飞书、企业微信、Node-RED、n8n、Home Assistant 或自己的服务：

```json
{
  "event": "bilibili.video.updated",
  "checked_at": "2026-02-17T22:18:00+08:00",
  "updates": [
    {
      "uid": 68559,
      "up_name": "22和33",
      "bvid": "BV1xxxxx",
      "title": "人生列车 Life Train【2026拜年纪单品】",
      "url": "https://www.bilibili.com/video/BV1xxxxx",
      "published_at": "2026-01-28T20:00:00+08:00"
    }
  ]
}
```

### 📱 Gotify

Gotify 会在手机或桌面客户端显示通知标题和视频汇总，点击消息中的链接即可前往 B 站观看。

## 选择部署方式

| 方式 | 适合谁 | 自动定时 | 状态持久化 |
| --- | --- | --- | --- |
| Docker Compose（推荐） | 有 NAS、VPS、家庭服务器 | 内置 cron | 本地数据卷 |
| Docker CLI | 已有自己的容器管理方式 | 内置 cron | 手动挂载数据卷 |
| GitHub Actions | 没有服务器，希望免费运行 | Actions schedule | Actions cache |
| 本机直接运行 | 调试、临时运行或自定义集成 | 需外部调度 | 本地文件 |
| 系统 cron / 任务计划 | 不使用 Docker 的长期部署 | 系统负责 | 本地文件 |

## 5 分钟开始：Docker Compose

### 1. 下载项目

```bash
git clone https://github.com/Artistkisa/bilibili-up-update-tracker.git
cd bilibili-up-update-tracker
cp .env.example .env
```

Windows PowerShell：

```powershell
Copy-Item .env.example .env
```

### 2. 编辑 `.env`

下面是最小 Email 配置：

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

UID 可以从 UP 主空间地址获取：`https://space.bilibili.com/68559` 中的 `68559`。

### 3. 启动

```bash
docker compose up -d --build
docker compose logs -f
```

容器会按照 `CHECK_CRON` 执行。监控状态保存在 `./data`，运行日志保存在 `./logs`，容器异常退出后会自动重启。

常用命令：

```bash
docker compose ps
docker compose restart
docker compose logs --tail=100
docker compose down
```

## 其他部署方式

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

适合没有服务器的用户。Fork 仓库后，在仓库设置中添加：

**Secrets**

- `UP_USERS_JSON`
- Email：`EMAIL_SMTP_HOST`、`EMAIL_SMTP_PORT`、`EMAIL_USER`、`EMAIL_PASS`、`EMAIL_TO`
- Webhook：`WEBHOOK_URL`、`WEBHOOK_HEADERS_JSON`
- Gotify：`GOTIFY_URL`、`GOTIFY_TOKEN`

**Variables**

- `NOTIFY_CHANNELS`，例如 `email` 或 `email,gotify`
- 可选：`GOTIFY_PRIORITY`

然后进入 **Actions → Monitor Bilibili UP → Run workflow** 手动测试。

GitHub Actions 的 cron 使用 UTC。默认 `0 2 * * *` 对应北京时间每天 10:00；如需修改，请编辑 `.github/workflows/monitor.yml`。运行时的 `CHECK_CRON` 不会改变 Actions schedule。

### 本机直接运行

要求 Python 3.11 或更高版本：

```bash
python -m pip install -r requirements.txt
cp config.example.yaml config.yaml
python src/monitor.py
```

Windows PowerShell 使用：

```powershell
Copy-Item config.example.yaml config.yaml
python src\monitor.py
```

直接运行只检查一次，适合测试配置或交给其他调度工具调用。

### Linux / macOS cron

```bash
crontab -e
```

例如每小时检查一次：

```cron
0 * * * * cd /path/to/bilibili-up-update-tracker && /usr/bin/python3 src/monitor.py >> logs/cron.log 2>&1
```

### Windows 任务计划程序

创建基本任务，将程序设置为 Python，可执行参数设置为：

```text
D:\path\to\bilibili-up-update-tracker\src\monitor.py
```

“起始于”设置为项目目录，并按需要选择每天或每小时执行。

## 配置方式

推荐复制示例：

```bash
cp config.example.yaml config.yaml
```

配置优先级固定为：

```text
命令行参数 > 环境变量 > config.yaml > 旧版 src/config.py > 内置默认值
```

真实的 `.env` 和 `config.yaml` 已被 Git 忽略，不要提交密码或 Token。

### YAML 示例

```yaml
up_users:
  - uid: 68559
    name: 22和33

data_file: data/monitor_data.json

notifications:
  email:
    enabled: true
    smtp_host: smtp.qq.com
    smtp_port: 587
    username: your_email@qq.com
    password: 邮箱授权码
    recipients:
      - recipient@example.com

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

完整字段见 [`config.example.yaml`](config.example.yaml)。

### 命令行覆盖

```bash
python src/monitor.py --config /path/config.yaml
python src/monitor.py --data-file /path/state.json
python src/monitor.py --up 68559:22和33 --up 403748305:BML制作指挥部
python src/monitor.py --notify webhook --notify gotify
```

密码和 Token 不提供 CLI 参数，避免被记录到 shell 历史。

### 环境变量

| 分类 | 变量 |
| --- | --- |
| 基础 | `CONFIG_FILE`、`DATA_FILE`、`UP_USERS_JSON` |
| Docker 调度 | `CHECK_CRON`、`TZ` |
| 通知选择 | `NOTIFY_CHANNELS` |
| Email | `EMAIL_SMTP_HOST`、`EMAIL_SMTP_PORT`、`EMAIL_USER`、`EMAIL_PASS`、`EMAIL_TO` |
| Webhook | `WEBHOOK_URL`、`WEBHOOK_HEADERS_JSON`、`WEBHOOK_TIMEOUT` |
| Gotify | `GOTIFY_URL`、`GOTIFY_TOKEN`、`GOTIFY_PRIORITY`、`GOTIFY_TIMEOUT` |

## 通知渠道

### Email

使用 SMTP + STARTTLS。QQ 邮箱需要使用授权码，而不是登录密码。多个收件人使用逗号分隔：

```dotenv
EMAIL_TO=one@example.com,two@example.com
```

### 通用 Webhook

程序向 `WEBHOOK_URL` 发送 `POST application/json`，并支持自定义请求头：

```dotenv
NOTIFY_CHANNELS=webhook
WEBHOOK_URL=https://example.com/bilibili-hook
WEBHOOK_HEADERS_JSON={"Authorization":"Bearer your-token"}
```

核心载荷与上方“通知效果”中的 Webhook 示例一致。

### Gotify

在 Gotify 中创建 Application，复制 Token：

```dotenv
NOTIFY_CHANNELS=gotify
GOTIFY_URL=https://gotify.example.com
GOTIFY_TOKEN=application-token
GOTIFY_PRIORITY=5
```

多个渠道可以同时启用：

```dotenv
NOTIFY_CHANNELS=email,webhook,gotify
```

只有所有启用渠道均发送成功，视频才会被标记为已通知。这样不会因某个渠道临时故障而永久漏报，但成功渠道可能在重试时收到重复通知。

## 从 v1.0 升级

v1.1 不再要求修改 `src/config.py`：

1. 将 UP 主列表迁移到 `config.yaml` 或 `UP_USERS_JSON`。
2. 将邮箱配置迁移到 YAML 或环境变量。
3. Docker 用户改用 `compose.yaml` 和 `.env`。
4. 确保原有 `data/monitor_data.json` 被保留。

v1.1 仍会在没有任何新配置来源时读取旧 `src/config.py`，但会显示弃用警告；该兼容计划在 v1.2 移除。

## 常见问题

**首次运行为什么没有通知？**

首次运行只记录当前最新视频，避免把历史内容当作新投稿。

**怎么修改检查频率？**

Docker/Compose 修改 `.env` 中的 `CHECK_CRON`；GitHub Actions 修改 workflow 的 UTC cron；本机部署修改系统 cron 或任务计划。

**为什么同一通知收到了两次？**

多渠道模式下，只要一个渠道失败，下一次会重试全部渠道，以保证不会永久漏报。

**数据保存在哪里？**

默认位于 `data/monitor_data.json`。Docker Compose 会映射到宿主机的 `./data`。

**如何查看错误？**

Compose 使用 `docker compose logs -f`；本机运行会直接输出各通知渠道的错误原因。

## 开发与测试

```bash
python -m unittest discover -s tests -v
python -m compileall -q src tests
docker compose config
docker compose build
```

欢迎提交 Issue 和 Pull Request。

## License

[MIT](LICENSE)
