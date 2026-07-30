"""Notification channel implementations."""

import json
import smtplib
from datetime import datetime
from email.header import Header
from email.mime.text import MIMEText
from urllib.parse import urlencode
from urllib.parse import urlsplit
from urllib.request import Request, urlopen


def format_time(timestamp):
    if not timestamp:
        return "未知"
    try:
        return datetime.fromtimestamp(timestamp).astimezone().strftime("%Y-%m-%d %H:%M")
    except (TypeError, ValueError, OSError):
        return str(timestamp)


def format_play_count(value):
    try:
        count = int(value)
    except (TypeError, ValueError):
        return str(value) if value is not None else "未知"
    if count >= 100_000_000:
        amount = count / 100_000_000
        return f"{amount:g}亿"
    if count >= 10_000:
        amount = count / 10_000
        return f"{amount:g}万"
    return str(count)


def format_message(updates, all_results, total_up):
    lines = [
        "📺 B站 UP 主更新汇总", "=" * 35, "",
        f"📅 检查时间：{datetime.now().astimezone().strftime('%Y-%m-%d %H:%M:%S %Z')}",
        f"📊 本次更新：{len(updates)} 个", f"👥 监控 UP 主：{total_up} 个", "",
        "=" * 35, "🎉 新视频列表", "=" * 35, "",
    ]
    for index, update in enumerate(updates, 1):
        video = update["video"]
        lines.extend([
            f"{index}. 【{update['name']}】", f"   📹 {video['title']}",
            f"   🔗 {video['link']}", f"   🕐 发布时间：{format_time(video['created'])}",
            f"   ⏱️ 时长：{video['length']}",
            f"   👁️ 播放量：{format_play_count(video['play'])}", "",
        ])
    failed = [item["name"] for item in all_results if not item.get("success")]
    if failed:
        lines.append(f"⚠️ 获取失败：{', '.join(failed)}")
    return "\n".join(lines)


def webhook_payload(updates, checked_at):
    return {
        "event": "bilibili.video.updated",
        "checked_at": checked_at,
        "updates": [
            {
                "uid": item["uid"], "up_name": item["name"],
                "bvid": item["video"]["bvid"], "title": item["video"]["title"],
                "url": item["video"]["link"],
                "published_at": datetime.fromtimestamp(item["video"]["created"]).astimezone().isoformat()
                if item["video"].get("created") else None,
            }
            for item in updates
        ],
    }


def send_email(config, subject, body):
    message = MIMEText(body, "plain", "utf-8")
    message["Subject"] = Header(subject, "utf-8")
    message["From"] = config["username"]
    message["To"] = ", ".join(config["recipients"])
    with smtplib.SMTP(config["smtp_host"], int(config["smtp_port"])) as server:
        server.starttls()
        server.login(config["username"], config["password"])
        server.sendmail(config["username"], config["recipients"], message.as_string())


def post_json(url, payload, headers=None, timeout=10):
    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("Notification URL must be an absolute HTTP(S) URL")
    request_headers = {"Content-Type": "application/json"}
    request_headers.update(headers or {})
    request = Request(
        url, data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers=request_headers, method="POST",
    )
    with urlopen(request, timeout=float(timeout)) as response:
        if not 200 <= response.status < 300:
            raise RuntimeError(f"HTTP {response.status}")


def send_gotify(config, subject, body):
    base_url = config["url"].rstrip("/") + "/message"
    url = f"{base_url}?{urlencode({'token': config['token']})}"
    post_json(
        url,
        {"title": subject, "message": body, "priority": int(config.get("priority", 5))},
        timeout=config.get("timeout", 10),
    )


def send_notifications(settings, updates, all_results, checked_at):
    subject = f"🎬 B站 UP 主更新汇总（{len(updates)}个更新）"
    body = format_message(updates, all_results, len(settings["up_users"]))
    payload = webhook_payload(updates, checked_at)
    outcomes = []
    for channel in ("email", "webhook", "gotify"):
        config = settings["notifications"][channel]
        if not config.get("enabled"):
            continue
        try:
            if channel == "email":
                send_email(config, subject, body)
            elif channel == "webhook":
                post_json(config["url"], payload, config.get("headers"), config.get("timeout", 10))
            else:
                send_gotify(config, subject, body)
            outcomes.append({"channel": channel, "success": True, "error": None})
        except Exception as exc:
            outcomes.append({"channel": channel, "success": False, "error": str(exc)})
    return outcomes
