#!/usr/bin/env python
# semaforo como clase

import os
import cv2
import time
import ctypes
import datetime
import threading
import multiprocessing
from shooterv9 import Shooter


class ControladorCamara():
	def __init__(self):
		# Se declaran las variables de control con el proceso paralelo
		self.programaPrincipalCorriendo = multiprocessing.Value('i',1)
		self.capture = False
		self.nombreFolderWORKDIR = 'WORKDIR'
		self.input_q = multiprocessing.Queue(maxsize = 10)
		self.procesoParalelo = multiprocessing.Process(target = self.procesadoParalelo, args = (self.input_q,))
		self.procesoParalelo.start()
	def encenderCamaraEnSubDirectorio(self, nombreFoldertoSave):
		date = datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S')
		self.capture = True
		try: 
			self.input_q.put([self.nombreFolderWORKDIR, self.capture, date, nombreFoldertoSave],False)
		except Exception as e:
			print('SLOT AVAILABLE!!! Size: '+str(self.input_q.qsize())+' '+str(e))
		return self

	def apagarCamara(self):
		self.capture = False
		return self
	def apagarControlador(self):
		programaPrincipalCorriendo = multiprocessing.Value('i',0)
		self.procesoParalelo.join()

	def procesadoParalelo(self,input_q):
		#if os.uname()[1] == 'alvarohurtado-305V4A':
		miCamara = Shooter()
		while self.programaPrincipalCorriendo.value == 1:
			#print('inside while the value is', self.programaPrincipalCorriendo.value )
			data = input_q.get()
			folder_demo, capture, date, folder = data[0], data[1], data[2], data[3]
			miCamara.start()
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
			shoot.encenderCamaraEnSubDirectorio('Destiny')
			counter = 0
		print(counter)
		time.sleep(1)

