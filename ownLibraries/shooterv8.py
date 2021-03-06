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
		self.camera.framerate = 5

		self.camera.zoom = (p0x, p0y, p1x, p1y)
		#self.camera.shutter_speed = 190000
		#self.camera.iso = 800
		self.camera.start_preview()

		# Create circular buff deque of len 5
		self.circular_buff = collections.deque(maxlen=5)

		print('EXITOSAMENTE CREE LA CLASE SHOOTER')


	def establecerRegionInteres(self,cutPoly):
		self.cutPoly = cutPoly
		self.primerPunto = self.cutPoly[0] 				# Array like [p0,p1]
		self.segundoPunto = self.cutPoly[1]

	def encenderCamaraEnSubDirectorio(self, folder_WORK, fecha, folder ):
		#self.miReporte.moverRegistroACarpeta(fecha)
		self.fechaInfraccion = fecha
		self.saveDirWORK = self.root + "/" + folder_WORK
		self.saveDir = self.directorioDeGuardadoGeneral +"/" + folder

		if not os.path.exists(self.saveDir):
			os.makedirs(self.saveDir)

		if not os.path.exists(self.saveDirWORK):
			os.makedirs(self.saveDirWORK) 
			print('Cree WORKDIR para trabajar el buffer de Forma Exitosa en ' + self.saveDirWORK + ' para: '+ self.saveDir)
		self.start()
		#print('Encendi Camara de Forma Exitosa en ' + self.saveDir)
		

	

	def writter(self):
		self.frame_number = 0
		while self.frame_number < self.maxCapturas:

			save_in_file = self.saveDir+"/{}-{}.jpg".format(self.fechaInfraccion, self.frame_number)
			save_in_work_dir = 	self.saveDirWORK+"/{}.jpg".format(self.frame_number)
			self.circular_buff.appendleft([save_in_work_dir, save_in_file])
			#print('GUARDADO en: '+ self.saveDirWORK+'/{}.jpg'.format(self.frame_number))
			#yield "image%02d.jpg" % frame
			yield save_in_work_dir
			#yield "./imagen_{}.jpg".format(self.frame_number)
			self.frame_number += 1

		# Once the while is finish move the files to his folders.
		self.move_relevant_files()



	def move_relevant_files(self):

		# Get by index  frame 0 ,1 ,3 or 4, example:
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

		"""
		# Get by last value in past: get the last two photos

		photo0 = self.circular_buff.popleft()
		#photo1 = self.circular_buff.popleft()

		photo_zero_present = self.circular_buff.pop()
		photo_two_present = self.circular_buff.pop()

		src0, dest0 = photo0[0], photo0[1]
		#src1, dest1 = photo1[0], photo1[1]

		src_zero, dest_zero = photo_zero_present[0], photo_zero_present[1]
		src_two, dest_two = photo_two_present[0], photo_two_present[1]
		"""

		photo0 = self.circular_buff[-1]
		src0, dst0 = photo0[0], photo0[1]

		src_one = self.circular_buff[-2]
		src_one, dst_one = src_one[0], src_one[1]

		src_two = self.circular_buff[-3]
		src_two, dst_two = src_two[0], src_two[1]

		try:
			shutil.copy(src0, dst0)
		except:
			print('DELETION WARNING for {}, delering source {}'.format(dst0, src0))
			os.remove(src0)
		try:
			shutil.copy(src_one, dst_one)
		except:
			print('DELETION WARNING for {}, delering source {}'.format(dst_one, src_one))
			os.remove(src_one)
		try:
			shutil.copy(src_two, dst_two)
		except Exception as e:
			print('DELETION WARNING for {}, delering source {}'.format(dst_two, src_two))
			os.remove(src_two)

		print('Capturado posible infractor!')


		# Get present photo






	def start(self):
		start = time.time()
		self.camera.capture_sequence(self.writter(), format='jpeg', use_video_port=True, resize=(self.scale_factor_in_X, self.scale_factor_in_Y))
		finish = time.time()
		#print("Captured %d frames at %.2ffps" % (self.maxCapturas,self.maxCapturas / (finish - start)))

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

