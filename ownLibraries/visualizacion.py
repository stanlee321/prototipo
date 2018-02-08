import cv2
import time
import math
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
		self.logo = np.zeros((1,1,3))
		self.logoInv = np.zeros((1,1,3))
		self.alpha = 0.7

		#Formato
		self.opacidad = 1.0
		self.altoBarraInformacion = 0
		self.font = font = cv2.FONT_HERSHEY_SIMPLEX
		self.colorRectanguloMaximo = (0,0,255)
		self.colorRectanguloMedio = (100,100,255)
		self.colorRectanguloIrrelevante = (100,100,100)
		self.colorRectanguloConError = (255,255,255)
		self.colorRectanguloPaz = (0,255,0)
		self.paletaColores = [(255,0,0),(255,255,0),(0,255,255),(255,0,255),(255,255,255),(100,100,100),(100,255,100),(255,100,100),(255,255,100),(100,255,255),(255,100,255),(200,200,200),(0,255,0),(255,0,0),(255,255,0),(0,255,255),(255,0,255),(255,255,255),(100,100,100),(100,255,100),(255,100,100),(255,255,100),(100,255,255),(255,100,255),(200,200,200),(0,255,0),(255,0,0),(255,255,0),(0,255,255),(255,0,255),(255,255,255),(100,100,100),(100,255,100),(255,100,100),(255,255,100),(100,255,255),(255,100,255),(200,200,200),(0,255,0),(255,0,0),(255,255,0),(0,255,255),(255,0,255),(255,255,255),(100,100,100),(100,255,100),(255,100,100),(255,255,100),(100,255,255),(255,100,255),(200,200,200),(0,255,0),(255,0,0),(255,255,0),(0,255,255),(255,0,255),(255,255,255),(100,100,100),(100,255,100),(255,100,100),(255,255,100),(100,255,255),(255,100,255),(200,200,200),(0,255,0),(255,0,0),(255,255,0),(0,255,255),(255,0,255),(255,255,255),(100,100,100),(100,255,100),(255,100,100),(255,255,100),(100,255,255),(255,100,255),(200,200,200),(0,255,0),(255,0,0),(255,255,0),(0,255,255),(255,0,255),(255,255,255),(100,100,100),(100,255,100),(255,100,100),(255,255,100),(100,255,255),(255,100,255),(200,200,200),(0,255,0),(255,0,0),(255,255,0),(0,255,255),(255,0,255),(255,255,255),(100,100,100),(100,255,100),(255,100,100),(255,255,100),(100,255,255),(255,100,255),(200,200,200),(0,255,0),(255,0,0),(255,255,0),(0,255,255),(255,0,255),(255,255,255),(100,100,100),(100,255,100),(255,100,100),(255,255,100),(100,255,255),(255,100,255),(200,200,200),(0,255,0),(255,0,0),(255,255,0),(0,255,255),(255,0,255),(255,255,255),(100,100,100),(100,255,100),(255,100,100),(255,255,100),(100,255,255),(255,100,255),(200,200,200)]
		self.ultimoColor = 0
		
		self.logoSize = 80
		self.placeLogoX = 320 - self.logoSize

	def inicializar(self):
		del self.targets
		del self.misPuntos
		self.targets = []
		self.misPuntos = []
		self.ultimoColor = 0

	def establecerLogo(self,nombreArchivo):
		self.logo = cv2.resize(cv2.imread(nombreArchivo),(self.logoSize,self.logoSize))
		self.logoInv = cv2.cvtColor(self.logo,cv2.COLOR_BGR2GRAY)
		ret, self.maskLogo = cv2.threshold(self.logoInv, 10, 255, cv2.THRESH_BINARY)
		self.maskLogoInv = cv2.bitwise_not(self.maskLogo)

	def aplicarConstantes(self,frameNP):
		if self.logo.shape != (1,1,3):
			auxiliar = frameNP[0:self.logoSize, self.placeLogoX:(self.placeLogoX+self.logoSize)]
			img1_bg = cv2.bitwise_and(auxiliar,auxiliar,mask = self.maskLogoInv)
			img2_fg = cv2.bitwise_and(self.logo,self.logo,mask = self.maskLogo)
			#auxiliar = cv2.addWeighted(self.logo,self.alpha,auxiliar,1-self.alpha,0,frameNP[0:self.logoSize, 270:270+self.logoSize])
			dst = cv2.add(img1_bg,img2_fg)
			#dst = cv2.addWeighted(img1_bg,self.alpha,img2_fg,1-self.alpha,0,img2_fg)
			#dst = img1_bg	# Negro con la silueta del logo
			#dst = img2_fg
			#auxiliar = cv2.add(self.logo,auxiliar)
			frameNP[0:self.logoSize, self.placeLogoX:(self.placeLogoX+self.logoSize)] = dst#shader -> cv2.addWeighted(img1_bg,self.alpha,dst,1-self.alpha,0,dst)
		frameNP = cv2.putText(frameNP, datetime.datetime.now().strftime('%A %d %B %Y %I:%M:%S%p')+' f{}'.format(self.numeroFrame), (4,236), self.font, 0.4,(255,255,255),1,cv2.LINE_AA)
		return frameNP

	def aplicarAFrame(self,frameNP):
		for poligono in self.poligonos:
			frameNP = cv2.polylines(frameNP,np.int32([poligono]),1,(160,160,160))
		for ind in range(len(self.misPuntos)):
			puntoInformacion = self.misPuntos[ind]
			punto = (int(puntoInformacion[0][0]),int(puntoInformacion[0][1]))
			color = puntoInformacion[1]
			frameNP = cv2.circle(frameNP, punto, 1, color, -1)

		for target in self.targets:
			x,y,w,h = target[0]
			estado = target[1]
			r = w+h
			if r<20:
				r = 20
			if estado == 'Confirmado':
				#frameNP = cv2.rectangle(frameNP, (x,y),(x+w-1, y+h-1),(0,0,255),1)
				frameNP = cv2.circle(frameNP, (x,y), r, (0,0,255), 1)
			elif estado == 'Cruzo':
				#frameNP = cv2.rectangle(frameNP, (x,y),(x+w-1, y+h-1),(0,255,0),1)
				frameNP = cv2.circle(frameNP, (x,y), r, (0,255,0), 1)
			elif estado == 'Referencia':
				#frameNP = cv2.rectangle(frameNP, (x,y),(x+w-1, y+h-1),(0,0,0),1)
				frameNP = cv2.circle(frameNP, (x,y), r, (0,0,0), 1)
			else:
				#frameNP = cv2.rectangle(frameNP, (x,y),(x+w-1, y+h-1),self.paletaColores[self.ultimoColor],1)
				frameNP = cv2.circle(frameNP, (x,y), r, self.paletaColores[self.ultimoColor], 1)
				
			frameNP = cv2.circle(frameNP, (x+w//2,y+h//2),2,(0,255,0),-1)
		xSem = int(self.poligonos[0][0][0] -5)
		ySem = int(self.poligonos[0][0][1] -5)
		frameNP = cv2.circle(frameNP, (xSem,ySem),4,self.colorSemaforo,-1)
		
		return frameNP

	def colocarPoligono(self,poligonoNP):
		self.poligonos.append(poligonoNP)
		if cv2.pointPolygonTest(poligonoNP,(self.placeLogoX, self.logoSize),True)>=0:	# Si esta dentro del carril valido se mueve:
				self.placeLogoX = 0

	def colocarObjetivo(self,rectangulo,prioridad):
		self.targets.append([rectangulo,prioridad])

	def colocarPunto(self,pointTuple,color):
		self.misPuntos.append([pointTuple,color])

	def colocarObjetivo(self,rectangulo,estado):
		self.targets.append([rectangulo,estado])

	def colocarObjeto(self,puntosList,estado):
		x,y,h,w = self.unificarPuntos(puntosList)
		self.colocarObjetivo([x,y,h,w],estado)
		self.colocarPuntos(puntosList,estado)

	def unificarPuntos(self,puntosList):
		x = 0
		y = 0
		n = 0
		for punto in puntosList:
			x += tuple(punto)[0]
			y += tuple(punto)[1]
			n += 1
		if n == 0:
			return 0,0,0,0
		x = int(x/n)
		y = int(y/n)
		h = 0
		w = 0
		for punto in puntosList:
			w += (tuple(punto)[0]-x)*(tuple(punto)[0]-x)
			h += (tuple(punto)[1]-y)*(tuple(punto)[1]-y)
		
		h = int(math.sqrt(h/n))
		w = int(math.sqrt(w/n))

		return x,y,h,w

	def colocarPuntos(self,puntosList,estado):
		for punto in puntosList:
			if estado == 'Confirmado':
				self.colocarPunto(tuple(punto),(0,0,255))
			elif estado == 'Cruzo':
				self.colocarPunto(tuple(punto),(0,255,0))
			elif estado == 'Referencia':
				self.colocarPunto(tuple(punto),(0,0,0))
			else:
				self.colocarPunto(tuple(punto),self.paletaColores[self.ultimoColor])
		self.ultimoColor += 1

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
		
