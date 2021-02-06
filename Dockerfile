FROM python:3.6.9-alpine

COPY . /app

WORKDIR /app

RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.aliyun.com/g' /etc/apk/repositories \
    && apk update \
    && apk add supervisor tzdata --no-cache \
    && apk add --virtual mypacks libffi-dev build-base --no-cache \
    && cp /usr/share/zoneinfo/Asia/Shanghai /etc/localtime \
    && rm -rf /var/cache/apk/* \
    && mkdir -p /etc/supervisor.d \
    && pip config set global.index-url http://mirrors.aliyun.com/pypi/simple/ \
    && pip install -r requirements.txt --no-cache-dir --trusted-host mirrors.aliyun.com \
    && mkdir -p log instance \
    && apk del mypacks

#COPY config.py ./instance/config.py
COPY health_eye_api.ini /etc/supervisor.d/health_eye_api.ini
CMD ["/usr/bin/supervisord"]