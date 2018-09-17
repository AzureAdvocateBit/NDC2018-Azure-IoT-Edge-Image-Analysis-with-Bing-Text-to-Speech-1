FROM ubuntu:xenial
# FROM python

EXPOSE 3002
EXPOSE 8000

WORKDIR /app



RUN apt-get update && \
    apt-get install -y --no-install-recommends libcurl4-openssl-dev python-pip libboost-python-dev && \
    rm -rf /var/lib/apt/lists/* 

COPY /build/amd64-requirements.txt ./
RUN pip install setuptools
RUN pip install -r amd64-requirements.txt

RUN apt-get update && \
    apt-get install -y --no-install-recommends libgtk2.0-dev && \
    rm -rf /var/lib/apt/lists/*

ADD /app/ .
ADD /build/ .

CMD [ "python", "-m", "app" ]