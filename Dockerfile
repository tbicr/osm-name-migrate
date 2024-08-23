FROM ubuntu:22.04

ARG DEBIAN_FRONTEND=noninteractive
WORKDIR /app

RUN apt-get update && \
    apt-get install ca-certificates wget python3 python3-dev python3-pip python3-venv \
            protobuf-compiler libprotobuf-dev build-essential osmctools osmium-tool postgresql-client osm2pgsql \
            -y --no-install-recommends && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN pip install -U pip wheel && \
    pip install ipython[notebook] pandas matplotlib psycopg2-binary shapely osmium osmapi requests requests-oauthlib PyGithub
