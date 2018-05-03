#!/usr/bin/env python
# semaforoFinal.py
import cv2
import numpy as np
import os
import pickle
import time
import multiprocessing
import collections
import datetime
import sqlite3
from collections import Counter
import  scipy.misc
import sys

import logging 
import pandas as pd


class GetColor():

	def __init__(self):

		# Set initial time 
		TODAYDATE = datetime.datetime.now().strftime('%Y-%m-%d')
		# Some paths to Folders
		LOG_FOLDER  = 	os.getenv('HOME') + '/' + 'WORKDIR' + '/' + 'Logs/'
		DBS_FOLDER	=	os.getenv('HOME') + '/' + 'WORKDIR' + '/' + 'DBS/'
		self.TS_DATA_FOLDER	= 	os.getenv('HOME') + '/' + 'WORKDIR'	+ '/' + 'tseriesdata/'
		
		# Create Folders if this does not exists
		if not os.path.exists(LOG_FOLDER):
			os.makedirs(LOG_FOLDER)
		else:
			# Folder {}.format(LOG_FOLDER) already exist
			pass
		if not os.path.exists(DBS_FOLDER):
			os.makedirs(DBS_FOLDER)
		else:
			# Folder {}.format(DBS_FOLDER) already exist
			pass
		if not os.path.exists(self.TS_DATA_FOLDER):
			os.makedirs(self.TS_DATA_FOLDER)
		else:
			# Folder {}.format(TS_DATA_FOLDER) already exist
			pass

		# Some paths to files
		LOG_PATH	=	LOG_FOLDER + 'LOGGIN_semaforo_{}.log'.format(TODAYDATE)
		# Path to  DB for keep traffic light transition states
		self.today_semaphoro_db_path = os.getenv('HOME') + '/' + 'WORKDIR' + '/' +'DBS/' + 'semaphoro_periods_{}.db'.format(TODAYDATE)
		# Paths to Machine Learning models
		path_to_svm_model 		= os.getenv('HOME') + '/' + 'trafficFlow' + '/' + 'prototipo' +'/' + 'model' + '/' + 'NN_relu.pkl'# 'NN_4.pkl' # 'linear_3.pkl'#'linear_2.pkl'#'binary_bw3F.pkl'

		# Check Models path
		if os.path.isfile(path_to_svm_model): # If Model exist load into memory
			print ("Using previous model... {}".format(path_to_svm_model))
			self.model = pickle.load(open(path_to_svm_model, "rb"))
		else:
			print ("No model found in {}, please check the path to the ML model!!".format(path_to_svm_model))

		# Set Logging configs
		LOG_FORMAT  =  	"%(levelname)s %(asctime)s - - %(message)s"
		logging.basicConfig(filename = LOG_PATH,
							level = logging.DEBUG,
							format = LOG_FORMAT)
		# Create Logger
		self.logger = logging.getLogger()

		# idx to string
		self.idx_to_str = {0:'VERDE', 1:'ROJO', -1:'off'}
		
		self.str_to_ids = {'verde':0 , 'else': 1, 'amarillo':2, 'rojo': 1, 'off': -1}

		# Expected shape INPUT of the image_semaphoro_raw (Weidth,Height,Channels)
		self.SHAPE = (24,8,3)


		# Periodos
		self.tiempoParaPeriodo 		= time.time()
		self.ultimoPeriodo 			= time.time() - self.tiempoParaPeriodo


		# 2 minutos y medio sera el timeout para determinar que no se esta viendo semaforo
		self.maximoTiempoPeriodo	= 150


		# PlaceHolder
		self.global_actual_state	= str

		# LOCAL  maxlen of 2 for check transitions in Flanco
		self.raw_states 		= collections.deque(maxlen=2)

		# Init raw_states with a global actual state
		self.raw_states.append(self.global_actual_state)


		# Litlle filter deque FIFO
		self.littleFilter = collections.deque(maxlen=20)
		self.numeroDeVerdes = 0
		self.numeroDeRojos = 0
		
	def _extract_feature(self, raw_image):
		SHAPE 		= (8, 24)
		hsv 		= cv2.cvtColor(raw_image, cv2.COLOR_BGR2HSV)

		# GREEN range
		lower_green = np.array([40,20,0], dtype=np.uint8)		# OPEN Green channels
		upper_green = np.array([90,255,255 ], dtype=np.uint8)   #95.255.255  ideal my square.
		
		# Combine the Channels and add some filters
		mask_green 	= cv2.inRange(hsv, lower_green, upper_green)
		filter_1 = cv2.bilateralFilter(mask_green,35,75,75)
		filter_G = cv2.GaussianBlur(filter_1,(5,5),0)
		inputImage 	= cv2.resize(filter_G, SHAPE, interpolation = cv2.INTER_CUBIC)

		if (np.mean(inputImage)) < 10:
			inputImage = np.ones(SHAPE,  dtype=np.uint8)
		else:
			pass

		# Set 1D array
		inputImage 	= inputImage.flatten()
		# Normalize to 0-1 range
		inputImage 	= inputImage / 255

		# Return Data for Machine Learning Classification
		return inputImage.reshape(1, -1)

	def _find_color(self, imagen):
		raw 	= np.reshape(imagen,(24,8,3))
		# ML PROCESS
		X = self._extract_feature(raw)
		tic = time.time()
		Y = self.model.predict(X)[0]
		tac = time.time()

		self.logger.info('Time of classification is: {}'.format(tac - tic))
		if  Y == 'green':
			return 0
		else:
			return 1

	def prediction(self, imagen_raw):

		# Obtain the prediction
		Y = self._find_color(imagen_raw)

		# Use litle filter
		self.littleFilter.append(Y)
		numeroDeEstados = dict(collections.Counter(self.littleFilter))
		for k, v in numeroDeEstados.items():
			if k == 0:
				self.numeroDeVerdes = v
			elif k == 1:
				self.numeroDeRojos = v
		if self.numeroDeVerdes > 18:
			Y = 0
		else:
			Y = 1
		if self.numeroDeRojos > 16:
			Y = 1
		else:
			Y = 0

		# Reset times
		periodoAMostrar = 0

		# Append the prediction to global buffer
		self.raw_states.append(Y)
		# Reset global counter
		self._checkflanco_simple()

		# Check the global flanco and calculate the mean and std of this past period
		if self.flanco == 1:
			periodoAMostrar 	   = self.ultimoPeriodo
			self.tiempoParaPeriodo = time.time()

		self.ultimoPeriodo = time.time() - self.tiempoParaPeriodo

		if self.ultimoPeriodo > self.maximoTiempoPeriodo:
			Y = -1
		else:
			pass

		# Assign string to index
		color_prediction = self.idx_to_str[Y]
		numerico = Y

		return numerico, color_prediction
			
	def _checkflanco_simple(self):
		past, current = self.raw_states[0], self.raw_states[1]
		#
		# Compare the current and pass colors to set self.flanco value 
		#
		if current == past:
			self.flanco = 0
		elif current !=  past:
			self.flanco = 1
		else:
			# transition to  RYG
			print('No match found, current: {},  past: {}, returning 0'.format(current, past))

	@staticmethod
	def _createTable(path_to_semaphoro_db):

		# Create table with default values as:
		conn = sqlite3.connect(path_to_semaphoro_db)
		c 	 =  conn.cursor()
		c.execute('CREATE TABLE IF NOT EXISTS semaphoro_table(SDateStamp TEXT, SPrediction TEXT, SFlanco REAL, SPeriod REAL)')

	@staticmethod
	def dynamic_data_entry(path_to_semaphoro_db, DateStamp, Prediction, Flanco, Period):

		conn = sqlite3.connect(path_to_semaphoro_db)
		c 	 =  conn.cursor()

		c.execute("INSERT INTO  semaphoro_table(SDateStamp, SPrediction, SFlanco, SPeriod) VALUES (?,?,?,?)",\
			(str(DateStamp), str(Prediction), float(Flanco), float(Period)))
		conn.commit()
		# Close coneccions
		c.close()
		conn.close()

	def __call__(self, imagen_raw):
		numerical, color_prediction = self.prediction(imagen_raw)
		return numerical, color_prediction




# Some Globals

directorioDeTrabajo = os.getenv('HOME') + '/trafficFlow/prototipo'
directorioDeVideos  = os.getenv('HOME') + '/trafficFlow/trialVideos'
folderDeInstalacion = directorioDeTrabajo + '/installationFiles'


def main(video):
	archivoDeVideo = video
	archivoParametrosACargar = archivoDeVideo[:-4]+'.npy'

	parametrosInstalacion = np.load(directorioDeVideos+'/'+archivoParametrosACargar)
	indicesSemaforo 	=  parametrosInstalacion[0]

	# Indice as array
	indicesSemaforo = np.array(indicesSemaforo)
	cap = cv2.VideoCapture(directorioDeVideos+'/'+archivoDeVideo)
	# Create semaphoro class
	semaphoro = GetColor()
	mover = True
	montoAMober = []
	while True:
		_, frameVideo = cap.read()

		pixeles = np.array([frameVideo[indicesSemaforo[0][1],indicesSemaforo[0][0]]])
		for indiceSemaforo in indicesSemaforo[1:]:
			pixeles = np.append(pixeles,[frameVideo[indiceSemaforo[1],indiceSemaforo[0]]], axis=0)

		data = semaphoro(pixeles)
		print(data)
		raw 	= np.reshape(pixeles,(24,8,3))

		SHAPE 		= (8*6,24*6)

	
		inputImage 	= cv2.resize(raw, SHAPE, interpolation = cv2.INTER_CUBIC)
		
	
		cv2.imshow('fitler', inputImage)

		#cv2.imshow('Semaphoro', frameVideo)
		ch = 0xFF & cv2.waitKey(5)
		if ch == ord('q'):
			break
	cv2.destroyAllWindows()

if __name__ == '__main__':
	print(sys.argv)
	for entrada in sys.argv:
		print('INPUTS ARE', entrada)
		if ('.mp4' in entrada)|('.avi' in entrada):
			archivoDeVideo = entrada
	main(archivoDeVideo)