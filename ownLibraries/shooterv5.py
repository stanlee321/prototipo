#!/usr/bin/env python
# semaforo como clase

import os
import cv2
import time
import datetime
import threading
import multiprocessing

from picamera.array import PiRGBArray
from picamera import PiCamera
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

	def __init__(self, video_source = 0, width = 3280, height = 2464, cutPoly=([0,0],[1640,1200]), capturas = 3):
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
		#self.input_q = multiprocessing.Queue(maxsize = 4)
		self.input_q = []
		process = multiprocessing.Process(target = self.writter, args=((self.input_q,)))
		process.daemon = True
		self.pool = multiprocessing.Pool(4, self.writter, (self.input_q,))
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
		#while not input_queue.empty:
		while True:
			try:

				print('input queue is ...', input_queue)
				#data = input_queue.get()
				data, numero_de_captura = input_queue[0], input_queue[1]
				#placa, numero_de_captura, saveDir, fechaInfraccion  = data[0], data[1], data[2], data[3]
				#print('GUARDADO en: '+ saveDir+'/{}-{}.jpg'.format(fechaInfraccion[:-3], numero_de_captura))
				#cv2.imwrite(saveDir+'/{}-{}.jpg'.format(fechaInfraccion, numero_de_captura), placa)
				t1 = time.time()
				#cv2.imwrite('./imagen_{}.jpg'.format(numero_de_captura), placa, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
				cv2.imwrite('./imagen_{}.jpg'.format(numero_de_captura), input_queue)
				#imsave('./imagen_{}.jpg'.format(numero_de_captura), placa)
				#scipy.misc.imsave('./imagen_{}.jpg'.format(numero_de_captura), placa)
				t2 = time.time()
				print('WRTIE TOOK: ', t2-t1)
			except:
				pass

	def start(self):
		if self.eyesOpen == True:
			t10 = time.time()
			#self.miReporte.info('Iam in')
			#self.video_capture = PiVideoStream(resolution=( self.width, self.height),framerate=32).start() 
			camera = PiCamera()
			camera.resolution = (self.width, self.height)
			camera.framerate = 5
			rawCapture = PiRGBArray(camera, size=(self.width, self.height))
			stream = camera.capture_continuous(rawCapture, format="bgr", use_video_port=True)
			captura = 0
			for (i, frame) in enumerate(stream):
				t1 = time.time()
				print('captura Numero: ', captura)
				# Read plate
				placa = frame.array

				t2 = time.time()
				print('read placa took: ', t2-t1)
				print('placa Inputshape: ', placa.shape)
				t3 = time.time()
				placaActual = placa[self.primerPunto[1]: self.segundoPunto[1], self.primerPunto[0]: self.segundoPunto[0]]
				t4 = time.time()
				print('Cutting took,: ', t4-t3)

				t5 = time.time()
				#self.input_q.put((placaActual, captura, self.saveDir, self.fechaInfraccion))
				self.input_q.append((placa,i))
				t6 = time.time()
				print('put took, ', t6-t5 )

				t7 = time.time()
				rawCapture.truncate(0)
				t8 = time.time()
				print('Truncate took', t8-t7)
				#  If Self.run is False everything starts to stop and close
				#if self.eyesOpen  == False: # self.counter > self.maxCounter:
				#	self.eyesOpen = False
				#	self.video_capture.release()
				captura += 1
				if captura == self.maxCapturas:
					self.pool.map(self.writter, self.input_q)
					self.input_q = []
					break
				else:
					pass
			print('finish limit of captures, releasing...')
			self.eyesOpen = False
			#self.video_capture.release()
			stream.close()
			rawCapture.close()
			camera.close()
			t11 = time.time()

			print('ALL TOOK<<<>>> : ', t11-t10)
			"""
			while True:
				if self.video_capture.grab() == False:
					print('Camera sucessfully released ...!')
					break
				else:
					print('Releasing camera....')
					self.video_capture.release()
			#else:
			#	self.video_capture.release()
			"""

		if self.eyesOpen == False:

			pass
		
		self.thread = threading.Thread(target=self.start, args=())
		self.thread.daemon = True									# Daemonize thread
		self.thread.start()

		#self.miReporte.info('Doing something imporant in the background')


#DEMO DEMO DEMO 

shoot = Shooter()
counter = 0
eyes = False

#def main():
#	shoot = Shooter()



if __name__ == '__main__':
	while True:
		counter +=1 
		if counter == 10:
			shoot.eyesOpen = not eyes
			eyes = not eyes
			counter = 0
			#main()
		print(counter)
		time.sleep(1)