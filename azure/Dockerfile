FROM python:3.10.15-slim

RUN pip config set global.index-url https://mirrors.huaweicloud.com/repository/pypi/simple && \
    pip config set global.trusted-host repo.huaweicloud.com && \
    pip config set global.timeout 120 && \
    pip config set global.no-cache-dir True && \
    pip install --upgrade pip


WORKDIR /app/azure

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY azure_celery.py .
CMD celery -A azure_celery worker --loglevel=INFO -Q azure_infer -n azure_worker