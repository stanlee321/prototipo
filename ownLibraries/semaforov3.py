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

import logging 
import pandas as pd


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
		#raw 	= np.reshape(raw,(24,8,3))
		
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
			time.sleep(self.sleeptime)
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


	@staticmethod	
	def _extract_feature(raw_image):
		SHAPE 		= (24, 8)
		img 		= cv2.cvtColor(raw_image, cv2.COLOR_BGR2RGB)
		hsv 		= cv2.cvtColor(raw_image, cv2.COLOR_BGR2HSV)

		# SOME MASKS
		lower_yellow = 	np.array([255,255,255], dtype=np.uint8) # CLOSE all the colors for YELLOW
		upper_yellow =	np.array([255,255,255], dtype=np.uint8)

		# RED range
		lower_red 	= np.array([255,255, 255], dtype=np.uint8) 	# CLOSE all the colors for RED
		upper_red 	= np.array([180,255,255], dtype=np.uint8)

		# GREEN range
		lower_green = np.array([22,10,0], dtype=np.uint8)		# OPEN Green channels
		upper_green = np.array([95,255,255 ], dtype=np.uint8)

		# Combine the Channels
		mask_red 	= cv2.inRange(hsv, lower_red, 		upper_red)
		mask_yellow = cv2.inRange(hsv, lower_yellow,	upper_yellow)
		mask_green 	= cv2.inRange(hsv, lower_green, 	upper_green)
		full_mask 	= mask_red + mask_yellow + mask_green

		# Put the mask and filter the R, Y , G colors in _imagen_
		res 		= cv2.bitwise_and(raw_image, raw_image, mask = full_mask)
		inputImage 	= cv2.resize(res, SHAPE, interpolation = cv2.INTER_CUBIC)

		# Set 1D array
		inputImage 	= inputImage.flatten()
		
		# Normalize to 0-1 range
		inputImage 	= inputImage / 255

		# Return Data for Machine Learning Classifica
		return inputImage.reshape(1, -1)

	@staticmethod
	def _sigmoid(x):
		s = 1 / (1+np.exp(-np.asarray(x)))
		return s

	def _find_color(self, imagen):
		# ML PROCESS
		X = self._extract_feature(imagen)
		Y = self.svm.predict(X)[0]
		###########################
		# END SVM PART (CLASSIFICATION) 
		###########################
		# Return prediction from SVM

		if   Y == 'green':
			return 0
		else:
			return 1


	def prediction(self, imagen_raw):

		# Obtain the prediction
		Y = self._find_color(imagen_raw)

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

			if round(periodoAMostrar) <= self.is_noice_thress: # If periodo para mostrar is less of 0 , this is noice ... pass
				self.logger.warning('NOICE NOICE with  periodoAMostrar: {}'.format(periodoAMostrar))
			else:
				self.periodos_dict[color_prediction].append(periodoAMostrar) 	# append the periods to the global dict deques
				
				actualTime 	= datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S') # Get acutal time to row data
				AUX_ROW 	= {'periodo': periodoAMostrar, 'time': actualTime}		# Auxilar Dictionary to pass into the dicts.

				self.periodosToNumpy[color_prediction].append(AUX_ROW) 			# append to periodostoNumpy
				
				print('color_prediction', self.periodos_dict	)
				# calculate the mean and std of this periodos
				self.mean_values[color_prediction] = np.mean(self.periodos_dict[color_prediction])  # TODO Check Limits 0: to...
				self.std_values[color_prediction]  = np.std(self.periodos_dict[color_prediction])	# TODO Check Limits 0: to...


				# Check if list is in the limit of 40 elements.
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
	"""
	TODO MAKE THIS FUNCTIONAL
	def filter(self):
		queue		= list(self.global_shard)
		try:
			n_elements	= dict(Counter(queue))

			print(n_elements)
			n_elses 	= n_elements['else']
			n_greens 	= n_elements['verde']


			prob_elses  = np.mean(Real.sigmoid(n_elses))
			prob_greens = np.mean(Real.sigmoid(n_greens))

			if prob_elses > prob_greens:
				return 'else'
			else:
				return 'verde'
		except:
			return queue[-1]
	"""
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
		run_camera = 1 
		while run_camera == 1:
			if 	self.resiver.poll(): # Check if exist input images from main program.
				# Read images form sender
				imagen = self.resiver.recv()

				# Return predictions 
				numerical, color_prediction, flanco, periodoAMostrar = self.prediction(imagen)

				# if Flanco is != from 0, add the above results to DB 
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


if __name__ == '__main__':
	path_to_video_test	= os.getenv('HOME') + '/' + 'trafficFlow' + '/' + 'trialVideos' +'/' + 'out.mp4'
	data 				= np.load('../installationFiles/mySquareSEMAPHORO.npy')
	path_to_workdir 	= os.getenv('HOME') + '/' + 'WORKDIR' + '/' + 'imagen.png'

	cap 				= cv2.VideoCapture(path_to_video_test)

	# Load position of semaphoro
	sem_img 	= data[-1]
	px0 		= int(sem_img[0][0])
	py0 		= int(sem_img[0][1])
	px1 		= int(sem_img[1][0]*1.12)
	py1 		= int(sem_img[1][1])

	print('INSTALLTION DATA', sem_img)
	# Create semaphoro class
	semaphoro = CreateSemaforo(periodo = 0)
	while True:
		_, img = cap.read()

		# Feed with images to semaphoro
		cropped = img[py1:py0, px0:px1]
		cropped_r = cv2.resize(cropped, (24,8))
		#scipy.misc.imsave(path_to_workdir, cropped)
		#cv2.rectangle(img,(px0,py0),(px1,py1),(0,255,0),1)
		data = semaphoro.obtenerColorEnSemaforo(cropped)
		print(data)
		cv2.imshow('Semaphoro', cv2.resize(cropped,(320,240)))
		#cv2.imshow('Semaphoro', img)
		ch = 0xFF & cv2.waitKey(5)
		if ch == ord('q'):
			semaphoro.stop()
			break
	cv2.destroyAllWindows()
	c = cv2.waitKey(0)

