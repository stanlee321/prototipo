import sys


# Cloud Tools
from CloudDetectPlate import PlateRecognition
from CloudUploadtoS3 import  UploadToS3
from CloudCreateJSON import CreateJSON
from CloudCarDetector import CarDetector

# Some tools
from createPlate import WritePlate




class CloudSync():

	def __init__(self):
		# Instansiate objects
		self.plateRegionDetector =  CarDetector()#PlateRegionDetector()
		self.plateRecog = PlateRecognition() #
		self.writePlate = WritePlate()
		self.createJSON  = CreateJSON()
		self.uploadToS3 = UploadToS3()


	def __call__(self, path_to_folder = '../'):
		"""
		plates_region_detected = []
		region_images_paths = self.plateRegionDetector(folder_to_images= path_to_folder)

		for possible_path_to_image in region_images_paths:
			print('working on posible region')
			print(possible_path_to_image)

			# Get infomration
			pre_recognition =  self.plateRecog(path_to_image = possible_path_to_image)
			print('pre_recognition is:', pre_recognition)
			if len(pre_recognition) > 1:
				box, prob, plate  = pre_recognition[0], pre_recognition[1], pre_recognition[2]

				detection = {'path': possible_path_to_image,
							 'plate':plate,
							 'box':box,
							 'prob': prob 
					}

				plates_region_detected.append(detection)
				#break
			else:
				print(' NO PLATES IN IMAGE {}'. format(possible_path_to_image))

		if len(plates_region_detected) > 1:
			
			if 	plates_region_detected[0]['plate'] == plates_region_detected[-1]['plate']:	
				
				
				recognition = [	plates_region_detected[0]['path'],
								plates_region_detected[0]['box'],
								plates_region_detected[0]['prob'],
								plates_region_detected[0]['plate'] 
							]
			
			
			else:
				if float(plates_region_detected[0]['prob']) > float(plates_region_detected[-1]['prob']):

					recognition = [	plates_region_detected[0]['path'],
									plates_region_detected[0]['box'],
									plates_region_detected[0]['prob'],
									plates_region_detected[0]['plate']
								]
				else:

					recognition = [	plates_region_detected[-1]['path'],
									plates_region_detected[-1]['box'],
									plates_region_detected[-1]['prob'],
									plates_region_detected[-1]['plate']
								]
		elif len(plates_region_detected) == 1:
			recognition = [	plates_region_detected[0]['path'],
								plates_region_detected[0]['box'],
								plates_region_detected[0]['prob'],
								plates_region_detected[0]['plate']
						] 
				
		else:
			recognition = []

		
		# Serve the last recognition
		print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
		print('>>>>>>>>>>>>>>>>> RECOGNITION IS >>>>>>>>>>>>>>>>>>>>>>>>>>')
		print(recognition)

		"""
		print('"""""""""""""""""""""""" SINC TO AWS"""""""""""""""""""""""')
		recognition = ['/home/stanlee321/2018-02-21_reporte/11-04-53_ROJO_izquierdo_x1_-Infraccion_3855PFB_100/2018-02-21_11-04-53_2wm_croped.jpg', [{'y': 294, 'x': 165}, {'y': 318, 'x': 290}, {'y': 370, 'x': 277}, {'y': 347, 'x': 155}], '0.93', '3855PFB']


		if len(recognition) > 1:
			
			# Read data
			path_to_image, box, prob, plate  = recognition[0], recognition[1], recognition[2], recognition[3]
			

			# Write the detected plate as png with bounding box
			path_to_new_image = self.writePlate(	path_to_image = path_to_image,
													region = box,
													plate = plate)

			# log.info('IMAGE TO BE UPLOADED {}'.format('path_to_new_image'))

			# Get parameters for the sync to s3 and also write JSON with thre
			# routes to video and detected plate

			parameters = self.createJSON(	path_to_image = path_to_image,
											prob = prob,
											plate = plate )

			local_directory = 	parameters['local_directory']
			bucket 			= 	parameters['bucket']
			destination 	=	parameters['destination']

			# Upload to S3
			uploadToS3.upload(local_directory, bucket, destination)
		else:
			print('NO INFORMATION for proceed')


print('JOB DONE!')

if __name__ == '__main__':
	import os

	#if len(sys.argv) < 3 :
	#	print ('usage:\n python pyANPD.py <image_file_path> <y/n>' )
	#	exit(0)

	#path_to_folder = sys.argv[1]

	cloudSync =  CloudSync()
	
	directorioDeTrabajo = os.getenv('HOME') + '/2018-02-21_reporte/' + '11-04-53_ROJO_izquierdo_x1_-Infraccion_3855PFB_100/'


	paths_to_images = cloudSync(path_to_folder = directorioDeTrabajo)

	print(paths_to_images)