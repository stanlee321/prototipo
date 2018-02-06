#!/usr/bin/env python
# semaforo como clase

import os
import time
import datetime
import threading
import multiprocessing

import picamera
import time
import numpy as np
import shutil
import collections
import glob
import pandas as pd
import sqlite3
import multiprocessing




class Shutter(multiprocessing.Process):
	"""
	General PICAMERA DRIVER Prototipe
	"""
	nombreCarpeta 		= datetime.datetime.now().strftime('%Y-%m-%d')	+	'_reporte'
	directorioDeReporte = os.getenv('HOME') +	'/'	 + nombreCarpeta
	directorioDeNumpy 	= os.getenv('HOME') +	'/trafficFlow/prototipo/installationFiles/'
	directorioROOT		= os.getenv('HOME')
	date_hour_string 	= datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S:%f')
	installation_data 	= np.load(Shooter.directorioDeNumpy	+'datos.npy')

	def __init__(self, video_source = 0, width = 3280, height = 2464, cutPoly=([10,10],[3280,2464]), capturas = 3, input_q):
		super(Shutter, self).__init__()
		# Initial aparemeters
		self.video_source 		= video_source
		self.width 				= width		# Integer Like
		self.height 			= height	# Integer Like
		self.maxCapturas 		= capturas
		

		# FOR ROI
		self.cutPoly 			= Shutter.installation_data[-1] 			# ARRAY like (primerPunto, segundoPunto)
		self.primerPunto 		= self.cutPoly[0] 							# Array like [p0,p1]
		self.segundoPunto 		= self.cutPoly[1]							# Array like [p0,p1]

		p0x = self.primerPunto[0]/self.width
		p0y = self.primerPunto[1]/self.height

		p1x = self.segundoPunto[0]/self.width
		p1y = self.segundoPunto[1]/self.height

		self.scale_factor_in_X = (self.segundoPunto[0] - self.primerPunto[0])
		self.scale_factor_in_Y = (self.segundoPunto[1] - self.primerPunto[1])


		# Dir where to save images
		self.directorioDeGuardadoGeneral = Shutter.directorioDeReporte
		self.root 						 = Shutter.directorioROOT
		self.fechaInfraccion 			 = str
		self.saveDir 					 = str
		self.frame_number 				 = int


		# PICMEARA INIT
		self.camera 					= picamera.PiCamera()
		self.camera.resolution 			= self.camera.MAX_RESOLUTION
		self.camera.framerate 			= 2 # original 1
		self.camera.zoom 				= (p0x, p0y, p1x, p1y)
		#self.camera.shutter_speed = 190000
		#self.camera.iso = 800
		self.camera.start_preview()


		# None paratemer for controll save files
		self.save_in_file 		= None
		folder_WORK 			= 'WORKDIR'
		self.saveDirWORK 		= self.root + "/" + folder_WORK

		# Variable para marcar paquete de frames
		self.frame_marcado			= None
		self.folder 				= str
		self.ilive 					= True
		self.circular_buff_shooter 	= collections.deque(maxlen=12)

		# Queues for comunicate the information between the Observer and Shutter
		self.input_q  = input_q

		print('EXITOSAMENTE CREE LA CLASE SHOOTERv10!!!')


	def writter(self):
		self.frame_number = 0
		while self.frame_number < self.maxCapturas:

			index 				=   (datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S')).split(':')[-1]
			save_in_work_dir 	= 	self.saveDirWORK+"/_f{}f_i{}i_.jpg".format(self.frame_number, index)

			self.circular_buff_shooter.appendleft(save_in_work_dir)
			self.input_q.put(save_in_work_dir)
			self.frame_number 	+= 1
			yield save_in_work_dir

	def apagar_shutter(self):
		pass

	def run(self):
		self.camera.capture_sequence(self.writter(), format='jpeg', use_video_port=True, resize=(self.scale_factor_in_X, self.scale_factor_in_Y))
		
		# CLEAN UNUSED IMAGES 
		files_in_work_dir = glob.glob(self.saveDirWORK + '/*.jpg')
		work_dir_len = len(files_in_work_dir)

		if work_dir_len > 24: #increased size of images to save in dir from 6 then clean
			for img_path in files_in_work_dir:
				if img_path in self.circular_buff_shooter:
					pass
				else:
					os.remove(img_path)



if __name__ == '__main__':
	#DEMO DEMO DEMO 

	shoot = Shooter()
	counter = 0
	eyes = False

	while True:
		counter +=1 
		if counter == 10:
			eyes = not eyes
			shoot(state = eyes)
			counter = 0
			#main()
		print(counter)
		time.sleep(1)

