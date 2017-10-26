#!/usr/bin/env python
# previo, completo flujo mas el background con ruido
# actual contempla el lane transform

import os
import cv2
import time
import glob
import pickle
import logging
import datetime
import numpy as np

from shooter import Shooter
from mireporte import MiReporte
from areaderesguardo import AreaDeResguardo

from collections import defaultdict
font = cv2.FONT_HERSHEY_SIMPLEX

class GeneradorEvidencia():
	def __init__(self, carpetaReporte,mifps = 10):
		self.carpetaDeReporteActual = carpetaReporte
		self.framesPorSegundoEnVideo = mifps
		self.ventana = 5

		self.dicts_by_name = defaultdict(list)


	def inicializarEnCarpeta(self,carpetaReporte):
		self.carpetaDeReporteActual = carpetaReporte

	def generarReporteInfraccion(self, informacionTotal, infraccion = True):
		fourcc = cv2.VideoWriter_fourcc(*'XVID')

		try:
			#print(informacionTotal)
			frameInferior = infraccion['frameInicial'] - self.ventana
			frameSuperior = infraccion['frameFinal'] + self.ventana
			height, width, layers = informacionTotal[1]['frame'].shape
			prueba = cv2.VideoWriter(self.carpetaDeReporteActual+'/'+infraccion['name']+'.avi',fourcc, self.framesPorSegundoEnVideo,(width,height))
			
			# Check valid frame 
			if frameInferior < 0:
				inicio = 0
			else:
				inicio = frameInferior

			if frameSuperior > len(informacionTotal):
				final = len(informacionTotal)
			else:
				final = frameSuperior

			print('Generada infr de: ',inicio,' a ',final,' len: ',final-inicio,' fecha: ',infraccion['name'])
			
			for indiceVideo in range(inicio, final):
				time.sleep(0.01)
				cv2.putText(informacionTotal[indiceVideo]['frame'], str(indiceVideo), (30,30), font, 0.4,(255,255,255),1,cv2.LINE_AA)
				prueba.write(informacionTotal[indiceVideo]['frame'])

			prueba.release()
			return 1
		
		except Exception as e:
			print('>>>>>>>>>>>>>>>>>>>Migrando a modo debug: ',e)
			if infraccion:
				height, width, layers = informacionTotal[0]['frame'].shape
				prueba = cv2.VideoWriter(self.carpetaDeReporteActual+'/'+infraccion['name']+'.avi',fourcc, self.framesPorSegundoEnVideo,(width,height))
				inicio = 0
				final = len(informacionTotal)
				print('Generada debug de: ',inicio,final,' len: ',final-inicio,' total lista: ',len(informacionTotal))
				for indiceVideo in range(inicio,final):
					prueba.write(informacionTotal[indiceVideo]['frame'])
				prueba.release()
			else:
				return 0
		return -1
