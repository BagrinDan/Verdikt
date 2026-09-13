FROM ubuntu:22.04

RUN apt-get update && apt-get install -y wget git unzip python3

RUN wget https://github.com/github/codeql-action/releases/latest/download/codeql-bundle-linux64.tar.gz -O /tmp/codeql.tar.gz

RUN tar -xvzf /tmp/codeql.tar.gz -C /opt/ && rm /tmp/codeql.tar.gz

ENV PATH="/opt/codeql:${PATH}"

RUN codeql --version