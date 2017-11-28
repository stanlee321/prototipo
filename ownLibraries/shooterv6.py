#!/usr/bin/env python
# semaforo como clase

import os
import cv2
import time
import datetime
import threading
import multiprocessing


import picamera
import time
import cv2
#from io import BytesIO
#from skimage.io import imsave
import scipy
import scipy.misc
import scipy.ndimage
class Shooter():
	""" General PICAMERA DRIVER Prototipe
	"""
	directorioDeReporte = os.getenv('HOME')+'/casosReportados'
	date_hour_string = datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S:%f')

	def __init__(self, video_source = 0, width = 3280, height = 2464, cutPoly=([0,0],[3280,2464]), capturas = 3):
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
		self.frame_number = 0
		
		#thread = threading.Thread(target=self.start, args=())
		#thread.daemon = True									# Daemonize thread
		#thread.start() 


		# PICMEARA INIT

		self.camera = picamera.PiCamera()
		#self.camera.resolution = (3240,2464)
		self.camera.resolution = (self.width,self.height)
		self.camera.framerate = 1
		self.camera.start_preview()
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
		self.start()
		print('Encendi Camara de Forma Exitosa en '+self.saveDir)

	def encenderCamara(self):
		#self.miReporte.moverRegistroACarpeta(fecha)
		self.eyesOpen = True

	def apagarCamara(self):
		self.eyesOpen = False
		print('Realizada las capturas, cerrando ojos...')
	

	def writter(self):
		#while not input_queue.empty:
		self.frame_number = 0
		while self.frame_number < self.maxCapturas:
			print('GUARDADO en: '+ self.saveDir+'/{}-{}.jpg'.format(self.fechaInfraccion[:-3], self.frame_number))
			#yield "image%02d.jpg" % frame
			
			yield self.saveDir+"/{}-{}.jpg".format(self.fechaInfraccion, self.frame_number)
			#yield "./imagen_{}.jpg".format(self.frame_number)
			self.frame_number += 1



	def start(self):
		if self.eyesOpen == True:
			start = time.time()
			self.camera.capture_sequence(self.writter(), use_video_port=True)
			finish = time.time()
			print("Captured %d frames at %.2ffps" % (self.maxCapturas,self.maxCapturas / (finish - start)))
			self.apagarCamara()
		if self.eyesOpen == False:
			pass

	def __call__(self, state = False):
		self.eyesOpen = state
		self.start()

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