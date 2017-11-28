#!/usr/bin/env python
# semaforo como clase

import os
import cv2
import time
import ctypes
import datetime
import threading
import multiprocessing

class controladorCamara():
	def __init__(self):
		# Se declaran las variables de control con el proceso paralelo
		programaPrincipalCorriendo = multiprocessing.Value('i',1)
		numeroImagenes = multiprocessing.Value('i',0)
		nombreCarpeta = multiprocessing.Value('c',datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S'))
		procesoParalelo = multiprocessing.Process(target = procesadoParalelo, args = (programaPrincipalCorriendo,numeroImagenes,nombreCarpeta))
		procesoParalelo.start()

	def encenderCamaraEnSubDirectorio(self,nombreFolder):
		nombreCarpeta.value = nombreFolder
		numeroImagenes.value = numeroImagenes.value + 2

	def apagarCamara(self):
		numeroImagenes.value = 0

	def apagarControlador(self):
		programaPrincipalCorriendo = multiprocessing.Value('i',0)
		procesoParalelo.join()

	def procesadoParalelo(self,programaPrincipal,numeroImagen,carpeta):
		#if os.uname()[1] == 'alvarohurtado-305V4A':
		miCamara = Shooter()
		while programaPrincipal.value == 1:
			if numeroImagen.value > 0:
				miCamara.capturoEnDirectorio(carpeta.value)
				numeroImagen.value = numeroImagen.value -1



class Shooter():
	""" General PICAMERA DRIVER Prototipe
	"""
	directorioDeReporte = os.getenv('HOME')+'/casosReportados'
	date_hour_string = datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S:%f')

	def __init__(self, video_source = 0, width = 2592, height = 1944, cutPoly=([0,0],[2592,1944]), capturas = 3):
	#def __init__(self, video_source = 0, width = 680, height = 420, cutPoly=([0,0],[200,200]), saveDir='./test/'):
		#self.miReporte = MiReporte(levelLogging=10)
		#self.miReporte.info( 'Starting the  PiCam')
		#print('Cree objeto de forma exitosa')
		self.eyesOpen = False
		# Initial aparemeters
		self.video_source = video_source
		self.width = width		# Integer Like
		self.height = height	# Integer Like
		self.maxCapturas = capturas
		# FOR ROI
		self.cutPoly = cutPoly 	# ARRAY like (primerPunto, segundoPunto)
		self.primerPunto = self.cutPoly[0] 				# Array like [p0,p1]
		self.segundoPunto = self.cutPoly[1]				# Array like [p0,p1]

		# Dir where to save images
		
		self.directorioDeGuardadoGeneral = self.directorioDeReporte
		self.fechaInfraccion = str
		self.saveDir = str
		
		#self.saveDir = self.directorioDeGuardadoGeneral +"/"+self.fechaInfraccion
		#self.segundo_milisegundo = datetime.datetime.now().strftime('%S.%f')
		## MultiPro and threadning
		self.input_q = multiprocessing.Queue(maxsize = 6)

		process = multiprocessing.Process(target = self.writter, args=((self.input_q,)))
		process.daemon = True
		pool = multiprocessing.Pool(4, self.writter, (self.input_q,))

		thread = threading.Thread(target=self.start, args=())
		thread.daemon = True									# Daemonize thread
		thread.start() 
		print('EXITOSAMENTE CREE LA CLASE SHOOTER')

	def establecerRegionInteres(self,cutPoly):
		self.cutPoly = cutPoly
		self.primerPunto = self.cutPoly[0] 				# Array like [p0,p1]
		self.segundoPunto = self.cutPoly[1]

	def encenderCamaraEnSubDirectorio(self, folder, fecha):
		#self.miReporte.moverRegistroACarpeta(fecha)
		self.fechaInfraccion = fecha
		self.saveDir = self.directorioDeGuardadoGeneral +"/" + folder
		if not os.path.exists(self.saveDir):
			os.makedirs(self.saveDir) 
		self.eyesOpen = True
		print('Encendi Camara de Forma Exitosa en '+self.saveDir)

	def encenderCamara(self):
		#self.miReporte.moverRegistroACarpeta(fecha)
		self.eyesOpen = True

	def apagarCamara(self):
		self.eyesOpen = False
		print('Camara Apagada')
	

	def writter(self, input_queue):
		while True:
			data = input_queue.get()
			placa, numero_de_captura, saveDir, fechaInfraccion  = data[0], data[1], data[2], data[3]
			print('GUARDADO en: '+ saveDir+'/{}-{}.jpg'.format(fechaInfraccion[:-3], numero_de_captura))
			cv2.imwrite(saveDir+'/{}-{}.jpg'.format(fechaInfraccion, numero_de_captura), placa)
			#cv2.imwrite('./imagen_{}.jpg'.format(numero_de_captura), placa)
			

	def start(self):
		if self.eyesOpen == True:
			#self.miReporte.info('Iam in')
			self.video_capture = cv2.VideoCapture(self.video_source) 
			self.video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.width) 
			self.video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height) 
			for captura in range(self.maxCapturas):
				print('captura Numero: ', captura)
				# Read plate
				_, placa = self.video_capture.read()
				print('placa Inputshape: ', placa.shape)
				placaActual = placa[self.primerPunto[1]:self.segundoPunto[1], self.primerPunto[0]: self.segundoPunto[0]]
				self.input_q.put((placaActual, captura, self.saveDir, self.fechaInfraccion))
				#  If Self.run is False everything starts to stop and close
				#if self.eyesOpen  == False: # self.counter > self.maxCounter:
				#	self.eyesOpen = False
				#	self.video_capture.release()
				#	break
			print('finish limit of captures, releasing...')
			self.eyesOpen = False
			self.video_capture.release()
			while True:
				if self.video_capture.grab() == False:
					print('Camera sucessfully released ...!')
					break
				else:
					print('Releasing camera....')
					self.video_capture.release()
			#else:
			#	self.video_capture.release()
	
		self.thread = threading.Thread(target=self.start, args=())
		self.thread.daemon = True									# Daemonize thread
		self.thread.start()
