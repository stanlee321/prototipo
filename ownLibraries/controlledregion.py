"""
This class contains all installation obtained data and derivatives of that
"""

import os
import sys
import cv2
import math
import numpy as np

class ControlledRegion():
	"""
	This class consists in all geometric elements regarding:
	- Departure
	- Arrival 
	- Arrival to the left
	- Arrival to the right
	Including all auxiliar geometric figures from them
	"""
	def __init__(self,poligonoPartida,poligonoLlegada,poligonoDerecha,poligonoIzquierda,anguloCarril=0):
		self.departureArea = np.array(poligonoPartida)
		self.arrivalArea = np.array(poligonoLlegada)
		self.rightArrivalArea = np.array(poligonoDerecha)
		self.leftArrivalArea = np.array(poligonoIzquierda)
		self.carrilAngle = -anguloCarril
		self.desplazamiento = np.array([8*math.cos(self.carrilAngle),8*math.sin(self.carrilAngle)])
		self.angulo = 18
		# La linea de pintado LK y trasera son los puntos del paso de cebra
		self.lineaDePintadoLK =  np.array([poligonoPartida[0],poligonoPartida[3]])
		self.lineaTraseraLK =  np.array([poligonoPartida[1],poligonoPartida[2]])
		ditanciaEnX = self.lineaDePintadoLK[1][0] - self.lineaDePintadoLK[0][0]
		ditanciaEnY = self.lineaDePintadoLK[1][1] - self.lineaDePintadoLK[0][1]
		vectorParalelo = self.lineaDePintadoLK[1] - self.lineaDePintadoLK[0]
		self.vectorParaleloUnitario = (vectorParalelo)/self._tamanoVector(vectorParalelo)
		self.vectorPerpendicularUnitario = np.array([self.vectorParaleloUnitario[1],-self.vectorParaleloUnitario[0]])
		self.numeroDePuntos = 15
		
		self.carrilValido = self.createWiderWholeRoute()
		self.carrilInicialYMedio = self.createInitialAndMiddleZone()

		# la linea de referencia para tamanio sera del largo del paso de cebra, su longitud servira para descartar puntos que se alejen del resto
		self.maximaDistanciaEntrePuntos = self._tamanoVector(np.array(poligonoPartida[0])-np.array(poligonoPartida[1]))

		self.stepX = ditanciaEnX/self.numeroDePuntos
		self.stepY = ditanciaEnY/self.numeroDePuntos
		self.lk_params = dict(  winSize  = (15,15),
								maxLevel = 7,
								criteria = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03))

		self.lineaFijaDelantera = np.zeros((self.numeroDePuntos+1,1,2))
		self.lineaDeResguardoDelantera = self.crearLineaDeResguardo()
		self.lineaDeResguardoAlteradaDelantera = self.lineaDeResguardoDelantera

		# Se inicializa la perspectiva con 1/9 del largo del paso de cebra como ancho
		self.areaFlujo = self.obtenerRegionFlujo(self.departureArea)
		self.optimalStep = 2

	def createWiderWholeRoute(self):
		# Input type: self.carrilValido = np.array([poligonoPartida[0],poligonoPartida[1],poligonoPartida[2],poligonoPartida[3],poligonoLlegada[2],poligonoLlegada[3],poligonoLlegada[0],poligonoLlegada[1]])
		# Se modifican los puntos
		# partida: 0-,3+
		# llegada: 1+,2-
		# La matriz de rotacion por un angulo de 15 grados
		carrilValido = np.array([self.departureArea[0],self.departureArea[1],self.departureArea[2],self.departureArea[3],self.arrivalArea[2],self.arrivalArea[3],self.arrivalArea[0],self.arrivalArea[1]])
		self.angulo = 14
		cos15 = math.cos(self.angulo*math.pi/180)
		sin15 = math.sin(self.angulo*math.pi/180)
		rotacionNegativa = np.array([[cos15,sin15],[-sin15,cos15]])
		rotacionPositiva = np.array([[cos15,-sin15],[sin15,cos15]])
		llegada1_p7 = carrilValido[6]+rotacionPositiva.dot(carrilValido[7]-carrilValido[6])
		llegada1_p4 = carrilValido[5]+rotacionNegativa.dot(carrilValido[4]-carrilValido[5])

		llegada1_p0 = carrilValido[1]+rotacionNegativa.dot(carrilValido[0]-carrilValido[1])
		llegada1_p3 = carrilValido[2]+rotacionPositiva.dot(carrilValido[3]-carrilValido[2])

		carrilValido[0]=llegada1_p0
		carrilValido[3]=llegada1_p3
		carrilValido[4]=llegada1_p4
		carrilValido[7]=llegada1_p7

		# Hasta este punto se obtiene el carril valido simplemente ensanchado
		# Ahora concatenamos con los puntos de llegada a Derecha e Izquierda

		carrilValido = np.array([	carrilValido[0],
									carrilValido[1],
									carrilValido[2],
									carrilValido[3],
									self.rightArrivalArea[2],
									self.rightArrivalArea[3],
									self.rightArrivalArea[0],
									self.rightArrivalArea[1],
									carrilValido[4],
									carrilValido[5],
									carrilValido[6],
									carrilValido[7],
									self.leftArrivalArea[2],
									self.leftArrivalArea[3],
									self.leftArrivalArea[0],
									self.leftArrivalArea[1]])

		return carrilValido

	def createInitialAndMiddleZone(self):
		carrilInicialYMedio = np.array([self.departureArea[0],self.departureArea[1],self.departureArea[2],self.departureArea[3],self.arrivalArea[2],self.arrivalArea[1]])
		return carrilInicialYMedio

	def crearLineaDeResguardo(self):
		"""
		La linea de resguardo es una linea preparada para entrar en el algoritmo de lucas Kanade y controlar el flujo o seguir objetos que crucen la zona de partida
		"""
		lineaAuxiliar = np.array([[self.lineaDePintadoLK[0]]])
		for numeroDePunto in range(1,self.numeroDePuntos+1):
			lineaAuxiliar = np.append(lineaAuxiliar,[[self.lineaDePintadoLK[0]+numeroDePunto*np.array([self.stepX,self.stepY])]],axis=0)
		self.lineaFijaDelantera = lineaAuxiliar
		self.lineaFijaDelantera = np.array(self.lineaFijaDelantera,dtype = np.float32)
		return lineaAuxiliar

	def obtenerRegionFlujo(self,npArrayDePartida):
		punto01 = npArrayDePartida[0]
		punto02 = npArrayDePartida[1]
		punto03 = npArrayDePartida[2]
		punto04 = npArrayDePartida[3]
		unitario12 = (punto02 - punto01)/self._tamanoVector(punto02 - punto01)
		unitario43 = (punto03 - punto04)/self._tamanoVector(punto03 - punto04)
		largoPasoCebra = self._tamanoVector(punto04-punto01)
		punto02 = punto01+largoPasoCebra/3*unitario12
		punto03 = punto04+largoPasoCebra/3*unitario43

		return np.array([punto01,punto02,punto03,punto04]).astype(int)

	def _tamanoVector(self,vector):
		# Metodo auxiliar por la recurencia de esta aplicacion
		return math.sqrt(vector[0]**2+vector[1]**2)


	def _puntoEstaEnRectangulo(self,punto,rectangulo):
		# Metodo auxiliar por la recurencia de esta aplicacion
		estadoARetornar = False
		if (punto[0]>rectangulo[0])&(punto[0]<rectangulo[0]+rectangulo[2])&(punto[1]>rectangulo[1])&(punto[1]<rectangulo[1]+rectangulo[3]):
			estadoARetornar = True
		return estadoARetornar
