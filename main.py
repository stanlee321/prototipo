
from flask import Flask, render_template, Response
import cv2
import numpy as np
import time
import threading
import multiprocessing
# Some Globals


configs = {'show_video': False}

# Init Web Server parameters
app = Flask(__name__)


@app.route('/')
def index():
	return render_template('index.html')

@app.route('/installation/')
def installation():
	return render_template('controlboard.html', show = configs['show_video'])


@app.route('/monitoring/')
def monitoring():
	return render_template('monitoring.html', show = configs['show_video'])


@app.route('/video_feed', methods=['GET', 'POST'])
def video_feed():
    return Response(feed_video(),
						mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/my-link/')
def my_link():
	print('Clicked')
	global configs

	if configs['show_video'] == True:
		configs['show_video'] = False
	elif configs['show_video'] == False:
		configs['show_video'] = True
	else:
		pass

	print('Show video is',configs['show_video'])

	return (''), 204


def feed_video(frane):
	while True:
		# Get frame as web frame
		ret, jpeg 	= 	cv2.imencode('.jpeg', frame)
		framebytes 	= 	jpeg.tobytes()

		yield (b'--frame\r\n'
					b'Content-Type: image/jpeg\r\n\r\n' +  framebytes + b'\r\n\r\n')
		

def _mainCamera():
	stream 		= cv2.VideoCapture(0)
	while True:
		_, frameFlujo 	=	stream.read()
		cv2.imshow('test', frameFlujo)
		ch = 0xff & cv2.waitKey(5)
		if ch == ord('q'):
			break

if __name__ == '__main__':
	#_mainCamera()

	app.run(host='0.0.0.0', debug=True, threaded=True)
