# https://towardsdatascience.com/deploying-keras-deep-learning-models-with-flask-5da4181436a2
# https://docs.microsoft.com/en-us/azure/app-service/containers/quickstart-python

import json
import io
import numpy as np
import h5py
from keras.models import load_model
import os.path
from flask import Flask, request
import flask
from PIL import Image
import tensorflow as tf
import base64

app = Flask(__name__)

# 4MB Max image size limit
app.config['MAX_CONTENT_LENGTH'] = 4 * 1024 * 1024

# class_indices = ['axes', 'boots', 'carabiners', 'crampons', 'gloves', 'hardshell_jackets',
#                  'harnesses', 'helmets', 'insulated_jackets', 'pulleys', 'rope', 'tents']

class_indices = ['Apple Granny Smith', 'Apple Red 1', 'Avocado', 'Banana', 'Kiwi', 'Orange', 'Passion Fruit', 'Tamarillo', 'Tomato 2', 'Tomato 4']


model = None
global graph
graph = tf.get_default_graph()


def load_myModel():
    # load the pre-trained Keras model (here we are using a model
    # pre-trained on ImageNet and provided by Keras, but you can
    # substitute in your own networks just as easily)
    global model
    model = load_model('./fruit-model.hdf5')


def scale(image, max_size=(100, 100)):
    from PIL import Image
    x, y = image.size
    size = max(x, y)
    new_img = Image.new('RGB', (size, size), "white")
    new_img.paste(image, (int((size - x) / 2), int((size - y) / 2)))
    return new_img.resize(max_size, Image.BICUBIC)


@app.route('/')
def hello_world():
    # Just here as a simple ping test
    return 'Hello, World!'


@app.route('/')
def index():
    return 'CustomVision.ai model host harness'


@app.route('/image', methods=['POST'])
def predict_image_handler():
    try:
        print('data received')
        imageData = None
        if ('imageData' in request.files):
            imageData = request.files['imageData']
        else:
            imageData = io.BytesIO(request.get_data())

        img = Image.open(imageData)
        img = scale(img)

        data = np.asarray(img).reshape((1, 100, 100, 3))
        data = data * (1./255)

        # with graph.as_default():
        #     result = model.predict_classes(data)

        with graph.as_default():
            predictions = list(model.predict_proba(data))

        if len(predictions) == 0:
            return 'no results'

        # print(str(result))
        # return 'completed'

        # results = []

        # results.append({'Tag': class_indices[result[0]], 'Probability': 1})
        # str(result)
        # return result

        # rounded = [float(np.round(x,8)) for x in predictions]

        # print(str(rounded))
        print(predictions)
        # print(predictions[:,39])

        result = []
        idx = 0
        for p in predictions:
            for i in p:
                print('idx =' + str(idx))
                print(i)
                truncated_probablity = np.float64(round(i,8))
                if (truncated_probablity > 1e-8):
                    result.append({'Tag': class_indices[idx], 'Probability': i })
                idx += 1

        sortResponse = sorted(result, key=lambda k: k['Probability'], reverse=True)
        print(str(sortResponse))

        return str(sortResponse)

        # return "{\"result\":\"%s\"}" % class_indices[result[0]]
        # return 'hello world'
        # return json.dumps(results)
    except Exception as e:
        print('EXCEPTION:', str(e))
        return 'Error processing image', 500


# Like the CustomVision.ai Prediction service /url route handles url's
# in the body of hte request of the form:
#     { 'Url': '<http url>'}
@app.route('/url', methods=['POST'])
def predict_url_handler():
    try:
        image_url = json.loads(request.get_data())['Url']
        # results = predict_url(image_url)
        return "{\"result\":\"hello world\"}"
    except Exception as e:
        print('EXCEPTION:', str(e))
        return 'Error processing image'


if __name__ == '__main__':
    load_myModel()
    print('starting server')
    app.run(host='0.0.0.0', port=8000)

