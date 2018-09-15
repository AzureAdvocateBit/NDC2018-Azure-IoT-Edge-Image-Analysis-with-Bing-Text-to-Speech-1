FROM arm32v7/debian:stretch
COPY ./qemu-arm-static /usr/bin/qemu-arm-static

# https://medium.com/@abhizcc/installing-latest-tensor-flow-and-keras-on-raspberry-pi-aac7dbf95f2

# Install dependencies
RUN apt-get update &&  apt-get install -y \
        python3 \
        python3-pip \
        build-essential \
        python3-dev \        
        # Keras requirements
        python3-numpy libblas-dev liblapack-dev libatlas-base-dev gfortran \
        python3-setuptools python3-scipy python3-h5py  \
        # pillow requirments
        libjpeg-dev  zlib1g-dev libfreetype6-dev 



COPY /build/arm32v7-requirements.txt arm32v7-requirements.txt

RUN pip3 install --upgrade pip 
RUN pip install setuptools==39.1.0
RUN pip install --upgrade https://www.piwheels.org/simple/tensorflow/tensorflow-1.9.0-cp35-none-linux_armv7l.whl
RUN pip uninstall -y mock && pip install mock

# Install Keras

# RUN apt-get install -y python3-numpy libblas-dev liblapack-dev libatlas-base-dev gfortran \
#         python3-setuptools python3-scipy 
# RUN apt-get update && apt-get install -y python3-h5py 
RUN pip install keras
# RUN pip uninstall -y  setuptools

# RUN apt install -y zlib1g-dev
# RUN apt-get install -y libjpeg-dev  zlib1g-dev libfreetype6-dev 
RUN pip install pillow
RUN pip install flask
RUN pip install ptvsd==3.0.0
# RUN pip install --upgrade setuptools 
# RUN pip install -r arm32v7-requirements.txt

#TensorFlow 1.5.0
# RUN pip install http://ci.tensorflow.org/view/Nightly/job/nightly-pi-python3/122/artifact/output-artifacts/tensorflow-1.5.0-cp34-none-any.whl

ADD app /app

# Expose the port
EXPOSE 80

# Set the working directory
WORKDIR /app

# Run the flask server for the endpoints
CMD ["python3","main.py"]