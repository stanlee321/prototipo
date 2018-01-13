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
import sqlite3

from watermark import WaterMarker
import multiprocessing
class Shooter():
	""" General PICAMERA DRIVER Prototipe
	"""
	nombreCarpeta = datetime.datetime.now().strftime('%Y-%m-%d')+'_reporte'
	directorioDeReporte = os.getenv('HOME')+'/'+nombreCarpeta
	directorioDeNumpy = os.getenv('HOME')+'/trafficFlow/prototipo/installationFiles/'
	directorioWORKDIR = os.getenv('HOME')
	date_hour_string = datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S:%f')
	path_to_logo = 	os.getenv('HOME')+'/'+ 'trafficFlow' +'/' +'prototipo/'+ 'watermark'+ '/dems.png'

	def __init__(self, video_source = 0, width = 3280, height = 2464, cutPoly=([10,10],[3280,2464]), capturas = 1):
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
		self.camera.framerate = 2 # original 1

		self.camera.zoom = (p0x, p0y, p1x, p1y)
		#self.camera.shutter_speed = 190000
		#self.camera.iso = 800
		self.camera.start_preview()

		# None paratemer for controll save files
		self.save_in_file = None
		folder_WORK = 'WORKDIR'
		self.saveDirWORK = self.root + "/" + folder_WORK

		# Variable para marcar paquete de frames
		self.frame_marcado = None
		self.folder = str
		self.ilive = True
		self.circular_buff_shooter = collections.deque(maxlen=12)
		self.input_q = multiprocessing.Queue()

		self.procesoParaleloDos = multiprocessing.Process(target = self.processo_paraleloDos, args = (self.input_q,))
		self.procesoParaleloDos.start()
		print('EXITOSAMENTE CREE LA CLASE SHOOTERv10!!!')

		
	def establecerRegionInteres(self,cutPoly):
		self.cutPoly = cutPoly
		self.primerPunto = self.cutPoly[0] 				# Array like [p0,p1]
		self.segundoPunto = self.cutPoly[1]


	def writter(self):
		self.frame_number = 0
		
		while self.frame_number < self.maxCapturas:
			index =  (datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S')).split(':')[-1]
			save_in_work_dir = 	self.saveDirWORK+"/_f{}f_i{}i_.jpg".format(self.frame_number, index)

			self.circular_buff_shooter.appendleft(save_in_work_dir)
			self.input_q.put(save_in_work_dir)
			self.frame_number += 1
			yield save_in_work_dir

	def apagar_pi(self):
		self.procesoParaleloDos.join()
		return self

	def start(self):
		#print('here alive...')
		self.camera.capture_sequence(self.writter(), format='jpeg', use_video_port=True, resize=(self.scale_factor_in_X, self.scale_factor_in_Y))
		
		# CLEAN UNUSED IMAGES 
		files_in_work_dir = glob.glob(self.saveDirWORK + '/*.jpg')
		work_dir_len = len(files_in_work_dir)

		if work_dir_len > 24: #increased size of images to save in dir from 6
			for img_path in files_in_work_dir:
				if img_path in self.circular_buff_shooter:
					pass
				else:
					os.remove(img_path)

	def processo_paraleloDos(self, input_queue):

		# Get the WaterMarker
		nombreCarpeta = Shooter.nombreCarpeta
		directorioDeReporte = Shooter.directorioDeReporte
		path_to_logo = Shooter.path_to_logo
		path_to_run = os.getenv('HOME')+'/'+ 'WORKDIR' + '/' + 'run_camera.npy'

		watermarker = WaterMarker(path_to_logo)
		observador = Observer()
		# Load the state of the While loop
		run_camera = np.load(path_to_run)
		while run_camera == 1:

			save_in_work_dir = input_queue.get()
			observador.circular_buff.appendleft(save_in_work_dir)
			#print('CIRCULAR BUFF FROM OBSERVER', observador.circular_buff)
			# Read Homework
			homework = observador.leer_DB()
			if len(homework) > 0: # infracciones en DB:
				#print('FOUND HOMEWORK', homework)
				for work in homework:
					print('WORK', work)
					timestamp = work[0][0]
					date   = work[0][2]
					folder = work[0][2]
					index_real  = work[0][3]
				saveDir = directorioDeReporte + '/' + folder
				# copy captures
				timestamp = timestamp+' index:'+ index_real
				observador.encenderCamaraEnSubDirectorio('WORKDIR', date, folder)
				observador.move_captures(index_real)
				watermarker.put_watermark(saveDir, timestamp)
			else:
				pass

			try:
				# Load status to run the camera or exit from this while loop
				run_camera = np.load(path_to_run)
			except Exception as e:
				print('I cant read exit by this reason:', e)

		print('Saliendo del While Loop en ShooterControllerv2')
		print('>>Picamera OFF<<')


################################################################
################################################################
#################### OBSERVER CLAS #############################
################################################################
class Observer():

	nombreCarpeta = datetime.datetime.now().strftime('%Y-%m-%d')+'_reporte'
	directorioDeReporte = os.getenv('HOME')+'/'+nombreCarpeta
	directorioDeNumpy = os.getenv('HOME')+'/trafficFlow/prototipo/installationFiles/'
	directorioWORKDIR = os.getenv('HOME')
	date_hour_string = datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S:%f')
	path_to_logo = 	os.getenv('HOME')+'/'+ 'trafficFlow' +'/' +'prototipo/'+ 'watermark'+ '/dems.png'

	def __init__(self):

		# Dir where to save images

		self.directorioDeGuardadoGeneral = Observer.directorioDeReporte
		self.root = Observer.directorioWORKDIR
		self.fechaInfraccion = str
		self.saveDir = str
		self.frame_number = 0

		self.frame_marcado = str
		self.folder = str
		folder_WORK = 'WORKDIR'
		self.saveDirWORK = self.root + "/" + folder_WORK

		# Create circular buff deque of len 6
		self.circular_buff = collections.deque(maxlen=12)

	@staticmethod
	def leer_DB():
		# Read old metadata
		date_for_db = str(datetime.datetime.now().strftime('%Y-%m-%d'))
		path_to_metadata = os.getenv('HOME')+'/'+ 'WORKDIR' + '/' + 'shooter_database_{}_cache.db'.format(date_for_db)
		# Init DB
		conn = sqlite3.connect(path_to_metadata,timeout=1)
		c =  conn.cursor()
		#c.execute("SELECT * FROM stufftoPlot WHERE value=3 AND keyword='Python'")
		#c.execute("SELECT keyword,unix,value FROM stufftoPlot WHERE unix >1515634491")
		c.execute("SELECT * FROM shooter_table WHERE Status = 'OPEN'")
		#data = c.fetchone()
		data = c.fetchall()

		homework = []
		for row in data:
			metadata = data
			homework.append(metadata)
		#print('HOMEWORK', homework)
		c.execute("UPDATE shooter_table SET Status = ? WHERE Status = ?", ('CLOSED','OPEN'))
		conn.commit()

		c.close()
		conn.close()
		return homework

	def move_captures(self, index_real):
		self.frame_marcado = index_real
		#print('debug 1', self.circular_buff)
		if self.frame_marcado != None:
			# Once the while is finish move the files to his folders.
			self.move_relevant_files(self.frame_marcado)
		else:
			pass
	def encenderCamaraEnSubDirectorio(self, folder_WORK, fecha, folder):
		self.fechaInfraccion = fecha
		self.folder = folder
		self.saveDir = self.directorioDeGuardadoGeneral +"/" + str(self.folder)

		if not os.path.exists(self.saveDir):
			os.makedirs(self.saveDir)

		if not os.path.exists(self.saveDirWORK):
			os.makedirs(self.saveDirWORK) 
			#print('Cree WORKDIR para trabajar el buffer de Forma Exitosa en ' + self.saveDirWORK + ' para: '+ self.saveDir)
		
		self.save_in_file = self.saveDir+"/{}".format(self.fechaInfraccion)

	def move_relevant_files(self, frame_marcado):
		print('CIRCUALR BUFF IS', self.circular_buff)
		marcados_list  = []
		for i, image_route in enumerate(self.circular_buff):
			#print('3.- image ROUTE', image_route)
			image_route_splited = image_route.split('i')

			if frame_marcado in image_route_splited:
				marcados_list.append(i)
				#print('FRAME MARCADOS,:', image_route)
			else:
				#marcados_list.append(i-1)
				pass
		print('mARCADOS LIST IST :', marcados_list)
		if len(marcados_list) != 0:
			marcado_frame = marcados_list[-1]

			#indice = self.circular_buff.index(marcado_frame)
			indice = marcado_frame

			src_0 = self.circular_buff[indice+1] 
				
			dst_0 = self.save_in_file + '_0.jpg'

			try:
				src_one = self.circular_buff[indice+1]
				dst_one = self.save_in_file + '_1.jpg'
			except:
				src_one = self.circular_buff[indice-2]
				dst_one = self.save_in_file + '_1.jpg'

			try:
				src_two = self.circular_buff[indice-1]
				dst_two = self.save_in_file + '_2.jpg' # -1
			except Exception as e:
				print('src two cant move by this:', e)
				src_two = self.circular_buff[indice]
				dst_two = self.save_in_file + '_2.jpg' # -1
			self.copiar_las_imagenes(src_0,dst_0,src_one, dst_one, src_two, dst_two)

		else:
			pass


		self.frame_marcado = None


	def copiar_las_imagenes(self, src_0,dst_0,src_one, dst_one, src_two, dst_two):

		print('COPIAR A :')
		print('0:',src_0, ">>>>>>",dst_0)
		print('1:',src_one,">>>>>>", dst_one)
		print('2:', src_two, ">>>>>>", dst_two)
		try:
			#print('copying from:', src_0, 'to:', dst_0)
			shutil.copy(src_0, dst_0)
		except Exception as e:
			print('DELETION WARNING for {}, delering source {}'.format(dst_0, src_0))
			print('OR:', e)
			os.remove(src_0)

		try:
			#print('copying from:', src_one, 'to:', dst_one)
			shutil.copy(src_one, dst_one)
		except Exception as e:
			print('DELETION WARNING for {}, delering source {}'.format(dst_one, src_one))
			print('OR:', e)
			os.remove(src_one)

		try:
			#print('copying from:', src_two, 'to:', dst_two)
			shutil.copy(src_two, dst_two)
		except Exception as e:
			print('DELETION WARNING for {}, delering source {}'.format(dst_two, src_two))
			print('OR:', e)
			os.remove(src_two)
		print('Capturado posible infractor!')
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

