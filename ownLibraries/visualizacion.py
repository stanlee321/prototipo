import cv2
import time
import random
import datetime
import numpy as np
# Draw a diagonal blue line with thickness of 5 px
from abc import ABCMeta, abstractmethod

class Acetato(object):
	"""docstring for Acetato"""
	def __init__(self):
		self.miFechaHora = datetime.datetime.now().strftime('%A %d %B %Y %I:%M:%S%p')
		# Informacion
		self.poligonos = []
		self.targets = []
		self.misPuntos = []
		self.colorSemaforo = (0,0,0)
		self.numeroFrame = 0

		#Formato
		self.opacidad = 1.0
		self.altoBarraInformacion = 0
		self.font = font = cv2.FONT_HERSHEY_SIMPLEX
		self.colorRectanguloMaximo = (0,0,255)
		self.colorRectanguloMedio = (100,100,255)
		self.colorRectanguloIrrelevante = (100,100,100)
		self.colorRectanguloConError = (255,255,255)
		self.colorRectanguloPaz = (0,255,0)

	def inicializar(self):
		del self.targets
		del self.misPuntos
		self.targets = []
		self.misPuntos = []

	def aplicarAFrame(self,frameNP):
		for poligono in self.poligonos:
			frameNP = cv2.polylines(frameNP,np.int32([poligono]),1,(160,160,160))
		for puntoInformacion in self.misPuntos:
			punto = puntoInformacion[0]
			color = puntoInformacion[1]
			frameNP = cv2.circle(frameNP, punto, 1, (100*color,100*color,255), -1)
		for target in self.targets:
			x,y,w,h = target[0]
			prioridad = target[1]
			if prioridad == 0:
				frameNP = cv2.rectangle(frameNP, (x,y),(x+w-1, y+h-1),self.colorRectanguloMaximo,1)
			elif prioridad == 1:
				frameNP = cv2.rectangle(frameNP, (x,y),(x+w-1, y+h-1),self.colorRectanguloMedio,1)
			elif prioridad == 2:
				frameNP = cv2.rectangle(frameNP, (x,y),(x+w-1, y+h-1),self.colorRectanguloIrrelevante,1)
			elif prioridad == 3:
				frameNP = cv2.rectangle(frameNP, (x,y),(x+w-1, y+h-1),self.colorRectanguloPaz,1)
			else:
				frameNP = cv2.rectangle(frameNP, (x,y),(x+w-1, y+h-1),self.colorRectanguloConError,1)
			frameNP = cv2.circle(frameNP, (x+w//2,y+h//2),2,(0,255,0),-1)
		xSem = int(self.poligonos[0][0][0] -5)
		ySem = int(self.poligonos[0][0][1] -5)
		frameNP = cv2.circle(frameNP, (xSem,ySem),4,self.colorSemaforo,-1)
		frameNP = cv2.putText(frameNP, datetime.datetime.now().strftime('%A %d %B %Y %I:%M:%S%p')+' f{}'.format(self.numeroFrame), (4,236), self.font, 0.4,(255,255,255),1,cv2.LINE_AA)
		return frameNP

	def colocarPoligono(self,poligonoNP):
		self.poligonos.append(poligonoNP)

	def colocarObjetivo(self,target,prioridad):
		rectangulo = target
		self.targets.append([rectangulo,prioridad])

	def colocarPunto(self,pointTuple,estado):
		self.misPuntos.append([pointTuple,estado])

	def colorDeSemaforo(self,colorInt):
		if colorInt == 1:
			self.colorSemaforo = (0,0,255)
		elif colorInt == 0:
			self.colorSemaforo = (0,255,0)
		elif colorInt == 2:
			self.colorSemaforo = (0,255,255)
		else:
			self.colorSemaforo = (0,0,0)

	def establecerNumeroFrame(self,numero):
		self.numeroFrame = numero

class Target(object):
	"""docstring for Target"""
	def __init__(self, arg):
		super(Target, self).__init__()
		self.arg = arg
		
