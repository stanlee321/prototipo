import json, requests, os, random
from time import sleep
from PIL import Image, ImageDraw
import cv2
import glob
import os
import requests
#os.chdir("/mydir")

#capture an image

class CarDetector():
	def __init__(self):
		self.API_KEY =  'NyEWKG4sr8ymeXOzE9rDfUJ69qBatIOhcbWp0OOVIAx'
		self.MODEL_ID = 'bee0b774-b81c-401a-ad0d-baf5d3eef886'
		self.URL = "https://app.nanonets.com/api/v2/ObjectDetection/Model/{}/LabelFile/".format(self.MODEL_ID)
		self.shape = (2560,1920)
		# Taking in acoout the 5 mpx resolution 2560 x 1920

		self.scaleX = 8
		self.scaleY = 8

		self.new_shape = (int(self.shape[0]/self.scaleX) , int(self.shape[1]/self.scaleY ))
		self.original_local_files = []
	def load_images_paths(self, folder_to_images):
		print('incomingg folder is', folder_to_images)
		paths_to_images = []
		# List directory
		for image in glob.glob("{}*.jpg".format(folder_to_images)):
			paths_to_images.append(image)
		return paths_to_images

	def preprocess_images(self, paths_to_images):

		local_images_paths = []

		for i, path in enumerate(paths_to_images):
			raw_image = cv2.imread(path)
			
			image_shape = raw_image.shape
			
			image = cv2.resize(raw_image, self.new_shape)
			local_images_paths.append('{}_resized.jpg'.format(path[:path.rfind('.')]))
			cv2.imwrite('{}_resized.jpg'.format(path[:path.rfind('.')]), image)
		return local_images_paths

	def get_centroid(self, x, y, w, h):

		x1 = int(w / 2)
		y1 = int(h / 2)
		cx = x + x1
		cy = y + y1
		return (cx, cy)


	def get_coord(self, folder_to_images):

		objects_coord = []

		paths_to_images = self.load_images_paths(folder_to_images)
		local_res_images_paths = self.preprocess_images(paths_to_images)

		self.original_local_files = paths_to_images

		print('FINAL IS ', local_res_images_paths)

		for i, image in enumerate(local_res_images_paths):

			#make a prediction on the image
			data = {'file': open(image, 'rb'),
					'modelId': ('', self.MODEL_ID)}


			headers = {
				'accept': 'multipart/form-data'
			}
			
			try:
				response = requests.post(self.URL,headers = headers, files= data, auth=requests.auth.HTTPBasicAuth(self.API_KEY, ''))
				response = json.loads(response.text)

				im = Image.open(image)
				draw = ImageDraw.Draw(im, mode="RGBA")
				prediction = response["result"][0]["prediction"]
				#input_image = response["result"][0]["input"]

				for index, pred in enumerate(prediction):
					x, y = pred["xmin"], pred["ymin"]
					w, h = pred["xmax"], pred["ymax"]

					AREA = (w-x)*(h-y)
					centroid = self.get_centroid(x,y,w,h)
					if  (0 <= int(centroid[0]) < 500) and (  120 <= int(centroid[1]) < 300 ) and (AREA > 1000) :
						
						draw.rectangle((x,y, w,h), fill=(random.randint(1, 255),random.randint(1, 255),random.randint(1, 255),127))
						detection = {
									'coor' : (x,y,w,h),
									 'img-url': '{}_detected.jpg'.format(image[:image.rfind('.')])
								}
						objects_coord.append(detection)

				im.save('{}_detected.jpg'.format(image[:image.rfind('.')]))

			except Exception as e:
				print('Exception for return empy list', e)
				objects_coord = []

		return objects_coord

	def __call__(self, folder_to_images):

		# append croped cars
		cars_regions  = []

		objects_coord = self.get_coord(folder_to_images)
		for original in self.original_local_files:
			for obj_coor in objects_coord:
				x,y,w,h  =  obj_coor['coor']
				image_detected = obj_coor['img-url']
				if (image_detected[:image_detected.rfind('_re')] + '.jpg') == original:
					print('mATCH FOUND')
					original_image = cv2.imread(original)
					print('ORIGINAL SHAPE', original_image.shape)

					original_image_upscaled = cv2.resize(original_image, self.shape)
					print('UPSCALED IMAGE IS', original_image_upscaled.shape)
					x0 = x*self.scaleX
					y0 = y*self.scaleY

					x1 = w*self.scaleX
					y1 = h*self.scaleY

					print('X0',x0, 'Y0', y0)
					print('X1',x1, 'Y1', y1)
					print('crop from ', image_detected)
					print('crop to', original)

					croped_original = original_image_upscaled[y0: y1,
															 x0: x1]

					cv2.imwrite('{}_croped.jpg'.format(original[:original.rfind('.')]), croped_original)

					cars_regions.append('{}_croped.jpg'.format(original[:original.rfind('.')]))

				else:
					print('not match')

				#if image_detected[:image_detected.rfind('x')]

		return cars_regions

if __name__ == '__main__':


	carDetector = CarDetector()
	directorioDeTrabajo = os.getenv('HOME') + '/2018-02-21_reporte/' + '11-04-53_ROJO_izquierdo_x1_-Infraccion_3855PFB_100/'
	paths_to_images = carDetector(directorioDeTrabajo)

	print('Cars REGIONS ARE:', paths_to_images)

