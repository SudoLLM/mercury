FROM python:3.10.14

RUN pip config set global.index-url https://mirrors.huaweicloud.com/repository/pypi/simple && \
    pip config set global.trusted-host repo.huaweicloud.com && \
    pip config set global.timeout 120 && \
    pip install --upgrade pip

WORKDIR /app/azure
COPY requirements.txt /app/azure/requirements.txt
RUN pip install -r requirements.txt
# 使用原始源安装 mcelery, 镜像不够新
RUN pip install -i https://pypi.org/simple mcelery==0.1.0

COPY azure_celery.py /app/azure/azure_celery.py

CMD celery -A azure_celery worker --loglevel=INFO -Q azure_infer -n azure_worker