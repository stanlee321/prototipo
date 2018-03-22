"""
This new prototipe works with a Flask server the raspberry pi 
"""
import cv2
import time

#!/usr/bin/env python
import imutils
import time, sys

import multiprocessing
import time
import numpy as np

import requests


# Función principal
def _mainProgram( ingest_queue = None):
	# Import some global varialbes
	miCamara = cv2.VideoCapture(0)
	time.sleep(2)
	addr = 'http://localhost:5000'
	test_url = addr + '/get_images'

	content_type = 'image/jpeg'
	headers = {'content-type': content_type}
	while True:
		# Read camera
		ret, frameFlujo = miCamara.read()
		frameFlujo = cv2.resize(frameFlujo,(320,240))
		configs = np.load('./configs_server.npy')
		if configs[0] == True:
			try:
				_, img_encoded = cv2.imencode('.jpg', frameFlujo)
				r = requests.post(test_url, data=img_encoded.tostring(), headers=headers)
			except Exception as e:
				print('This happen ,', e)

if __name__ == '__main__':
	_mainProgram()
