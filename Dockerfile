FROM python:3.11-slim

WORKDIR /app

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends cron tzdata \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY docker-entrypoint.sh /usr/local/bin/bilibili-tracker-entrypoint

RUN useradd -r -s /bin/false -d /app appuser \
    && mkdir -p /app/data /app/logs \
    && chown -R appuser:appuser /app/data /app/logs \
    && chmod +x /usr/local/bin/bilibili-tracker-entrypoint

ENV TZ=Asia/Shanghai \
    CHECK_CRON="0 10 * * *" \
    DATA_FILE=/app/data/monitor_data.json

ENTRYPOINT ["/usr/local/bin/bilibili-tracker-entrypoint"]
