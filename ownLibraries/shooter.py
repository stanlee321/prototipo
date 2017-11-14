#!/usr/bin/env python
# semaforo como clase

import os
import cv2
import time
import datetime
import threading
import multiprocessing

class Shooter():
	""" General PICAMERA DRIVER Prototipe
	"""
	directorioDeTrabajo =os.getenv('HOME')+'/casosReportados'
	date_hour_string = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S-%f')

	def __init__(self, video_source = 0, width = 2592, height = 1944, cutPoly=([0,0],[2592,1944])):
	#def __init__(self, video_source = 0, width = 680, height = 420, cutPoly=([0,0],[200,200]), saveDir='./test/'):
		#self.miReporte = MiReporte(levelLogging=10)
		#self.miReporte.info( 'Starting the  PiCam')
		#print('Cree objeto de forma exitosa')
		self.eyesOpen = False
		# Initial aparemeters
		self.video_source = video_source
		self.width = width		# Integer Like
		self.height = height	# Integer Like
		self.counter  = 0
		self.maxCounter = 2
		# FOR ROI
		self.cutPoly = cutPoly 	# ARRAY like (primerPunto, segundoPunto)
		self.primerPunto = self.cutPoly[0] 				# Array like [p0,p1]
		self.segundoPunto = self.cutPoly[1]				# Array like [p0,p1]

		# Dir where to save images
		
		self.directorioDeGuardadoGeneral = self.directorioDeTrabajo
		self.fechaInfraccion = self.date_hour_string
		self.saveDir = self.directorioDeGuardadoGeneral +"/"+self.fechaInfraccion
		self.segundo_milisegundo = datetime.datetime.now().strftime('%S.%f')
		
		#self.video_capture = WebcamVideoStream(src=self.video_source, width=self.width, height=self.height).start()

		#self.thread = multiprocessing.Process(target=self.start, args=())
		self.thread = threading.Thread(target=self.start, args=())
		self.thread.daemon = True									# Daemonize thread
		self.thread.start() 
		print('EXITOSAMENTE CREE LA CLASE SHOOTER')

	def establecerRegionInteres(self,cutPoly):
		self.cutPoly = cutPoly

	def encenderCamaraEnSubDirectorio(self,folder,fecha):
		#self.miReporte.moverRegistroACarpeta(fecha)
		self.fechaInfraccion =fecha
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
	
	def start(self):
		time.sleep(0.01)
		print('<<<<<<<<<INTO???? while???,>>>>>>>>>> ', self.eyesOpen)

		if self.eyesOpen == True:
			print('self.eyesOpen', self.eyesOpen)
			#self.miReporte.info('Iam in')
			self.video_capture = cv2.VideoCapture(self.video_source)
			self.video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
			self.video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
			_, placa = self.video_capture.read()
			print('placashape??', placa.shape)
			while True:
				# Read plate
				_, placa = self.video_capture.read()
				print('PLACA SHAPE', placa.shape)
				placaActual = placa[self.primerPunto[1]:self.segundoPunto[1], self.primerPunto[0]: self.segundoPunto[0]]
				self.miReporte.info('VER AQUI: ',self.saveDir+'/{}_{}.jpg'.format(self.fechaInfraccion,self.counter))
				print('GUARDADO en: '+self.saveDir+'/{}-{}.jpg'.format(self.fechaInfraccion[:-3],self.counter))
				#cv2.imwrite(self.saveDir+'/{}-{}.jpg'.format(self.fechaInfraccion,self.counter), placaActual)
				#cv2.imshow('CAPTURADO',cv2.resize(placaActual,(placaActual.shape[1]//2,placaActual.shape[0]//2))) 
				self.counter += 1	
				#  If Self.run is False everything starts to stop and close
				time.sleep(.05)
				print('self.counter', self.counter, '>??', self.maxCounter)
				print('self.eyesOpen', self.eyesOpen)
				if self.eyesOpen  == False or self.counter > self.maxCounter :# self.counter > self.maxCounter:
					self.eyesOpen = False
					self.video_capture.release()
					self.counter = 0
					#print('APAGADO AUTOMATICO')
					#self.miReporte.info(' Ending all the program...')
					break
			
		if self.eyesOpen == False:
			#self.miReporte.info('passing..')
			#time.sleep(1)
			pass
		
		self.thread = threading.Thread(target=self.start, args=())
		self.thread.daemon = True									# Daemonize thread
		self.thread.start()

		#self.miReporte.info('Doing something imporant in the background')

"""

DEMO DEMO DEMO 


shoot = Shooter()
counter = 0
eyes = False

#def main():
#	shoot = Shooter()



if __name__ == '__main__':
	while True:
		self.miReporte.info('Eyes Open?', shoot.eyesOpen)
		self.miReporte.info('COunter: ', counter)
		counter +=1 
		if counter == 5:
			shoot.eyesOpen = not eyes
			eyes = not eyes
			counter = 0
			#main()
		time.sleep(1)

"""