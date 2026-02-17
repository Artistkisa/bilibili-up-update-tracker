# Bilibili UP Update Tracker

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> 🔔 Track Bilibili UP主 video updates, get email notifications when new videos are uploaded

English | [简体中文](README.md)

## ✨ Features

- 📊 **Multi-UP Update Tracking** - Track updates from multiple UP主 simultaneously
- ⚡ **Async Fetching** - Fast concurrent video fetching with asyncio
- 🔒 **Anti-Detection** - Built on bilibili-api-python, handles signatures & rate limits
- 📧 **Email Notifications** - Get notified when tracked UP主 upload new videos
- 🐳 **Easy Deploy** - Docker & cron support

## 🚀 Quick Start

### 1. Requirements

- Python 3.8 or higher
- pip package manager

### 2. Install

```bash
# Clone repository
git clone https://github.com/yourusername/bilibili-up-update-tracker.git
cd bilibili-up-update-tracker

# Install dependencies
pip install -r requirements.txt
```

**Dependencies:**
- `bilibili-api-python` - Bilibili API library
- `aiohttp` - Async HTTP client

### 3. Configure

All configuration is in `src/config.py`:

#### 2.1 Add UP主 to Track

```python
UP_LIST = {
    # Format: UID: "Display Name"
    # Get UID from Bilibili space URL: https://space.bilibili.com/{UID}
    
    68559: "22和33",              # Example: Bilibili official
    403748305: "BML制作指挥部",     # Example: Bilibili official
    
    # Add your favorite UP主 here:
    # 12345678: "UP主名字",
    # 87654321: "Another UP",
}
```

**How to find UID:**
1. Go to the UP主's Bilibili space page
2. Look at the URL: `https://space.bilibili.com/12345678`
3. The number `12345678` is the UID

#### 2.2 Configure Email Notifications

```python
EMAIL_CONFIG = {
    "smtp_host": "smtp.qq.com",      # SMTP server
    "smtp_port": 587,                # SMTP port (587 for TLS)
    "smtp_user": "your_email@qq.com", # Your email address
    "smtp_pass": "your_auth_code",    # Email auth code (NOT password!)
    "to": ["recipient@example.com"]   # Recipient email(s)
}
```

**Common SMTP Settings:**

| Provider | SMTP Host | Port | Auth Code Guide |
|----------|-----------|------|-----------------|
| QQ Mail | smtp.qq.com | 587 | [Official Doc](https://service.mail.qq.com/cgi-bin/help?subtype=1&id=28&no=1001256) |
| Gmail | smtp.gmail.com | 587 | [Google Support](https://support.google.com/accounts/answer/185833) |
| 163 Mail | smtp.163.com | 25/465 | [Official Help](https://help.mail.163.com/faqDetail.do?code=d7a5dc8471cd0c0e8b4b12f4f2748598) |
| Outlook | smtp.office365.com | 587 | [Microsoft Support](https://support.microsoft.com/en-us/account-billing/how-to-get-a-app-password-in-microsoft-account-ff0e6c71-5aa8-4f36-8d6f-19aa9041d2e3) |

### 4. Run

```bash
cd src
python monitor.py
```

**Notes:**
- First run will auto-install missing dependencies (requires internet)
- First run records current state, no email sent
- Subsequent runs check for updates and send email notifications

**Supported Platforms:**
- ✅ Linux - Full support (direct run + cron scheduling)
- ✅ macOS - Full support (direct run + cron scheduling)
- ✅ Windows - Direct run supported (scheduling needs manual setup)

## 📧 Email Notification Example

When new videos are detected, you'll receive an email like this:

```
📺 B站 UP 主更新汇总
===================================

📅 检查时间：2026-02-17 22:18:00
📊 本次更新：2 个
👥 监控 UP 主：17 个

===================================
🎉 新视频列表
===================================

1. 【22和33】
   📹 人生列车Life Train【2026拜年纪单品】
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

===================================
📋 监控的 UP 主列表
===================================

✅ 22和33
✅ BML制作指挥部
✅ 黄霄雲
✅ ... (other UP主)

===================================

💡 提示：
- 每天 10:00 自动检查一次
- 有更新时发送汇总邮件
- 点击链接可直接观看视频
```

## 📁 Project Structure

```
bilibili-up-update-tracker/
├── src/
│   ├── monitor.py          # Main script
│   └── config.py           # Configuration (UP主 list + email)
├── data/                   # Data storage (auto-created)
├── logs/                   # Logs (auto-created)
├── requirements.txt        # Python dependencies
├── Dockerfile              # Docker config
├── LICENSE                 # MIT License
└── README.md               # This file
```

## 🐳 Docker Deploy

```bash
# Build
docker build -t bilibili-up-update-tracker .

# Run
docker run -d \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/src/config.py:/app/src/config.py \
  --name bilibili-tracker \
  bilibili-up-update-tracker
```

## ⏰ Schedule Automatic Checks (Cron)

To run the script automatically every day on Linux/Mac, set up a cron job:

```bash
# 1. Edit crontab
crontab -e

# 2. Add this line (run daily at 10:00 AM)
0 10 * * * cd /path/to/bilibili-up-update-tracker/src && python monitor.py >> ../logs/cron.log 2>&1
```

**Common Schedules:**

| Frequency | Cron Expression | Description |
|-----------|-----------------|-------------|
| Daily at 10:00 | `0 10 * * *` | Once a day at 10 AM |
| Twice daily | `0 10,22 * * *` | At 10 AM and 10 PM |
| Every 6 hours | `0 */6 * * *` | 4 times a day |
| Every hour | `0 * * * *` | Every hour on the hour |

**Cron Format:**
```
* * * * *
│ │ │ │ │
│ │ │ │ └── Day of week (0-7, 0 and 7 are Sunday)
│ │ │ └──── Month (1-12)
│ │ └────── Day of month (1-31)
│ └──────── Hour (0-23)
└────────── Minute (0-59)
```

**Verify Cron Setup:**

```bash
# List current cron jobs
crontab -l

# View cron logs (Ubuntu/Debian)
grep CRON /var/log/syslog
```

## 📄 License

MIT License
