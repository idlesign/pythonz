# pull official base image
FROM ubuntu:18.04

# set work directory
WORKDIR /usr/src/pythonz

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update
RUN apt-get upgrade -y
RUN apt-get install -y python3-pip
# install dependencies
RUN pip3 install --upgrade pip
# берет requirements которые находятся в этой же папке
COPY ./requirements.txt .
RUN pip3 install -r requirements.txt

# copy project
COPY . .

ENTRYPOINT [ "python3" ]

#usage
#docker-compose build
#docker-compose up -d