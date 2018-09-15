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

ptvsd.enable_attach("glovebox", address=('0.0.0.0', 3002))
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
                image_len = struct.unpack('<L', connection.read(struct.calcsize('<L')))[0]
                if not image_len:
                    break
                # Construct a stream to hold the image data and read the image
                # data from the connection
                image_stream = io.BytesIO()
                image_stream.write(connection.read(image_len))
                image_stream.seek(0)
                image = Image.open(image_stream)

                buffer = cStringIO.StringIO()
                image.save(buffer, format="JPEG")

                ba = buffer.getvalue()

                img_str = base64.b64encode(ba)

                # Set up the HTTP POST
                headers = {'Content-Type': 'application/octet-stream'}
                response = requests.post(
                    imageProcessingEndpoint, headers=headers, params=imageProcessingParams, data=ba)

                jsonData = json.dumps(response.json())

                print(jsonData)

                if jsonData != "[]":
                    send_to_Hub_callback(jsonData)


                # print(img_str)

                print('Image is %dx%d' % image.size)
                image.verify()
                print('Image is verified')
            except:
                print('error')
                connection.close()
                connection = server_socket.accept()[0].makefile('rb')

    finally:
        connection.close()
        server_socket.close()


def main(connectionString, imageProcessingEndpoint="", imageProcessingParams="", verbose=False):
    try:
        try:
            global hubManager
            hubManager = HubManager.HubManager(
                connectionString, 10000, IoTHubTransportProvider.MQTT, verbose)
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
