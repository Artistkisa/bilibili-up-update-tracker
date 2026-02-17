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
    "smtp_host": "smtp.qq.com",
    "smtp_port": 587,
    "smtp_user": "your_email@qq.com",
    "smtp_pass": "your_auth_code",  # QQ邮箱授权码，不是密码
    "to": ["recipient@example.com"]
}

# Data file path
DATA_FILE = "data/monitor_data.json"

# Optional: Proxy configuration
# PROXY = "http://127.0.0.1:7890"
PROXY = None