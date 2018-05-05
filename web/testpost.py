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
import base64
import requests
import json
from PIL import Image
import io
# Función principal
def _mainProgram( ingest_queue = None):
	# Import some global varialbes
	#addr = 'https://60hy47r5sk.execute-api.us-east-1.amazonaws.com/prod'
	addr = 'https://fkhqxq9cf9.execute-api.us-east-1.amazonaws.com/prod'
	test_url = addr + '/plateRecog'

	content_type = 'application/json'
	headers = {'Content-Type': content_type, 
				'contentHandling': 'CONVERT_TO_TEXT'}
	# Read camera
	image = cv2.imread('out.jpg')

	# Encode
	_, img_encoded = cv2.imencode('.jpeg', image)
	jpg_as_text = base64.b64encode(img_encoded)
	data = jpg_as_text

	try:
		print('HI')
		r = requests.post(test_url, data = data, headers=headers)
		print('RSPONSE IS', r.json())
	except Exception as e:
		print('This happen', e)

if __name__ == '__main__':
	_mainProgram()
