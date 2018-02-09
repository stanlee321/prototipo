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
			semaphoro = Simulation(self.input_q, periodo)
			semaphoro.start()
		else:
			# Case real one
			semaphoro = Real(self.input_q, self.ouput_q)
			semaphoro.start()
	def obtenerColorEnSemaforo(self, raw_images):
		self.input_q.put(raw_images)
		data = self.ouput_q.get()
		#numerico, literal, flanco, period = data[0], data[1], data[2], data[3]
		#return numerico, literal, flanco, period
		return data
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

		if os.path.isfile(path_to_svm_model) and os.path.isfile(self.path_to_img):
			print ("Using previous model... {}".format(path_to_svm_model))
			print ("Reading route to imagen.npy... {}".format(self.path_to_img))
			self.svm = pickle.load(open(path_to_svm_model, "rb"))
			self.imagen_semaphoro_raw = self.path_to_img
		else:
			print ("No model found in {}, please check the path to the ML model!!".format(path_to_svm_model))


		# idx to string
		self.idx_to_str = {1:'verde', 0:'else'}

		# expected shape of the image_semaphoro_raw (Weidth,Height,Channels)
		self.SHAPE = (24,8,3)
		# read Queue for put the results from inference.
		self.input_q = input_q
		self.ouput_q = ouput_q

		self.previous_state = None
		self.actual_state 	= None
		self.periodo = []

		# aux list
		#self.join_list 	= [0]*10
		self.littleFilter = [0]*19
		self.numericoAuxiliar = 0

		self.start_part = collections.deque(maxlen=10)
		self.mid_part   = collections.deque(maxlen=10)
		self.end_part  	= collections.deque(maxlen=10)
		# Deque for filter
		self.filter_deque = collections.deque(maxlen=10)
		self.filter_deque.append(self.actual_state)

		self.raw_states = collections.deque(maxlen=2)
		self.raw_states.append(self.actual_state)
		self.flanco = 0


		# Periodos
		self.tiempoParaPeriodo 		= time.time()
		self.ultimoPeriodo 			= time.time() - self.tiempoParaPeriodo
		self.maximoTiempoPeriodo	= 150			# 2 minutos y medio sera el timeout para determinar que no se esta viendo semaforo
		self.collection_periodos = collections.deque(maxlen=10)
		self.periodos_dict = {'verde':[], 'else':[]}

		self.mean_values = {'verde': float, 'else':float}
		self.std_values  = {'verde': float, 'else':float}


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
		
		X = self.extract_feature(imagen)
		Y = self.svm.predict(X)[0]
		###########################
		# END SVM PART (CLASSIFICATION) ML PROCESS
		###########################
		# Return prediction from SVM
		#print('prediction is', Y)
		if   Y == 'green':
			return 1
		else:
			return 0


	def prediction(self, imagen):


		Y = self.find_color(imagen)
		periodoAMostrar = 0

		#self.raw_states.append(colorPrediction)
		
		color_prediction = self.idx_to_str[Y]
		self.raw_states.append(color_prediction)
		self.checkflanco()
		if self.flanco == 1:
			periodoAMostrar 	   = self.ultimoPeriodo
			self.tiempoParaPeriodo = time.time()
			self.periodos_dict[color_prediction].append(periodoAMostrar)
			self.mean_values[color_prediction] = np.mean(self.periodos_dict[color_prediction][0:-1])#np.sum(self.periodos_dict[color_prediction])/len(self.periodos_dict[color_prediction])
			self.std_values[color_prediction]  = np.std(self.periodos_dict[color_prediction][0:-1])

			candidato = {'prediction': color_prediction, periodo_anterior[]}

			try:
				maximun_in_verde = np.max(self.mean_values['verde'])
				maximun_in_else  = np.max(self.mean_values['else'])

				periodo_amarillo = maximun_in_else  -  maximun_in_verde
				print('Periodo amarillo must be', periodo_amarillo) 

			except:
				pass
			print('COLOR', color_prediction)
			print('MEAN VALUES ARE:', self.mean_values)
			print('STD VALUES ARE:', self.std_values)

			#ultimo_value = self.periodos_dict[color_prediction][-1] 

			#if  ultimo_value - 1 <= ultimo_value <= ultimo_value +1:

			#	print('STILL IN THRESS,:', ultimo_value)

		self.ultimoPeriodo = time.time() - self.tiempoParaPeriodo

		return color_prediction, self.flanco, periodoAMostrar
		

	def checkflanco(self):
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

#  R-- G -> Y -> R --G 

	def filter(self):

		len_of_queue	= len(self.raw_states)

		first_part  	= list(self.raw_states)[0:9]
		mid_part 		= list(self.raw_states)[10:19]
		second_part 	= list(self.raw_states)[20:29]
		periodoAMostrar = 0

		try:

			t_one  = np.mean(Real.sigmoid(first_part))
			t_mid  = np.mean(Real.sigmoid(mid_part))
			t_two  = np.mean(Real.sigmoid(second_part))

			self.start_part.append(t_one)
			self.mid_part.append(t_mid)
			self.end_part.append(t_two)


			A = np.mean(np.array(list(self.start_part)))
			B = np.mean(np.array(list(self.mid_part)))
			C = np.mean(np.array(list(self.end_part)))
			print(A,B,C)	
			Z = np.max([A,B,C])
			print('Z is', Z)
			# if actual in red region
			if 0.60 <= Z <= 0.79 :
				self.actual_state = 1
			# green region
			if 0.41 <= Z <= 0.59:
				self.actual_state =  0
			#None
			if Z <= 0.4:
				self.actual_state = -1

			#self.littleFilter[19] = self.littleFilter[18]
			#self.littleFilter[18] = self.littleFilter[17]
			#self.littleFilter[17] = self.littleFilter[16]
			#self.littleFilter[16] = self.littleFilter[15]
			#self.littleFilter[15] = self.littleFilter[14]
			#self.littleFilter[14] = self.littleFilter[13]
			#self.littleFilter[13] = self.littleFilter[12]
			#self.littleFilter[12] = self.littleFilter[11]

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
			self.littleFilter[0] = self.actual_state
			numeroDeVerdes 	= 0
			numeroDeRojos 	= 0
			for colorNumeral in self.littleFilter:
				if colorNumeral==0:
					numeroDeVerdes+=1
				if colorNumeral==1:
					numeroDeRojos+=1
			if numeroDeVerdes	>=7:
				numerico = 0

			if numeroDeRojos	>=5:
				numerico = 1
			flancoCorrecto = 0

			# Si llegue a un valor valido entonces es posible generar flanco
			if (self.actual_state==0)|(self.actual_state==1)|(self.actual_state==2):
				#Si hay cambio entonces genero flanco:
				if self.actual_state != self.numericoAuxiliar:
					if self.actual_state == 0:
						flancoCorrecto = -1
					elif self.actual_state >= 1:
						flancoCorrecto = 1
					if (self.numericoAuxiliar == 2)&(self.actual_state==1):		# Si el valor anterior es amarillo se descarta el flanco
						flancoCorrecto = 0
					self.numericoAuxiliar = numerico
			else: # Si no llego a un valor valido repito
				self.actual_state = self.numericoAuxiliar

			# Si el flanco es correcto entonces genero los valores de periodo
			if flancoCorrecto == -1:
				periodoAMostrar = self.ultimoPeriodo
				self.tiempoParaPeriodo = time.time()

			self.ultimoPeriodo = time.time() - self.tiempoParaPeriodo
			# Si el periodo excede los 2 minutos (normalmente 2, 1 para debug) entonces señalo que no hay semaforo
			if self.ultimoPeriodo >self.maximoTiempoPeriodo:
				flancoCorrecto = 1				# Flanco verde para guardar la información que se tenga
				numerico = -2
			return self.actual_state, self.idx_to_str[self.actual_state], flancoCorrecto, periodoAMostrar
		except:
			print('Not ready yet')



	def run(self):
		while True:
			imagen = self.input_q.get(timeout=1)
			#color, literal_color, flanco, period = self.prediction(imagen)
			color_prediction, flanco, periodoAMostrar = self.prediction(imagen)
			#self.ouput_q.put([self.actual_state, literal_color, flanco, period])
			self.ouput_q.put([color_prediction, flanco, periodoAMostrar])


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
		#time.sleep(0.05)

		# Feed with images to semaphoro
		cropped = img[py1:py0, px0:px1]
		cropped_r = cv2.resize(cropped, (24,8))
		#scipy.misc.imsave(path_to_workdir, cropped)
		#cv2.rectangle(img,(px0,py0),(px1,py1),(0,255,0),1)
		data = semaphoro.obtenerColorEnSemaforo(cropped)
		#print(data)
		cv2.imshow('Semaphoro', cv2.resize(cropped,(320,240)))
		#cv2.imshow('Semaphoro', img)
		ch = 0xFF & cv2.waitKey(5)
		if ch == ord('q'):
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
		self.blueprint_semaforo = None
		if self.periodoSemaforo > 0 :
			self.blueprint_semaforo =  Simulado(periodoSemaforo = self.periodoSemaforo)
		else:
			self.blueprint_semaforo = Real()
	
	def obtenerColorEnSemaforo(self, imagenUnidimensional):
		numerico, literal, flancoErrado = self.blueprint_semaforo.encontrarSemaforoObtenerColor(imagen = imagenUnidimensional )
		#print('COLOR EN BRUTO: '+literal)
		if self.periodoSemaforo == 0 :
"""