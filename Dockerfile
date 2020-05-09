FROM node:13-alpine AS client

COPY client/ client/

RUN yarn --cwd client install \
    && yarn --cwd client build

FROM python:3.8-alpine

WORKDIR /app

ENV KUBECTL_VERSION=1.18.0
ENV HELM_VERSION=3.1.2

RUN apk add --update --no-cache --virtual build-dependencies curl \
    && curl -LO https://storage.googleapis.com/kubernetes-release/release/v${KUBECTL_VERSION}/bin/linux/amd64/kubectl \
    && mv ./kubectl /usr/local/bin \
    && chmod +x /usr/local/bin/kubectl \
    && curl -L https://get.helm.sh/helm-v${HELM_VERSION}-linux-amd64.tar.gz | tar xvz \
    && mv linux-amd64/helm /usr/local/bin/helm \
    && chmod +x /usr/local/bin/helm \
    && rm -rf linux-amd64 \
    && helm repo add stable https://kubernetes-charts.storage.googleapis.com \
    && apk del build-dependencies \
    && rm -f /var/cache/apk/*

COPY server/requirements.txt /app
RUN apk add --update --no-cache --virtual build-dependencies build-base linux-headers \
    && pip install -r requirements.txt \
    && apk del build-dependencies \
    && rm -f /var/cache/apk/*

COPY server/ /app/
COPY --from=client /client/node_modules/monaco-editor/min /app/static/js
COPY --from=client /client/build/ /app/

CMD ["uvicorn", "--host", "0.0.0.0", "--log-config", "logging.conf", "main:app"]