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
import os

class ControladorCamara():
	def __init__(self):
		# Se declaran las variables de control con el proceso paralelo
		self.programaPrincipalCorriendo = multiprocessing.Value('i',1)
		self.capture = False # Start saving to this from the creation of the object
		self.nombreFolderWORKDIR = 'WORKDIR'
		self.nombreFoldertoSave = None
		self.date = None
		self.ilive = True
		self.input_q = multiprocessing.Queue(maxsize = 5)
		#self.aux_queue = multiprocessing.Queue()

		self.procesoParalelo = multiprocessing.Process(target = self.procesadoParalelo, args = (self.input_q,))
		self.procesoParalelo2 = multiprocessing.Process(target = self.feed_queue, args = (self.ilive, self.nombreFoldertoSave, self.input_q,))
		self.procesoParalelo.start()
		self.procesoParalelo2.start()

	def encenderCamaraEnSubDirectorio(self, nombreFoldertoSave):
		self.capture = True
		self.nombreFoldertoSave = nombreFoldertoSave
		os.makedirs(os.getenv('HOME')+'/'+ 'WORKDIR' + '/' + 'PRUEBAS' + '/' + self.nombreFoldertoSave)
		print('creadted auxiliar folder ... in : ', os.getenv('HOME')+'/'+ 'WORKDIR' + '/' + 'PRUEBAS' + '/' + self.nombreFoldertoSave)
		#try:
		#	self.aux_queue.put([self.ilive, self.nombreFoldertoSave])
		#except Exception as e:
		#	print('SLOT AVAILABLE!!! Size: '+str(self.aux_queue.qsize())+' '+str(e))

		#try: 
		#	self.input_q.put([self.nombreFolderWORKDIR, self.capture, date, nombreFoldertoSave], False)
		#except Exception as e:
		#	print('SLOT AVAILABLE!!! Size: '+str(self.input_q.qsize())+' '+str(e))
		#return self
		#self.feed_queue(True, self.nombreFoldertoSave, self.input_q)

	def apagarCamara(self):
		self.capture = False
		return self
	def apagarControlador(self):
		programaPrincipalCorriendo = multiprocessing.Value('i',0)
		self.procesoParalelo.join()

	def feed_queue(self,ilive, nombredelFolder, input_q):

		while True:
			#if aux_queue.empty() != True:
			#	data = aux_queue.get()
			#	ilive , nombreFoldertoSave = data[0], data[1]
			#	print('ilive:', ilive)
			#	print('nobmreddelFolder is:', nombreFoldertoSave)
			#	nombredelFolder = nombreFoldertoSave
			#else:
			#	pass

			input_q.put(['WORKDIR', True, date, nombredelFolder])

	def procesadoParalelo(self, input_q):
		#if os.uname()[1] == 'alvarohurtado-305V4A':
		miCamara = Shooter()
		#while self.programaPrincipalCorriendo.value == 1:
		while True:
			# Capturing in workdir *.jpg's
			miCamara.start()
			#data = input_q.get()
			#print('HI im in procesadoParalelo')
			#folder_demo, capture, date, folder = data[0], data[1], data[2], data[3]

			path = os.getenv('HOME')+'/'+ 'WORKDIR' + '/' + 'PRUEBAS' + '/'
			folder = [os.path.join(root, name) for root, dirs, files in os.walk(path)][-1]
			date = datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S')
			print('folder is>>>>>', folder)
			if folder != 'None':
				miCamara.encenderCamaraEnSubDirectorio('WORKDIR', date, folder)
				folder = 'None'

if __name__ == '__main__':
	#DEMO DEMO DEMO 
	import numpy as np

	shoot = ControladorCamara()
	mask = np.zeros((320,320))
	mask = mask.astype(np.uint8)

	while True:

		cv2.putText(mask, 'press s to capture photos in ./Destiny folder', (10, mask.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
		cv2.imshow('mask for test', mask)
		if cv2.waitKey(1) & 0xFF == ord("s"):
			shoot.encenderCamaraEnSubDirectorio('Destiny')
		if cv2.waitKey(1) & 0xFF == ord("q"):
			break