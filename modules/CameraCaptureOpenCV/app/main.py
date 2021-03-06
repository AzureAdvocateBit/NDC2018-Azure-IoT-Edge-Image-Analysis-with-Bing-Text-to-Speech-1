# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import os
import random
import sys
import time


import iothub_client
from iothub_client import (IoTHubClient, IoTHubClientError, IoTHubError,
                           IoTHubMessage, IoTHubMessageDispositionResult,
                           IoTHubTransportProvider)

import CameraCapture
from CameraCapture import CameraCapture


# global counters
SEND_CALLBACKS = 0


def send_to_Hub_callback(strMessage):
    if strMessage == []:
        return
    message = IoTHubMessage(bytearray(strMessage, 'utf8'))
    hubManager.send_event_to_output("output1", message, 0)

# Callback received when the message that we're forwarding is processed.


def send_confirmation_callback(message, result, user_context):
    global SEND_CALLBACKS
    SEND_CALLBACKS += 1


class HubManager(object):

    def __init__(
            self,
            connectionString,
            messageTimeout,
            protocol,
            verbose):
        '''
        Communicate with the Edge Hub

        :param str connectionString: Edge Hub connection string
        :param int messageTimeout: the maximum time in milliseconds until a message times out. The timeout period starts at IoTHubClient.send_event_async. By default, messages do not expire.
        :param IoTHubTransportProvider protocol: Choose HTTP, AMQP or MQTT as transport protocol.  Currently only MQTT is supported.
        '''
        self.connectionString = connectionString
        self.messageTimeout = messageTimeout
        self.protocol = protocol
        self.client_protocol = self.protocol
        self.client = IoTHubClient(self.connectionString, self.protocol)
        self.client.set_option("messageTimeout", self.messageTimeout)
        if verbose:
            self.client.set_option("logtrace", 1)  # enables MQTT logging
        self.set_certificates()  # some embedded platforms need certificate information

    def set_certificates(self):
        isWindows = sys.platform.lower() in ['windows', 'win32']
        return
        if not isWindows:
            CERT_FILE = os.environ['CertFile',
                                   '/etc/ssl/certs/ca-certificates.crt']
            print("Adding TrustedCerts from: {0}".format(CERT_FILE))
            # this brings in x509 privateKey and certificate
            file = open(CERT_FILE)
            try:
                self.client.set_option("TrustedCerts", file.read())
                print ("set_option TrustedCerts successful")
            except IoTHubClientError as iothub_client_error:
                print ("set_option TrustedCerts failed (%s)" %
                       iothub_client_error)
            file.close()

    def send_event_to_output(self, outputQueueName, event, send_context):
        self.client.send_event_async(
            outputQueueName, event, send_confirmation_callback, send_context)


def main(
        connectionString,
        videoPath,
        bingSpeechKey,
        predictThreshold,
        imageProcessingEndpoint="",
        imageProcessingParams="",
        showVideo=False,
        verbose=False,
        loopVideo=True,
        convertToGray=False,
        resizeWidth=0,
        resizeHeight=0,
        annotate=False,
):
    '''
    Capture a camera feed, send it to processing and forward outputs to EdgeHub

    :param str connectionString: Edge Hub connection string. Mandatory.
    :param int videoPath: camera device path such as /dev/video0 or a test video file such as /TestAssets/myvideo.avi. Mandatory.
    :param str imageProcessingEndpoint: service endpoint to send the frames to for processing. Example: "http://face-detect-service:8080". Leave empty when no external processing is needed (Default). Optional.
    :param str imageProcessingParams: query parameters to send to the processing service. Example: "'returnLabels': 'true'". Empty by default. Optional.
    :param bool showVideo: show the video in a windows. False by default. Optional.
    :param bool verbose: show detailed logs and perf timers. False by default. Optional.
    :param bool loopVideo: when reading from a video file, it will loop this video. True by default. Optional.
    :param bool convertToGray: convert to gray before sending to external service for processing. False by default. Optional.
    :param int resizeWidth: resize frame width before sending to external service for processing. Does not resize by default (0). Optional.
    :param int resizeHeight: resize frame width before sending to external service for processing. Does not resize by default (0). Optional.ion(
    :param bool annotate: when showing the video in a window, it will annotate the frames with rectangles given by the image processing service. False by default. Optional. Rectangles should be passed in a json blob with a key containing the string rectangle, and a top left corner + bottom right corner or top left corner with width and height.
    '''
    try:
        print ("\nPython %s\n" % sys.version)
        print ("Camera Capture Azure IoT Edge Module. Press Ctrl-C to exit.")
        try:
            global hubManager
            hubManager = HubManager(
                connectionString, 10000, IoTHubTransportProvider.MQTT, verbose)
        except IoTHubError as iothub_error:
            print ("Unexpected error %s from IoTHub" % iothub_error)
            return
        with CameraCapture(videoPath, bingSpeechKey, predictThreshold, imageProcessingEndpoint, imageProcessingParams, showVideo, verbose, loopVideo, convertToGray, resizeWidth, resizeHeight, annotate, send_to_Hub_callback) as cameraCapture:
            cameraCapture.start()
    except KeyboardInterrupt:
        print ("Camera capture module stopped")


def __convertStringToBool(env):
    if env in ['True', 'TRUE', '1', 'y', 'YES', 'Y', 'Yes']:
        return True
    elif env in ['False', 'FALSE', '0', 'n', 'NO', 'N', 'No']:
        return False
    else:
        raise ValueError('Could not convert string to bool.')


if __name__ == '__main__':
    try:
        CONNECTION_STRING = os.getenv('IotHubCS')
        VIDEO_PATH = os.getenv('Video', '0')
        PREDICT_THRESHOLD = os.getenv('Threshold', .95)
        IMAGE_PROCESSING_ENDPOINT = os.getenv('AiEndpoint')
        IMAGE_PROCESSING_PARAMS = os.getenv('IMAGE_PROCESSING_PARAMS', "")
        SHOW_VIDEO = __convertStringToBool(os.getenv('SHOW_VIDEO', 'False'))
        VERBOSE = __convertStringToBool(os.getenv('VERBOSE', 'False'))
        LOOP_VIDEO = __convertStringToBool(os.getenv('LOOP_VIDEO', 'True'))
        CONVERT_TO_GRAY = __convertStringToBool(
            os.getenv('CONVERT_TO_GRAY', 'False'))
        RESIZE_WIDTH = int(os.getenv('RESIZE_WIDTH', 0))
        RESIZE_HEIGHT = int(os.getenv('RESIZE_HEIGHT', 0))
        ANNOTATE = __convertStringToBool(os.getenv('ANNOTATE', 'False'))
        BING_SPEECH_KEY = os.getenv('BingKey')

    except ValueError as error:
        print (error)
        sys.exit(1)

    main(CONNECTION_STRING, VIDEO_PATH, BING_SPEECH_KEY, PREDICT_THRESHOLD, IMAGE_PROCESSING_ENDPOINT, IMAGE_PROCESSING_PARAMS,
         SHOW_VIDEO, VERBOSE, LOOP_VIDEO, CONVERT_TO_GRAY, RESIZE_WIDTH, RESIZE_HEIGHT, ANNOTATE)
