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
from .watermark import WaterMarker


class Shutter(multiprocessing.Process):
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
	def __init__(self, video_source = 0, width = 2592, height = 1944, cutPoly=([10,10],[2592,1944]), capturas = 3):

		super(Shutter, self).__init__()

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

		# Queues for comunicate the information between the Observer and Shutter
		self.input_q  	= multiprocessing.Queue()

		self.observador = Observer(self.input_q)
		self.observador.start()
		print('EXITOSAMENTE CREE LA CLASE SHOOTERv11!!!')

	def apagar_observador(self):
		self.observador.join()

	def run(self):
		# PICMEARA INIT
		self.camera 					= picamera.PiCamera()
		self.camera.resolution 			= (2592,1944)#self.camera.MAX_RESOLUTION
		self.camera.framerate 			= 2 # original 1
		self.camera.zoom 				= (self.p0x, self.p0y, self.p1x, self.p1y)
		self.camera.exposure_mode 		= 'sports'
		#self.camera.shutter_speed = 190000
		#self.camera.iso = 800
		self.camera.start_preview()

		run_camera = np.load(Shutter.path_to_run_camera)

		while run_camera == 1:
			index 				=   (datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S')).split(':')[-1]
			writte_names		= 	[self.saveDirWORK+"/_f{}f_i{}i_.jpg".format(f_number, index) for f_number in range(self.maxCapturas)]
			
			for route in sorted(writte_names):
				self.circular_buff_shooter.appendleft(route)
				self.input_q.put(route)
			self.camera.capture_sequence(writte_names, format='jpeg', use_video_port=True, resize=(self.scale_factor_in_X, self.scale_factor_in_Y))
			
			# CLEAN UNUSED IMAGES 
			files_in_work_dir 	 = glob.glob(self.saveDirWORK + '/*.jpg')
			work_dir_len		 = len(files_in_work_dir)

			if work_dir_len > 24: #increased size of images to save in dir from 6 then clean
				for img_path in files_in_work_dir:
					if img_path in self.circular_buff_shooter:
						pass
					else:
						os.remove(img_path)

			run_camera = np.load(Shutter.path_to_run_camera)

		print('END OF RUN IN SHUTTER????')
		print('Finished...')




class Observer(multiprocessing.Process):

	nombreCarpeta 		= datetime.datetime.now().strftime('%Y-%m-%d')+'_reporte'
	directorioDeReporte = os.getenv('HOME')+'/' + nombreCarpeta
	directorioDeNumpy 	= os.getenv('HOME')+'/trafficFlow/prototipo/installationFiles/'
	directorioROOT 		= os.getenv('HOME')
	date_hour_string 	= datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S:%f')
	path_to_logo 		= os.getenv('HOME')+'/'+ 'trafficFlow' +'/' +'prototipo/'+ 'watermark'+ '/dems.png'

	path_to_run_camera 		= os.getenv('HOME')+'/'+ 'WORKDIR' + '/' + 'run_camera.npy'
	path_to_tasks_deque 	= os.getenv('HOME')+'/'+ 'WORKDIR' + '/' + 'tasks_deque.npy'


	def __init__(self, input_q):
		super(Observer, self).__init__()
		# Dir where to save images

		self.directorioDeGuardadoGeneral = Observer.directorioDeReporte
		self.root 						 = Observer.directorioROOT
		self.fechaInfraccion 			 = str
		self.saveDir 					 = str
		self.frame_number 				 = 0

		self.run_camera 				 = False


		self.frame_marcado 				 = str
		self.folder 					 = str
		folder_WORK 					 = 'WORKDIR'
		self.saveDirWORK 				 = self.root + "/" + folder_WORK
		self.save_with_name				 = str  							# aux name for images

		# Fro db
		self.date_for_db		 		= str(datetime.datetime.now().strftime('%Y-%m-%d'))


		# Create circular buff deque of len 6
		self.circular_buff 				 = collections.deque(maxlen=12)

		# load queues from exterior world
		self.input_q = input_q

		# create watermarker class
		self.watermarker = WaterMarker(Observer.path_to_logo)


		print('Sucessfully started Observer CLASS!!!')


	def leer_DB(self):
		# Read old metadata
		self.date_for_db = 	str(datetime.datetime.now().strftime('%Y-%m-%d'))

		path_to_metadata = 	os.getenv('HOME')+'/'+ 'WORKDIR' + '/' + 'shooter_database_{}_cache.db'.format(self.date_for_db)
		
		# Init DB
		conn 			 = 	sqlite3.connect(path_to_metadata,timeout=1)
		c 				 =  conn.cursor()
		#c.execute("SELECT * FROM stufftoPlot WHERE value=3 AND keyword='Python'")
		#c.execute("SELECT keyword,unix,value FROM stufftoPlot WHERE unix >1515634491")
		c.execute("SELECT * FROM shooter_table WHERE Status = 'OPEN'")
		data = c.fetchall()

		homework = []
		for row in data:
			metadata = data
			homework.append(metadata)

		c.execute("UPDATE shooter_table SET Status = ? WHERE Status = ?", ('CLOSED','OPEN'))
		conn.commit()

		c.close()
		conn.close()

		return homework

	def move_captures(self, index_real):
		self.frame_marcado = index_real
		if self.frame_marcado != None:
			# Once the while is finish move the files to his folders.
			self.move_relevant_files(self.frame_marcado)
		else:
			pass


	def encenderCamaraEnSubDirectorio(self, fecha, folder):

		# Load variables
		self.fechaInfraccion 	= fecha
		self.folder 			= folder
		self.saveDir 			= Observer.directorioDeReporte +"/" + str(self.folder)


		# Check if exist folder where to save images
		existe = os.path.exists(self.saveDir)
		if not os.path.exists(self.saveDir):
			os.makedirs(self.saveDir)
			#os.mkdir(self.saveDir)

		# Create aux folder to work in
		if not os.path.exists(self.saveDirWORK):
			os.makedirs(self.saveDirWORK) 

		#print('Cree WORKDIR para trabajar el buffer de Forma Exitosa en ' + self.saveDirWORK + ' para: '+ self.saveDir)

		self.save_with_name = self.saveDir + "/{}".format(self.fechaInfraccion)

	def move_relevant_files(self, frame_marcado):
		marcados_list  = []
		print('frame_marcado is', frame_marcado)
		print('self. circular_buff is', self.circular_buff)
		for i, image_route in enumerate(self.circular_buff):
			image_route_splited = image_route.split('i')

			if frame_marcado in image_route_splited:
				marcados_list.append(i)
			# If index is not in list, chose his value - 1
			else:
				frame_marcado_as_int = int(frame_marcado) - 1
				frame_marcado_as_str = str(frame_marcado_as_int)

				if frame_marcado_as_str in image_route_splited:
					marcados_list.append(i)
				else:
					pass

		print('LIST OF AMRCADOS IS', marcados_list)
		if len(marcados_list) != 0:
			for marcado_frame in marcados_list:

				#indice = self.circular_buff.index(marcado_frame)
				indice = marcado_frame

				src_0 = self.circular_buff[indice] 
					
				dst_0 = self.save_with_name + '_0.jpg'

				try:
					src_one = self.circular_buff[indice+1]
					dst_one = self.save_with_name + '_1.jpg'
				except:
					src_one = self.circular_buff[indice-2]
					dst_one = self.save_with_name + '_1.jpg'

				try:
					src_two = self.circular_buff[indice-2]
					dst_two = self.save_with_name + '_2.jpg' # -1
				except Exception as e:
					print('src two cant move by this:', e)
					src_two = self.circular_buff[indice]
					dst_two = self.save_with_name + '_2.jpg' # -1
				self.copiar_las_imagenes(src_0,dst_0,src_one, dst_one, src_two, dst_two)

			else:
				pass
			self.frame_marcado = None

	@staticmethod
	def copiar_las_imagenes(src_0, dst_0, src_one, dst_one, src_two, dst_two):
		try:
			#print('copying from:', src_0, 'to:', dst_0)
			shutil.copy(src_0, dst_0)
		except Exception as e:
			#print('DELETION WARNING for {}, delering source {}'.format(dst_0, src_0))
			print('OR:', e)

		try:
			#print('copying from:', src_one, 'to:', dst_one)
			shutil.copy(src_one, dst_one)
		except Exception as e:
			#print('DELETION WARNING for {}, delering source {}'.format(dst_one, src_one))
			print('OR:', e)

		try:
			shutil.copy(src_two, dst_two)
		except Exception as e:
			#print('DELETION WARNING for {}, delering source {}'.format(dst_two, src_two))
			print('OR:', e)
		print('Capturado posible infractor!')


	def run(self):
		run_camera = np.load(Observer.path_to_run_camera)
		while run_camera == 1:
			try:
				folders_queue 		= np.load(Observer.path_to_tasks_deque)
			except:
				print('Bussy np.load(), passing...')
				queu = collections.deque(maxlen=2)
				np.save(Observer.path_to_tasks_deque, queu)

			try:
				path_image_workdir = self.input_q.get(timeout=5)
				self.circular_buff.appendleft(path_image_workdir)

				if  len(folders_queue) != 0:
					print('Iam into the tasksss!!!, tasks are', len(folders_queue))
					print('TASKs are,', folders_queue)
					homework = self.leer_DB()
					if len(homework) > 0: 
						for work in homework:
							timestamp 	= work[0][0]
							date   		= work[0][1]
							folder 		= work[0][1]
							index_real  = work[0][2]

						saveDir = Observer.directorioDeReporte + '/' + folder

						timestamp = timestamp#+' index:'+ index_real
						self.encenderCamaraEnSubDirectorio(date, folder)
						self.move_captures(index_real)
						#self.watermarker.put_watermark(saveDir, timestamp)
					# return an empnty task basket
					queu = collections.deque(maxlen=2)
					np.save(Observer.path_to_tasks_deque, queu)
			except:
				pass
			# return state of while loop camera
			try:
				run_camera = np.load(Observer.path_to_run_camera)
			except:
				#q = collections.deque(maxlen=2)
				#np.save(Observer.path_image_workdir,q)
				print('Cant Load run_camera state, turning off the OBSERVER')
				run_camera = 0


		print('EXIRING FROM OBSERVER....')




if __name__ == '__main__':
	shutt = Shutter()
	shutt.start()
	counter = 0
	while True:
		counter +=1 
		if counter == 10:
			print(shutt.circular_buff_shooter)
		time.sleep(1)

		if counter == 30:
			np.load(shutt.path_to_run_camera, 0)
			shutt.join()
			break

