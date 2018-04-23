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
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib import style


class CreateSemaforo():
	"""
		This Class init Semaforo , Real or Simulation case.
	"""
	def __init__(self, periodo = 30):
		self.periodo = periodo

		# Create Pipis for send and resive the information betwhen process.
		self.resiver,  self.sender   = multiprocessing.Pipe(duplex=False)
		self.consumer, self.producer = multiprocessing.Pipe(duplex=False)

		if periodo > 0: # If periodo is > 0 create Simulation
			self.semaphoro = Simulation(self.producer, periodo)
			self.semaphoro.start()
		else:
			self.semaphoro = Real(self.resiver, self.producer)
			self.semaphoro.start()


	def obtenerColorEnSemaforo(self, raw):

		# If Debug with video pass else uncomment
		raw 	= np.reshape(raw,(24,8,3))
		
		if self.periodo > 0:  # If simulation
			# Read the data from the producer in simulation.
			data = self.consumer.recv()
			return data[0], data[1], data[2], data[3]
		else:

			# Send the images to The Producer
			self.sender.send(raw)

			# Read the ouputs from The Producer
			data = self.consumer.recv()
			return data[0], data[1], data[2], data[3], data[4], data[5], data[6] #numerico, literal, flanco, period
	def stop(self):
		self.semaphoro.terminate()
		self.semaphoro.join()



class Simulation(multiprocessing.Process):
	"""
	 	 This Class is a Traffic Light simulator
	 """
	def __init__(self, producer, periodo):
		super(Simulation, self).__init__()
		print('WELCOME to SIMULATION')
		self.producer	= producer

		self.periodo 	= periodo
		self.count 		= 0.0
		self.actual_state 	= 1  			# g = 1, y = 2, r = 3
		self.sleeptime 		= 1.0
		self.states 		= collections.deque(maxlen=2)
		self.states.append(self.actual_state)
		
		self.flanco = 0
		self.idx_to_str = {0:'verde', 1:'rojo', 2:'amarillo',-1:'NONE'}

	def counter(self):
		self.count += 1
		return self
	def check_simulated_state(self):
		self.counter()
		self.states.append(self.actual_state)

		self.actual_state = self.states[-1]


		if self.actual_state == 1:
			if self.count == self.periodo:
				self.count = 0.0
				self.actual_state = 2
		if self.actual_state == 2:
			if self.count == 3.0:
				self.count = 0.0
				self.actual_state = 0
		if self.actual_state == 0:
			if self.count == self.periodo:
				self.count = 0.0
				self.actual_state = 1
		self.checkflanco()

	def checkflanco(self):
		past, current = self.states[0], self.states[1]

		#
		# Compare the current and pass colors to set self.flanco value 
		#
		if current == past:					# if actual state = previous_state
			self.flanco = 0
		elif current == 0 and past == 2:	 
			self.flanco = 1	
		elif current == 1 and past == 0:
			self.flanco = -1
		elif current == 2 and past == 1:
			self.flanco = 1
		else:
			print('No match found, current: {},  past: {}, returning 0',format(current, past))

	def run(self):
		while True:
			self.check_simulated_state()
			numerico = self.actual_state
			literal  = self.idx_to_str[self.actual_state]
			flanco   = self.flanco
			periodo  = self.count
			self.producer.send([numerico, literal,flanco,periodo])


class Real(multiprocessing.Process):
	"""
		TRAFFIC LIGHT STATE DETECTOR

		INPUTS: 	Raw (24*8*3) raw numpy array pixels

		OUTPUTS:	list of type [numerical, color_prediction, flanco, periodoAMostrar]
					
		INNER STATES RESUMEN:

			if current state == past state:					
				return flanco 0
			elif (current state == 'verde') and (past state == 'rojo')
				return flanco -1	
			elif (current state == 'amarillo') and (past state == 'verde')
				return flanco 1
			elif (current state == 'rojo')  and (past state == 'amarillo')
				return flanco 2
			elif (current == 'verde') and (past == 'else')
				return flanco -1
			else
				print('No match found, current state: {},  past state: {}, returning 0'.format(current, past))

		SEMAFORO COLOR RETURNS AND NAMES (color_prediction and numerical values)

			{'verde':0 , 'else': 1, 'amarillo':2, 'rojo': 1, 'off': -1}

	"""
		

	def __init__(self, input_q, ouput_q):
		super(Real, self).__init__()
		print('......Starting REAL TRAFICLIGHT....')

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
		path_to_svm_model 		= os.getenv('HOME') + '/' + 'trafficFlow' + '/' + 'prototipo' +'/' + 'model' + '/' + 'linear_3.pkl'#'linear_2.pkl'#'binary_bw3F.pkl'

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
		self.idx_to_str = {0:'verde', 1:'else', -1:'off'}
		self.str_to_ids = {'verde':0 , 'else': 1, 'amarillo':2, 'rojo': 1, 'off': -1}

		# Expected shape INPUT of the image_semaphoro_raw (Weidth,Height,Channels)
		self.SHAPE = (24,8,3)

		# Load the Pipes 
		self.resiver  = input_q
		self.producer = ouput_q


		# Periodos
		self.tiempoParaPeriodo 		= time.time()
		self.ultimoPeriodo 			= time.time() - self.tiempoParaPeriodo

		self.tiempo_para_periodo_amarillo 	= time.time()
		self.ultimo_periodo_amarillo		= time.time() - self.tiempo_para_periodo_amarillo


		# 2 minutos y medio sera el timeout para determinar que no se esta viendo semaforo
		self.maximoTiempoPeriodo	= 150

		# Random numbers for init Traffic Light  Prob. Distributions model
		random_number_1 = np.random.random_sample()*100
		random_number_2 = np.random.random_sample()*100
		random_number_3 = np.random.random_sample()*100
		random_number_4 = np.random.random_sample()*100


		# Deques for states data circulation 
		self.principal_shard    = collections.deque(maxlen=2)	# GLOBAL maxlen of 2 for check transitions in Flanco
		self.raw_states 		= collections.deque(maxlen=2)	# LOCAL  maxlen of 2 for check transitions in Flanco
		VERDE_deque				= collections.deque(maxlen=20)  # For keep track the VERDE periods
		ELSE_deque				= collections.deque(maxlen=20)	# For keep track the ELSE periods.

		# Dictionary placeholder to save the traffic light transitions times.
		self.periodos_dict = {'verde':VERDE_deque, 'else':ELSE_deque}

		# Dictionary to save the values to exterior world
		self.periodosToNumpy = {'verde' : [] , 'else': []}

		# Dictionary to save Stadistical Values from Transitions
		self.mean_values = {'verde': random_number_1, 'else':random_number_2}
		self.std_values  = {'verde': random_number_3, 'else':random_number_4}


		# PlaceHolders for actual and previous states
		# Globals
		self.global_actual_state	= str
		self.global_previous_state	= str
		# Locals
		self.local_actual_state		= str
		self.local_previous_state	= str



		# Init raw_states with a global actual state
		self.raw_states.append(self.global_actual_state)
		
		# Init Flanco to 0
		self.flanco = 0

		# Limit to know if this period is Noice, less of this time, this periodo es noice...
		self.is_noice_thress = 6

		# No Traffic Light limit
		self.no_traffic_light_time		= 150			# 150 Segs limit ot say there'r not TrafficLight 

		# Limit shart to save
		self.bucketLimit 				= 30			# every 30 minutes save
		
		# Index to keep track of buckets 
		self.bucketIndex				= 0 

		# Init a countdown for the states
		self.countdown = Timer()
	
		# Create DB for keep track of Traffic Light states across the day
		self._createTable(self.today_semaphoro_db_path)

		# Little Filter

		self.littleFilter =  collections.deque(maxlen=20)
		self.numeroDeVerdes = 0
		self.numeroDeRojos = 0


		# Automata controllers
		self.correctionX = 0
		self.correctionY = 0
		self.automataIndex = 0

		# Mean values dequeue
		self.maxLenMeanImages = 1000
		self.lastMeanImage = 0
		self.meansImagesDeque = collections.deque(maxlen= self.maxLenMeanImages)
		
		# Centroids in imagen
		self.centroidsXDeque = collections.deque(maxlen=self.maxLenMeanImages)
		self.centroidsYDeque = collections.deque(maxlen=self.maxLenMeanImages)
		# Time tracks
		self.datetimeDeque = collections.deque(maxlen=self.maxLenMeanImages)

		# append signal for initial values
		self.append = True

		# send the signal to move or no the semaforo
		self.move = False

		# send signal to analyse queue

		self.actualImagesMeans = collections.deque(maxlen= self.maxLenMeanImages)
		self.actualCentroidsXDeque = collections.deque(maxlen= self.maxLenMeanImages)
		self.actualCentroidsYDeque = collections.deque(maxlen= self.maxLenMeanImages)

		# Tokers for move the imagen 
		self.tokens = 5

		# If 1000 queues completed, send signal to analyce state of semaforo
		self.analyce = False
		
		# Placeholder for Actual state of semaforo
		self.actualState = 0
		
		# Acumulador de periodos
		self.acumulator = {'verde' : [] , 'else': []}


	@staticmethod
	def _calCentroid(x, y, w, h):
		x1 = int(w / 2)
		y1 = int(h / 2)
		cx = x + x1
		cy = y + y1
		return (cx, cy)

	@staticmethod
	def _getCentroid(full_mask):
		"""
			Find the contour  and later calculate the centroid of this contour
		"""

		_, contours, _ = cv2.findContours(full_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_TC89_L1)


		for (_, contour) in enumerate(contours):
			(x, y, w, h) = cv2.boundingRect(contour)
			centroid = Real._calCentroid(x, y, w, h)
			return centroid



	def _imagesStats(self, inputImage):
		
		centroid 	= Real._getCentroid(inputImage)
		mean 		= np.mean(inputImage)

		self.lastMeanImage  = mean
		if (centroid is not None) and ( mean != 0.0):
			# append to deque of meansImages
			if self.append is False:
				if self.actualState == 0:	
					self.actualImagesMeans.append(mean)
					self.actualCentroidsXDeque.append(centroid[0])
					self.actualCentroidsYDeque.append(centroid[1])
				else:
					pass
			else:
				self.meansImagesDeque.append(mean)
				self.centroidsXDeque.append(centroid[0])
				self.centroidsYDeque.append(centroid[1])
		else:
			pass

		if len(self.meansImagesDeque) == self.maxLenMeanImages:

			if self.append is True:

				patronMean =  np.max(np.mean(self.meansImagesDeque))
				
				xcmax  =  np.max(self.centroidsXDeque)
				ycmax  =  np.max(self.centroidsYDeque)
				xcmin  =  np.min(self.centroidsXDeque)
				ycmin  =  np.min(self.centroidsYDeque)
				
				centroidXMean = np.mean(self.centroidsXDeque)
				centroidYMean = np.mean(self.centroidsYDeque)

				print('LIMIT REACHED; SAVING FILES')
				# Automata dict info
				automataInfo = {'patronMean': patronMean, \
								'xcmax': xcmax, 'ycmax': ycmax,\
								'xcmin': xcmin, 'ycmin': ycmin,
								'centroidXMean': centroidXMean, 'centroidYMean':centroidYMean}

				# Create dataframe from dict
				df  	= pd.DataFrame.from_dict(automataInfo, orient='index')
				data 	= df.transpose()

				# Loggers amd Path infoLOG_FOLDER  
				now 	= datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S')
				PATH_TO_SAVE_CSV  =	self.TS_DATA_FOLDER  + 'initial_values-{}-{}.csv'.format(now, self.automataIndex)
				self.logger.info('SAVING periodosToNumpy with route {} '.format(PATH_TO_SAVE_CSV))

				# Save to disk
				data.to_csv(PATH_TO_SAVE_CSV, sep=',', encoding='utf-8')

				
				# Reset queues
				self.meansImagesDeque = collections.deque(maxlen= self.maxLenMeanImages)		
				# Centroids in imagen
				self.centroidsXDeque = collections.deque(maxlen=self.maxLenMeanImages)
				self.centroidsYDeque = collections.deque(maxlen=self.maxLenMeanImages)
				# Time tracks
				self.datetimeDeque = collections.deque(maxlen=self.maxLenMeanImages)

				# Not longer enter here
				self.append = False
			else:
				pass
		if len(self.actualImagesMeans) == self.maxLenMeanImages:
			#	# Analyice queue
			self.analyce = True
			self.actualImagesMeans = collections.deque(maxlen= self.maxLenMeanImages)


		
	def _extract_feature(self, raw_image):
		SHAPE 		= (8, 24)
		hsv 		= cv2.cvtColor(raw_image, cv2.COLOR_BGR2HSV)

		# GREEN range
		lower_green = np.array([40,20,0], dtype=np.uint8)		# OPEN Green channels
		upper_green = np.array([90,255,255 ], dtype=np.uint8)   #95.255.255  ideal my square.
		# Combine the Channels
		mask_green 	= cv2.inRange(hsv, lower_green, upper_green)

		"""
		TODO PUT A BILATERAL FILTER HERE
		"""
		filter_G = cv2.GaussianBlur(mask_green,(15,15),0)
		inputImage 	= cv2.resize(filter_G, SHAPE, interpolation = cv2.INTER_CUBIC)

		if (np.mean(inputImage)) < 10:
			inputImage = np.ones(SHAPE,  dtype=np.uint8)
		else:
			#inputImage = cv2.resize(full_mask, SHAPE, interpolation = cv2.INTER_CUBIC)
			pass
		self._imagesStats(inputImage)	
	
		# Check automat
		if self.append is False:
			self._automata()

		# Set 1D array
		inputImage 	= inputImage.flatten()
		# Normalize to 0-1 range
		inputImage 	= inputImage / 255

		# Return Data for Machine Learning Classifica
		return inputImage.reshape(1, -1)

	def _automata(self):

		
		records = [f for f in os.listdir(self.TS_DATA_FOLDER) if ('temp-record-' not in f)]
		
		dataframes = [pd.read_csv(self.TS_DATA_FOLDER + '/' + record) for record in records]

		df = pd.concat(dataframes)


		patronMean =  df['patronMean'].tolist()[0]
		distance = patronMean - np.mean(self.actualImagesMeans)		
		
		"""
		TODO calculate the displamente with the referecne
		and the actualDqueues

		xcmax  =  df['xcmax'].tolist()[0]
		ycmax  =  df['ycmax'].tolist()[0]
		xcmin  =  df['xcmin'].tolist()[0]
		ycmin  =  df['ycmin'].tolist()[0]
		

		centroidXMean = df['centroidXMean'].tolist()[0]
		centroidYMean = df['centroidYMean'].tolist()[0]

		if (len(self.actualCentroidsXDeque) != 0) and (len(self.actualCentroidsYDeque) !=0):
				diffX  =  centroidXMean - np.max(self.actualCentroidsXDeque)
				diffY  =  centroidYMean - np.max(self.actualCentroidsYDeque) 
		else:
			diffX  =  centroidXMean
			diffY  =  centroidYMean
		"""
		
		self.logger.info('Patron fron Init Condition:: {}'.format(patronMean))
		self.logger.info('Actual separation Distance:: {}'.format(distance))

		if  (distance) > 20:
			self.logger.warning('Semaforo are moving, reacalibrando...aviable Tokens {}'. format(self.tokens))
			if self.tokens  > 0:	
				if self.analyce is True:
					self.correctionX = 1 #diffX  * beta
					self.correctionY = 1 #diffY  * beta
					self.move = True
					self.tokens -= 1
					self.analyce = False
					self.logger.warning('Token used, remains {}'. format(self.tokens))
				else:
					self.move = False
			else:
				self.move = False
		else:
			self.correctionX = 0
			self.correctionY = 0

		#PATH_TO_SAVE_CSV  =	self.TS_DATA_FOLDER  + 'temp-record.csv'
		#tracksDF.to_csv(PATH_TO_SAVE_CSV, sep=',', encoding='utf-8')

	@staticmethod
	def _sigmoid(x):
		#s = 1 / (1+np.exp(-np.asarray(x)))
		s = 1 / (1+np.exp(-x))
		return s

	def _find_color(self, imagen):
		# ML PROCESS
		X = self._extract_feature(imagen)
		tic = time.time()
		Y = self.model.predict(X)[0]
		tac = time.time()

		print('TIME IS', tac - tic)

		if  Y == 'green':
			return 0
		else:
			return 1

	def prediction(self, imagen_raw):

		# Obtain the prediction

		Y = self._find_color(imagen_raw)
		self.actualState = Y
		# Use litle filter
		self.littleFilter.append(Y)

		numeroDeEstados = dict(collections.Counter(self.littleFilter))
		#print('numerode estados', numeroDeEstados)
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

		# Reset global counter
		periodoAMostrar = 0
		
		# get color as literal
		color_prediction = self.idx_to_str[Y]

		# Append the prediction to global buffer
		self.raw_states.append(color_prediction)

		# Calculate the global flanco
		self._checkflanco_simple()

		# Check the global flanco and calculate the mean and std of this past period
		if self.flanco == 1:
			periodoAMostrar 	   = self.ultimoPeriodo
			self.tiempoParaPeriodo = time.time()

			if periodoAMostrar <= self.is_noice_thress: # If periodo para mostrar is less of 6 , this is noice ... pass
				self.logger.warning('NOICE NOICE with  periodoAMostrar: {}'.format(periodoAMostrar))
				print(periodoAMostrar)
				#self.acumulator[color_prediction].append(periodoAMostrar)
			else:
				self.periodos_dict[color_prediction].append(periodoAMostrar) 	# append the periods to the global dict deques
				
				
				actualTime 	= datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S') # Get acutal time to row data
				AUX_ROW 	= {'periodo': periodoAMostrar, 'time': actualTime}		# Auxilar Dictionary to pass into the dicts.

				self.periodosToNumpy[color_prediction].append(AUX_ROW) 			# append to periodostoNumpy
				
				# calculate the mean and std of this periodos
				self.mean_values[color_prediction] = np.mean(self.periodos_dict[color_prediction])  # TODO Check Limits 0: to...
				self.std_values[color_prediction]  = np.std(self.periodos_dict[color_prediction])	# TODO Check Limits 0: to...


				# Check if list is in the limit of 40 elements.
				# Then save to disk this info
				if (len(self.periodosToNumpy['verde']) == self.bucketLimit) and (len(self.periodosToNumpy['else']) == self.bucketLimit):
					# Save to disk uncompleted data
					df  	= pd.DataFrame.from_dict(self.periodosToNumpy, orient='index')
					data 	= df.transpose()

					# Loggers amd Path infoLOG_FOLDER  = 	'
					now 	= datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S')
					PATH_TO_SAVE_CSV  =	self.TS_DATA_FOLDER  + 'periodos-{}-{}.csv'.format(now, self.bucketIndex)
					self.logger.info('SAVING periodosToNumpy with route {} '.format(PATH_TO_SAVE_CSV))
					# Save to disk
					data.to_csv(PATH_TO_SAVE_CSV, sep='\t', encoding='utf-8')

					# Reset the Dict
					self.periodosToNumpy = {'verde' : [] , 'else': []}

					# Increase bucketIndex 
					self.bucketIndex += 1
		else:
			pass

		print('PREIDOS DICT : DQUEUE: ', self.periodos_dict)
		print('PERIODOS',self.periodosToNumpy)		# append to periodostoNumpy		
		# calculate the mean and std of this periodos
		print('MEAN VALUES',self.mean_values)
		print('STD VALUES', self.std_values)
		# Update the last period
		self.ultimoPeriodo = time.time() - self.tiempoParaPeriodo
		

		# Check if  acumulate mean_values of "ELSE" are mayor of 150
		if self.mean_values['else'] > self.no_traffic_light_time:			# TODO check if is comvenient use STD
			return self.str_to_ids['off'], self.idx_to_str[-1], 0, self.mean_values['else'] # -1, off, 0, exceded time

		# if STD of verde and else are less of 1.5 in the distribution ...continue to the G-Y-R semaphoro
		if (self.std_values['verde'] < 1.5 ) and (self.std_values['else'] < 1.5 ) :

			# if exist enought values in the distribution to calculate the 
			# STD above of 0.0 continue to G-Y-R semaphoro 
			if (self.std_values['verde'] != 0.0 ) and (self.std_values['else'] != 0.0 ):
				
				# Start to calculate the periodos of the three colors:
				periodo_verde 	 = self.mean_values['verde'] + self.std_values['verde']
				periodo_else	 = self.mean_values['else'] + self.std_values['else']

				# Inference, this must be the colors of yellow and red.
				periodo_amarillo = periodo_else - periodo_verde
				periodo_rojo 	 = periodo_else - periodo_amarillo

				# Assing to the global_actual_sate the value of actual color_prediction
				self.global_actual_state = color_prediction


				# if exist verde and else  in deque buffer of len two , transition.... from
				if self.raw_states[-2] == 'verde' and self.raw_states[-1] == 'else':
					# TRANSITION FROM  verde to else 'amarillo'
					self.local_previous_state 	= 'verde'
					self.local_actual_state		= 'amarillo'
					# Init  the stopmatch for the amarillo period
					self.countdown.init_time = time.time()
				else:
					pass
				
				# Check if stopmatch time was started, else pass
				if self.countdown.init_time != None:
					# if started check the time
					value = float(self.countdown.elapsed().split(': ')[-1])

					# if time is above of amarillo period
					if value  > periodo_amarillo:
						self.local_previous_state 	= 'amarillo'
						self.local_actual_state 	= 'rojo'
						self.countdown.stop()
					else:
						pass
				else:
					pass

				# Check if exist transition from else 'rojo' from global buffer to 'verde'
				if (self.raw_states[-2] == 'else') and (self.raw_states[-1] == 'verde'):
					# TRANSITION FROM  else 'rojo' to verde
					self.local_previous_state 	= 'rojo'
					self.local_actual_state 	= 'verde'
				else:
					pass

				# append this to principal_shard which mantain the G-Y-R transitions.
				self.principal_shard.append(self.local_actual_state)


				# Statements for   check the local flancos
				if self.local_actual_state == 'verde':
					self.local_previous_state  == 'rojo'
					flanco 		= self._checkflanco_full()
					numerico	= self.str_to_ids[self.local_actual_state]

					if flanco != 0:
						return numerico, self.local_actual_state, flanco, periodo_rojo
					else:
						return numerico, self.local_actual_state, flanco, 0


				elif self.local_actual_state == 'amarillo':
					self.local_previous_state  == 'verde'
					flanco 			= self._checkflanco_full()
					numerico		= self.str_to_ids[self.local_actual_state]

					if flanco != 0:
						return numerico, self.local_actual_state, flanco, periodo_verde
					else:
						return numerico, self.local_actual_state, flanco, 0


				elif self.local_actual_state == 'rojo':
					self.local_previous_state  == 'amarillo'
					flanco 		= self._checkflanco_full()
					numerico	= self.str_to_ids[self.local_actual_state]

					if flanco != 0:
						return numerico, self.local_actual_state, flanco, periodo_amarillo
					else:
						return numerico, self.local_actual_state, flanco, 0
				else:
					# Off semaforo case
					pass
			else:
				#print('Still returiong the binary case...')
				numerico = 	self.str_to_ids[color_prediction]
				return numerico, color_prediction, self.flanco, periodoAMostrar

		else:
			numerico = 	self.str_to_ids[color_prediction]
			#print('Returning Single  binary return...')
			return numerico, color_prediction, self.flanco, periodoAMostrar
			

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

	def _checkflanco_full(self):
		if len(self.principal_shard) == 2:
			past, current = self.principal_shard[0], self.principal_shard[1]
			#
			# Compare the current and pass colors to set self.flanco value 
			#
			if current == past:					
				return  0
			elif (current == 'verde') and (past == 'rojo'):	
				return -1	
			elif (current == 'amarillo') and (past == 'verde'):
				return  1
			elif (current == 'rojo')  and (past == 'amarillo'):
				return 2
			elif (current == 'verde') and (past == 'else'):
				return -1
			else:
				print('No match found, current: {},  past: {}, returning 0'.format(current, past))
		else:
			return 0

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

	def run(self):
		while True:
			if 	self.resiver.poll(): # Check if exist input images from main program.
				# Read images form sender
				imagen = self.resiver.recv()
				# Return predictions 

				numerical, color_prediction, flanco, periodoAMostrar = self.prediction(imagen)

				# if Flanco is != from 0, add the above results to DB 

				if flanco != 0:

					if os.path.isfile(self.today_semaphoro_db_path): # If Model exist load into memory
						date = datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S')
						try:
							Real.dynamic_data_entry(self.today_semaphoro_db_path, date, color_prediction, flanco, periodoAMostrar)		
						except Exception as e:
							self.logger.warning('ERROR TRYGIN TO WRITE IN DB! with: {}'.format(e))
							
					else:
						# Notify that there was not folder
						self.logger.info('THERE WAS NOT DB FOLDER in {}'. format(self.today_semaphoro_db_path))
						# Create a new DB with TOdays date
						TODAY = datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S')
						self.today_semaphoro_db_path = os.getenv('HOME') + '/' + 'WORKDIR' + '/' +'DBS/' + 'semaphoro_periods_{}.db'.format(TODAY)


						# Attempt to create a new DB
						self._createTable(self.today_semaphoro_db_path)

						# Notify that data saving.. in new direction
						self.logger.info('SAVING DB DATA in... {}'.format(self.today_semaphoro_db_path))

						date = datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S')
						try:
							Real.dynamic_data_entry(self.today_semaphoro_db_path, date, color_prediction, flanco, periodoAMostrar)		
						except Exception as e:
							self.logger.warning('ERROR TRYGIN TO WRITE IN DB! with: {}'.format(e))
				# Send the results back to consumer in main program				
				self.producer.send([numerical, color_prediction, flanco, periodoAMostrar, self.correctionX, self.correctionY, self.move])
			
			#else:
			#	print('DEBUGS Error Here in reading images, returning feaults  WE..')
			#	print('WE ARE NOT RESIVING IMAGES FROM MAIN PROGRAM!!!!..')
			#	print('SENDING DEAFULTS....')
				#self.consumer.send([0,'nan',0, 0, 0])



class Timer(object):
    """A simple timer class"""
    
    def __init__(self, periodos=[]):
        self.periodos = periodos
        self.init_time = None#time.time()
    @property
    def init_time(self):
        return self.__init_time
    @init_time.setter
    def init_time(self,t):
        self.__init_time = t

    def stop(self, message="Total: "):
        """Stops the timer.  Returns the time elapsed"""
        self.stop_l = time.time()
        self.__init_time = None
        #print(message + str(self.stop_l - self.__init_time))

    def elapsed(self, message="Elapsed: "):
        """Time elapsed since start was called"""
        return message + str(time.time() - self.__init_time)

    def start(self):
        """Starts the timer"""
        self.__init_time = time.time()
        return self.__init_time



# Some Globals

directorioDeTrabajo = os.getenv('HOME') + '/trafficFlow/prototipo'
directorioDeVideos  = os.getenv('HOME') + '/trafficFlow/trialVideos'
folderDeInstalacion = directorioDeTrabajo + '/installationFiles'


def get_centroid(x, y, w, h):
	x1 = int(w / 2)
	y1 = int(h / 2)
	cx = x + x1
	cy = y + y1
	return (cx, cy)

def main(video):
	archivoDeVideo = video
	archivoParametrosACargar = archivoDeVideo[:-4]+'.npy'

	parametrosInstalacion = np.load(directorioDeVideos+'/'+archivoParametrosACargar)
	indicesSemaforo 	=  parametrosInstalacion[0]

	# Indice as array
	indicesSemaforo = np.array(indicesSemaforo)
	cap = cv2.VideoCapture(directorioDeVideos+'/'+archivoDeVideo)
	# Create semaphoro class
	semaphoro = CreateSemaforo(periodo = 0)
	mover = True
	montoAMober = []
	while True:
		_, frameVideo = cap.read()
		#print('Indices from while are ', indicesSemaforo)
		# Feed with images to semaphoro
		print('dinices semaforo shape', indicesSemaforo.shape)
		print('axis0', indicesSemaforo[0])
		#print('axis1', indicesSemaforo[0][1])
		#print('indices', indicesSemaforo)

		pixeles = np.array([frameVideo[indicesSemaforo[0][1],indicesSemaforo[0][0]]])
		for indiceSemaforo in indicesSemaforo[1:]:
			pixeles = np.append(pixeles,[frameVideo[indiceSemaforo[1],indiceSemaforo[0]]], axis=0)

		data = semaphoro.obtenerColorEnSemaforo(pixeles)
		print(data)


		raw 	= np.reshape(pixeles,(24,8,3))

		SHAPE 		= (8*6,24*6)
		hsv 		= cv2.cvtColor(raw, cv2.COLOR_BGR2HSV)

		# GREEN range
		lower_green = np.array([50,20,0], dtype=np.uint8)		#50# OPEN Green channels
		upper_green = np.array([90,255,255], dtype=np.uint8)   #95.255.255  ideal my square.

		
		# Combine the Channels
		mask_green 	= cv2.inRange(hsv, lower_green, 	upper_green)
	
		filter_g = cv2.bilateralFilter(mask_green,35,5,75)
		filter_g = cv2.GaussianBlur(mask_green,(5,5),0)
		full_mask 	= filter_g
		
		_, contours, _ = cv2.findContours(full_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_TC89_L1)
	
		for (i, contour) in enumerate(contours):
			(x, y, w, h) = cv2.boundingRect(contour)
			centroid = get_centroid(x, y, w, h)
		print('MOVE BY THIs UNIT', data[4], data[5])
		mover = data[6]
		if (data[6] is True):
			if data[5] != 0:	
				print('MVOIENDO SEMAFORO')

				for i, indice in enumerate(indicesSemaforo):
					indice[0] -= data[4]**2  
					indice[1] += data[5]**2

				mover = False
			else:
				pass
		else:
			pass
		#res 		= cv2.bitwise_and(img, hsv, mask = full_mask)
		res =  np.stack((full_mask,)*3, -1)

		#print(res.shape)

		inputImage 	= cv2.resize(res, SHAPE, interpolation = cv2.INTER_CUBIC)
		#print('Mean image', np.mean(inputImage))
		
		if np.mean(inputImage) < 10:
			inputImage = np.ones((24*6,8*6),  dtype=np.uint8)
		else:
			inputImage 	= cv2.resize(res, SHAPE, interpolation = cv2.INTER_CUBIC)
	
		cv2.circle(inputImage, (centroid[0]*6, centroid[1]*6), 2, (0,255,0), -1)
		#cv2.circle(inputImage, (x, h), 2, (0,255,0), -1)

		#cv2.imshow('Ohne', full_mask)
		cv2.imshow('fitler', inputImage)
		cv2.imshow('Semaphoro', cv2.resize(np.reshape(pixeles, (24,8,3)),(320,240)))
		#cv2.imshow('Semaphoro', cv2.resize(frameVideo,(320,240)))

		#cv2.imshow('Semaphoro', frameVideo)
		ch = 0xFF & cv2.waitKey(5)
		if ch == ord('q'):
			semaphoro.stop()
			break
	cv2.destroyAllWindows()

if __name__ == '__main__':
	print(sys.argv)
	for entrada in sys.argv:
		print('INPUTS ARE', entrada)
		if ('.mp4' in entrada)|('.avi' in entrada):
			archivoDeVideo = entrada
	main(archivoDeVideo)