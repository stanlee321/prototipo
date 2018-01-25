#!/usr/bin/env python
# semaforoFinal.py

import cv2
import numpy as np
import os
import pickle
import time
import threading
import multiprocessing
import collections
from collections import Counter

class Semaphoro():
	"""
		Class to check the states of a semaforo, also simulates one
		Init:
			periodo : int  # by feault 0, that means it runs the real case one
	"""
	def __init__(self, periodo = 30):
		# Set target of multiprocessing
		self.input_q = multiprocessing.Queue()
		if periodo > 0:
			# Case of simulation
			semaphoro = Simulation(self.input_q, periodo)
			semaphoro.start()
		else:
			# Case real one
			semaphoro = Real(self.input_q)
			semaphoro.start()
	def obtenerColorEnSemaforo(self):
		data = self.input_q.get()
		numerico, literal, flanco = data[0], data[1], data[2]
		return numerico, literal, flanco
	
	def stop(self):
		self.p.join()

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
		if current == past:
			self.flanco = 0
		elif current == 3 and past == 2:
			self.flanco = 1	
		elif current == 1 and past == 3:
			self.flanco = -1
		elif current == 2 and past == 1:
			self.flanco = 1
		else:
			print('No match found {}, {}, returning 0',format(current, past))

	def run(self):
		while True:
			time.sleep(self.sleeptime)
			self.check_simulated_state()
			self.input_q.put([self.actual_state, self.count, self.flanco])

	

class Real(multiprocessing.Process):
	"""
	Real Method,  use a SVM classifier to find color in some input ROI imagen, ouputs are:
	colorPrediction, literalColour, flanco

	Attributes:
		self.svm: 	load the Machine Learning, Support Vector Machine model trained on Red, Green, Black images 

		self.lower_yellow and so on... are range of colors where the SVM  where trained and
										the input image of the semaforo is thressholded.

	"""

	def __init__(self, queue):
		super(Real, self).__init__()
		print('......Starting REAL semaphoro....')
		# LOAD THE TRAINED SVM MODEL ... INTO THE MEMORY????
		path_to_svm_model = os.getenv('HOME') + '/' + 'trafficFlow' + '/' + 'prototipo' +'/' + 'model' + '/' + 'svm_model_(8, 24)_96_39.pkl'
		self.path_to_img = os.getenv('HOME') + '/' + 'WORKDIR' + '/' + 'imagen.npy'
		if os.path.isfile(path_to_svm_model) and os.path.isfile(path_to_img):
			print ("Using previous model... {}".format(path_to_svm_model))
			print ("Reading route to imagen.npy... {}".format(path_to_img))
			self.svm = pickle.load(open(path_to_svm_model, "rb"))
			self.imagen_semaphoro_raw = path_to_img
		else:
			print ("No model found in {}, please check the path to the ML model!!".format(path_to_svm_model))

		# expected shape of the image_semaphoro_raw (Weidth,Height,Channels)
		self.SHAPE = (8,24,3)
		# read Queue for put the results from inference.
		self.input_q = queue


		# YELLOW /(Orangen) range
		self.lower_yellow = np.array([18,40,190], dtype=np.uint8) # 18,40,190
		self.upper_yellow = np.array([27,255,255], dtype=np.uint8)

		# RED range
		self.lower_red = np.array([255,255,255], dtype=np.uint8) #_,100,_ # 140,70,_
		self.upper_red = np.array([180,255,255], dtype=np.uint8)

		# GREEN range
		self.lower_green = np.array([70,10,0], dtype=np.uint8) #_,0,_ , _,50,_
		self.upper_green = np.array([90,255,255], dtype=np.uint8)

		# Deque for filter
		self.filter_dequeu = collections.deque(maxlen=10)

		self.previous_state = None
		self.actual_state = None

	@staticmethod
	def reader(plain_img):
		# Posible positino of colors
		lenght_of_stream = len(list(plain_img))
		red    = plain_img[0: int(0.35*lenght_of_stream)]
		yellow = plain_img[int(0.35*lenght_of_stream): int(0.75*lenght_of_stream)]
		green  = plain_img[int(0.75*lenght_of_stream): ]
		return red,yellow,green

	@staticmethod
	def extract_feature(image_file):

		SHAPE = (24, 8)
		img = cv2.imread(image_file)
		img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

		hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
		# SOME MASKS
		mask_red = cv2.inRange(hsv, self.lower_red, self.upper_red)
		mask_yellow = cv2.inRange(hsv, self.lower_yellow, self.upper_yellow)
		mask_green = cv2.inRange(hsv, self.lower_green, self.upper_green)

		full_mask = mask_red + mask_yellow + mask_green

		# Put the mask and filter the R, Y , G colors in _imagen_
		res = cv2.bitwise_and(img, img, mask= full_mask)
		#res = cv2.bilateralFilter(res,35,35,35)
		img = cv2.resize(res, SHAPE, interpolation = cv2.INTER_CUBIC)
		img = img.flatten()
		img = img/255
#		x = x.reshape(1, -1)
		return img

	@staticmethod
	def sigmoid(t):
		s = 1 / (1+np.exp(-t))
		return s

	def find_color(self):

		imagen = self.path_to_img

		X = self.extract_feature(imagen)
		Y = self.svm.predict(X)[0]
		###########################
		# END SVM PART (CLASSIFICATION) ML PROCESS
		###########################
		# Return prediction from SVM
		if   Y == 'green':
			return 0
		elif Y == 'red':
			return 1
		elif Y == 'yellow':
			return 2
		elif Y == 'black':
			return -1
		else:
			pass

	def prediction(self):
		colorPrediction = self.find_color()

		self.filter_deque.append(colorPrediction)


		prediction = self.filter()


		if colorPrediction == 1:
			literalColour = 'ROJO'
		elif colorPrediction == 0:
			literalColour = 'VERDE'
		else:
			literalColour = 'No hay Semaforo'

		return colorPrediction, literalColour, self.flanco


	def filter(self):
		queu_len = len(self.filter_deque)
		raw_deque = self.filter_deque
		counts = Counter(raw_deque)

		# Check number of values in deque
		uniques = list(set(raw_deque))

		if len(uniques) == 1:
			#normal condiction
			actual_state = uniques[-1]

		if len(uniques) == 2:

			n1 = counts[uniques[-1]]
			n2 = counts[uniques[-2]]

			c_state_1   = max(n1,n2)
			c_state_2   = min(n1,n2)

			state_1_p = c_state_1 / queu_len
			state_2_p = c_state_2 / queu_len
			
			if  state_1_p > state_2_p :

				previous_state = uniques[-1]
				actual_state   = uniques[-2] 

			elif state_1_p < state_2_p:
			
				previous_state = uniques[-2]
				actual_state   = uniques[-1]
			
			elif state_1_p == state_2_p:
				previous_state = uniques[-1]
				actual_state   = uniques[-2] 
			else:
				pass
		if len(uniques) > 2:
			self.fill_holes(raw_deque)
			# anromal situation

	def fill_holes(self, raw_deque):
		maping = {}
		aux_list = []
		for i, value in enumerate(raw_deque):
			value = raw_deque.index(value)
			aux_list.append(value)
			maping[value] = aux_list



	def checkflanco(self):
		past, current = self.states[0], self.states[1]
		#
		# Compare the current and pass colors to set self.flanco value 
		#
		if current == past:
			self.flanco = 0
		elif current == 3 and past == 2:
			self.flanco = 1	
		elif current == 1 and past == 3:
			self.flanco = -1
		elif current == 2 and past == 1:
			self.flanco = 1
		else:
			print('No match found {}, {}, returning 0',format(current, past))
	def run(self):
		while True:
			color, literal_color, flanco = self.prediction()
			self.input_q.put([self.actual_state, self.count, self.flanco])




if __name__ == '__main__':
	#cap = cv2.VideoCapture('./installationFiles/sar.mp4')
	#data = np.load('./installationFiles/sar.npy')
	#print(data)
	semaphoro = Semaphoro(periodo = 30)
	#poligono  = data[0]
	#print(data[0])
	counter = 0 
	while True:
		#_, img = cap.read()
		time.sleep(1)
		print(semaphoro.obtenerColorEnSemaforo())
		#print('STATES:', semaphoro.numerico, semaphoro.literal,semaphoro.flanco)
		print(' Main While loop',  counter)
		counter +=1
		#cv2.imshow('mask_image',img)

		ch = 0xFF & cv2.waitKey(5)
		if ch == 27:
			break
	cv2.destroyAllWindows()
	c = cv2.waitKey(0)



"""
class CreateSemaforo(Semaforo):
	
	#Create the requested semaforo according the the periodoSemaforo values,
	#Attributes:
	#	periodoSemaforo == 0 for Real semoforo creation
	#	periodoSemaforo != for Simulated Semaforo
	#	self.blueprint_semaforo, is the interface for parent and childs classes attributes 
	#							and methods sharing.
	
	def __init__(self, periodoSemaforo=30):
		self.periodoSemaforo = periodoSemaforo
		#
		# Init parent attributes and methods
		#
		super().__init__()
		self.littleFilter = [0,0,0,0,0,0,0,0,0,0,0,0]	
		self.blueprint_semaforo = None
		self.numericoAuxiliar = 0
		if self.periodoSemaforo > 0 :
			self.blueprint_semaforo =  Simulado(periodoSemaforo = self.periodoSemaforo)
		else:
			self.blueprint_semaforo = Real()
	
	def obtenerColorEnSemaforo(self, imagenUnidimensional):
		numerico, literal, flancoErrado = self.blueprint_semaforo.encontrarSemaforoObtenerColor(imagen = imagenUnidimensional )
		#print('COLOR EN BRUTO: '+literal)
		periodoAMostrar = 0
		if self.periodoSemaforo == 0 :
			self.littleFilter[11] = self.littleFilter[10]
			self.littleFilter[10] = self.littleFilter[9]
			self.littleFilter[9] = self.littleFilter[8]
			self.littleFilter[8] = self.littleFilter[7]
			self.littleFilter[7] = self.littleFilter[6]
			self.littleFilter[6] = self.littleFilter[5]
			self.littleFilter[5] = self.littleFilter[4]
			self.littleFilter[4] = self.littleFilter[3]
			self.littleFilter[3] = self.littleFilter[2]
			self.littleFilter[2] = self.littleFilter[1]
			self.littleFilter[1] = self.littleFilter[0]
			self.littleFilter[0] = numerico
			numeroDeVerdes = 0
			numeroDeRojos = 0
			for colorNumeral in self.littleFilter:
				if colorNumeral==0:
					numeroDeVerdes+=1
				if colorNumeral==1:
					numeroDeRojos+=1
			if numeroDeVerdes>=7:
				numerico = 0
			if numeroDeRojos>=5:
				numerico = 1
			
		flancoCorrecto = 0

		# Si llegue a un valor valido entonces es posible generar flanco
		if (numerico==0)|(numerico==1)|(numerico==2):
			#Si hay cambio entonces genero flanco:
			if numerico != self.numericoAuxiliar:
				if numerico == 0:
					flancoCorrecto = -1
				elif numerico >= 1:
					flancoCorrecto = 1
				if (self.numericoAuxiliar == 2)&(numerico==1):		# Si el valor anterior es amarillo se descarta el flanco
					flancoCorrecto = 0
				self.numericoAuxiliar = numerico
		else: # Si no llego a un valor valido repito
			numerico = self.numericoAuxiliar

		# Si el flanco es correcto entonces genero los valores de periodo
		if flancoCorrecto == -1:
			periodoAMostrar = self.blueprint_semaforo.ultimoPeriodo
			self.blueprint_semaforo.tiempoParaPeriodo = time.time()

		self.blueprint_semaforo.ultimoPeriodo = time.time() - self.blueprint_semaforo.tiempoParaPeriodo
		# Si el periodo excede los 2 minutos (normalmente 2, 1 para debug) entonces señalo que no hay semaforo
		if self.blueprint_semaforo.ultimoPeriodo >self.maximoTiempoPeriodo:
			flancoCorrecto = 1				# Flanco verde para guardar la información que se tenga
			numerico = -2
		

		return numerico, literal, flancoCorrecto, periodoAMostrar


"""