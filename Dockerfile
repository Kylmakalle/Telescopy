FROM python:3.7.4-alpine

RUN mkdir -p /usr/src/bot
WORKDIR /usr/src/bot
ADD . /usr/src/bot

RUN pip install -r requirements.txt
