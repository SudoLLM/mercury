FROM python:3.10.14

RUN pip config set global.index-url https://mirrors.huaweicloud.com/repository/pypi/simple && \
    pip config set global.trusted-host repo.huaweicloud.com && \
    pip config set global.timeout 120 && \
    pip install --upgrade pip

WORKDIR /app/flower
COPY requirements.txt /app/flower/requirements.txt
RUN pip install -r requirements.txt
# 使用原始源安装 mcelery, 镜像不够新
RUN pip install -i https://pypi.org/simple mcelery==0.1.0

COPY mflower.py /app/flower/mflower.py

CMD celery -A mflower flower \
    --persistent=True \
    --db="data/flower_db" \
    --state-save-interval=60000 \
    --enable_events
