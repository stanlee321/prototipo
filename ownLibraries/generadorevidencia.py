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

	def generarReporteInfraccion(self, informacionTotal, infraccion = True):
		fourcc = cv2.VideoWriter_fourcc(*'XVID')
		generandoDebug = False
		try:
			nombreInfraccion = infraccion['name'][:-7]
			generandoDebug = False
		except:
			nombreInfraccion = datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S')
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
			file_list = []
			for indiceVideo in range(inicio, final):
				prueba.write(informacionTotal[indiceVideo]['frame'])
				if self.guardoRecortados:
					nombreArchivoZip = directorioActual+"/"+nombreInfraccion+".zip"
					myZip = zipfile.ZipFile (nombreArchivoZip, "w", zipfile.ZIP_DEFLATED)
					contadorDeRecortados = 0
					for imagen in informacionTotal[indiceVideo]['recortados']:
						nombreRecorte = directorioActual+'/photo_{}_{}.jpg'.format(contadorDeRecortados,indiceVideo)
						cv2.imwrite(nombreRecorte,imagen)
						contadorDeRecortados+=1

					file_list = glob.glob( directorioActual+'/*.jpg')
					
					if len(file_list):
						with zipfile.ZipFile(directorioActual+'/{}.zip'.format(nombreInfraccion), 'w') as zip:
							for file_name in file_list:
								zip.write(file_name, basename(file_name)) 
								#myZip.write(nombreRecorte)
						myZip.close()
			for f in file_list:
				os.remove(f)

			prueba.release()
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