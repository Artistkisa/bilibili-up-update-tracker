import os
from pathlib import Path


def env_or_default(name, default):
    """Treat unset and empty environment variables the same way."""
    return os.getenv(name) or default

# List of UP主 to track (UID: display_name)
# Get UID from Bilibili space URL, e.g.: https://space.bilibili.com/68559

UP_LIST = {
    # Bilibili official accounts
    68559: "22和33",
    403748305: "BML制作指挥部",
    
    # Add your favorite UP主 here...
    # 123456: "UP主名字",
}

# Email configuration
EMAIL_CONFIG = {
    "smtp_host": env_or_default("EMAIL_SMTP_HOST", "smtp.qq.com"),
    "smtp_port": int(env_or_default("EMAIL_SMTP_PORT", "587")),
    "smtp_user": env_or_default("EMAIL_USER", "your_email@qq.com"),
    "smtp_pass": env_or_default("EMAIL_PASS", "your_auth_code"),  # QQ邮箱授权码，不是密码
    "to": [
        address.strip()
        for address in env_or_default("EMAIL_TO", "recipient@example.com").split(",")
        if address.strip()
    ],
}

# 默认保存到项目根目录的 data，确保本机、Actions 和 Docker 使用同一路径。
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = Path(env_or_default("DATA_FILE", str(PROJECT_ROOT / "data" / "monitor_data.json")))
