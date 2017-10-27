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
font = cv2.FONT_HERSHEY_SIMPLEX

class GeneradorEvidencia():
	def __init__(self, carpetaReporte,mifps = 10,guardoRecortados = True):
		self.carpetaDeReporteActual = carpetaReporte
		self.framesPorSegundoEnVideo = mifps
		self.ventana = 5
		self.height, self.width = 240, 320
		self.guardoRecortados = guardoRecortados
		self.dicts_by_name = defaultdict(list)


	def inicializarEnCarpeta(self,carpetaReporte):
		self.carpetaDeReporteActual = carpetaReporte

	def generarReporteInfraccion(self, informacionTotal, infraccion = True,numero = 0):
		fourcc = cv2.VideoWriter_fourcc(*'XVID')
		generandoDebug = False
		try:
			nombreInfraccion = infraccion['name'][:-7]
			generandoDebug = False
		except:
			nombreInfraccion = datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S')+'_{}i'.format(numero)
			generandoDebug = True
		directorioActual = self.carpetaDeReporteActual + '/'+nombreInfraccion
		if not os.path.exists(directorioActual):
			print('Creado: '+directorioActual)
			os.makedirs(directorioActual) 

		if generandoDebug==False:
			#print(informacionTotal)
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
			print('Generada infr de: ',inicio,' a ',final,' len: ',final-inicio,' fecha: ',nombreInfraccion)

			directorioRecorte = directorioActual+'/recorte'
			for indiceVideo in range(inicio, final):
				prueba.write(informacionTotal[indiceVideo]['frame'])
				if self.guardoRecortados:
					contadorDeRecortados = 0
					
					if not os.path.exists(directorioRecorte):
						os.makedirs(directorioRecorte) 
					for imagen in informacionTotal[indiceVideo]['recortados']:
						nombreRecorte = directorioRecorte+'/photo_{}_{}.jpg'.format(contadorDeRecortados,indiceVideo)
						cv2.imwrite(nombreRecorte,imagen)
						contadorDeRecortados+=1
			prueba.release()
			os.chdir(directorioActual)
			#os.system('tar -cf '+directorioActual+'/placa.tar '+directorioRecorte+'/*')
			os.system('tar -czf '+directorioActual+'/placa.tar -C '+directorioRecorte +' .')
			os.system('rm -rf '+directorioRecorte)
			
			return 1
		
		else:
			
			prueba = cv2.VideoWriter(directorioActual+'/'+nombreInfraccion+'.avi',fourcc, self.framesPorSegundoEnVideo,(self.width,self.height))
			inicio = 0
			final = len(informacionTotal)
			print('Generada debug de: ',inicio,final,' len: ',final-inicio,' total lista: ',len(informacionTotal))
			for indiceVideo in range(inicio,final):
				try:
					prueba.write(informacionTotal[indiceVideo]['frame'])
				except:
					print('No pude guardar frame: ',indiceVideo)
			prueba.release()
			return 0