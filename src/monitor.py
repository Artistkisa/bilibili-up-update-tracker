#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
B站 UP 主更新监控
批量监控 UP 主更新，发送邮件通知
"""

import sys
import json
import asyncio
import smtplib
from datetime import datetime
from pathlib import Path
from email.mime.text import MIMEText
from email.header import Header

# 导入配置
try:
    from config import UP_LIST, EMAIL_CONFIG, DATA_FILE, PROXY
except ImportError:
    print("错误：无法导入配置，请检查 src/config.py 是否存在")
    sys.exit(1)

# 尝试导入 bilibili_api
try:
    from bilibili_api import user
except ImportError:
    print("bilibili_api 未安装，正在安装...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "bilibili-api-python", "aiohttp"])
    from bilibili_api import user


def load_data():
    """加载历史数据"""
    data_path = Path(DATA_FILE)
    try:
        if data_path.exists():
            return json.loads(data_path.read_text(encoding='utf-8'))
    except Exception as e:
        print(f"读取数据文件失败: {e}", file=sys.stderr)
    return {
        "lastCheck": None,
        "upData": {},
        "updateCount": 0
    }


def save_data(data):
    """保存数据"""
    data_path = Path(DATA_FILE)
    try:
        data_path.parent.mkdir(parents=True, exist_ok=True)
        data_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')
    except Exception as e:
        print(f"保存数据文件失败: {e}", file=sys.stderr)


async def fetch_up_video(uid, name):
    """获取单个 UP 主最新视频"""
    try:
        u = user.User(uid=uid)
        videos = await u.get_videos(ps=1, pn=1, order=user.VideoOrder.PUBDATE)
        
        vlist = videos.get('list', {}).get('vlist', [])
        if not vlist:
            return {'uid': uid, 'name': name, 'success': True, 'video': None}
        
        latest = vlist[0]
        return {
            'uid': uid,
            'name': name,
            'success': True,
            'video': {
                'bvid': latest.get('bvid'),
                'title': latest.get('title'),
                'created': latest.get('created'),
                'length': latest.get('length'),
                'play': latest.get('play'),
                'link': f"https://www.bilibili.com/video/{latest.get('bvid')}"
            }
        }
    except Exception as e:
        return {'uid': uid, 'name': name, 'success': False, 'error': str(e)}


def format_time(timestamp):
    """格式化时间戳"""
    if not timestamp:
        return "未知"
    try:
        dt = datetime.fromtimestamp(timestamp)
        return dt.strftime("%Y-%m-%d %H:%M")
    except:
        return str(timestamp)


def format_email(updates, all_results):
    """格式化邮件内容"""
    lines = [
        "📺 B站 UP 主更新汇总",
        "=" * 35,
        "",
        f"📅 检查时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"📊 本次更新：{len(updates)} 个",
        f"👥 监控 UP 主：{len(UP_LIST)} 个",
        "",
        "=" * 35,
        "🎉 新视频列表",
        "=" * 35,
        ""
    ]
    
    for i, up in enumerate(updates, 1):
        v = up['video']
        lines.extend([
            f"{i}. 【{up['name']}】",
            f"   📹 {v['title']}",
            f"   🔗 {v['link']}",
            f"   🕐 发布时间：{format_time(v['created'])}",
            f"   ⏱️ 时长：{v['length']}",
            f"   👁️ 播放量：v['play']}",
            ""
        ])
    
    lines.extend([
        "=" * 35,
        "📋 监控的 UP 主列表",
        "=" * 35,
        ""
    ])
    
    for result in all_results:
        if result.get('success'):
            status = "✅" if result.get('video') else "⚠️"
            video_status = "" if result.get('video') else "（无视频）"
            lines.append(f"{status} {result['name']}{video_status}")
        else:
            lines.append(f"❌ {result['name']}：获取失败")
    
    lines.extend([
        "",
        "=" * 35,
        "",
        "💡 提示：",
        "- 每天 10:00 自动检查一次",
        "- 有更新时发送汇总邮件",
        "- 点击链接可直接观看视频",
        "",
        "🤖 OpenClaw 自动监控系统"
    ])
    
    return "\n".join(lines)


def send_email(subject, body):
    """发送邮件"""
    try:
        cfg = EMAIL_CONFIG
        msg = MIMEText(body, 'plain', 'utf-8')
        msg['Subject'] = Header(subject, 'utf-8')
        msg['From'] = cfg['smtp_user']
        msg['To'] = ', '.join(cfg['to'])
        
        with smtplib.SMTP(cfg['smtp_host'], cfg['smtp_port']) as server:
            server.starttls()
            server.login(cfg['smtp_user'], cfg['smtp_pass'])
            server.sendmail(cfg['smtp_user'], cfg['to'], msg.as_string())
        
        return True
    except Exception as e:
        print(f"发送邮件失败: {e}", file=sys.stderr)
        return False


async def main():
    data = load_data()
    
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 开始检查 {len(UP_LIST)} 个 UP 主...\n")
    
    # 并发获取所有 UP 主信息
    tasks = [fetch_up_video(uid, name) for uid, name in UP_LIST.items()]
    results = await asyncio.gather(*tasks)
    
    # 检查更新
    updates = []
    first_run = not data['upData']
    
    for result in results:
        if not result['success']:
            print(f"❌ [{result['name']}] 获取失败: {result.get('error', '未知错误')}")
            continue
        
        uid = result['uid']
        name = result['name']
        video = result['video']
        
        if not video:
            print(f"⚠️  [{name}] 无视频")
            continue
        
        # 初始化数据
        uid_str = str(uid)
        if uid_str not in data['upData']:
            data['upData'][uid_str] = {
                'lastBvid': None,
                'lastTitle': None,
                'upName': name
            }
        
        up_data = data['upData'][uid_str]
        
        # 检查是否更新
        if up_data['lastBvid'] is None:
            print(f"📝 [{name}] 首次记录: {video['title'][:40]}...")
            up_data['lastBvid'] = video['bvid']
            up_data['lastTitle'] = video['title']
        elif video['bvid'] != up_data['lastBvid']:
            print(f"🎉 [{name}] 有新视频: {video['title'][:40]}...")
            updates.append(result)
            up_data['lastBvid'] = video['bvid']
            up_data['lastTitle'] = video['title']
            data['updateCount'] += 1
        else:
            print(f"✅ [{name}] 无更新")
    
    # 保存数据
    data['lastCheck'] = datetime.now().isoformat()
    save_data(data)
    
    # 发送邮件（有更新且不是首次运行）
    if updates and not first_run:
        print(f"\n📧 发送邮件通知（{len(updates)} 个更新）...")
        subject = f"🎬 B站 UP 主更新汇总（{len(updates)}个更新）"
        body = format_email(updates, results)
        if send_email(subject, body):
            print("✅ 邮件发送成功")
        else:
            print("❌ 邮件发送失败")
    elif first_run:
        print("\n📝 首次运行，已记录当前状态，不发送邮件")
    else:
        print("\n✅ 无更新，不发送邮件")
    
    # 构建输出
    result = {
        "hasUpdate": len(updates) > 0,
        "shouldAlert": len(updates) > 0 and not first_run,
        "updateCount": len(updates),
        "totalUp": len(UP_LIST),
        "updates": updates,
        "checkTime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "totalUpdates": data['updateCount']
    }
    
    print(f"\n---RESULT---")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    if not result['shouldAlert']:
        print("\nHEARTBEAT_OK")


if __name__ == "__main__":
    asyncio.run(main())