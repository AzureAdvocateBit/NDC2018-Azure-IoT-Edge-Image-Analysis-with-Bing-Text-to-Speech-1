# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import os
import random
import sys
import time
import requests
import json
import ptvsd
import HubManager
import io
import socket
import struct
from PIL import Image
import base64
import cStringIO

# import iothub_client
# from iothub_client import (IoTHubClient, IoTHubClientError, IoTHubError,
#                            IoTHubMessage, IoTHubMessageDispositionResult,
#                            IoTHubTransportProvider)
from iothub_client import (IoTHubError, IoTHubMessage, IoTHubTransportProvider)
hubManager = None
IMAGE_CLASSIFY_THRESHOLD = 0.95
# ptvsd.enable_attach("glovebox", address=('0.0.0.0', 3002))
# ptvsd.wait_for_attach()


def send_to_Hub_callback(strMessage):
    message = IoTHubMessage(bytearray(strMessage, 'utf8'))
    hubManager.send_event_to_output("output1", message, 0)


def sendFrameForProcessing(imageProcessingEndpoint, imageProcessingParams, verbose):
    global count, jpgdata

    connection = server_socket.accept()[0].makefile('rb')
    try:
        while True:
            try:
                # Read the length of the image as a 32-bit unsigned int. If the
                # length is zero, quit the loop
                image_len = struct.unpack(
                    '<L', connection.read(struct.calcsize('<L')))[0]
                if not image_len:
                    break
                # Construct a stream to hold the image data and read the image
                # data from the connection
                image_stream = io.BytesIO()
                image_stream.write(connection.read(image_len))
                image_stream.seek(0)

                image = {'imageData': image_stream}

                try:
                    requests.post('http://localhost:80/image',
                                  files=image, hooks={'response': c_request_response})
                except Exception as e:
                    print(e)

            except:
                print('error')
                connection.close()
                connection = server_socket.accept()[0].makefile('rb')

    finally:
        connection.close()
        server_socket.close()


# Image classifier module callback where we display on the oled (if connected).
def c_request_response(r, *args, **kwargs):
    response = json.loads(r.content)
    # print(response)

    sortResponse = sorted(
        response, key=lambda k: k['Probability'], reverse=True)[0]
    probability = sortResponse['Probability']

    print(sortResponse)
    if probability > IMAGE_CLASSIFY_THRESHOLD:
        #     tts.Text2Speech(sortResponse['Tag'])

        # label = sortResponse['Tag']
        # print('Label: {}, Probability: {:.2f}'.format(label, probability))

        # Send the prediction to IoT Edge.
        message = IoTHubMessage(r.content)
        hubManager.client.send_event_async(
            "predictions", message, send_confirmation_callback, response)

def send_confirmation_callback(message, result, user_context):
    print("Confirmation received with result: {} message: {}\n".format(
        result, user_context))

# device_twin_callback is invoked when twin's desired properties are updated.
def device_twin_callback(update_state, payload, user_context):
    global IMAGE_CLASSIFY_THRESHOLD

    print("\nTwin callback called with:\nupdateStatus = {}\npayload = {}".format(
        update_state, payload))
    data = json.loads(payload)
    if "desired" in data:
        data = data["desired"]

    if "ImageClassifyThreshold" in data:
        IMAGE_CLASSIFY_THRESHOLD = float(data["ImageClassifyThreshold"])

def main(connectionString, imageProcessingEndpoint="", imageProcessingParams="", verbose=False):
    try:
        try:
            global hubManager
            hubManager = HubManager.HubManager(
                connectionString, 10000, IoTHubTransportProvider.MQTT, verbose)
            hubManager.client.set_device_twin_callback(device_twin_callback, 0)
        except IoTHubError as iothub_error:
            print("Unexpected error %s from IoTHub" % iothub_error)
            return

        sendFrameForProcessing(imageProcessingEndpoint,
                               imageProcessingParams, verbose)

    except KeyboardInterrupt:
        print("Camera capture module stopped")


def __convertStringToBool(env):
    if env in ['True', 'TRUE', '1', 'y', 'YES', 'Y', 'Yes']:
        return True
    elif env in ['False', 'FALSE', '0', 'n', 'NO', 'N', 'No']:
        return False
    else:
        raise ValueError('Could not convert string to bool.')


if __name__ == '__main__':
    try:
        # CONNECTION_STRING = os.environ['EdgeHubConnectionString']
        CONNECTION_STRING = 'HostName=glovebox-iothub.azure-devices.net;DeviceId=ubuntu;SharedAccessKey=J8SvZ4Ued728owP30S/LDHu/XmL1TLjnYBZdK6jKG6A='
        IMAGE_PROCESSING_ENDPOINT = os.getenv('IMAGE_PROCESSING_ENDPOINT', "")
        IMAGE_PROCESSING_PARAMS = os.getenv('IMAGE_PROCESSING_PARAMS', "")
        VERBOSE = __convertStringToBool(os.getenv('VERBOSE', 'False'))

    except ValueError as error:
        print(error)
        sys.exit(1)

    # Start a socket listening for connections on 0.0.0.0:8000 (0.0.0.0 means
    # all interfaces)
    server_socket = socket.socket()
    server_socket.bind(('0.0.0.0', 8000))
    server_socket.listen(0)

    main(CONNECTION_STRING, IMAGE_PROCESSING_ENDPOINT,
         IMAGE_PROCESSING_PARAMS, VERBOSE)
