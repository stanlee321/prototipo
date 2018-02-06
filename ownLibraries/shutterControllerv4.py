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
from .shooterv11 import Shutter
from .observerpicamera import Observer
import sqlite3
import shutil



class ControladorCamara():
	work_in_folder		 	= 'WORKDIR'
	path_to_run_camera 		= os.getenv('HOME')+'/'+ 'WORKDIR' + '/' + 'run_camera.npy'
	path_to_work 			= os.getenv('HOME')+'/'+ 'WORKDIR' + '/'
	path_to_logo 		= os.getenv('HOME')+'/'+ 'trafficFlow' +'/' +'prototipo/'+ 'watermark'+ '/dems.png'

	def __init__(self):

		# Save to disk the state of camera 1 for ON
		self.run_capture 				= False
		self.save_in_folder				= None
		# Create paths to  databases.
		self.date 						= datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S')
		self.date_for_db 				= datetime.datetime.now().strftime('%Y-%m-%d')
		self.timestamp 					= datetime.datetime.now()
		self.ts 		  				= self.timestamp.strftime("%A %d %B %Y %I:%M:%S%p")

		self.path_to_cache 				= ControladorCamara.path_to_work + 'shooter_database_{}_cache.db'.format(self.date_for_db)
		self.db_name 					= ControladorCamara.path_to_work + 'shooter_database_{}.db'.format(self.date_for_db)
		
		# Create first connection for db
		conn = sqlite3.connect(db_name)
		c 	 =  conn.cursor()
		self.create_table(c)
		self.dynamic_data_entry(c, conn, ts, 'WORKDIR', str(date), 'XX', 'CLOSED')

		# Create second connection for db_cache
		conn = sqlite3.connect(path_to_cache)
		c 	 =  conn.cursor()
		self.create_table(c)
		self.dynamic_data_entry(c, conn, ts, 'WORKDIR', str(date), 'XX', 'CLOSED')


		# Create input and output Queues for send and resive
		# the information.
		self.input_q  = multiprocessing.Queue()
		self.output_q = multiprocessing.Queue()

		# Create miCamara object with the queues as init parameters.
		miCamara  	= Shutter(self.input_q)
		miCamara.start()
		
		observador 	= Observer(self.output_q)
		observador.start()


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
		self.save_in_folder = save_in_folder
		shutil.copy(self.path_to_cache, self.path_to_db)

		# Update parameters before put into db
		IMAGE_FOLDER_NAME 	= self.save_in_folder.split('/')[-1]
		date 				= datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S')
		INDEX 				= str(date.split(':')[-1]) 						# MOST IMPORTANT FOR SYNC WITH THE PARALLEL PROCESS
		timestamp 			= datetime.datetime.now()
		TS 					= timestamp.strftime("%A %d %B %Y %I:%M:%S%p:%f")
		STATUS 				= 'OPEN'										# Mark as a OPEN work

		self.date_for_db 	= datetime.datetime.now().strftime('%Y-%m-%d')	# Check the datetime for the db  and connect  to the db.
		conn 				= sqlite3.connect(self.path_to_db)
		c 					= conn.cursor()
		ControladorCamara.create_table(c)									# if db does not exist, create table in the db		

		# UPDATE NEW ROW
		ControladorCamara.dynamic_data_entry(c, conn, TS, IMAGE_FOLDER_NAME, INDEX, STATUS)

		# Interchange db_cache for db
		shutil.copy(self.path_to_db, self.path_to_cache)


		return self

	def apagarControlador(self):
		print('Resived Signal to Shutdown the picamera...')
		self.run_camera = False
		return self

	def resivir_info(self):
		while self.run_camera == True:

			#print('CIRCULAR BUFF FROM OBSERVER', observador.circular_buff)
			# Read Homework
			save_in_folder = self.input_q.get() 
			self.output_q.put(save_in_folder)
		
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
