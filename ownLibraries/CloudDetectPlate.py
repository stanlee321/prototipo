# -*- coding: utf-8 -*-

import json
import numpy as np
import os
import subprocess
from subprocess import call
from pandas.io.json import json_normalize
import ast
import sys

import re


class PlateRecognition():
	def __init__(self):

		self.S3Path = 'https://s3.amazonaws.com/'
		self.S3Bucket = 'raw-assets-dems'
		self.subDirName = None
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
	def get_information_of_images(image_path):


		information_of_the_image_as_json_file = PlateRecognition.get_json_from_api(image_path)
		information_of_the_image_as_json_file = information_of_the_image_as_json_file.replace('false','False')
		information_of_the_image_as_json_file = ast.literal_eval(information_of_the_image_as_json_file)

		# Transform result json to pandas df from the api , just the key == 'results' , the rest
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

	def __call__(self, path_to_image = ''):
		try:
			information =  PlateRecognition.get_information_of_images(path_to_image)
		except Exception as e:
			print('EEROR in getting information of image OR:', e)
			print('Returning empty list')
			information = []

		if len(information) > 1:
			print('---- Plate found in image: ', path_to_image)
			# TODO: makse use of metadata in information[3]
			return  [information[0], information[1], information[2]] # region, prob, plate,
		else:
			print('No plate in image', information)
			return information

if __name__ == '__main__':

	if len(sys.argv) < 2:
		print ('usage:\n python pyANPD.py <image_file_path>')
		exit(0)
	path = sys.argv[1]
	platerec = PlateRecognition()

	information = platerec(path)

	print('information : {}'.format(information))