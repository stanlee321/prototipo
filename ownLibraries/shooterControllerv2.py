#!/usr/bin/env python
# semaforo como clase

import os
import cv2
import time
import ctypes
import datetime
import threading
import multiprocessing
from .shooterv9 import Shooter
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
		#self.aux_queue = multiprocessing.Queue()
		date = datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S')

		self.procesoParalelo = multiprocessing.Process(target = self.procesadoParalelo, args = (self.ilive,))
		self.procesoParalelo.start()

		# Create initial dataframe

		# Get WORDIR route
		self.path_to_work = os.getenv('HOME')+'/'+ 'WORKDIR' + '/'
		# Create Dataframe, setting None as init condition
		frame = {'WORKDIR_IMG': ['WORKDIR'], 'SAVE_IMG_IN': [date], 'INDEX': ['XX'], 'STATUS':['CLOSED']}
		dataframe = pd.DataFrame(frame)	

		# Save Dataframe to the WorkDir Route as metadata.csv
		dataframe.to_csv(self.path_to_work + 'metadata.csv', index=False, sep=',')

	def encenderCamaraEnSubDirectorio(self, nombreFoldertoSave):
		print('En ShooterControllerv2 resivo nombre de archivo : ', nombreFoldertoSave)

		# Read old metadata
		path_to_metadata = os.getenv('HOME')+'/'+ 'WORKDIR' + '/' + 'metadata.csv'
		old_metadata = pd.read_csv(path_to_metadata)

		# For get the frame inside of the yield loop
		date = datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S')
		index = date.split(':')[-1]


		# Create new row
		row = {'WORKDIR_IMG': ['WORKDIR'], 'SAVE_IMG_IN': [nombreFoldertoSave], 'INDEX': [str(index)], 'STATUS':['OPEN']}
		new_row = pd.DataFrame(row)

		# Append new row to old metadata
		new_metadata = pd.concat([old_metadata, new_row])
		new_metadata.to_csv(path_to_metadata, index=False, sep=',')

		print('METADATA LISTO PARA SER GURADADO', new_metadata.head())
		return self

	def apagarCamara(self):
		self.capture = False
		return self
	def apagarControlador(self):
		programaPrincipalCorriendo = multiprocessing.Value('i',0)
		self.procesoParalelo.join()

	def procesadoParalelo(self, ilive):
		#if os.uname()[1] == 'alvarohurtado-305V4A':
		miCamara = Shooter()
		while self.programaPrincipalCorriendo.value == 1:

			miCamara.start()
			# Read metadata
			path_to_metadata = os.getenv('HOME')+'/'+ 'WORKDIR' + '/' + 'metadata.csv'
			try:
				metadata = pd.read_csv(path_to_metadata)
			except:
				print('io prblem in read_csv, creating default dframe')
				dframe = {'WORKDIR_IMG': ['WORKDIR'], 'SAVE_IMG_IN': ['None'], 'INDEX': ['XX'],'STATUS':['OPEN']}
				metadata = pd.DataFrame(dframe)
			

			date = datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S')
			folder = metadata.SAVE_IMG_IN.values[-1]
			index = str(metadata.INDEX.values[-1])
			status = metadata.STATUS.values[-1]

			if  status != 'CLOSED':
				miCamara.encenderCamaraEnSubDirectorio('WORKDIR', date, folder, index)


if __name__ == '__main__':
	#DEMO DEMO DEMO 
	import numpy as np
	import datetime
	shoot = ControladorCamara()
	mask = np.zeros((320,320))
	mask = mask.astype(np.uint8)

	while True:

		date =  datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S')
		#folder_raiz = date.split('_')[0]
		#folder = date.split('_')
		#path = folder_raiz + '/' + folder
		cv2.putText(mask, 'press s to capture photos in ./Destiny folder', (10, mask.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
		cv2.imshow('mask for test', mask)
		if cv2.waitKey(1) & 0xFF == ord("s"):
			shoot.encenderCamaraEnSubDirectorio(date)
		if cv2.waitKey(1) & 0xFF == ord("q"):
			break