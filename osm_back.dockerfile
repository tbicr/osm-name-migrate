FROM ubuntu:22.04

ARG DEBIAN_FRONTEND=noninteractive
WORKDIR /app

RUN apt-get update && \
    apt-get install osmium-tool python3-pyosmium python3-shapely \
            -y --no-install-recommends && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
