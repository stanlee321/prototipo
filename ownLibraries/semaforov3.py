#!/usr/bin/env python
# semaforoFinal.py
import cv2
import numpy as np
import os
import pickle
import time
import multiprocessing
import collections
from collections import Counter
import  scipy.misc

class Semaphoro():
	"""
		Class to check the states of a semaforo, also simulates one
		Init:
			periodo : int  # by feault 0, that means it runs the real case one
	"""
	def __init__(self, periodo = 30):
		# Set target of multiprocessing
		self.input_q = multiprocessing.Queue()
		self.ouput_q = multiprocessing.Queue()
		if periodo > 0:
			# Case of simulation
			self.semaphoro = Simulation(self.input_q, periodo)
			self.semaphoro.start()
		else:
			# Case real one
			self.semaphoro = Real(self.input_q, self.ouput_q)
			self.semaphoro.start()
	def obtenerColorEnSemaforo(self, raw):

		raw_images 	= np.reshape(raw,(24,8,3))
		self.input_q.put(raw_images)
<<<<<<< HEAD
		try:
			data = self.ouput_q.get()
			return data
		except:
			pass
=======
		data 		= self.ouput_q.get()
>>>>>>> a69f4acb7ce8ed255c454732f259de1e3ff23d2e
		#numerico, literal, flanco, period = data[0], data[1], data[2], data[3]
		#return numerico, literal, flanco, period
	def stop(self):
		self.semaphoro.join()
		self.semaphoro.exit()



class Simulation(multiprocessing.Process):
	"""docstring for ProcessSimulation"""
	def __init__(self, queue, periodo):
		super(Simulation, self).__init__()
		print('WELCOME to SIMULATION')
		self.input_q = queue
		self.periodo = periodo
		self.count = 0.0
		self.actual_state = 1  			# g = 1, y = 2, r = 3
		self.sleeptime = 1.0
		self.states = collections.deque(maxlen=2)
		self.states.append(self.actual_state)
		
		self.flanco = 0
	def counter(self):
		self.count += 1
		return self
	def check_simulated_state(self):
		self.counter()
		self.states.append(self.actual_state)

		print('bedore dequeu', self.count)
		print('dequeu', self.states)


		self.actual_state = self.states[-1]


		if self.actual_state == 1:
			if self.count == self.periodo:
				self.count = 0.0
				self.actual_state = 2
		if self.actual_state == 2:
			if self.count == 3.0:
				self.count = 0.0
				self.actual_state = 3
		if self.actual_state == 3:
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
		elif current == 3 and past == 2:	# if current state = 
			self.flanco = 1	
		elif current == 1 and past == 3:
			self.flanco = -1
		elif current == 2 and past == 1:
			self.flanco = 1
		else:
			print('No match found, current: {},  past: {}, returning 0',format(current, past))

	def run(self):
		while True:
			time.sleep(self.sleeptime)
			self.check_simulated_state()
			self.input_q.put([self.actual_state, self.count, self.flanco])


class Real(multiprocessing.Process):


	def __init__(self, input_q, ouput_q):
		super(Real, self).__init__()
		print('......Starting REAL semaphoro....')
		
		# LOAD THE TRAINED SVM MODEL ... INTO THE MEMORY????
		path_to_svm_model = os.getenv('HOME') + '/' + 'trafficFlow' + '/' + 'prototipo' +'/' + 'model' + '/' + 'binary.pkl'
		path_to_keras_model = os.getenv('HOME') + '/' + 'trafficFlow' + '/' + 'prototipo' +'/' + 'model' + '/' + 'model.h5'

		self.path_to_img = os.getenv('HOME') + '/' + 'WORKDIR' + '/' + 'imagen.png'

		if os.path.isfile(path_to_svm_model):# and os.path.isfile(self.path_to_img):
			print ("Using previous model... {}".format(path_to_svm_model))
			#print ("Reading route to imagen.npy... {}".format(self.path_to_img))
			self.svm = pickle.load(open(path_to_svm_model, "rb"))
			#self.imagen_semaphoro_raw = self.path_to_img
		else:
			print ("No model found in {}, please check the path to the ML model!!".format(path_to_svm_model))


		# idx to string
		self.idx_to_str = {0:'verde', 1:'else'}
		self.str_to_ids = {'verde':0 , 'else': 1, 'amarillo':2, 'rojo': 1 }

		# expected shape of the image_semaphoro_raw (Weidth,Height,Channels)
		self.SHAPE = (24,8,3)
		# read Queue for put the results from inference.
		self.input_q = input_q
		self.ouput_q = ouput_q


		self.periodo = []


		# Periodos
		self.tiempoParaPeriodo 		= time.time()
		self.ultimoPeriodo 			= time.time() - self.tiempoParaPeriodo

		self.tiempo_para_periodo_amarillo 	= time.time()
		self.ultimo_periodo_amarillo		= time.time() - self.tiempo_para_periodo_amarillo

		self.maximoTiempoPeriodo	= 150			# 2 minutos y medio sera el timeout para determinar que no se esta viendo semaforo

		random_number_1 = np.random.random_sample()*100
		random_number_2 = np.random.random_sample()*100
		random_number_3 = np.random.random_sample()*100
		random_number_4 = np.random.random_sample()*100


		self.periodos_dict = {'verde':[], 'else':[]}
		self.mean_values = {'verde': random_number_1, 'else':random_number_2}
		self.std_values  = {'verde': random_number_3, 'else':random_number_4}


		self.global_actual_state	= str
		self.global_previous_state	= str

		self.global_shard    	= collections.deque(maxlen=40)	


		self.principal_shard    = collections.deque(maxlen=2)	
		self.raw_states 		= collections.deque(maxlen=2)

		self.raw_states.append(self.global_actual_state)
		

		self.flanco = 0

		self.local_actual_state		= str
		self.local_previous_state	= str

		self.countdown = Timer()



	@staticmethod	
	def extract_feature(image_file):
		img 		= image_file
		SHAPE 		= (24, 8)
		img 		= cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
		hsv 		= cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

		# SOME MASKS
		lower_yellow = 	np.array([255,255,255], dtype=np.uint8) #_18_40_190
		upper_yellow =	np.array([255,255,255], dtype=np.uint8)

		# RED range
		lower_red 	= np.array([255,255, 255], dtype=np.uint8) #_,70,_
		upper_red 	= np.array([180,255,255], dtype=np.uint8)

		# GREEN range
		lower_green = np.array([22,10,0], dtype=np.uint8)
		upper_green = np.array([95,255,255 ], dtype=np.uint8)


		mask_red 	= cv2.inRange(hsv, lower_red, 		upper_red)
		mask_yellow = cv2.inRange(hsv, lower_yellow,	upper_yellow)
		mask_green 	= cv2.inRange(hsv, lower_green, 	upper_green)

		full_mask 	= mask_red + mask_yellow + mask_green

		# Put the mask and filter the R, Y , G colors in _imagen_
		res 		= cv2.bitwise_and(img, img, mask = full_mask)
		#res = cv2.bilateralFilter(res,35,35,35)
		#cv2.imshow('Semaphoro', cv2.resize(res,(320,240)))

		img 		= cv2.resize(res, SHAPE, interpolation = cv2.INTER_CUBIC)
		img 		= img.flatten()
		img 		= img / 255
		img         = img.reshape(1, -1)
		return img

	@staticmethod
	def sigmoid(x):
		x = np.asarray(x)
		s = 1 / (1+np.exp(-x))
		return s

	def find_color(self,imagen):
		# ML PROCESS
		X = self.extract_feature(imagen)
		Y = self.svm.predict(X)[0]
		###########################
		# END SVM PART (CLASSIFICATION) 
		###########################
		# Return prediction from SVM

		if   Y == 'green':
			return 0
		else:
			return 1


	def prediction(self, imagen):

		# Obtain the prediction
		Y = self.find_color(imagen)

		# Reset global counter
		periodoAMostrar = 0
		
		# get color as literal
		color_prediction = self.idx_to_str[Y]

		#self.global_shard.append(color_prediction_raw)
		#color_prediction = self.filter()

		# Append the prediction to global buffer
		self.raw_states.append(color_prediction)


		# Calculate the global flanco
		self._checkflanco_simple()
		
		# Check the global flanco and calculate the mean and std of this period
		if self.flanco == 1:
			periodoAMostrar 	   = self.ultimoPeriodo
			self.tiempoParaPeriodo = time.time()
			# If periodo para mostrar is less of 0 , this is noice ... pass
			if round(periodoAMostrar) <= 0:
				print('Noice...')
			else:
				# append the periods to the global dict 
				self.periodos_dict[color_prediction].append(periodoAMostrar)

				# calculate the mean and std of this periodos
				self.mean_values[color_prediction] = np.mean(self.periodos_dict[color_prediction][0:])
				self.std_values[color_prediction]  = np.std(self.periodos_dict[color_prediction][0:])
		else:
			pass


		# Update the last period
		self.ultimoPeriodo = time.time() - self.tiempoParaPeriodo
			
		if self.mean_values['else'] > 150:
			return 'No hay Semaphoro!!!!!!!!', 0, 0
		# if std of verde and else are less of 1.5 continue to the G-Y-R semaphoro
		if (self.std_values['verde'] < 1.5 ) and (self.std_values['else'] < 1.5 ) :

			# if exist enought values to calculate the std above of 0.0 continue to G-Y-R semaphoro 
			

			if (self.std_values['verde'] != 0.0 ) and (self.std_values['else'] != 0.0 ):
				
				# calculate the periodos of the three colors:
				periodo_verde 	 = self.mean_values['verde'] + self.std_values['verde']
				periodo_else	 = self.mean_values['else'] + self.std_values['else']
				periodo_amarillo = periodo_else - periodo_verde
				periodo_rojo 	 = periodo_else - periodo_amarillo

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
					pass
				#print(self.local_actual_state, flanco, periodo_amarillo)
				#color_prediction = self.local_actual_state

				#return color_prediction, self.flanco, periodoAMostrar
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

	def run(self):
		while True:
			imagen = self.input_q.get(timeout=1)
			#color, literal_color, flanco, period = self.prediction(imagen)
			numerical, color_prediction, flanco, periodoAMostrar = self.prediction(imagen)
			#self.ouput_q.put([self.actual_state, literal_color, flanco, period])
			self.ouput_q.put([numerical, color_prediction, flanco, periodoAMostrar])





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
	path_to_video_test	= os.getenv('HOME') + '/' + 'trafficFlow' + '/' + 'trialVideos' +'/' + 'mySquare.mp4'
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
	semaphoro = Semaphoro(periodo = 0)
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
			#semaphoro.stop()
			break
	cv2.destroyAllWindows()
	c = cv2.waitKey(0)

