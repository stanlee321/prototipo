#!/usr/bin/env python

import numpy as np
import cv2
import matplotlib.pyplot as plt

class FlowDetector():
	def __init__(self,angle=55):	#size (320,240)
		#Auxiliar variables
		# La primera imagen de inicializacion puede entrar en escala a color
		self.anchoZebra = 0
		self.largoZebra = 0
		self.sizeZebra = (self.anchoZebra,self.largoZebra)
		self.centrox = 0
		self.centroy = 0
		self.centroFrame = (self.centrox,self.centroy)

		self.auxiliar_image = np.array([])

		# Class variables
		self.theta = angle
		self.optimalStep = 14	#8 ruidoso

		# flow sume fx,fy va
		self.vertices = []

		# parámetrosFisicos
		self.velocidades=[]
		self.momentumActual = 0


		# Variables para el filtro:
		self.MagnitudesVelocidad = np.array((0.0,0.0,0.0,0.0))
		self.MagnitudesVelocidadFiltradas = np.array((0.0,0.0,0.0,0.0))
		self.velocidadesFiltradas = []
		self.a_coeff = np.array((1.,-1.1429805,0.4128016,0,0,0)) #0.8hz
		self.b_coeff = np.array((0.06745527, 0.13491055, 0.06745527,0,0,0))
		#self.a_coeff = np.array(( 1.,-1.45424359,0.57406192,0,0,0)) #0.5 hz
		#self.b_coeff = np.array((0.02995458,0.05990916,0.02995458,0,0,0))
		self.a_coeff = np.array(( 1.,-2.37409474,1.92935567,-0.53207537))# AGRESSIVE
		self.b_coeff = np.array(( 0.00289819,0.00869458,0.00869458,0.00289819))
		
		# Deteccion de automoviles
		## Cambio aqui para menor densidad
		self.minimoValorVelocidad = 4	# Da inicio a un lobulo de acuerdo a su amplitud, 5 para automoviles rapidos
		self.velocidadesSinNegativo = []
		self.pulsosAutomoviles_funcionSigno = []
		self.minimoMomentum = 20
		self.indiceActual = 0

		#Auxiliares
		self.font = cv2.FONT_HERSHEY_SIMPLEX

	def borrarRegistros(self):
		self.velocidades=[]
		self.velocidadesFiltradas = []
		self.velocidadesSinNegativo = []
		self.pulsosAutomoviles_funcionSigno = []


	def inicializarClase(self,imagen):
		# La primera imagen de inicializacion puede entrar en escala a color
		self.anchoZebra = imagen.shape[1]
		self.largoZebra = imagen.shape[0]
		self.sizeZebra = (self.anchoZebra,self.largoZebra)
		self.centrox = self.anchoZebra // 2
		self.centroy = self.largoZebra // 2
		self.centroFrame = (self.centrox,self.centroy)

		self.auxiliar_image = self.introduce_image(imagen)

	def introduce_image(self,imagen):
		try:
			imagen = cv2.cvtColor(np.array(imagen), cv2.COLOR_BGR2GRAY)
		except:
			print('Chequea la imagen dude')
		return imagen

	# Unicamente alteramos la imagen como auxiliar, con los estándares de normalización
	def set_previousImage(self,previousImage):
		self.auxiliar_image = self.introduce_image(previousImage)
		return self.auxiliar_image

	def draw_vector(self,imagen,vector,color):
		cv2.line(imagen,(self.centroFrame[0],self.centroFrame[1]),(self.centroFrame[0]+int(vector[0]),self.centroFrame[1]+int(vector[1])),color,2)
		return imagen

	def procesarNuevoFrame(self, current_image):
		y, x = np.mgrid[self.optimalStep/2:self.largoZebra:self.optimalStep, self.optimalStep/2:self.anchoZebra:self.optimalStep].reshape(2,-1)
		y = np.int32(y)
		x = np.int32(x)
		#flow = cv2.calcOpticalFlowFarneback(self.auxiliar_image, current_image, pyr_scale, levels, winsize, iterations, poly_n, poly_sigma, flags, flow)
		current_image = self.introduce_image(current_image)
		flow = cv2.calcOpticalFlowFarneback(self.auxiliar_image, current_image, None, 0.5, 3, 15, 3, 5, 1.2, 0) #(self.auxiliar_image, current_image, None, 0.7, 3, 9, 3, 5, 1.2, 0)
		fx, fy = flow[y,x].T
		total_flow_framex = sum(fx)
		total_flow_framey = sum(fy)
		total_flow = np.array([total_flow_framex, total_flow_framey])
		module = np.sqrt(total_flow[0]**2  + total_flow[1]**2)
		lines = np.vstack([x, y, x+fx, y+fy]).T.reshape(-1, 2, 2)
		lines = np.int32(lines + 0.5)
		self.auxiliar_image = current_image
		return total_flow, module, lines
		
	def procesarFlujoEnTiempoReal(self,vector):
		unitary_vector = np.array([-1,0])
		scalar_vel = vector[0]*unitary_vector[0] + vector[1]*unitary_vector[1]
		vector_vel = scalar_vel * unitary_vector
		noisyVector = np.sqrt(vector_vel[0]**2 + vector_vel[1]**2)

		#Filtrando vector
		self.MagnitudesVelocidad[3] = self.MagnitudesVelocidad[2]
		self.MagnitudesVelocidad[2] = self.MagnitudesVelocidad[1]
		self.MagnitudesVelocidad[1] = self.MagnitudesVelocidad[0]
		self.MagnitudesVelocidad[0] = scalar_vel
		
		self.MagnitudesVelocidadFiltradas[3] = self.MagnitudesVelocidadFiltradas[2]
		self.MagnitudesVelocidadFiltradas[2] = self.MagnitudesVelocidadFiltradas[1]
		self.MagnitudesVelocidadFiltradas[1] = self.MagnitudesVelocidadFiltradas[0]
		self.MagnitudesVelocidadFiltradas[0] = - self.a_coeff[1]*self.MagnitudesVelocidadFiltradas[1]-self.a_coeff[2]*self.MagnitudesVelocidadFiltradas[2]-self.a_coeff[3]*self.MagnitudesVelocidadFiltradas[3]+self.b_coeff[0]*self.MagnitudesVelocidad[0]+self.b_coeff[1]*self.MagnitudesVelocidad[1]+self.b_coeff[2]*self.MagnitudesVelocidad[2]+self.b_coeff[3]*self.MagnitudesVelocidad[3]
		
		smooth_vector = self.MagnitudesVelocidadFiltradas[0]*unitary_vector

		velocidadReal = self.MagnitudesVelocidadFiltradas[0]*7.2/100 #km/h
		self.velocidades.append(self.MagnitudesVelocidad[0])
		self.velocidadesFiltradas.append(self.MagnitudesVelocidadFiltradas[0])
		if self.MagnitudesVelocidadFiltradas[0] <= self.minimoValorVelocidad:
			self.velocidadesSinNegativo.append(0)
		else:
			self.velocidadesSinNegativo.append(self.MagnitudesVelocidadFiltradas[0])
		
		self.pulsosAutomoviles_funcionSigno.append(100*np.sign(self.velocidadesSinNegativo[len(self.velocidadesSinNegativo)-1]-self.velocidadesSinNegativo[len(self.velocidadesSinNegativo)-2]))
		self.momentumActual += self.velocidadesSinNegativo[len(self.velocidadesSinNegativo)-1]
		flancoDeSubida = self.pulsosAutomoviles_funcionSigno[len(self.pulsosAutomoviles_funcionSigno)-1]-self.pulsosAutomoviles_funcionSigno[len(self.pulsosAutomoviles_funcionSigno)-2]
		self.indiceActual = 0
		# En el flanco de subida se resetea el momentum
		if (flancoDeSubida > 0)&(self.pulsosAutomoviles_funcionSigno[len(self.pulsosAutomoviles_funcionSigno)-1]==100):
			self.indiceActual = 1
		# En el flanco de bajada se resetea el momentum a -1 simbolizando que no hay automovil

		if (flancoDeSubida > 0):
			self.momentumActual = 0

		if (flancoDeSubida < 0):
			self.indiceActual = -self.momentumActual

		return self.momentumActual, smooth_vector, noisyVector, velocidadReal, self.indiceActual

	def obtenerPulsoAutomoviles(self):
		return self.pulsosAutomoviles_funcionSigno[len(self.pulsosAutomoviles_funcionSigno)-1]

	def obtenerVelocidadSinNegativo(self):
		return self.velocidadesSinNegativo[len(self.velocidadesSinNegativo)-1]