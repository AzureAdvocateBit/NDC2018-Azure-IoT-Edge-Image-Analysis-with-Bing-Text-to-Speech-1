#!/usr/bin/env python

import sys
import os
import json
import picamera
import requests
import io
import os
import numpy as np
# import local devicecheck module
import devicecheck
import hubmanager
import oleddisplay
import pyaudio
from iothub_client import IoTHubMessage



oled_display = None
hub = None
IMAGE_CLASSIFY_THRESHOLD = .5


def play_audio(samples, fs=44100, volume=0.5):
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paFloat32,
                    channels=1,
                    rate=fs,
                    output=True)

    # play. May repeat with different volume values (if done interactively) 
    stream.write(volume*samples)
    stream.stop_stream()
    stream.close()
    p.terminate()

def play_sample():
    f = 440.0        # sine frequency, Hz, may be float    
    duration = 1.0   # in seconds, may be float
    fs = 44100       # sampling rate, Hz, must be integer
    # generate samples, note conversion to float32 array
    # for paFloat32 sample values must be in range [-1.0, 1.0]
    samples = (np.sin(2*np.pi*np.arange(fs*duration)*f/fs)).astype(np.float32)
    play_audio(samples)

# Pull camera images and stream data to image classifier module.
def stream_camera_data(camera):
    while True:
        stream = io.BytesIO()
        camera.capture(stream, format='jpeg')
        stream.seek(0)
        image = {'imageData': stream}

        try:
            requests.post('http://image-classifier-service:80/image', files=image, hooks={'response': c_request_response})
        except Exception as e:
            print(e)


# Image classifier module callback where we display on the oled (if connected).
def c_request_response(r, *args, **kwargs):
    print(r.content)
    # results = json.loads(r.content)
    # print(results)
    return
    
    label = results[0]['label']
    probability = results[0]['score']
    print('Label: {}, Probability: {:.2f}'.format(label, probability))
    # play_sample()
    # Display the results on the OLED display.
    if oled_display and probability >= IMAGE_CLASSIFY_THRESHOLD:
        text = 'L: {}, P: {:.2f}'.format(label, probability)
        oled_display.println(text)

    # Send the prediction to IoT Edge.
    message = IoTHubMessage(r.content)
    hub.client.send_event_async(
        "predictions", message, send_confirmation_callback, results)


def send_confirmation_callback(message, result, user_context):
    print("Confirmation received with result: {} message: {}\n".format(result, user_context))


# device_twin_callback is invoked when twin's desired properties are updated.
def device_twin_callback(update_state, payload, user_context):
    global IMAGE_CLASSIFY_THRESHOLD

    print("\nTwin callback called with:\nupdateStatus = {}\npayload = {}".format(update_state, payload))
    data = json.loads(payload)
    if "desired" in data:
        data = data["desired"]

    if "ImageClassifyThreshold" in data:
        IMAGE_CLASSIFY_THRESHOLD = float(data["ImageClassifyThreshold"])


if __name__ == '__main__':
    # Check if the OLED is connected.
    if devicecheck.check_for_oled():
        oled_display = oleddisplay.OledDisplay()
        oled_display.println('Point camera at an object')
    else:
        print('WARNING: OLED is not connected.  Text will not be displayed.')

    # Create the IoT Edge connection.
    hub = hubmanager.HubManager()
    hub.client.set_device_twin_callback(device_twin_callback, 0)

    # Create the camera object and start camera stream.
    camera = picamera.PiCamera()
    stream_camera_data(camera)
