FROM ubuntu:24.04

RUN apt update && \
    apt upgrade -y

RUN apt install -y  \
    curl libpq-dev python3-dev build-essential libjpeg-dev  \
    libxml2-dev libxslt1-dev  \
    libpcre3-dev libssl-dev

# add uv
ADD https://astral.sh/uv/install.sh /uv-installer.sh
RUN sh /uv-installer.sh && rm /uv-installer.sh
ENV PATH="/root/.local/bin/:$PATH"

ADD . /app
WORKDIR /app

RUN ./bootstrap.sh
