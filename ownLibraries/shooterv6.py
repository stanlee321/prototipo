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

		# PICMEARA INIT

		self.camera = picamera.PiCamera()
		#self.camera.resolution = (3240,2464)
		self.camera.resolution = (self.width,self.height)
		self.camera.framerate = 1
		self.camera.start_preview()

		self.input_q = multiprocessing.Queue(maxsize = 4)

		process = multiprocessing.Process(target = self.start, args=((self.input_q,)))
		process.daemon = True
		pool = multiprocessing.Pool(4, self.start, (self.input_q,))


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
		#self.eyesOpen = True
		self.feed(self.input_q)
		print('Encendi Camara de Forma Exitosa en ' + self.saveDir)

	def encenderCamara(self):
		#self.miReporte.moverRegistroACarpeta(fecha)
		self.eyesOpen = True

	def apagarCamara(self):
		self.eyesOpen = False
		print('Realizada las capturas, cerrando ojos...')
	

	def writter(self, data):
		#while not input_queue.empty:
		saveDir, fechaInfraccion, maxCapturas, frame_number = data[0], data[1], data[2]
		frame_number = 0
		while frame_number < maxCapturas:
			print('GUARDADO en: '+ saveDir+'/{}-{}.jpg'.format(self.fechaInfraccion[:-3], frame_number))
			#yield "image%02d.jpg" % frame
			yield saveDir+"/{}-{}.jpg".format(fechaInfraccion, frame_number)
			#yield "./imagen_{}.jpg".format(self.frame_number)
			frame_number += 1
	def start(self, input_q):
		data = input_q.get()
		while True:
			start = time.time()
			self.camera.capture_sequence(self.writter(data), use_video_port=True)
			finish = time.time()
			self.eyesOpen = False
			print("Captured %d frames at %.2ffps" % (self.maxCapturas,self.maxCapturas / (finish - start)))
	def feed(self, input_q):
		input_q.put([self.saveDir, self.fechaInfraccion, self.maxCapturas, self.frame_number])
		return self

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