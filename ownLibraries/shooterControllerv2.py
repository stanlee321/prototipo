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
import pandas as pd

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
		self.procesoParalelo.start()

		# Create initial dataframe

		# Get WORDIR route
		self.path_to_work = os.getenv('HOME')+'/'+ 'WORKDIR' + '/'
		# Create Dataframe, setting None as init condition
		frame = {'WORKDIR_IMG': ['WORKDIR'], 'SAVE_IMG_IN': ['None'], 'INDEX': ['XX']}
		self.dataframe = pd.DataFrame(frame)	

		# Save Dataframe to the WorkDir Route as metadata.csv
		self.dataframe.to_csv(self.path_to_work + 'metadata.csv', index=False)

	def encenderCamaraEnSubDirectorio(self, nombreFoldertoSave):
		self.nombreFoldertoSave = nombreFoldertoSave

		date = datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S')
		index = date.split(':')[-1]

		self.dataframe.INDEX = str(index)
		self.dataframe.SAVE_IMG_IN = nombreFoldertoSave
		self.dataframe.to_csv(self.path_to_work + 'metadata.csv', index=False)

		return self

	def apagarCamara(self):
		self.capture = False
		return self
	def apagarControlador(self):
		programaPrincipalCorriendo = multiprocessing.Value('i',0)
		self.procesoParalelo.join()

	def procesadoParalelo(self, input_q):
		#if os.uname()[1] == 'alvarohurtado-305V4A':
		miCamara = Shooter()
		while self.programaPrincipalCorriendo.value == 1:
			miCamara.start()


			path_to_metadata = os.getenv('HOME')+'/'+ 'WORKDIR' + '/' + 'metadata.csv'
			# Read metadata
			metadata = pd.read_csv(path_to_metadata)
			folder = metadata.SAVE_IMG_IN[0]
			index = str(metadata.INDEX[0])
			# Read datetime
			date = datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S')
			print('folder is >>>>>', folder)
			print('Index is >>>>>', index )

			if folder != 'None':
				miCamara.encenderCamaraEnSubDirectorio('WORKDIR', date, folder, index)


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