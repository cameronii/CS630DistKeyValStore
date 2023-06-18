FROM ubuntu:latest

RUN apt-get update && apt-get install -y python3.6 net-tools vim netcat iputils-ping
RUN apt-get update && apt-get install -y python3-pip
RUN pip3 install pillow

ADD Client.py MessageFormats.py /app/
WORKDIR /app/


