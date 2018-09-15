FROM ubuntu:xenial

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends libcurl4-openssl-dev python-pip libboost-python-dev git portaudio19-dev  && \
    rm -rf /var/lib/apt/lists/* 

COPY /build/amd64-requirements.txt ./
RUN pip install --upgrade pip
RUN pip install setuptools
RUN pip install -r amd64-requirements.txt

RUN apt-get update && \
    apt-get install -y --no-install-recommends libgtk2.0-dev && \
    rm -rf /var/lib/apt/lists/*


ADD /app/ .
ADD /build/ .
RUN ls
RUN python --version

ENV PYTHONUNBUFFERED=1

CMD [ "python", "-u", "./main.py" ]