#!/usr/bin/env python

import numpy as np
import cv2

class Estabilizador():
	def __init__(self,initial_image, rectangulo_a_seguir):	# [[x0,y0],[x1,y1]]
		self.rectanguloX0 = rectangulo_a_seguir[0][0]
		self.rectanguloY0 = rectangulo_a_seguir[0][1]
		self.rectanguloX0 = rectangulo_a_seguir[1][0]
		self.rectanguloY1 = rectangulo_a_seguir[1][1]
		self.imagen_auxiliar_croped = initial_image[rectanguloY0:rectanguloY1,rectanguloX0:rectanguloX1]
		self.imagen_auxiliar_croped = cv2.cvtColor(np.array(self.imagen_auxiliar_croped), cv2.COLOR_BGR2GRAY)
		self.feature_parameters = dict(maxCorners = 4, qualityLevel = 0.3, minDistance = 7, blockSize= 7)
		self.lk_parameters = dict(winSize = (15,15), maxLevel = 2, criteria = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT,10,0.03))
		self.colour = np.random.randint(0,255,(4,3))	# For four corners for 3 colours RGB between 0 and 255
		self.puntos_to_track = cv2.goodFeaturesToTrack(self.imagen_auxiliar_croped,mask=None,**self.feature_parameters)
		self.mask = np.zeros_like(self.imagen_auxiliar_croped)

	def obtener_vector_desplazamiento(self,nueva_Imagen):
		imagen_actual_croped = nueva_Imagen[rectanguloY0:rectanguloY1,rectanguloX0:rectanguloX1]
		imagen_actual_croped = cv2.cvtColor(np.array(imagen_actual_croped), cv2.COLOR_BGR2GRAY)
		puntos_tracked, st,err = cv2.calcOpticalFlowPyrLK(self.imagen_auxiliar_croped,imagen_actual_croped,self.puntos_to_track,**self.lk_parameters)
		good_new = puntos_tracked[st==1]
		good_old = puntos_to_track[st==1]
		vector_desplazamiento = (0,0)
		for i, (new,old) in enumerate(zip(good_new,good_old)):	# para cada punto obtienes las posiciones iniciales y finales
			a,b = new.ravel()
			c,d = old.ravel()
			vector_desplazamiento +=(c-a,d-b)
			#mask = cv2.line(mask,(a,b),(c,d),self.colour[i].tolist(),2)
			#frame = cv2.circle(imagen_actual_croped,(a,b),5,self.colour[i].tolist(),-1)
		vector_desplazamiento = vector_desplazamiento//4
		visualizacion = cv2.add(frame,mask)
		return visualizacion, vector_desplazamiento

	def estabilizar_imagen(self,imagen_a_estabilizar):
		filas,columnas = imagen_a_estabilizar.shape[:2]
		vector_a_desplazar = self.obtener_vector_desplazamiento(imagen_a_estabilizar)
		matriz_de_traslacion = np.float([[1,0,-vector_a_desplazar[0]],[0,1,-vector_a_desplazar[y]]])
		imagen_estabilizada = cv2.warpAffine(imagen_a_estabilizar,matriz_de_traslacion,(columnas,filas))
		return imagen_estabilizada
