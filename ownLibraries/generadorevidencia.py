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
		self.height, self.width = 240, 320

		self.dicts_by_name = defaultdict(list)


	def inicializarEnCarpeta(self,carpetaReporte):
		self.carpetaDeReporteActual = carpetaReporte

	def generarReporteInfraccion(self, informacionTotal, infraccion = True):
		fourcc = cv2.VideoWriter_fourcc(*'XVID')
		generandoDebug = False
		try:
			nombreInfraccion = infraccion['name'][:-7]
			generandoDebug = False
		except:
			nombreInfraccion = datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S')
			generandoDebug = True

		if generandoDebug==False:
			#print(informacionTotal)
			frameInferior = infraccion['frameInicial'] - self.ventana
			frameSuperior = infraccion['frameFinal'] + self.ventana
			directorioActual = self.carpetaDeReporteActual + '/'+nombreInfraccion
			if not os.path.exists(directorioActual):
				print('Creado: '+directorioActual)
				os.makedirs(directorioActual) 
			prueba = cv2.VideoWriter(directorioActual+'/'+nombreInfraccion+'.avi',fourcc, self.framesPorSegundoEnVideo,(self.width,self.height))
			
			# Check valid frame 
			if frameInferior < 0:
				inicio = 0
			else:
				inicio = frameInferior

			if frameSuperior > len(informacionTotal):
				final = len(informacionTotal)
			else:
				final = frameSuperior
			print('Generada infr de: ',inicio,' a ',final,' len: ',final-inicio,' fecha: ',nombreInfraccion)
			
			for indiceVideo in range(inicio, final):
				prueba.write(informacionTotal[indiceVideo]['frame'])
				contadorDeRecortados = 0
				for imagen in informacionTotal[indiceVideo]['recortados']:
					cv2.imwrite(directorioActual+'/photo_{}_{}.jpg'.format(contadorDeRecortados,indiceVideo),imagen)
					contadorDeRecortados+=1
			prueba.release()
			return 1
		
		else:
			if infraccion:
				prueba = cv2.VideoWriter(directorioActual+'/'+nombreInfraccion+'.avi',fourcc, self.framesPorSegundoEnVideo,(self.width,self.height))
				inicio = 0
				final = len(informacionTotal)
				print('Generada debug de: ',inicio,final,' len: ',final-inicio,' total lista: ',len(informacionTotal))
				for indiceVideo in range(inicio,final):
					prueba.write(informacionTotal[indiceVideo]['frame'])
				prueba.release()
			else:
				return 0
		return -1