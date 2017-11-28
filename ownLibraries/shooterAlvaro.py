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
		programaPrincipalCorriendo = multiprocessing.Value('i',1)
		numeroImagenes = multiprocessing.Value('i',0)
		self.root = root
		date = datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S')
		nombreCarpeta = multiprocessing.Value('c', ctypes.create_unicode_buffer(date))
		procesoParalelo = multiprocessing.Process(target = procesadoParalelo, args = (programaPrincipalCorriendo,numeroImagenes, fecha))
		procesoParalelo.start()

	def encenderCamaraEnSubDirectorio(self,nombreFolder):
		nombreCarpeta.value = nombreFolder
		numeroImagenes.value = numeroImagenes.value + 2
		return self

	def apagarCamara(self):
		numeroImagenes.value = 0
		return self
	def apagarControlador(self):
		programaPrincipalCorriendo = multiprocessing.Value('i',0)
		procesoParalelo.join()

	def procesadoParalelo(self,programaPrincipal,numeroImagen,fecha):
		#if os.uname()[1] == 'alvarohurtado-305V4A':
		miCamara = Shooter()
		while programaPrincipal.value == 1:
			if numeroImagen.value > 0:
				folder, fecha = '.', fecha
				miCamara.encenderCamaraEnSubDirectorio(folder, fecha)
				numeroImagen.value = numeroImagen.value -1



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

