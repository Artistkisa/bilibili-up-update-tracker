FROM python:3.11-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码
COPY src/ ./src/

# 创建数据目录
RUN mkdir -p data logs

# 设置工作目录
WORKDIR /app/src

# 运行
CMD ["python", "monitor.py"]