# base image
FROM python:3.6

RUN apt-get update -y


RUN apt-get install -y apt-transport-https apt-utils build-essential python3-dev default-libmysqlclient-dev \
    redis-tools mysql-client

RUN apt-get -y install netcat

# set working directory
WORKDIR /usr/src/app

# add and install requirements
COPY ./requirements.txt /usr/src/app/requirements.txt
RUN pip install -r requirements.txt

# add app
COPY . /usr/src/app

ENV FLASK_APP flasky.py

EXPOSE 5000