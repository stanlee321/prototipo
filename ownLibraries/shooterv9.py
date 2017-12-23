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

		# Create circular buff deque of len 6
		self.circular_buff = collections.deque(maxlen=6)

		# None paratemer for controll save files
		self.save_in_file = None
		folder_WORK = 'WORKDIR'
		self.saveDirWORK = self.root + "/" + folder_WORK

		# Variable para marcar paquete de frames
		self.frame_marcado = None
		print('EXITOSAMENTE CREE LA CLASE SHOOTER')


	def establecerRegionInteres(self,cutPoly):
		self.cutPoly = cutPoly
		self.primerPunto = self.cutPoly[0] 				# Array like [p0,p1]
		self.segundoPunto = self.cutPoly[1]

	def encenderCamaraEnSubDirectorio(self, folder_WORK, fecha, folder, index ):
		self.fechaInfraccion = fecha
		self.frame_marcado = index
		#if folder != None:
		self.saveDir = self.directorioDeGuardadoGeneral +"/" + folder

		if not os.path.exists(self.saveDir):
			os.makedirs(self.saveDir)

		if not os.path.exists(self.saveDirWORK):
			os.makedirs(self.saveDirWORK) 
			print('Cree WORKDIR para trabajar el buffer de Forma Exitosa en ' + self.saveDirWORK + ' para: '+ self.saveDir)
		
		self.save_in_file = self.saveDir+"/{}".format(self.fechaInfraccion)
		print('1.- Tengo que guardar Frames en::', self.save_in_file)
		#print('self frame MARCADO is', self.frame_marcado)
		#else:
		#	self.save_in_file = None
	

	def writter(self):
		self.frame_number = 0
		
		while self.frame_number < self.maxCapturas:
			index =  (datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S')).split(':')[-1]

			save_in_work_dir = 	self.saveDirWORK+"/_f{}f_i{}i_.jpg".format(self.frame_number, index)

			self.circular_buff.appendleft(save_in_work_dir)
			self.frame_number += 1
			yield save_in_work_dir

		# CLEAN UNUSED IMAGES 
		files_in_work_dir = glob.glob(self.saveDirWORK + '/*.jpg')
		work_dir_len = len(files_in_work_dir)
		#print('1 .- FOLDER LEN is:', work_dir_len)

		if work_dir_len > 6:
			for img_path in files_in_work_dir:
				if img_path in self.circular_buff:
					pass
				else:
					os.remove(img_path)

		if self.frame_marcado != None:
			# Once the while is finish move the files to his folders.
			self.move_relevant_files(self.frame_marcado)


	def move_relevant_files(self, frame_marcado):
		#print('2.- FRAME MARCADO IST:', frame_marcado)
		marcados_list  = []
		for i, image_route in enumerate(self.circular_buff):
			#print('3.- image ROUTE', image_route)
			image_route_splited = image_route.split('i')

			if frame_marcado in image_route_splited:
				marcados_list.append(i)
				#print('FRAME MARCADOS,:', image_route)
			else:
				marcados_list.append(i-1)
		
		if len(marcados_list) != 0:
			marcado_frame = marcados_list[-1]

			#indice = self.circular_buff.index(marcado_frame)
			indice = marcado_frame

			#print('DER INDEX IST VOM B ', indice)

			src_0 = self.circular_buff[indice] 
				
			dst_0 = self.save_in_file + '_0.jpg'

			try:
				src_one = self.circular_buff[indice+1]
				dst_one = self.save_in_file + '_1.jpg'
			except:
				src_one = self.circular_buff[indice-2]
				dst_one = self.save_in_file + '_1.jpg'


			src_two = self.circular_buff[indice-1]
			dst_two = self.save_in_file + '_-1.jpg'

			self.copiar_las_imagenes(src_0,dst_0,src_one, dst_one, src_two, dst_two)

				
		else:
			pass

		# CLEANING Variables
		path_to_metadata = os.getenv('HOME')+'/'+ 'WORKDIR' + '/' + 'metadata.csv'

		metadata = pd.read_csv(path_to_metadata)
		metadata.SAVE_IMG_IN = 	'None'
		metadata.INDEX = 'XX'
		metadata.to_csv(path_to_metadata, index=False, sep=',')

		self.frame_marcado = None

	def copiar_las_imagenes(self, src_0,dst_0,src_one, dst_one, src_two, dst_two):
		try:
			#print('copying from:', src_0, 'to:', dst_0)
			shutil.copy(src_0, dst_0)
		except:
			print('DELETION WARNING for {}, delering source {}'.format(dst_0, src_0))
			os.remove(src_0)

		try:
			#print('copying from:', src_one, 'to:', dst_one)
			shutil.copy(src_one, dst_one)
		except:
			print('DELETION WARNING for {}, delering source {}'.format(dst_one, src_one))
			os.remove(src_one)
		try:
			#print('copying from:', src_two, 'to:', dst_two)
			shutil.copy(src_two, dst_two)
		except:
			print('DELETION WARNING for {}, delering source {}'.format(dst_two, src_two))
			os.remove(src_two)
		print('Capturado posible infractor!')


	def start(self):
		#print('here alive...')
		self.camera.capture_sequence(self.writter(), format='jpeg', use_video_port=True, resize=(self.scale_factor_in_X, self.scale_factor_in_Y))

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

