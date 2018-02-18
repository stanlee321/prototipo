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
import sqlite3
import shutil
import collections
from .shutterv11 import Shutter
import pandas as pd
import glob

class ControladorCamara():
	work_in_folder		 	= 'WORKDIR'
	path_to_run_camera 		= os.getenv('HOME')+'/'+ 'WORKDIR' + '/' + 'run_camera.npy'
	path_to_tasks_deque 	= os.getenv('HOME')+'/'+ 'WORKDIR' + '/' + 'tasks_deque.npy'
	path_to_work 			= os.getenv('HOME')+'/'+ 'WORKDIR' + '/'
	path_to_logo 			= os.getenv('HOME')+'/'+ 'trafficFlow' +'/' +'prototipo/'+ 'watermark'+ '/dems.png'

	def __init__(self):

		# Init state for run the camera
		np.save(ControladorCamara.path_to_run_camera, 1) 		# 1 ON state

		# Save to disk the state of camera 1 for ON
		self.run_camera 				= True
		self.save_in_folder				= collections.deque(maxlen=2)
		np.save(ControladorCamara.path_to_tasks_deque, self.save_in_folder)
		# Create paths to  databases.
		self.date 						= datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S')
		self.date_for_db 				= datetime.datetime.now().strftime('%Y-%m-%d')
		self.timestamp 					= datetime.datetime.now()
		self.ts 		  				= self.timestamp.strftime("%A %d %B %Y %I:%M:%S%p")

		self.path_to_cache 				= ControladorCamara.path_to_work + 'shooter_database_{}_cache.db'.format(self.date_for_db)
		self.path_to_db 				= ControladorCamara.path_to_work + 'shooter_database_{}.db'.format(self.date_for_db)
		
		# Create first connection for db
		conn = sqlite3.connect(self.path_to_db)
		c 	 =  conn.cursor()
		self.create_table(c)
		self.dynamic_data_entry(c, conn, self.ts, str(self.date), 'XX', 'CLOSED')

		# Create second connection for db_cache
		conn = sqlite3.connect(self.path_to_cache)
		c 	 =  conn.cursor()
		self.create_table(c)
		self.dynamic_data_entry(c, conn, self.ts, str(self.date), 'XX', 'CLOSED')


		# Create input and output Queues for send and resive
		# the information.

		# Create miCamara object with the queues as init parameters.
		self.miCamara  	= Shutter()
		self.miCamara.start()
		
	@staticmethod
	def create_table(c):
		# Create table with default values as:

		# WORKDIR, 		dir where to start to work
		# SAVE_IMG_IN, 	dir where to copy the images from WORKDIR
		# INDEX, 		for sync the outer and inner process
		# STATUS, 		took pictures or not status
		c.execute('CREATE TABLE IF NOT EXISTS shooter_table(Datestamp TEXT,Folder TEXT,Idx TEXT,Status TEXT)')

	@staticmethod
	def dynamic_data_entry(c, conn, TS, IMAGE_FOLDER_NAME, INDEX, STATUS):
		c.execute("INSERT INTO  shooter_table(Datestamp, Folder, Idx, Status) VALUES (?,?,?,?)",\
			(TS, IMAGE_FOLDER_NAME, INDEX, STATUS))
		conn.commit()
		# Close coneccions
		c.close()
		conn.close()

	def encenderCamaraEnSubDirectorio(self, save_in_folder = None):
		# Interchange db and db_cache
		tasks_deque 		= np.load(ControladorCamara.path_to_tasks_deque)

		self.save_in_folder = collections.deque(tasks_deque)

		if len(self.save_in_folder) == 0 or 1:
			self.save_in_folder.appendleft(save_in_folder)
			for save_in_folder in self.save_in_folder:
				self.update_rows_in_db(save_in_folder, self.path_to_cache, self.path_to_db)
			np.save(ControladorCamara.path_to_tasks_deque, self.save_in_folder)

		elif len(self.save_in_folder) == 2:
			for save_in_folder in self.save_in_folder:
				self.update_rows_in_db(save_in_folder, self.path_to_cache, self.path_to_db)
		else:
			pass
	def update_rows_in_db(self,save_in_folder, path_to_cache, path_to_db):

		shutil.copy(path_to_cache, path_to_db)
		# Update parameters before put into db
		IMAGE_FOLDER_NAME 	= save_in_folder.split('/')[-1]
		date 				= datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S')
		INDEX 				= str(date.split(':')[-1]) 						# MOST IMPORTANT FOR SYNC WITH THE PARALLEL PROCESS
		timestamp 			= datetime.datetime.now()
		TS 					= timestamp.strftime("%A %d %B %Y %I:%M:%S%p:%f")
		STATUS 				= 'OPEN'										# Mark as a OPEN work

		date_for_db 		= datetime.datetime.now().strftime('%Y-%m-%d')	# Check the datetime for the db  and connect  to the db.
		conn 				= sqlite3.connect(path_to_db)
		c 					= conn.cursor()
		ControladorCamara.create_table(c)									# if db does not exist, create table in the db		

		# UPDATE NEW ROW
		ControladorCamara.dynamic_data_entry(c, conn, TS, IMAGE_FOLDER_NAME, INDEX, STATUS)
		# Interchange db_cache for db
		shutil.copy(self.path_to_db, self.path_to_cache)

		#np.save(ControladorCamara.path_to_tasks_deque, self.save_in_folder)

	def apagarControlador(self):
		print('Resived Signal to Shutdown the picamera...')
		np.save(ControladorCamara.path_to_run_camera, 0)
		self.miCamara.apagar_observador()
		self.miCamara.join()
		
		return self


if __name__ == '__main__':
	#DEMO DEMO DEMO 
	import numpy as np
	import datetime
	shutter = ControladorCamara()
	mask = np.zeros((320,320))
	mask = mask.astype(np.uint8)
	counter = -1
	while True:

		date =  datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S')

		rute_to_save = os.getenv('HOME')+'/'+ date
		
		#if counter % 10000:
		#	print('TIME IN THE EXTERIOR WORLD', counter)

		#counter +=1
		#folder_raiz = date.split('_')[0]
		#folder = date.split('_')
		#path = folder_raiz + '/' + folder
		cv2.putText(mask, 'press s to capture photos in ./Destiny folder', (10, mask.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
		cv2.imshow('mask for test', mask)
		if cv2.waitKey(1) & 0xFF == ord("s"):
			shutter.encenderCamaraEnSubDirectorio(rute_to_save)
		if cv2.waitKey(1) & 0xFF == ord("q"):
			shutter.apagarControlador() 
			break
