#!/usr/bin/env python

import numpy as np
import cv2

class Visualizador():
	def __init__(self, tamano='min'):	#tamano (320,240)
		#Position Variables
		self.w = 320
		self.h = 240
		self.scale = 1
		if tamano == 'max':
			self.w = 640
			self.h = 480
			self.scale = 2
			#print('maximum selected')
		self.size = (self.w,self.h)
		self.centrox = self.w // 2
		self.centroy = self.h // 2
		self.centroFrame = (self.centrox,self.centroy)

		#Auxiliares
		self.font = cv2.FONT_HERSHEY_SIMPLEX

	def draw_vector(self,imagen,vector,color):
		imagen = cv2.line(imagen,(self.centroFrame[0],self.centroFrame[1]),(self.centroFrame[0]+int(vector[0]),self.centroFrame[1]+int(vector[1])),color,2)
		return imagen

	def drawMagnitudAtBottomCorner(self,imagen,magnitud,indice):
		self.h,self.w = imagen.shape[:2]
		h2,w2 = visualizacionFlujoDeIntermedio.shape[:2]
		h3,w3 = visualizacionFlujoDePartida.shape[:2]
		ultimaVisualizacionDebug = np.zeros((max(h1,h2,h3),w1+w2+w3),np.uint8)

		ancho = 4
		offset = 5
		color = (255,255,255)
		if indice==0:
			color = (255,0,0)
		elif indice==1:
			color = (0,255,0)
		elif indice==2:
			color = (0,0,255)
		imagen = cv2.line(imagen,(int(self.w-offset-2*ancho*indice),int(self.h-offset)),(int(self.w-offset-2*ancho*indice),int(self.h-offset-2*magnitud)),color,ancho)
		return imagen

	def overlayRegions(self,imagen,vertices,indice):
		miCapa = imagen.copy()
		if indice==0 :
			cv2.fillPoly(miCapa,[np.array(vertices)],(255,0,0))
		elif indice==1:
			cv2.fillPoly(miCapa,[np.array(vertices)],(0,255,0))
		elif indice==2:
			cv2.fillPoly(miCapa,[np.array(vertices)],(0,0,255))
		else:
			print('Not applied mask!')
			return imagen

		opacity = 0.15
		newImage = cv2.addWeighted(miCapa, opacity, imagen, 1 - opacity, 0, imagen)
		return newImage

	def putLabelAtCorner(self,imagenALabelar, esquina, etiqueta):
		x_pos = 0
		y_pos = 0
		if esquina == 0:
			x_pos = 10
			y_pos = 10
		elif esquina == 1:
			x_pos = self.w//2
			y_pos = 10
		elif esquina == 2:
			x_pos = self.w//2
			y_pos = self.h
		elif esquina == 3:
			x_pos = 0
			y_pos = self.h
		resultado = cv2.putText(imagenALabelar,etiqueta,(x_pos,y_pos), self.fosnt, 0.5, (255,0,0), 2, cv2.LINE_AA)
		return resultado
