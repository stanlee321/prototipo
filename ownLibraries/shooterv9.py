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
#from io import BytesIO
#from skimage.io import imsave

class Shooter():
	""" General PICAMERA DRIVER Prototipe
	"""
	nombreCarpeta = datetime.datetime.now().strftime('%Y-%m-%d')+'_reporte'
	directorioDeReporte = os.getenv('HOME')+'/'+nombreCarpeta
	directorioDeNumpy = os.getenv('HOME')+'/trafficFlow/prototipo/installationFiles/'
	directorioWORKDIR = os.getenv('HOME')
	date_hour_string = datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S:%f')

	def __init__(self, video_source = 0, width = 3280, height = 2464, cutPoly=([10,10],[3280,2464]), capturas = 3):
	#def __init__(self, video_source = 0, width = 2592, height = 1944, cutPoly=([10,10],[2592,1944]), capturas = 5):
		
		data = np.load(Shooter.directorioDeNumpy+'datos.npy')
		# Initial aparemeters
		self.video_source = video_source
		self.width = width		# Integer Like
		self.height = height	# Integer Like
		self.maxCapturas = capturas
		# FOR ROI
		self.cutPoly = data[-1] 	# ARRAY like (primerPunto, segundoPunto)
		self.primerPunto = self.cutPoly[0] 				# Array like [p0,p1]
		self.segundoPunto = self.cutPoly[1]				# Array like [p0,p1]
		p0x = self.primerPunto[0]/self.width
		p0y = self.primerPunto[1]/self.height

		p1x = self.segundoPunto[0]/self.width
		p1y = self.segundoPunto[1]/self.height

		self.scale_factor_in_X = (self.segundoPunto[0] - self.primerPunto[0])
		self.scale_factor_in_Y = (self.segundoPunto[1] - self.primerPunto[1])

		# Dir where to save images

		
		self.directorioDeGuardadoGeneral = self.directorioDeReporte
		self.root = self.directorioWORKDIR
		self.fechaInfraccion = str
		self.saveDir = str
		self.frame_number = 0

		# PICMEARA INIT

		self.camera = picamera.PiCamera()
		#self.camera.resolution = (self.width,self.height)
		self.camera.resolution = self.camera.MAX_RESOLUTION
		self.camera.framerate = 1

		self.camera.zoom = (p0x, p0y, p1x, p1y)
		#self.camera.shutter_speed = 190000
		#self.camera.iso = 800
		self.camera.start_preview()

		# Create circular buff deque of len 5
		self.circular_buff = collections.deque(maxlen=5)

		# None paratemer for controll save files
		self.save_in_file = None
		folder_WORK = 'WORKDIR'
		self.saveDirWORK = self.root + "/" + folder_WORK
		print('EXITOSAMENTE CREE LA CLASE SHOOTER')


	def establecerRegionInteres(self,cutPoly):
		self.cutPoly = cutPoly
		self.primerPunto = self.cutPoly[0] 				# Array like [p0,p1]
		self.segundoPunto = self.cutPoly[1]

	def encenderCamaraEnSubDirectorio(self, folder_WORK, fecha, folder ):
		self.fechaInfraccion = fecha
		self.saveDir = self.directorioDeGuardadoGeneral +"/" + folder

		if not os.path.exists(self.saveDir):
			os.makedirs(self.saveDir)

		if not os.path.exists(self.saveDirWORK):
			os.makedirs(self.saveDirWORK) 
			print('Cree WORKDIR para trabajar el buffer de Forma Exitosa en ' + self.saveDirWORK + ' para: '+ self.saveDir)
		
		self.save_in_file = self.saveDir+"/{}-{}.jpg".format(self.fechaInfraccion, self.frame_number)
		print('save file is', self.save_in_file)

	

	def writter(self):
		self.frame_number = 0
		print('self.frame_number', self.frame_number)
		while self.frame_number < self.maxCapturas:
			save_in_work_dir = 	self.saveDirWORK+"/{}.jpg".format(self.frame_number)
			self.circular_buff.appendleft(save_in_work_dir)
			self.frame_number += 1
			yield save_in_work_dir
		# Once the while is finish move the files to his folders.
		if self.save_in_file != None:
			print('diff als none', self.save_in_file)
			self.move_relevant_files()
			self.save_in_file = None
	def move_relevant_files(self):

		# Get by index  frame 0 ,1 ,3 or 4, example:

		print(self.save_in_file)
		photo0 = self.circular_buff[-1]
		src0 = photo0
		dst0 = self.save_in_file


		src_one = self.circular_buff[-2]
		src_one = src_one
		dst_one = self.save_in_file

		#src_two = self.circular_buff[-3]
		#src_two, dst_two = src_two[0], src_two[1]
		print('Capturado posible infractor!')

	def start(self):
		start = time.time()
		self.camera.capture_sequence(self.writter(), format='jpeg', use_video_port=True, resize=(self.scale_factor_in_X, self.scale_factor_in_Y))
		finish = time.time()

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

