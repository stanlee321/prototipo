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
		self.carpetaParaEntrega = carpetaReporte+'Oficial'
		if not os.path.exists(self.carpetaParaEntrega):
			os.makedirs(self.carpetaParaEntrega)
		self.framesPorSegundoEnVideo = mifps
		self.ventana = 5
		self.height, self.width = 240, 320
		self.guardoRecortados = guardoRecortados
		self.dicts_by_name = defaultdict(list)

	def inicializarEnCarpeta(self,carpetaReporte):
		self.carpetaDeReporteActual = carpetaReporte

	def generarReporteInfraccion(self, informacionTotal, infraccion = True, numero = 0):
		fourcc = cv2.VideoWriter_fourcc(*'XVID')
		generandoDebug = False
		try:
			nombreInfraccion = infraccion['name']
			generandoDebug = False
		except:
			nombreInfraccion = datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S')+'_{}i'.format(numero)
			if (numero == 0)&(len(informacionTotal)<20):
				return 0
			generandoDebug = True

		directorioActual = self.carpetaDeReporteActual + '/'+nombreInfraccion
		directorioActualOficial = self.carpetaParaEntrega + '/'+nombreInfraccion
		if not os.path.exists(directorioActual):
			os.makedirs(directorioActual) 
		
		if generandoDebug==False:
			if not os.path.exists(directorioActualOficial):
				os.makedirs(directorioActualOficial) 
			frameInferior = infraccion['frameInicial'] - self.ventana
			frameSuperior = infraccion['frameFinal'] + self.ventana
			archivosEnCarpeta = glob.glob(directorioActual+'/*')
			for imagenACopiar in archivosEnCarpeta:
				shutil.copy(imagenACopiar,directorioActualOficial+'/'+nombreInfraccion+imagenACopiar[-6:])
				self.miReporte.info('Recuperado '+imagenACopiar[-5])
			
			prueba = cv2.VideoWriter(directorioActual+'/'+nombreInfraccion+'.avi',fourcc, self.framesPorSegundoEnVideo,(self.width,self.height))
			entrega = cv2.VideoWriter(directorioActualOficial+'/'+nombreInfraccion+'.avi',fourcc, self.framesPorSegundoEnVideo,(self.width,self.height))
			
			# Check valid frame 
			if frameInferior < 1:
				inicio = 1
			else:
				inicio = frameInferior

			if frameSuperior > len(informacionTotal):
				final = len(informacionTotal)
			else:
				final = frameSuperior
			self.miReporte.info('Generada infr de: '+nombreInfraccion+' de '+str(inicio)+' a '+str(final)+' fecha: ' + nombreInfraccion)
			if self.guardoRecortados:
				directorioRecorte = directorioActual+'/recorte'
				if not os.path.exists(directorioRecorte):
					os.makedirs(directorioRecorte) 
			for indiceVideo in range(inicio, final):
				prueba.write(informacionTotal[indiceVideo]['frame'])
				entrega.write(informacionTotal[indiceVideo]['captura'])
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