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
	directorioDeReporte = os.getenv('HOME')+'/casosReportados'
	directorioDeNumpy = os.getenv('HOME')+'/trafficFlow/prototipo/installationFiles/'
	date_hour_string = datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S:%f')

	#def __init__(self, video_source = 0, width = 3280, height = 2464, cutPoly=([10,10],[3280,2464]), capturas = 5):
	def __init__(self, video_source = 0, width = 2592, height = 1944, cutPoly=([10,10],[2592,1944]), capturas = 5):
		
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
		self.fechaInfraccion = str
		self.saveDir = str
		self.frame_number = 0

		# PICMEARA INIT

		self.camera = picamera.PiCamera()
		#self.camera.resolution = (self.width,self.height)
		self.camera.resolution = self.camera.MAX_RESOLUTION
		self.camera.framerate = 5

		self.camera.zoom = (p0x, p0y, p1x, p1y)
		#self.camera.shutter_speed = 190000
		#self.camera.iso = 800
		self.camera.start_preview()

		self.circular_buff = collections.deque(maxlen=5)

		print('EXITOSAMENTE CREE LA CLASE SHOOTER')


	def establecerRegionInteres(self,cutPoly):
		self.cutPoly = cutPoly
		self.primerPunto = self.cutPoly[0] 				# Array like [p0,p1]
		self.segundoPunto = self.cutPoly[1]

	def encenderCamaraEnSubDirectorio(self, folder_demo, fecha, folder ):
		#self.miReporte.moverRegistroACarpeta(fecha)
		self.fechaInfraccion = fecha
		self.saveDirWORK = self.directorioDeGuardadoGeneral +"/" + folder_demo
		self.saveDir = self.directorioDeGuardadoGeneral +"/" + folder

		if not os.path.exists(self.saveDir):
			os.makedirs(self.saveDir)

		if not os.path.exists(self.saveDirWORK):
			os.makedirs(self.saveDirWORK) 
		self.start()
		print('Encendi Camara de Forma Exitosa en ' + self.saveDir)
	

	def writter(self):
		#while not input_queue.empty:
		self.frame_number = 0
		while self.frame_number < self.maxCapturas:

			save_in_file = self.saveDir+"/{}-{}.jpg".format(self.fechaInfraccion, self.frame_number)
			save_in_work_dir = 	self.saveDirWORK+"/{}.jpg".format(self.frame_number)
			self.circular_buff.appendleft([save_in_work_dir, save_in_file])
			#print(self.circular_buff)
			print('GUARDADO en: '+ self.saveDirWORK+'/{}.jpg'.format(self.frame_number))
			#yield "image%02d.jpg" % frame
			yield save_in_work_dir
			#yield "./imagen_{}.jpg".format(self.frame_number)
			self.frame_number += 1
		# Move relevenat files [0] and [2]

		self.move_relevant_files()



	def move_relevant_files(self):

		# Get by index  frame 0 ,1 ,3 or 4
		"""
		photo0 = self.circular_buff[0]
		photo1 = self.circular_buff[1]

		photo3 = self.circular_buff[3]
		photo4 = self.circular_buff[4]


		src0, dest0 = photo0[0], photo0[1]
		src1, dest1 = photo1[0], photo1[1]

		src3, dest3 = photo3[0], photo3[1]
		src4, dest4 = photo4[0], photo4[1]


		shutil.move(src0, dest0)
		shutil.move(src1, dest1)

		shutil.move(src3, dest3)
		shutil.move(src4, dest4)
		"""
		# Get by last apperance: get the last two photos

		photo0 = self.circular_buff.pop()
		photo1 = self.circular_buff.pop()
		print('photo 0 is', photo0)
		print('photo 1 is', photo1)

		src0, dest0 = photo0[0], photo0[1]
		src1, dest1 = photo1[0], photo1[1]

		shutil.move(src0, dest0)
		shutil.move(src1, dest1)



	def start(self):
		start = time.time()
		self.camera.capture_sequence(self.writter(), format='jpeg', use_video_port=True, resize=(self.scale_factor_in_X, self.scale_factor_in_Y))
		finish = time.time()
		print("Captured %d frames at %.2ffps" % (self.maxCapturas,self.maxCapturas / (finish - start)))

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

