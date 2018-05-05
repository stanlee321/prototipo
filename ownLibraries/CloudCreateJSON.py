# -*- coding: utf-8 -*-

import cv2
import json
import numpy as np
import os
import subprocess
from subprocess import call
from pandas.io.json import json_normalize
import ast
import scipy.misc
import sys


class PlateRecognition():
	def __init__(self):
		pass

	@staticmethod
	def get_json_from_api(image):

		print('IMAGE is:', image)
		
		cmd = ['curl','X', 'POST', '-F','image=@{}'.format(image),'https://api.openalpr.com/v2/recognize?recognize_vehicle=1&country=us&secret_key=sk_DEMODEMODEMODEMODEMODEMO']

		p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
		out, err= p.communicate()
		out = out.decode('utf-8')

		m = out
		n = json.dumps(m)  
		o = json.loads(n)  
		return str(o)


	@staticmethod
	def get_plates(result):
		plates = result['candidates'][0]
		return plates

	@staticmethod
	def get_plate_region(result):
		region = result['coordinates'][0]
		return region

	@staticmethod
	def write_plate(path_to_image, region, plate):
		font = cv2.FONT_HERSHEY_SIMPLEX

		px0 = region[0]['x']
		py0 = region[0]['y']
		px1 = region[2]['x']
		py1 = region[2]['y']

		textx = region[0]['x']
		texty = region[0]['y']

		img = cv2.imread(path_to_image)
		img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
		img = cv2.rectangle(img,(px0,py0),(px1,py1),(0,255,0),3)

		img = cv2.putText(img, plate,(textx,int(texty*0.95)), font, 1,(0,255,3),2,cv2.LINE_AA)
		save_in = "{}_detected.jpg".format(path_to_image[:path_to_image.rfind('.')])
		scipy.misc.imsave(save_in, img)

	@staticmethod
	def get_information_of_images(image_path):

		# Check if there is images in WORKDIR
		# if there's image ...
		
		# idd and date from taked image
		information_of_the_image_as_json_file = PlateRecognition.get_json_from_api(image_path)
		information_of_the_image_as_json_file = information_of_the_image_as_json_file.replace('false','False')
		information_of_the_image_as_json_file = ast.literal_eval(information_of_the_image_as_json_file)
		# Transform result json to pandas df from the api , just the key == 'region' , the rest
		# does not bother us.
		result_pandas_df = json_normalize(information_of_the_image_as_json_file, 'results')
		# Possible plates from the above result in the format i.e :
		if len(result_pandas_df) == 0:
			return ['The API not detect any plate in the image']
		else:
			possible_plates = PlateRecognition.get_plates(result_pandas_df)

			# Working on the max confidence
			prob   			= possible_plates[0]['confidence']
			prob 			= str(round(float(prob)/100, 2))
			plate 			= possible_plates[0]['plate']			
			possible_region = PlateRecognition.get_plate_region(result_pandas_df)
			region 			= possible_region
			return [region, prob, plate, information_of_the_image_as_json_file]

	def __call__(self, path_to_image):

		information =  PlateRecognition.get_information_of_images(path_to_image)
		if len(information) > 1:
			print('---- Plate found in image: ', path_to_image)
			# get information from Json
			region, prob, plate, full_data = information[0], information[1], information[2], information[3] 
			
			# write the image with this info
			PlateRecognition.write_plate(path_to_image, region, plate)
			
			# record the full log from JSON in a npy
			
		else:
			print('No plate in image', information)



if __name__ == '__main__':

	if len(sys.argv) < 2:
		print ('usage:\n python pyANPD.py <image_file_path>')
		exit(0)
	path = sys.argv[1]
	platerec = PlateRecognition()

	platerec(path)