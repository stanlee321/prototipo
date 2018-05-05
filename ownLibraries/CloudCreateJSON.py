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
import boto3

import re
from os import walk
import io
try:
    to_unicode = unicode
except NameError:
    to_unicode = str

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
	def write_plate(path_to_image, path_to_new_image, region, plate):
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
		save_in = "{}_detected.jpg".format(path_to_new_image)
		scipy.misc.imsave(save_in, img)

	@staticmethod
	def get_information_of_images(image_path):

		# Check if there is images in WORKDIR
		# if there's image ...
		
		# idd and date from taked image
		information_of_the_image_as_json_file = PlateRecognition.get_json_from_api(image_path)
		information_of_the_image_as_json_file = information_of_the_image_as_json_file.replace('false','False')
		#print(information_of_the_image_as_json_file)
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

	def createSubDirOnS3(self, bucket = 'clean-assets-dems', subDirName=''):
		s3_client = boto3.client('s3')

		response = s3_client.put_object(
			Bucket= bucket,
			Body='',
			Key='{}/'.format(subDirName),
			ACL = 'public-read'
		)

	def getNames(self, path_to_image):

		splited_path = path_to_image.split('/')
		subDirName =  os.path.join(*splited_path[-2:-1]) # folder to images
		path_to_folder = os.path.join(*splited_path[:-1])

		f = []
		for (dirpath, dirnames, filenames) in walk(path_to_folder):
			f.extend(filenames)

		video_name = None
		image_name = None
		for i, file in enumerate(f) :
			if '.avi' in file:
				print(file)
				video_name = file
			else:
				pass

			if '_detected' in file:
				print(file)
				image_name = file
			else:
				pass

		return path_to_folder, image_name, video_name, subDirName
	def __call__(self, path_to_image):

		
	

		information =  PlateRecognition.get_information_of_images(path_to_image)

		if len(information) > 1:
			print('---- Plate found in image: ', path_to_image)
			# get information from Json
			region, prob, plate, full_data = information[0], information[1], information[2], information[3] 
			
			# write the image with this info
			path_to_new_image = path_to_image[:path_to_image.rfind('.')]

			PlateRecognition.write_plate(path_to_image, path_to_new_image,  region, plate)

			# Create names placeholders
			path_to_folder, image_name, video_name, subDirName = self.getNames(path_to_image)


			self.path_to_image_on_S3 = self.S3Path + self.S3Bucket + '/' + subDirName + '/' +  image_name
			self.path_to_video_on_S3 = self.S3Path + self.S3Bucket + '/' + subDirName + '/' +  video_name

			print(self.path_to_video_on_S3)
			print(self.path_to_image_on_S3 )


			infractionDate = video_name.split('_')[0]
			infractionHour = video_name.split('_')[1].replace('-',':')

			print(infractionDate)
			print(infractionHour)
			print(path_to_image)


			# TODO Create Sub Folder in S3 bucket
			self.createSubDirOnS3(self.S3Bucket, subDirName)


			toJSON = {	'plate': plate, 
						'prob': prob,
						'date': infractionDate,
						'hour': infractionHour,
						'image_path': self.path_to_image_on_S3,
					 	'video_path': self.path_to_video_on_S3
					 }

			# Write JSON file
			with io.open('{}/{}.json'.format(path_to_folder, subDirName), 'w', encoding='utf8') as outfile:
				str_ = json.dumps(toJSON,
									indent=4, sort_keys=True,
									separators=(',', ': '), ensure_ascii=False)
				outfile.write(to_unicode(str_))

			self.subDirName = subDirName

			return self.subDirName
		else:
			print('No plate in image', information)
			return self.subDirName

		print('DONE')

if __name__ == '__main__':

	if len(sys.argv) < 2:
		print ('usage:\n python pyANPD.py <image_file_path>')
		exit(0)
	path = sys.argv[1]
	platerec = PlateRecognition()

	platerec(path)