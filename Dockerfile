FROM python:3.11-slim

WORKDIR /app

# 安装 cron 和依赖
RUN apt-get update && apt-get install -y cron && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码
COPY src/ ./src/

# 创建数据目录
RUN mkdir -p data logs

# 创建 cron 任务（每天 10:00 运行）
RUN echo "0 10 * * * cd /app/src && python monitor.py >> /app/logs/cron.log 2>&1" | crontab -

# 启动 cron 并保持运行
CMD ["sh", "-c", "cron && tail -f /app/logs/cron.log"]
