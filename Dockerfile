FROM ubuntu:20.04

RUN apt-get update && \
    apt-get upgrade -y

RUN apt-get install -y python3-pip libpq-dev
RUN pip3 install --upgrade pip

ADD . /app
WORKDIR /app
ADD bootstrap_docker.sh /bootstrap_docker.sh
RUN /bootstrap_docker.sh
