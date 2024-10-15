FROM python:3.10.15-slim

RUN pip config set global.index-url https://mirrors.huaweicloud.com/repository/pypi/simple && \
    pip config set global.trusted-host repo.huaweicloud.com && \
    pip config set global.timeout 120 && \
    pip config set global.no-cache-dir True && \
    pip install --upgrade pip


WORKDIR /app/flower

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY mflower.py .
CMD celery -A mflower flower \
    --persistent=True \
    --db="data/flower_db" \
    --state-save-interval=60000 \
    --enable_events
