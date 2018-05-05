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

style.use("fivethirtyeight")

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
			return data[0], data[1], data[2], data[3] #numerico, literal, flanco, period
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
		path_to_svm_model 		= os.getenv('HOME') + '/' + 'trafficFlow' + \
									'/' + 'prototipo' +'/' + 'model' + '/' + 'binary.pkl'
		path_to_keras_model	 	= os.getenv('HOME') + '/' + 'trafficFlow' + \
									'/' + 'prototipo' +'/' + 'model' + '/' + 'model.h5'
		# Check Models path
		if os.path.isfile(path_to_svm_model): # If Model exist load into memory
			print ("Using previous model... {}".format(path_to_svm_model))
			self.svm = pickle.load(open(path_to_svm_model, "rb"))
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
		self.bool_to_str 	= { False:'verde', True:'else', -1:'off' }
		self.str_to_ids 	= { 'verde': 0 , 'else': 1, 'amarillo':2, 'rojo': 1, 'off': -1 }
		self.bool_to_int 	= {  False: 0, True:1, 'amarillo':2, 'rojo':1, 'off':-1 }

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
		self.flancoRaw = 0
		self.flancoSmoth = 0
		# Limit to know if this period is Noice, less of this time, this periodo es noice...
		self.is_noice_thress = 0

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

		# Litle filter
		#self.rawAssignation = collections.deque(maxlen=50)
		#self.assignation = collections.deque(maxlen=50)


		self.rawAssignation = {1 : collections.deque(maxlen=30) , 0:  collections.deque(maxlen=30) }
		self.assignation = {1 : collections.deque(maxlen=30) , 0:  collections.deque(maxlen=30) }
		self.periodosChecker = {1 : collections.deque(maxlen=30) , 0:  collections.deque(maxlen=30) }
		self.maximoPeriodoForState = {1 : 0.0, 0:  0.0 }
		self.pastState = {1 : collections.deque(maxlen=30) , 0:  collections.deque(maxlen=30) }
		self.flancoLastDurationRaw = {1 : 0.0 , 0:  0.0}
		self.flancoLastDurationFlaw = {1 : 0.0, 0:  0.0} 

		self.flancoRawDuration = {1 : collections.deque(maxlen=30) , 0:  collections.deque(maxlen=30) }
		self.Y_local = 0


		# For animation

	@staticmethod	
	def _extract_feature(raw_image):
		SHAPE 		= (24, 8)
		img 		= cv2.cvtColor(raw_image, cv2.COLOR_BGR2RGB)
		hsv 		= cv2.cvtColor(raw_image, cv2.COLOR_BGR2HSV)

		# SOME MASKS
		#lower_yellow = 	np.array([20,100,100], dtype=np.uint8) # CLOSE all the colors for YELLOW
		#upper_yellow =	np.array([30,255,255], dtype=np.uint8)

		# RED range
		#lower_red 	= np.array([255,255, 255], dtype=np.uint8) 	# CLOSE all the colors for RED
		#upper_red 	= np.array([180,255,255], dtype=np.uint8)

		# GREEN range
		lower_green = np.array([50,20,0], dtype=np.uint8)		# OPEN Green channels
		upper_green = np.array([90,255,255 ], dtype=np.uint8)   #95.255.255  ideal my square.

		# Combine the Channels
		#mask_red 	= cv2.inRange(hsv, lower_red, 		upper_red)
		#mask_yellow = cv2.inRange(hsv, lower_yellow,	upper_yellow)
		mask_green 	= cv2.inRange(hsv, lower_green, 	upper_green)
		full_mask 	= mask_green

		# Put the mask and filter the R, Y , G colors in _imagen_
		res 		= cv2.bitwise_and(hsv, img, mask = full_mask)
		inputImage 	= cv2.resize(res, SHAPE, interpolation = cv2.INTER_CUBIC)
		# Set 1D array
		inputImage 	= inputImage.flatten()
		
		# Normalize to 0-1 range
		inputImage 	= inputImage / 255

		# Return Data for Machine Learning Classifica
		return inputImage.reshape(1, -1)

	@staticmethod
	def _sigmoid(x):
		#s = 1 / (1+np.exp(-np.asarray(x)))
		s = 1 / (1+np.exp(-x))
		return s

	def _find_color(self, imagen):
		# ML PROCESS
		X = self._extract_feature(imagen)
		Y = self.svm.predict(X)[0]
		###########################
		# END SVM PART (CLASSIFICATION) 
		###########################
		# Return prediction from SVM

		if Y == 'green':
			return False
		else:
			return True

	def prediction(self, imagen_raw):

		# Obtain the prediction
		Y = self._find_color(imagen_raw)


		# Reset global counter
		periodoAMostrar = 0

		# convert integet to string
		color_prediction = self.bool_to_str[Y]

		# Append the prediction to calculate the flanco
		self.raw_states.append(color_prediction)

		# Calculate the flanco signal if exist transition
		self._checkflanco_simple()


		# Is exist change in flanco

		if self.flancoRaw == 1:

			# Calculate the duration of this period
			periodoAMostrar 	   = self.ultimoPeriodo

			# Append to periodos checker dict into the past state
			self.periodosChecker[not Y].append(periodoAMostrar)


			# check if the changes in period have sence

			for k, v in self.periodosChecker.items():
				# Get the max value in the keys
				self.maximoPeriodoForState[not Y] = np.max(self.periodosChecker[not Y])

				# Use this value as reference to past state
				self.pastState[not Y] = self.maximoPeriodoForState[not Y]

			if periodoAMostrar < self.maximoPeriodoForState[Y]:
				# append the values in actual State Y from periodosChecker past state Y
				self.flancoRawDuration[Y] = self.periodosChecker[Y]

			# Corrent the actual periodoAMostrar
			periodoAMostrar = np.sum(self.flancoRawDuration[Y])

			# Corrent the state
			color_prediction = self.bool_to_str[not Y]

			# Reset the counter 
			self.tiempoParaPeriodo = time.time()


		else:
			pass

		# Time until now fron actual period
		self.ultimoPeriodo = time.time() - self.tiempoParaPeriodo
		flanco = self.bool_to_int[self.flancoRaw]
		numerico = 	self.bool_to_int[Y]

		return 	numerico, color_prediction, flanco, periodoAMostrar
			

	def _checkflanco_simple(self):
		past, current = self.raw_states[0], self.raw_states[-1]


		#
		# Compare the current and pass colors to set self.flanco value 
		#
		if current == past:
			self.flancoRaw = False
		elif current !=  past:
			self.flancoRaw = True
		else:
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

	def run(self):
		while True:
			if 	self.resiver.poll(): # Check if exist input images from main program.
				# Read images form sender
				imagen = self.resiver.recv()
				# Return predictions 

				numerical, color_prediction, flanco, periodoAMostrar = self.prediction(imagen)

				# if Flanco is != from 0, add the above results to DB 

				"""
				if flanco != 0:

					if os.path.isfile(self.today_semaphoro_db_path): # If Model exist load into memory
						date = datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S')
						Real.dynamic_data_entry(self.today_semaphoro_db_path, date, color_prediction, flanco, periodoAMostrar)		

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
						Real.dynamic_data_entry(self.today_semaphoro_db_path, date, color_prediction, flanco, periodoAMostrar)		

				"""
				# Send the results back to consumer in main program				
				self.producer.send([numerical, color_prediction, flanco, periodoAMostrar])
			
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


def main(video):
	archivoDeVideo = video
	archivoParametrosACargar = archivoDeVideo[:-4]+'.npy'

	parametrosInstalacion = np.load(directorioDeVideos+'/'+archivoParametrosACargar)
	indicesSemaforo 	= parametrosInstalacion[0]
	poligonoSemaforo 	= np.array([indicesSemaforo[0],indicesSemaforo[184],indicesSemaforo[191],indicesSemaforo[7]])
	verticesPartida 	= parametrosInstalacion[1]
	verticesLlegada 	= parametrosInstalacion[2]
	verticesDerecha 	= parametrosInstalacion[3]
	verticesIzquierda 	= parametrosInstalacion[4]
	angulo 				= parametrosInstalacion[5][0]
	poligonoEnAlta 		= parametrosInstalacion[6]

	cap = cv2.VideoCapture(directorioDeVideos+'/'+archivoDeVideo)
	# Create semaphoro class
	semaphoro = CreateSemaforo(periodo = 0)

	fig = plt.figure()
	ax1 = fig.add_subplot(1,1,1)
	while True:
		_, frameVideo = cap.read()

		# Feed with images to semaphoro
		pixeles = np.array([frameVideo[indicesSemaforo[0][1],indicesSemaforo[0][0]]])
		for indiceSemaforo in indicesSemaforo[1:]:
			pixeles = np.append(pixeles,[frameVideo[indiceSemaforo[1],indiceSemaforo[0]]], axis=0)

		data = semaphoro.obtenerColorEnSemaforo(pixeles)
		print(data)


		raw 	= np.reshape(pixeles,(24,8,3))

		SHAPE 		= (320,240)
		img 		= cv2.cvtColor(raw, cv2.COLOR_BGR2RGB)
		hsv 		= cv2.cvtColor(raw, cv2.COLOR_BGR2HSV)

		# GREEN range
		lower_green = np.array([50,20,0], dtype=np.uint8)		#50# OPEN Green channels
		upper_green = np.array([90,255,255 ], dtype=np.uint8)   #95.255.255  ideal my square.

		# Combine the Channels
		mask_green 	= cv2.inRange(hsv, lower_green, 	upper_green)
		full_mask 	= mask_green

		# Put the mask and filter the R, Y , G colors in _imagen_
		#res 		= cv2.bitwise_and(img, hsv, mask = full_mask)

		inputImage 	= cv2.resize(full_mask, SHAPE, interpolation = cv2.INTER_CUBIC)



		cv2.imshow('fitler', inputImage)
		cv2.imshow('Semaphoro', cv2.resize(np.reshape(pixeles, (24,8,3)),(320,240)))
		#cv2.imshow('Semaphoro', cv2.resize(frameVideo,(320,240)))

		#cv2.imshow('Semaphoro', frameVideo)
		ch = 0xFF & cv2.waitKey(5)
		if ch == ord('q'):
			semaphoro.stop()
			break
	cv2.destroyAllWindows()
	c = cv2.waitKey(0)

if __name__ == '__main__':
	print(sys.argv)
	for entrada in sys.argv:
		print('INPUTS ARE', entrada)
		if ('.mp4' in entrada)|('.avi' in entrada):
			archivoDeVideo = entrada
	main(archivoDeVideo)