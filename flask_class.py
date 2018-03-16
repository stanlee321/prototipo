import multiprocessing
from flask import Flask, render_template, Response
import numpy as np
import cv2
import time

configs = np.array([False,False])
frame = None
# save config to disk
np.save('./configs.npy', configs)



app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/installation/')
def installation():
    return render_template('controlboard.html', show = configs[0])

@app.route('/monitoring/')
def monitoring():
    return render_template('monitoring.html', show = configs[0])

@app.route('/video_feed', methods=['GET', 'POST'])
def video_feed():
    return Response(feed_video(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')
@app.route('/my-link/')
def my_link():
    if configs[0] == True:
        configs[0] = False
        np.save('./configs.npy', configs)
        #send_local_configs_pipe.send(configs)
    elif configs[0] == False:
        configs[0] = True
        np.save('./configs.npy', configs)
    else:
        pass

    print('Show video is', configs[0])
    return (''), 204

def feed_video():
    while True:
        # Get frame as web frame
        frame = cv2.imread('cam.jpg')

        ret, jpeg   =   cv2.imencode('.jpeg', frame)
        framebytes  =   jpeg.tobytes()

        yield (b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n' +  framebytes + b'\r\n\r\n')


if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True, threaded=True)
