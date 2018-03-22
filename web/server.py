from flask import Flask, request ,render_template, Response
import numpy as np
import cv2
from videoClass import FeedVideo

feedVideo = FeedVideo()

# Frame to show

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/installation/')
def installation():
    global feedVideo
    return render_template('controlboard.html', show = feedVideo.configs[0])

@app.route('/monitoring/')
def monitoring():
    global feedVideo
    return render_template('monitoring.html', show = feedVideo.configs[0])

@app.route('/video_feed')
def video_feed():
    return Response(feedVideo(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/get_images', methods=['GET', 'POST'])
def get_images():
    global feedVideo
    r = request
    # convert string of image data to uint8
    nparr = np.fromstring(r.data, np.uint8)
    feedVideo.imagen  = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    return Response('Happy to recive your images...', 201)


@app.route('/my-link/')
def my_link():
    global feedVideo
    if feedVideo.configs[0] == True:
        feedVideo.configs[0] = False
        feedVideo.saveConfigsToDisk(path=feedVideo.configs_server_path)
    elif feedVideo.configs[0] == False:
        feedVideo.configs[0] = True
        feedVideo.saveConfigsToDisk(path=feedVideo.configs_server_path)
    else:
        pass
    return (''), 204

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=False, threaded=True)
