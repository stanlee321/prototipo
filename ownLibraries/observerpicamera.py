import multiprocessing
import os
import numpy as np
import collections
import datetime
import sqlite3

from .watermark import WaterMarker




class Observer(multiprocessing.Process):

	nombreCarpeta 		= datetime.datetime.now().strftime('%Y-%m-%d')+'_reporte'
	directorioDeReporte = os.getenv('HOME')+'/' + nombreCarpeta
	directorioDeNumpy 	= os.getenv('HOME')+'/trafficFlow/prototipo/installationFiles/'
	directorioROOT 		= os.getenv('HOME')
	date_hour_string 	= datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S:%f')
	path_to_logo 		= os.getenv('HOME')+'/'+ 'trafficFlow' +'/' +'prototipo/'+ 'watermark'+ '/dems.png'

	def __init__(self, output_q):
		super(Observer, self).__init__()
		# Dir where to save images

		self.directorioDeGuardadoGeneral = Observer.directorioDeReporte
		self.root 						 = Observer.directorioROOT
		self.fechaInfraccion 			 = str
		self.saveDir 					 = str
		self.frame_number 				 = 0

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
		self.output_q = output_q

		# create watermarker class
		self.watermarker = WaterMarker(Observer.path_to_logo)

		# check status
		self.save_in_folder = None
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
		for i, image_route in enumerate(self.circular_buff):
			image_route_splited = image_route.split('i')

			if frame_marcado in image_route_splited:
				marcados_list.append(i)
			else:
				pass
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
			print('DELETION WARNING for {}, delering source {}'.format(dst_0, src_0))
			print('OR:', e)

		try:
			#print('copying from:', src_one, 'to:', dst_one)
			shutil.copy(src_one, dst_one)
		except Exception as e:
			print('DELETION WARNING for {}, delering source {}'.format(dst_one, src_one))
			print('OR:', e)

		try:
			shutil.copy(src_two, dst_two)
		except Exception as e:
			print('DELETION WARNING for {}, delering source {}'.format(dst_two, src_two))
			print('OR:', e)
		print('Capturado posible infractor!')




	def run(self):
		while True:
			save_in_work_dir = self.output_q.get()


			if  self.save_in_folder != None:

				homework = self.leer_DB()

				self.circular_buff.appendleft(save_in_work_dir)
				if len(homework) > 0: 
					for work in homework:
						timestamp 	= work[0][0]
						date   		= work[0][2]
						folder 		= work[0][2]
						index_real  = work[0][3]

					saveDir = directorioDeReporte + '/' + folder

					timestamp = timestamp#+' index:'+ index_real
					self.encenderCamaraEnSubDirectorio('WORKDIR', date, folder)
					self.move_captures(index_real)
					self.watermarker.put_watermark(saveDir, timestamp)

				self.save_in_folder = None