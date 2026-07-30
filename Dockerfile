FROM python:3.11-slim

WORKDIR /app

# 安装 cron 和依赖
RUN apt-get update && apt-get install -y cron && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码
COPY src/ ./src/

# 创建非 root 用户（cron 任务以此用户运行）
RUN useradd -r -s /bin/false -d /app appuser

# 创建数据目录并设置权限
RUN mkdir -p /app/data /app/logs && chown -R appuser:appuser /app/data /app/logs

# 创建 cron 任务（以 appuser 身份执行）
RUN echo "0 10 * * * cd /app/src && DATA_FILE=/app/data/monitor_data.json /usr/local/bin/python3 monitor.py >> /app/logs/cron.log 2>&1" | crontab -u appuser -

# cron 守护进程需 root 启动，实际任务通过 crontab -u appuser 以非特权用户运行
CMD ["sh", "-c", "cron && tail -f /app/logs/cron.log"]
