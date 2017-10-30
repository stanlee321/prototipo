#!/usr/bin/env python
# previo, completo flujo mas el background con ruido
# actual contempla el lane transform

import os
import cv2
import time
import glob
import pickle
import logging
import zipfile
import datetime
import numpy as np
import glob
from os.path import basename
from shooter import Shooter
from mireporte import MiReporte
from areaderesguardo import AreaDeResguardo

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

	def generarReporteInfraccion(self, informacionTotal, infraccion = True, numero = 0):
		fourcc = cv2.VideoWriter_fourcc(*'XVID')
		generandoDebug = False
		try:
			nombreInfraccion = infraccion['name'][:-7]
			generandoDebug = False
		except:
			nombreInfraccion = datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S')+'_{}i'.format(numero)
			if (numero == 0)&(len(informacionTotal)<20):
				return 0
			generandoDebug = True
		directorioActual = self.carpetaDeReporteActual + '/'+nombreInfraccion
		if not os.path.exists(directorioActual):
			self.miReporte.info('Creado: '+directorioActual)
			os.makedirs(directorioActual) 

		if generandoDebug==False:
			frameInferior = infraccion['frameInicial'] - self.ventana
			frameSuperior = infraccion['frameFinal'] + self.ventana
			
			prueba = cv2.VideoWriter(directorioActual+'/'+nombreInfraccion+'.avi',fourcc, self.framesPorSegundoEnVideo,(self.width,self.height))
			
			# Check valid frame 
			if frameInferior < 1:
				inicio = 1
			else:
				inicio = frameInferior

			if frameSuperior > len(informacionTotal):
				final = len(informacionTotal)
			else:
				final = frameSuperior
			self.miReporte.info('Generada infr de: '+str(inicio)+' a '+str(final)+' len: '+str(final-inicio)+' fecha: ' + nombreInfraccion)
			if self.guardoRecortados:
				directorioRecorte = directorioActual+'/recorte'
				if not os.path.exists(directorioRecorte):
					os.makedirs(directorioRecorte) 
			for indiceVideo in range(inicio, final):
				prueba.write(informacionTotal[indiceVideo]['frame'])
				if self.guardoRecortados:
					contadorDeRecortados = 0
					for indiceImagen in range(len(informacionTotal[indiceVideo]['recortados'])):
						imagen = informacionTotal[indiceVideo]['recortados'][indiceImagen]
						if informacionTotal[indiceVideo]['rectangulos'][indiceImagen][2] == 0:
							estado = 'Saved'
						else:
							estado = 'Erased'
						nombreRecorte = directorioRecorte+'/photo_{}_{}_'.format(contadorDeRecortados,indiceVideo)+estado+'.jpg'
						cv2.imwrite(nombreRecorte,imagen)
						contadorDeRecortados+=1
			prueba.release()
			# Vuelvo a iterar por la imagen mas grande:
			ultimoValorMayor = 0
			indicesMejorFoto = (-1,0)
			for indiceVideo in range(inicio, final):
				for indiceImagen in range(len(informacionTotal[indiceVideo]['recortados'])):
					ancho = informacionTotal[indiceVideo]['rectangulos'][indiceImagen][0][2]
					alto = informacionTotal[indiceVideo]['rectangulos'][indiceImagen][0][3]
					valorActual = ancho*alto
					if valorActual>ultimoValorMayor:
						ultimoValorMayor = valorActual
						indicesMejorFoto = (indiceVideo,indiceImagen)

			if indicesMejorFoto[0] != -1:
				imagen = informacionTotal[indicesMejorFoto[0]]['recortados'][indicesMejorFoto[1]]
				nombreEvidencia = directorioActual+'/evidencia_{}_{}.jpg'.format(indicesMejorFoto[1],indicesMejorFoto[0])
				cv2.imwrite(nombreEvidencia,imagen)
			return 1
		else:
			prueba = cv2.VideoWriter(directorioActual+'/'+nombreInfraccion+'.avi',fourcc, self.framesPorSegundoEnVideo,(self.width,self.height))
			inicio = 0
			final = len(informacionTotal)
			self.miReporte.info('Generada debug de: '+str(inicio)+' '+str(final)+' len: '+str(final-inicio)+' total lista: '+str(len(informacionTotal)))
			for indiceVideo in range(inicio,final):
				try:
					prueba.write(informacionTotal[indiceVideo]['frame'])
				except:
					self.miReporte.error('No pude guardar frame: '+str(indiceVideo))
			prueba.release()
			return 0