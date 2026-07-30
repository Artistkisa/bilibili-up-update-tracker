#!/usr/bin/env python3
"""Bilibili UP update tracker."""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

from bilibili_api import user

from notifiers import send_notifications
from settings import ConfigError, load_settings


def empty_data():
    return {"lastCheck": None, "upData": {}, "updateCount": 0}


def load_data(data_file):
    data_path = Path(data_file)
    try:
        if data_path.exists():
            return json.loads(data_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"读取数据文件失败: {exc}", file=sys.stderr)
    return empty_data()


def save_data(data, data_file):
    data_path = Path(data_file)
    temp_path = data_path.with_suffix(data_path.suffix + ".tmp")
    try:
        data_path.parent.mkdir(parents=True, exist_ok=True)
        temp_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        temp_path.replace(data_path)
        return True
    except OSError as exc:
        print(f"保存数据文件失败: {exc}", file=sys.stderr)
        try:
            temp_path.unlink(missing_ok=True)
        except OSError:
            pass
        return False


def apply_updates(data, updates):
    for result in updates:
        uid_str = str(result["uid"])
        video = result["video"]
        up_data = data["upData"].setdefault(uid_str, {
            "lastBvid": None, "lastTitle": None, "upName": result["name"],
        })
        up_data["lastBvid"] = video["bvid"]
        up_data["lastTitle"] = video["title"]
        data["updateCount"] += 1


def commit_updates_after_notification(data, updates, notification_sent):
    if not notification_sent:
        return False
    apply_updates(data, updates)
    return True


async def fetch_up_video(uid, name):
    try:
        api_user = user.User(uid=uid)
        videos = await api_user.get_videos(ps=1, pn=1, order=user.VideoOrder.PUBDATE)
        video_list = videos.get("list", {}).get("vlist", [])
        if not video_list:
            return {"uid": uid, "name": name, "success": True, "video": None}
        latest = video_list[0]
        return {
            "uid": uid, "name": name, "success": True,
            "video": {
                "bvid": latest.get("bvid"), "title": latest.get("title"),
                "created": latest.get("created"), "length": latest.get("length"),
                "play": latest.get("play"),
                "link": f"https://www.bilibili.com/video/{latest.get('bvid')}",
            },
        }
    except Exception as exc:  # The upstream library exposes several API exception types.
        return {"uid": uid, "name": name, "success": False, "error": str(exc)}


def detect_updates(data, results):
    updates = []
    for result in results:
        if not result["success"]:
            print(f"❌ [{result['name']}] 获取失败: {result.get('error', '未知错误')}")
            continue
        video = result["video"]
        if not video:
            print(f"⚠️  [{result['name']}] 无视频")
            continue
        uid_str = str(result["uid"])
        up_data = data["upData"].setdefault(uid_str, {
            "lastBvid": None, "lastTitle": None, "upName": result["name"],
        })
        if up_data["lastBvid"] is None:
            print(f"📝 [{result['name']}] 首次记录: {video['title'][:40]}...")
            up_data["lastBvid"] = video["bvid"]
            up_data["lastTitle"] = video["title"]
        elif video["bvid"] != up_data["lastBvid"]:
            print(f"🎉 [{result['name']}] 有新视频: {video['title'][:40]}...")
            updates.append(result)
        else:
            print(f"✅ [{result['name']}] 无更新")
    return updates


async def run(settings):
    data = load_data(settings["data_file"])
    first_run = not data["upData"]
    checked_at = datetime.now().astimezone().isoformat()
    users = settings["up_users"]
    print(f"[{checked_at}] 开始检查 {len(users)} 个 UP 主...\n")
    results = await asyncio.gather(*[
        fetch_up_video(item["uid"], item["name"]) for item in users
    ])
    updates = detect_updates(data, results)

    notification_results = []
    notification_sent = False
    if updates and not first_run:
        print(f"\n📣 发送通知（{len(updates)} 个更新）...")
        notification_results = send_notifications(settings, updates, results, checked_at)
        for outcome in notification_results:
            if outcome["success"]:
                print(f"✅ {outcome['channel']} 通知成功")
            else:
                print(f"❌ {outcome['channel']} 通知失败: {outcome['error']}", file=sys.stderr)
        notification_sent = bool(notification_results) and all(
            outcome["success"] for outcome in notification_results
        )
        commit_updates_after_notification(data, updates, notification_sent)
        if not notification_sent:
            print("❌ 部分通知失败，本次更新将在下次检查时重试")
    elif first_run:
        print("\n📝 首次运行，已记录当前状态，不发送通知")
    else:
        print("\n✅ 无更新，不发送通知")

    data["lastCheck"] = checked_at
    data_saved = save_data(data, settings["data_file"])
    output = {
        "hasUpdate": bool(updates),
        "shouldAlert": bool(updates) and not first_run,
        "notificationSent": notification_sent,
        "notifications": notification_results,
        "dataSaved": data_saved,
        "updateCount": len(updates),
        "totalUp": len(users),
        "updates": updates,
        "checkTime": checked_at,
        "totalUpdates": data["updateCount"],
    }
    print("\n---RESULT---")
    print(json.dumps(output, indent=2, ensure_ascii=False))
    if not output["shouldAlert"]:
        print("\nHEARTBEAT_OK")
    if not data_saved:
        raise SystemExit(1)
    return output


def main(argv=None):
    try:
        settings = load_settings(argv)
    except ConfigError as exc:
        print(f"配置错误: {exc}", file=sys.stderr)
        return 2
    asyncio.run(run(settings))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
