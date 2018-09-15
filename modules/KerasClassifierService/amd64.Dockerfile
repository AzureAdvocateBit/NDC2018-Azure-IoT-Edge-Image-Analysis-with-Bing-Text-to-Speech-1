FROM tensorflow/tensorflow

RUN apt-get update && \
    apt-get install -y --no-install-recommends python3 libcurl4-openssl-dev python3-pip libboost-python-dev libhdf5-serial-dev  && \
    rm -rf /var/lib/apt/lists/* 

WORKDIR /

COPY /build/amd64-requirements.txt amd64-requirements.txt
# COPY /app/fruit-model.hdf5 fruit-model.hdf5

RUN pip3 install --upgrade pip
RUN pip3 install setuptools
RUN pip3 install -r amd64-requirements.txt

ENV LISTEN_PORT=80
EXPOSE 80

ADD app /
RUN ls

# Run the flask server for the endpoints
# CMD python app.py

CMD ["python3", "-m", "main"]

# CMD [ "python", "-u", "main.py" ]
