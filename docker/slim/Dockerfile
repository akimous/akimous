# NOTE: THIS DOCKERFILE IS GENERATED VIA "update.py".
# PLEASE DO NOT EDIT IT DIRECTLY.

FROM python:3.8-slim

RUN set -ex &&\
    apt-get update &&\
    apt-get install -yq --no-install-recommends gcc g++ &&\
    rm -rf /var/lib/apt/lists/* &&\
    mkdir /home/user

RUN pip install --no-cache-dir akimous

ENV HOME=/home/user
WORKDIR /home/user
EXPOSE 3179
CMD ["akimous"]
