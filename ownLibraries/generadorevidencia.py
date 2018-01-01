#!/usr/bin/env python
# previo, completo flujo mas el background con ruido
# actual contempla el lane transform

import os
import cv2
import time
import glob
import shutil
import logging
import datetime
import numpy as np

from collections import defaultdict
from ownLibraries.mireporte import MiReporte
font = cv2.FONT_HERSHEY_SIMPLEX

class GeneradorEvidencia():
	def __init__(self, carpetaReporte,mifps = 10,guardoRecortados = True):
		self.miReporte = MiReporte(levelLogging=logging.DEBUG,nombre=__name__)
		self.carpetaDeReporteActual = carpetaReporte
		self.framesPorSegundoEnVideo = mifps
		self.ventana = 5
		self.height, self.width = 240, 320
		self.guardoRecortados = guardoRecortados
		self.dicts_by_name = defaultdict(list)

	def inicializarEnCarpeta(self,carpetaReporte):
		self.carpetaDeReporteActual = carpetaReporte

	def generarReporteInfraccion(self, informacionTotal, infraccion = True, numero = 0,debug = False):
		fourcc = cv2.VideoWriter_fourcc(*'XVID')
		generandoDebugGlobal = False
		generarDobleVideo = debug
		try:
			nombreInfraccion = infraccion['name']
			generandoDebugGlobal = False
		except:
			nombreInfraccion = datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S')+'_{}i'.format(numero)
			if (numero == 0)&(len(informacionTotal)<20):
				return 0
			generandoDebugGlobal = True

		directorioActual = self.carpetaDeReporteActual + '/'+nombreInfraccion
		
		if not os.path.exists(directorioActual):
			os.makedirs(directorioActual) 
		
		if generandoDebugGlobal==False:
			frameInferior = infraccion['frameInicial'] - self.ventana
			frameSuperior = infraccion['frameFinal'] + self.ventana
			if generarDobleVideo:
				prueba = cv2.VideoWriter(directorioActual+'/'+nombreInfraccion+'_debug.avi',fourcc, self.framesPorSegundoEnVideo,(self.width,self.height))
			entrega = cv2.VideoWriter(directorioActual+'/'+nombreInfraccion+'.avi',fourcc, self.framesPorSegundoEnVideo,(self.width,self.height))
			
			# Check valid frame 
			if frameInferior < 1:
				inicio = 1
			else:
				inicio = frameInferior

			if frameSuperior > len(informacionTotal):
				final = len(informacionTotal)
			else:
				final = frameSuperior
			self.miReporte.info('\t\t'+'Generada infr de: '+nombreInfraccion+' de '+str(inicio)+' a '+str(final))
			if self.guardoRecortados:
				directorioRecorte = directorioActual+'/recorte'
				if not os.path.exists(directorioRecorte):
					os.makedirs(directorioRecorte) 
			for indiceVideo in range(inicio, final):
				if generarDobleVideo:
					prueba.write(informacionTotal[indiceVideo]['frame'])
				entrega.write(informacionTotal[indiceVideo]['captura'])
			if generarDobleVideo:
				prueba.release()
			entrega.release()

			# Vuelvo a iterar por la imagen mas grande:
			return 1
		else:
			prueba = cv2.VideoWriter(directorioActual+'/'+nombreInfraccion+'.avi',fourcc, self.framesPorSegundoEnVideo,(self.width,self.height))
			inicio = 0
			final = len(informacionTotal)
			self.miReporte.info('Generado DEBUG de: '+nombreInfraccion+' de '+str(inicio)+' '+str(final)+' total lista: '+str(len(informacionTotal)))
			for indiceVideo in range(inicio,final):
				try:
					prueba.write(informacionTotal[indiceVideo]['frame'])
				except:
					self.miReporte.error('No pude guardar frame: '+str(indiceVideo))
			prueba.release()
			return 0