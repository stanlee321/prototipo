#!/usr/bin/env python
# semaforo como clase

import os
import cv2
import time
import ctypes
import datetime
import threading
import multiprocessing
from .shooterv8 import Shooter


class ControladorCamara():
	def __init__(self):
		# Se declaran las variables de control con el proceso paralelo
		self.programaPrincipalCorriendo = multiprocessing.Value('i',1)
		self.capture = False
		self.input_q = multiprocessing.Queue(maxsize = 3)
		self.procesoParalelo = multiprocessing.Process(target = self.procesadoParalelo, args = (self.input_q,))
		self.procesoParalelo.start()
	def encenderCamaraEnSubDirectorio(self, nombreFolderWORKDIR = 'WORKDIR', nombreFoldertoSave):
		date = datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S')
		self.capture = True
		self.input_q.put([nombreFolderWORKDIR, self.capture, date, nombreFoldertoSave])
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
			data = input_q.get()
			folder_demo, capture, date, folder = data[0], data[1], data[2], data[3]
			if capture == True:
				miCamara.encenderCamaraEnSubDirectorio(folder_demo, date, folder)

if __name__ == '__main__':
	#DEMO DEMO DEMO 

	shoot = ControladorCamara()
	counter = 0
	eyes = False

	while True:
		counter +=1 
		if counter == 10:
			eyes = not eyes
			shoot.encenderCamaraEnSubDirectorio('WORKDIR', 'Destiny')
			counter = 0
			#main()
		print(counter)
		time.sleep(1)

