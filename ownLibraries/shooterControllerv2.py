#!/usr/bin/env python
# semaforo como clase

import os
import cv2
import time
import ctypes
import datetime
import threading
import pandas as pd
import multiprocessing
import numpy as np
from .shooterv9 import Shooter

class ControladorCamara():
	def __init__(self):
		# Se declaran las variables de control con el proceso paralelo
		#self.programaPrincipalCorriendo = multiprocessing.Value('i',1)
		self.capture = False # Start saving to this from the creation of the object
		self.nombreFolderWORKDIR = 'WORKDIR'
		# Path for run the while loop, values  0 or 1
		self.path_to_run_camera = os.getenv('HOME')+'/'+ 'WORKDIR' + '/' + 'run_camera.npy'
		np.save(self.path_to_run_camera, 1)
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

	def encenderCamaraEnSubDirectorio(self, rutahaciaFoldertoSave):
		#print('En ShooterControllerv2 resivo nombre de archivo : ', nombreFoldertoSave)
		nombreFoldertoSave = rutahaciaFoldertoSave.split('/')[-1]
		print('En ShooterControllerv3 resivo la ruta : ', rutahaciaFoldertoSave)
		print('Se esta guardando la imagen en :',nombreFoldertoSave )
		
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

		return self

	def apagarCamara(self):
		self.capture = False
		self.procesoParalelo.join()
		return self
	def apagarControlador(self):
		#print('2.- Estoy dentro del apagarControlador, el estado es:')
		# Order to stop the while loop process
		print('Resived Signal to Shutdown the picamera...')
		np.save(self.path_to_run_camera, 0)
		self.procesoParalelo.join()
		return self

	def procesadoParalelo(self, ilive):
		#if os.uname()[1] == 'alvarohurtado-305V4A':
		print('Aqui solo entro una sola vez')
		miCamara = Shooter()
		path_to_run = os.getenv('HOME')+'/'+ 'WORKDIR' + '/' + 'run_camera.npy'
		run_camera = np.load(path_to_run)
		while run_camera == 1:
			miCamara.start()
			# Read metadata
			path_to_metadata = os.getenv('HOME')+'/'+ 'WORKDIR' + '/' + 'metadata.csv'
			path_to_run = os.getenv('HOME')+'/'+ 'WORKDIR' + '/' + 'run_camera.npy'
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

			# Load status to run the camera or exit from this while loop
			try:
				run_camera = np.load(path_to_run)
				#print('Signal to run is', run_camera)
			except Exception as e:
				print('I cant read exit by this reason:', e)

		print('Saliendo del While Loop en ShooterControllerv2')
		print('>>Picamera OFF<<')

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