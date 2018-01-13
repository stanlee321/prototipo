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
import shutil

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

		# Create initial dataframe

		# Get WORDIR route
		self.path_to_work = os.getenv('HOME')+'/'+ 'WORKDIR' + '/'

		# Create Initial SQLITE3 database

		date_for_db = datetime.datetime.now().strftime('%Y-%m-%d')

		path_to_cache = self.path_to_work + 'shooter_database_{}_cache.db'.format(date_for_db)
		db_name = self.path_to_work + 'shooter_database_{}.db'.format(date_for_db)
		
		timestamp = datetime.datetime.now()
		ts = timestamp.strftime("%A %d %B %Y %I:%M:%S%p")

		conn = sqlite3.connect(db_name)
		c =  conn.cursor()

		self.create_table(c)
		self.dynamic_data_entry(c, conn, ts, 'WORKDIR', str(date), 'XX', 'CLOSED')


		conn = sqlite3.connect(path_to_cache)
		c =  conn.cursor()

		self.create_table(c)
		self.dynamic_data_entry(c, conn, ts, 'WORKDIR', str(date), 'XX', 'CLOSED')

		self.procesoParalelo = multiprocessing.Process(target = self.procesadoParalelo, args = (self.ilive,))
		self.procesoParalelo.start()


	def create_table(self, c):
		# Create table with default values as:

		# WORKDIR, dir where to start to work
		# SAVE_IMG_IN, dir where to copy the images from WORKDIR
		# INDEX, don't remember xD
		# STATUS, took pictures or not status
		c.execute('CREATE TABLE IF NOT EXISTS shooter_table(datestamp TEXT, WorkDir TEXT, Save_img_in TEXT,Idx TEXT,Status TEXT)')

	def dynamic_data_entry(self, c, conn, ts,workdir, save_img_in, index, status):
		ts = str(ts)
		WORKDIR = workdir
		SAVE_IMG_IN = save_img_in
		INDEX = str(index)
		STATUS = status
		c.execute("INSERT INTO  shooter_table(datestamp, WorkDir, Save_img_in, Idx, Status) VALUES (?,?,?,?,?)",\
			(ts,WORKDIR, SAVE_IMG_IN, INDEX, STATUS))
		conn.commit()
		

		# Close coneccions
		c.close()
		conn.close()


	def encenderCamaraEnSubDirectorio(self, rutahaciaFoldertoSave):

		nombreFoldertoSave = rutahaciaFoldertoSave.split('/')[-1]
		date_for_db = datetime.datetime.now().strftime('%Y-%m-%d')

		print('En ShooterControllerv3 resivo la ruta : ', rutahaciaFoldertoSave)
		print('Se esta guardando la imagen en :',nombreFoldertoSave )
		path_to_cache = os.getenv('HOME')+'/'+ 'WORKDIR' + '/' + 'shooter_database_{}_cache.db'.format(date_for_db)
		path_to_db = os.getenv('HOME')+'/'+ 'WORKDIR' + '/' + 'shooter_database_{}.db'.format(date_for_db)
		shutil.copy(path_to_cache, path_to_db)

		workdir = 'WORKDIR'
		save_img_in = nombreFoldertoSave

		# For get the frame inside of the yield loop
		date = datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S')
		index = str(date.split(':')[-1]) # MOST IMPORTANT FOR SYNC WITH THE PARALLEL PROCESS

		# time stamp
		timestamp = datetime.datetime.now()
		ts = timestamp.strftime("%A %d %B %Y %I:%M:%S%p")
		# Took or not captures from pi camera
		status = 'OPEN'

		# Init DB
		conn = sqlite3.connect(path_to_db)
		c =  conn.cursor()
		#self.create_table(c)

		# UPDATE NEW ROW
		self.dynamic_data_entry(c, conn, ts, workdir,timestamp, save_img_in, index, status)
		shutil.copy(path_to_db, path_to_cache)
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
		miCamara = Shooter()

		# Load the state of the While loop
		path_to_run = os.getenv('HOME')+'/'+ 'WORKDIR' + '/' + 'run_camera.npy'
		run_camera = np.load(path_to_run)
		while run_camera == 1:
			miCamara.start()
			# Load status to run the camera or exit from this while loop
			path_to_run = os.getenv('HOME')+'/'+ 'WORKDIR' + '/' + 'run_camera.npy'
			try:
				run_camera = np.load(path_to_run)
			except Exception as e:
				print('I cant read exit by this reason:', e)
		miCamara.apagar_pi()
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

		rute_to_save = os.getenv('HOME')+'/'+ date

		#folder_raiz = date.split('_')[0]
		#folder = date.split('_')
		#path = folder_raiz + '/' + folder
		cv2.putText(mask, 'press s to capture photos in ./Destiny folder', (10, mask.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
		cv2.imshow('mask for test', mask)
		if cv2.waitKey(1) & 0xFF == ord("s"):
			shoot.encenderCamaraEnSubDirectorio(rute_to_save)
		if cv2.waitKey(1) & 0xFF == ord("q"):
			break
