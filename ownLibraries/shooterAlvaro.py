#!/usr/bin/env python
# semaforo como clase

import os
import cv2
import time
import ctypes
import datetime
import threading
import multiprocessing
from shooterv6 import Shooter
import ctypes


class ControladorCamara():
	def __init__(self, root ='.'):
		# Se declaran las variables de control con el proceso paralelo
		self.programaPrincipalCorriendo = multiprocessing.Value('i',1)
		#numeroImagenes = multiprocessing.Value('i',0)
		self.numeroImagenes = 0
		self.root = root
		self.date = datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S')
		self.input_q = multiprocessing.Queue(maxsize = 3)
		#nombreCarpeta = multiprocessing.Value('c', ctypes.create_unicode_buffer(date))
		self.procesoParalelo = multiprocessing.Process(target = self.procesadoParalelo, args = (self.input_q,))
		self.procesoParalelo.start()

	def encenderCamaraEnSubDirectorio(self,nombreFolder):
		self.numeroImagenes += 2
		self.input_q.put([nombreFolder, self.numeroImagenes])
		#nombreCarpeta.value = nombreFolder
		#numeroImagenes.value = numeroImagenes.value + 2
		return self

	def apagarCamara(self):
		#numeroImagenes.value = 0
		self.numeroImagenes = 0
		return self
	def apagarControlador(self):
		programaPrincipalCorriendo = multiprocessing.Value('i',0)
		self.procesoParalelo.join()

	def procesadoParalelo(self,input_q):
		#if os.uname()[1] == 'alvarohurtado-305V4A':
		miCamara = Shooter()
		while self.programaPrincipalCorriendo.value == 1:
			numeroImagen, fecha = input_q.get()
			folder = '.'

			if numeroImagen > 0:
				miCamara.encenderCamaraEnSubDirectorio(folder, fecha)
				numeroImagen = numeroImagen -1



if __name__ == '__main__':
	#DEMO DEMO DEMO 

	shoot = ControladorCamara()
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

