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
from shooterv10 import Shooter
import sqlite3

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
		#frame = {'WORKDIR_IMG': ['WORKDIR'], 'SAVE_IMG_IN': [date], 'INDEX': [], 'STATUS':['CLOSED']}
		#dataframe = pd.DataFrame(frame)	

		# Save Dataframe to the WorkDir Route as metadata.csv
		#dataframe.to_csv(self.path_to_work + 'metadata.csv', index=False, sep=',')


		# Create Initial SQLITE3 database
		conn = sqlite3.connect(self.path_to_work + 'shooter_database.db')
		c =  conn.cursor()

		self.create_table(c)
		self.dynamic_data_entry(c, conn, 'WORKDIR', str(date), 'XX', 'CLOSED')


	def create_table(self, c):
		# Create table with default values as:

		# WORKDIR, dir where to start to work
		# SAVE_IMG_IN, dir where to copy the images from WORKDIR
		# INDEX, don't remember xD
		# STATUS, took pictures or not status
		c.execute('CREATE TABLE IF NOT EXISTS shooter_table(WorkDir TEXT,Save_img_in TEXT,Idx TEXT,Status TEXT)')

	def dynamic_data_entry(self, c, conn, workdir, save_img_in, index, status):

		WORKDIR = workdir
		SAVE_IMG_IN = save_img_in
		INDEX = str(index)
		STATUS = status
		c.execute("INSERT INTO  shooter_table(WorkDir, Save_img_in, Idx, Status) VALUES (?,?,?,?)",\
			(WORKDIR, SAVE_IMG_IN, INDEX, STATUS))
		conn.commit()
		

		# Close coneccions
		c.close()
		conn.close()


	def encenderCamaraEnSubDirectorio(self, nombreFoldertoSave):
		#print('En ShooterControllerv2 resivo nombre de archivo : ', nombreFoldertoSave)

		# Read old metadata
		path_to_metadata = os.getenv('HOME')+'/'+ 'WORKDIR' + '/' + 'shooter_database.db'
		workdir = 'WORKDIR'
		save_img_in = nombreFoldertoSave

		# For get the frame inside of the yield loop
		date = datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S')
		index = str(date.split(':')[-1]) # MOST IMPORTANT FOR SYNC WITH THE PARALLEL PROCESS

		# Took or not captures from pi camera
		status = 'OPEN'

		# Init DB
		conn = sqlite3.connect(path_to_metadata)
		c =  conn.cursor()
		self.create_table(c)

		# UPDATE NEW ROW
		# Append new row to old metadata and close connection
		self.dynamic_data_entry(c, conn, workdir, save_img_in, index, status)


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

		# Load the state of the While loop
		path_to_run = os.getenv('HOME')+'/'+ 'WORKDIR' + '/' + 'run_camera.npy'
		run_camera = np.load(path_to_run)
		while run_camera == 1:
			miCamara.start()
			# Read metadata
			path_to_metadata = os.getenv('HOME')+'/'+ 'WORKDIR' + '/' + 'shooter_database.db'
			path_to_run = os.getenv('HOME')+'/'+ 'WORKDIR' + '/' + 'run_camera.npy'
			try:
				# Init DB
				conn = sqlite3.connect(path_to_metadata)
				c =  conn.cursor()
				#c.execute("SELECT * FROM stufftoPlot WHERE value=3 AND keyword='Python'")
				#c.execute("SELECT keyword,unix,value FROM stufftoPlot WHERE unix >1515634491")
				c.execute("SELECT * FROM shooter_table ORDER BY Save_img_in DESC LIMIT 1 ")
				#data = c.fetchone()
				data = c.fetchall()
				for row in data:
					print(row)
					print(type(data))
					metadata = list(data)
					print('metadatta is', metadata)
				c.close()
				conn.close()


				#with open(path_to_metadata) as f:
				#    metadata = csv.reader(f)
				    #metadata = pd.read_csv(path_to_metadata)
			except Exception as e:
				print('<<DB 1 ERROR>> I cant open or read the DB by this erro:', e)
				#print('io prblem in read_csv, creating default dframe')
				#dframe = {'WORKDIR_IMG': ['WORKDIR'], 'SAVE_IMG_IN': ['None'], 'INDEX': ['XX'],'STATUS':['OPEN']}
				#metadata = pd.DataFrame(dframe)
			date = datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S')
			folder = metadata[0][1]
			index  = metadata[0][2]
			status = metadata[0][3]
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