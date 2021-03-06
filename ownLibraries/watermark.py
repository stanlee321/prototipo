#!/usr/bin/python3
# import the necessary packages

import numpy as np
import argparse
import cv2
import os
from PIL import Image
import datetime

# construct the argument parse and parse the arguments



class WaterMarker():
	def __init__(self, path_to_watermark):

		self.path_to_watermark = path_to_watermark

		# For text
		self.font                   = cv2.FONT_HERSHEY_SIMPLEX
		self.fontScale              = 1
		self.fontColor              = (0,0,0)#(255,255,255)
		self.lineType               = 2
		self.alpha = 0.25
		 
		self.watermark, self.wH, self.wW = WaterMarker.create_watermark(self.path_to_watermark)
	@staticmethod
	def convert_to_4channel(path_to_logo):
		file_name = path_to_logo
		out_file = file_name

		image = Image.open(file_name)
		imgSize = image.size
		mask=Image.new('L', image.size, color=255)
		image.putalpha(mask)
		image.save(out_file)


	@staticmethod
	def create_watermark(path_to_watermark):
		#print(path_to_watermark)
		# load the watermark image, making sure we retain the 4th channel
		# which contains the alpha transparency
		print('path to WaterMarker', path_to_watermark)
		watermark = cv2.imread(path_to_watermark, cv2.IMREAD_UNCHANGED)
		watermark = cv2.resize(watermark, (int(0.15*watermark.shape[0]),int(0.15*watermark.shape[1])))
		(wH, wW) = watermark.shape[:2]

		# split the watermark into its respective Blue, Green, Red, and
		# Alpha channels; then take the bitwise AND between all channels
		# and the Alpha channels to construct the actaul watermark
		# NOTE: I'm not sure why we have to do this, but if we don't,
		# pixels are marked as opaque when they shouldn't be

		(B, G, R, A) = cv2.split(watermark)
		B = cv2.bitwise_and(B, B, mask=A)
		G = cv2.bitwise_and(G, G, mask=A)
		R = cv2.bitwise_and(R, R, mask=A)
		watermark = cv2.merge([B, G, R, A])
		return watermark, wH, wW



	@staticmethod
	def list_images(basePath, contains=None):
		# return the set of files that are valid
		return WaterMarker.list_files(basePath, validExts=(".jpg", ".jpeg", ".png", ".bmp"), contains=contains)

	@staticmethod
	def list_files(basePath, validExts=(".jpg", ".jpeg", ".png", ".bmp"), contains=None):
		# loop over the directory structure
		for (rootDir, dirNames, filenames) in os.walk(basePath):
			# loop over the filenames in the current directory
			for filename in filenames:
				# if the contains string is not none and the filename does not contain
				# the supplied string, then ignore the file
				if contains is not None and filename.find(contains) == -1:
					continue

				# determine the file extension of the current file
				ext = filename[filename.rfind("."):].lower()

				# check to see if the file is an image and should be processed
				if ext.endswith(validExts):
					# construct the path to the image and yield it
					imagePath = os.path.join(rootDir, filename).replace(" ", "\\ ")
					yield imagePath
	def put_watermark(self, path_to_images, date):
		# loop over the input images
		print('PATH TO IMAGES,', path_to_images)
		to_delete = []
		for imagePath in WaterMarker.list_images(path_to_images):
			print('for of images', imagePath)

			try:
				to_delete.append(to_delete)
				route =imagePath.split('.')[0] 
				jpg = imagePath.split('.')[-1]
				output_folder = route + 'wm.'+ jpg	
				# load the input image, then add an extra dimension to the
				# image (i.e., the alpha transparency)
				image = cv2.imread(imagePath)
				(h, w) = image.shape[:2]
				image = np.dstack([image, np.ones((h, w), dtype="uint8") * 255])
			 
				# construct an overlay that is the same size as the input
				# image, (using an extra dimension for the alpha transparency),
				# then add the watermark to the overlay in the bottom-right
				# corner
				
				overlay = np.zeros((h, w, 4), dtype="uint8")
				overlay[h - self.wH - 1200:h - 1200, w - self.wW - 10:w - 10] = self.watermark
			 
				# blend the two images together using transparent overlays
				output = image.copy()
				cv2.addWeighted(overlay, self.alpha, output, 1.0, 0, output)
				
				bottomLeftCornerOfText = (int(0.1*w), int(0.96*h))
				#text = str(datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S'))
				#timestamp = datetime.datetime.now()
				#text = timestamp.strftime("%A %d %B %Y %I:%M:%S%p:%f")
				text = date
				cv2.putText(output, text, bottomLeftCornerOfText,\
							 self.font, self.fontScale,self.fontColor,self.lineType)
				# write the output image to disk
				filename = imagePath[imagePath.rfind(os.path.sep) + 1:]
				p = output_folder #os.path.sep.join((output_folder, filename))
				print('OUT OF IMAGE MUST VBE', p)
				cv2.imwrite(p, output)

				to_delete.append(imagePath)

			except Exception as e:
				print('This error trying to make watermark:', e)
		for old_image in to_delete:
			try:
				os.remove(old_image)
			except:
				#print('this file does not exist:', old_image)
				pass

if __name__ == '__main__':
	path_to_watermark = os.getenv('HOME')+'/'+ 'trafficFlow' +'/' +'prototipo'+'/'+ 'watermark'+ '/dems.png'
	path_to_images = os.getenv('HOME')+'/'+ 'trafficFlow' +'/' + 'test'
	make_watermarks = WaterMarker(path_to_watermark)
	make_watermarks.put_watermark(path_to_images,'2018-1-1')