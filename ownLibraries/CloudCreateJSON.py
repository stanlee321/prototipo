# -*- coding: utf-8 -*-

import json
import numpy as np
import os
import boto3
import re
import io
import sys

try:
    to_unicode = unicode
except NameError:
    to_unicode = str



class CreateJSON():
	"""
		Create a subfolder in s3 bucket 

		Creates a JSON in local directory
	"""
	def __init__(self):

		self.S3Path = 'https://s3.amazonaws.com/'
		self.S3Bucket = 'raw-assets-dems'

	def _createSubDirOnS3(self, bucket = 'clean-assets-dems', subDirName=''):
		s3_client = boto3.client('s3')

		response = s3_client.put_object(
			Bucket= bucket,
			Body='',
			Key='{}/'.format(subDirName),
			ACL = 'public-read'
		)

	def _getNames(self, path_to_image):

		splited_path = path_to_image.split('/')
		subDirName =  os.path.join(*splited_path[-2:-1]) # folder to images /folder/
		path_to_folder = os.path.join(*splited_path[:-1])

		f = []
		for (dirpath, dirnames, filenames) in os.walk(path_to_folder):
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


	def __call__(self, path_to_image = '',  prob = 0, plate = '' ):

		
		# Create names placeholders
		path_to_folder, image_name, video_name, subDirName = self._getNames(path_to_image)


		self.path_to_image_on_S3 = self.S3Path + self.S3Bucket + '/' + subDirName + '/' +  image_name
		self.path_to_video_on_S3 = self.S3Path + self.S3Bucket + '/' + subDirName + '/' +  video_name

		print(self.path_to_video_on_S3)
		print(self.path_to_image_on_S3 )

		infractionDate = video_name.split('_')[0]
		infractionHour = video_name.split('_')[1].replace('-',':')

		print(infractionDate)
		print(infractionHour)
		print(path_to_image)

		# Prepare route for upload files to s3 into the subfolder /subDirName
		self._createSubDirOnS3(self.S3Bucket, subDirName)

		toJSON = {	'plate': plate, 
					'prob': prob,
					'datetime	': infractionDate,
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


		params = { 'local_directory': path_to_folder,
					'bucket': self.S3Bucket,
					'destination': subDirName 
			}
		return params

if __name__ == '__main__':

	# Some local imports
	from createPlate import WritePlate
	from CloudDetectPlate import PlateRecognition
	from CloudUploadtoS3 import  UploadToS3

	if len(sys.argv) < 3 :
		print ('usage:\n python pyANPD.py <image_file_path> <y>' )
		exit(0)

	path_to_image = sys.argv[1]
	write = sys.argv[2]

	# Instansiate objects
	plateRec = PlateRecognition()
	writePlate = WritePlate()
	createJSON  = CreateJSON()
	uploadToS3 = UploadToS3()

	# Get infomration
	information =  plateRec(path_to_image = path_to_image)

	print(information)
	if len(information) > 0:
		
		region, prob, plate  = information[0], information[1], information[2]
		
		# Write plate if 
		if write  == 'y': # Writes plate in the same dir of path_to_image
			writePlate(path_to_image = path_to_image, region = region, plate = plate)
		else:
			pass

		parameters = createJSON(path_to_image = path_to_image,  prob = prob, plate = plate )
		local_directory, bucket, destination = parameters['local_directory'], parameters['bucket'], parameters['destination']
		uploadToS3.upload(local_directory, bucket, destination)
	else:
		print('NO INFORMATION for proceed')


	print('JOB DONE!')