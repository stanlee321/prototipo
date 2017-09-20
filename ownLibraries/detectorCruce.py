import os
import sys
import cv2
import time
import numpy as np


class detectorCruce():
	"""
	Detecta si un automovil cruzo del poligono de Partida, al poligono de Llegada
	"""
	def __init__(self,poligonoPartida,poligonoLlegada,numeroDePuntos = 10):
		self.areaDeResguardo = np.array(poligonoPartida)
		self.areaDeConfirmacion = np.array(poligonoLlegada)
		self.lineaDePintadoLK =  np.array([poligonoPartida[0],poligonoPartida[3]])
		self.lineaTraseraLK =  np.array([poligonoPartida[1],poligonoPartida[2]])
		ditanciaEnX = self.lineaDePintadoLK[1][0] - self.lineaDePintadoLK[0][0]
		stepX = ditanciaEnX//numeroDePuntos
		stepY = ditanciaEnY//numeroDePuntos
		ditanciaEnY = self.lineaDePintadoLK[1][1] - self.lineaDePintadoLK[0][1]
		self.miLineaInteligente = []
		for number in range(numeroDePuntos):
			self.miLineaInteligente.append(self.lineaDePintadoLK[0]+)
			