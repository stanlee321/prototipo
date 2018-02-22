#!/usr/bin/env python
# semaforo como clase

import os
import cv2
import time
import ctypes
import datetime
import threading
import pandas as pd
import multiprocessing
import numpy as np
import sqlite3
import shutil
import collections
import pandas as pd
import glob

import picamera
class Shutter():
	"""
	General PICAMERA DRIVER Prototipe

	"""
	nombreCarpeta 		= datetime.datetime.now().strftime('%Y-%m-%d')	+	'_reporte'
	directorioDeReporte = os.getenv('HOME') +	'/'	 + nombreCarpeta
	directorioDeNumpy 	= os.getenv('HOME') +	'/trafficFlow/prototipo/installationFiles/'
	directorioROOT		= os.getenv('HOME')
	date_hour_string 	= datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S:%f')
	installation_data 	= np.load(directorioDeNumpy	+'datos.npy')
	path_to_run_camera 	= os.getenv('HOME')+'/'+ 'WORKDIR' + '/' + 'run_camera.npy'


	#def __init__(self, video_source = 0, width = 3280, height = 2464, cutPoly=([10,10],[3280,2464]), capturas = 3):
	def __init__(self, video_source = 0, width = 2592, height = 1944, cutPoly=([10,10],[2592,1944]), capturas = 3, pipe = None):


		np.save(Shutter.path_to_run_camera, 1) 		# 1 ON state
		self.run_camera 		= True
		# Initial aparemeters
		self.video_source 		= video_source
		self.width 				= width		# Integer Like
		self.height 			= height	# Integer Like
		self.maxCapturas 		= capturas
		

		# FOR ROI
		self.cutPoly 			= Shutter.installation_data[-1] 			# ARRAY like (primerPunto, segundoPunto)
		self.primerPunto 		= self.cutPoly[0] 							# Array like [p0,p1]
		self.segundoPunto 		= self.cutPoly[1]							# Array like [p0,p1]

		self.p0x = self.primerPunto[0]/self.width
		self.p0y = self.primerPunto[1]/self.height

		self.p1x = self.segundoPunto[0]/self.width
		self.p1y = self.segundoPunto[1]/self.height

		self.scale_factor_in_X = (self.segundoPunto[0] - self.primerPunto[0])
		self.scale_factor_in_Y = (self.segundoPunto[1] - self.primerPunto[1])


		# Dir where to save images
		self.directorioDeGuardadoGeneral = Shutter.directorioDeReporte
		self.root 						 = Shutter.directorioROOT
		self.fechaInfraccion 			 = str
		self.saveDir 					 = str
		self.frame_number 				 = int



		# None paratemer for controll save files
		self.save_in_file 		= None
		folder_WORK 			= 'WORKDIR'
		self.saveDirWORK 		= self.root + "/" + folder_WORK

		# Variable para marcar paquete de frames
		self.frame_marcado			= None
		self.folder 				= str
		self.ilive 					= True
		self.circular_buff_shooter 	= collections.deque(maxlen=12)


		print('EXITOSAMENTE CREE LA CLASE SHOOTERv11!!!')

	def apagar_observador(self):
		np.save(ControladorCamara.path_to_run_camera, 0)

	def run(self):
		# PICMEARA INIT
		self.camera 					= picamera.PiCamera()
		self.camera.resolution 			= (2592,1944)#self.camera.MAX_RESOLUTION
		self.camera.framerate 			= 5 # original 2
		self.camera.zoom 				= (self.p0x, self.p0y, self.p1x, self.p1y)
		self.camera.exposure_mode 		= 'sports'
		#self.camera.shutter_speed = 190000
		#self.camera.iso = 800
		self.camera.start_preview()

		run_camera = np.load(Shutter.path_to_run_camera)

		while run_camera == 1:

			tic = time.time()

			date				=   (datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S'))

			# create a list of names to save
			writte_names		= 	[self.saveDirWORK+"/_group_{}_date_{}_.jpg".format(group, date) for group in range(self.maxCapturas)]
			
			# Create a buffer of USEFUL filenames
			for route in sorted(writte_names):
				self.circular_buff_shooter.appendleft(route)

			# save sequence of frames with the list above as inputs
			self.camera.capture_sequence(writte_names, format='jpeg', use_video_port=True, resize=(self.scale_factor_in_X, self.scale_factor_in_Y))
			
			# CLEAN UNUSED IMAGES 
			files_in_work_dir 	 = glob.glob(self.saveDirWORK + '/*.jpg')
			work_dir_len		 = len(files_in_work_dir)

			if work_dir_len > 24: # if exist 24 jpgs and more in dir, >>>> clean
				for img_path in files_in_work_dir:
					# filter files that still are in circular buff
					if img_path in self.circular_buff_shooter:
						pass
					else:
						os.remove(img_path)

			run_camera = np.load(Shutter.path_to_run_camera)

			tac = time.time()

			print('TIC-TAC', tac - tic)


		print('END OF RUN IN SHUTTER????')
		print('Finished...')


if __name__ == '__main__':
	#DEMO DEMO DEMO 
	import numpy as np
	import datetime
	shutter = Shutter()

	shutter.run()
