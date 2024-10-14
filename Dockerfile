FROM python:3.10.14

WORKDIR /app/mercury

COPY ./requirements.txt /app/mercury/requirements.txt

RUN pip config set global.index-url https://mirrors.huaweicloud.com/repository/pypi/simple && \
    pip config set global.trusted-host repo.huaweicloud.com && \
    pip config set global.timeout 120 && \
    pip install --upgrade pip && \
    pip install -r requirements.txt

# 使用初始源, 因为镜像不够新
RUN pip install -i https://pypi.org/simple mcelery==0.1.0

WORKDIR /app/mercury/src

COPY ./src /app/mercury/src

ENTRYPOINT uvicorn main:app --host 0.0.0.0 --port 3333