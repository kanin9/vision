import sys

from PIL import Image
from flask import Flask, request, jsonify
import datetime
import numpy as np
import cv2
from mss import mss
import time
import threading
from fer import FER

app = Flask(__name__)


@app.route('/process', methods=['post'])
def process():
    file = request.files['media']

    img = Image.open(file.stream).convert('RGB')

    imgnp = np.array(img)
    # Convert RGB to BGR
    imgnp = imgnp[:, :, ::-1].copy()

    detector = FER()
    faces = detector.detect_emotions(imgnp)
    data = {
    }

    sample = 0
    for face in faces:
        sample += 1
        emotions = face['emotions']
        print(emotions)
        # .logger.info(emotions)
        sortedEmotions = sorted(emotions, key=emotions.get, reverse=True)
        dominant = sortedEmotions[0]

        for emotion in emotions:
            score = emotions[emotion]
            if emotion in data:
                data[emotion]['score'] += score
                data[emotion]['sample'] += 1
            else:
                data[emotion] = {
                    'score': score,
                    'sample': 1
                }

        score = emotions[dominant]
        #app.logger.info(type(score))
        (x, y, w, h) = face['box']
        imgnp = cv2.rectangle(imgnp, (x, y), (x + w, y + h), (0, 0, 255), 2)
        imgnp = cv2.putText(imgnp, dominant, (x, y + h), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA, )
        imgnp = cv2.putText(imgnp, str(score), (x, y + h + 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2,
                            cv2.LINE_AA, )

    if data != {}:
        cv2.imwrite('myimg.jpg', imgnp)

    now = datetime.datetime.now()
    stamp = '{:d}:{:02d}:{:02d}'.format(now.hour, now.minute, now.second)

    mapping = {
        'time': stamp,
        'emotions': data,
        'sample': sample
    }

    return jsonify(mapping)


if __name__ == "__main__":
    app.run('0.0.0.0', 4444)
