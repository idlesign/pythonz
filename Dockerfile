FROM ubuntu:20.04

RUN apt-get update && \
    apt-get upgrade -y

RUN apt-get install -y python3-pip libpq-dev
RUN pip3 install --upgrade pip

ADD . /app
WORKDIR /app

RUN pip3 install wheel && \
    pip3 install -r requirements.txt && \
    pip3 install -r tests/requirements.txt && \
    pip3 install -e .

#RUN mkdir state

RUN pythonz migrate && \
    pythonz createsuperuser --noinput

