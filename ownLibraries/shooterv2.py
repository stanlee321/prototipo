#!/usr/bin/env python
# semaforo como clase

import os
import cv2
import time
import datetime
import threading
import multiprocessing
from multiprocessing import Process, Queue, Value, Pool

class Shooter():
	""" General PICAMERA DRIVER Prototipe
	"""
	directorioDeTrabajo = os.getenv('HOME')+'/casosReportados'
	date_hour_string = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S-%f')

	def __init__(self, video_source = 0, width = 2592, height = 1944, cutPoly=([0,0],[2592,1944])):
	#def __init__(self, video_source = 0, width = 680, height = 420, cutPoly=([0,0],[200,200]), saveDir='./test/'):


		self.eyesOpen = False
		self.state = 'rojo'
		# Initial aparemeters
		self.video_source = video_source
		self.width = width		# Integer Like
		self.height = height	# Integer Like
		self.counter  = 0
		self.maxCapturas = 3
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
		self.imagenes_and_state = Queue()
		self.buffer_of_placas = RingBuffer(6)

		self.thread = Process(target=self.start, args=())
		self.thread.daemon = True									# Daemonize thread
		self.thread.start() 
		#self.thread.join()
		#pool = Pool(2, self.start)
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
		self.eyesOpen = True
		print('Camara Encendida')

	def apagarCamara(self):
		self.eyesOpen = False
		print('Camara Apagada')
	def semphstate(self, state):
		self.state = state
	
	def writter(self, input_q):
		imagen, state = input_q.get()
		while state == 'verde':
			placaActual = placa[self.primerPunto[1]:self.segundoPunto[1], self.primerPunto[0]: self.segundoPunto[0]]
			print('GUARDADO en: '+ self.saveDir+'/{}-{}.jpg'.format(self.fechaInfraccion[:-3],self.counter))
			cv2.imwrite(self.saveDir+'/{}-{}.jpg'.format(self.fechaInfraccion,self.counter), self.buffer_of_placas.get())

		print('appendando imagnes to buffer_of_placas')
		self.buffer_of_placas.append(imagen.get())
		print('buffer of placas', len(self.buffer_of_placas))

	def start(self):
		print('started....')
		self.counter += 1
		while True:
			print('hello')
			if self.eyesOpen == True:
				# Init PICamera
				self.video_capture = cv2.VideoCapture(self.video_source)
				self.video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
				self.video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)

				for captura in range(self.maxCapturas):
					# Read plate
					_, placa = self.video_capture.read()
					self.imagenes_and_state.put(placa, self.state)
					self.counter += 1	
					#time.sleep(.05)
					if self.eyesOpen  == False :# self.counter > self.maxCounter:
						print('>>> Closing Eyes....')
						self.eyesOpen = False
						self.video_capture.release()
						self.counter = 0
				# Reset parameters
				self.eyesOpen = False
				self.counter = 0
				self.video_capture.release()

				
			elif self.eyesOpen == False:
				print('actually eyes closed')
				self.writter(self.imagenes_and_state)
				#self.miReporte.info('passing..')
				#time.sleep(1)
				#pass
		else:
			print('wtf we r doing')

		#self.thread = threading.Thread(target=self.start, args=())
		#self.thread.daemon = True									# Daemonize thread
		#self.thread.start()


class RingBuffer:
    """ class that implements a not-yet-full buffer """
    def __init__(self,size_max):
        self.max = size_max
        self.data = []

    class Full:
        """ class that implements a full buffer """
        def append(self, x):
            """ Append an element overwriting the oldest one. """
            self.data[self.cur] = x
            self.cur = (self.cur+1) % self.max
        def get(self):
            """ return list of elements in correct order """
            return self.data[self.cur:]+self.data[:self.cur]

    def append(self,x):
        """append an element at the end of the buffer"""
        self.data.append(x)
        if len(self.data) == self.max:
            self.cur = 0
            # Permanently change self's class from non-full to full
            self.__class__ = self.Full

    def get(self):
        """ Return a list of elements from the oldest to the newest. """
        return self.data




if __name__ == '__main__':
	
	shoot = Shooter()
	counter = 0
	eyes = False
	state = 'rojo'
	#def main():
	#	shoot = Shooter()

	while True:
		counter +=1 
		if counter == 5:
			print('into simulated process...')
			shoot.eyesOpen = not eyes
			shoot.semphstate = 'verde'
			eyes = not eyes
			counter = 0
		print(shoot.counter)
		time.sleep(1)
	
