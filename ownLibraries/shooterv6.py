#!/usr/bin/env python
# semaforo como clase

import os
import time
import datetime
import threading
import multiprocessing


import picamera
import time
#from io import BytesIO
#from skimage.io import imsave

class Shooter():
	""" General PICAMERA DRIVER Prototipe
	"""
	directorioDeReporte = os.getenv('HOME')+'/casosReportados'
	date_hour_string = datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S:%f')

	#def __init__(self, video_source = 0, width = 3280, height = 2464, cutPoly=([0,0],[3280,2464]), capturas = 2):
	def __init__(self, video_source = 0, width = 2592, height = 1944, cutPoly=([0,0],[200,200]), capturas = 2):
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

		self.scale_factor_in_X = int(self.segundoPunto[0]/self.width)
		self.scale_factor_in_Y = int(self.segundoPunto[1]/self.height)

		print('SCALES ARE:')
		print('in X', self.scale_factor_in_X)
		print('in Y', self.scale_factor_in_Y)

		p0x = self.primerPunto[0]/self.width
		p0y = self.primerPunto[1]/self.height

		p1x = self.segundoPunto[0]/self.width
		p1y = self.segundoPunto[1]/self.height

		print('scales for zoom are', p0x, p0y, p1x, p1y)
		# Dir where to save images

		
		self.directorioDeGuardadoGeneral = self.directorioDeReporte
		self.fechaInfraccion = str
		self.saveDir = str
		self.frame_number = 0

		# PICMEARA INIT

		self.camera = picamera.PiCamera()
		#self.camera.resolution = (self.width,self.height)
		self.camera.resolution = self.camera.MAX_RESOLUTION
		self.camera.framerate = 1

		self.camera.zoom = (self.p0x, self.p0y, self.p1x, self.p1y)
		#self.camera.shutter_speed = 190000
		#self.camera.iso = 800
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
		print('Encendi Camara de Forma Exitosa en ' + self.saveDir)

	def encenderCamara(self):
		self.eyesOpen = True

	def apagarCamara(self):
		self.eyesOpen = False
		print('Realizada las capturas, cerrando ojos...')
	

	def writter(self):
		#while not input_queue.empty:
		self.frame_number = 0
		while self.frame_number < self.maxCapturas:
			print('GUARDADO en: '+ self.saveDir+'/{}-{}.png'.format(self.fechaInfraccion[:-3], self.frame_number))
			#yield "image%02d.jpg" % frame
			
			yield self.saveDir+"/{}-{}.png".format(self.fechaInfraccion, self.frame_number)
			#yield "./imagen_{}.jpg".format(self.frame_number)
			self.frame_number += 1

	def start(self):
		start = time.time()
		self.camera.capture_sequence(self.writter(), format='png', use_video_port=True, resize=(self.scale_factor_in_X, self.scale_factor_in_Y))
		finish = time.time()
		self.eyesOpen = False
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

