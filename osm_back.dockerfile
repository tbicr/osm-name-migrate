FROM ubuntu:20.04

ARG DEBIAN_FRONTEND=noninteractive
WORKDIR /app

RUN apt-get update && \
    apt-get install osmium-tool python3-pip -y --no-install-recommends && \
    apt-get clean && \
    pip3 install osmium shapely && \
    rm -rf /var/lib/apt/lists/*
