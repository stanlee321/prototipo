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
import subprocess
# Función principal
def _mainProgram( ingest_queue = None):
	# Import some global varialbes
	addr = 'https://60hy47r5sk.execute-api.us-east-1.amazonaws.com/prod'
	test_url = addr + '/PostAsset'

	#content_type = 'image/jpeg'
	content_type = 'application/json'
	headers = {'Content-Type': content_type, 
				'contentHandling': 'CONVERT_TO_TEXT'}
	# Read camera
	image = cv2.imread('index.jpeg')
	#image = Image.open(io.BytesIO('index.jpeg'))
	#image = Image.open('index.jpeg')

	#ret, frameFlujo = miCamara.read()
	#frameFlujo = cv2.resize(frameFlujo,(320,240))
	_, img_encoded = cv2.imencode('.jpeg', image)

	jpg_as_text = base64.b64encode(img_encoded)
	
	data = jpg_as_text
	try:
		#print('HI')
		cmd = ['curl','X', 'POST', '-H','Content-Type: application/json', '-d','@{}'.format(jpg_as_text),'https://60hy47r5sk.execute-api.us-east-1.amazonaws.com/prod/PostAsset']
		p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
		out, err= p.communicate()
		out = out.decode('utf-8')
		m = out
		print('RSPONSE IS', m)
	except Exception as e:
		print('This happen', e)
	"""
	try:
		#data = {'user_avatar': {'body': img_encoded}}
		#dataJSON = json.dumps(data)

		r = requests.post(test_url, data=img_encoded.tostring(), headers=headers)
		#r = requests.post(test_url, data=dataJSON, headers=headers)
		print(r)
	except Exception as e:
		print('This happen ,', e)
	"""
if __name__ == '__main__':
	_mainProgram()
