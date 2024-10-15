FROM python:3.10.15-slim

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