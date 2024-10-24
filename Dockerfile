FROM python:3.10.15-slim AS without_flame

RUN pip config set global.index-url https://mirrors.huaweicloud.com/repository/pypi/simple && \
    pip config set global.trusted-host repo.huaweicloud.com && \
    pip config set global.timeout 120 && \
    pip config set global.no-cache-dir True && \
    pip install --upgrade pip

RUN sed -i "s@deb.debian.org@mirrors.huaweicloud.com@g" /etc/apt/sources.list.d/debian.sources && \
    apt-get update && \
    # for mysqlclient
    apt-get install -y pkg-config default-libmysqlclient-dev build-essential


WORKDIR /app/mercury

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY ./src .
CMD uvicorn main:app --host 0.0.0.0 --port 3333


FROM without_flame

ENV WITH_FLAME=True
RUN apt-get install -y git
RUN --mount=type=secret,id=GITHUB_TOKEN \
    GITHUB_TOKEN=$(cat /run/secrets/GITHUB_TOKEN) && \
    git clone --branch v0.0.1 https://${GITHUB_TOKEN}@github.com/SudoLLM/talking-head-libs.git /app/talking-head-libs
RUN pip install /app/talking-head-libs/flame-jax && \
    pip install /app/talking-head-libs/flame-jax/flame_vendor && \
    cp -r /app/talking-head-libs/flame-jax/flame_vendor/assets /app/assets && \
    rm -rf /app/talking-head-libs