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

class GeneradorEvidencia():
	def __init__(self, carpetaReporte,mifps = 10):
		self.carpetaDeReporteActual = carpetaReporte
		self.framesPorSegundoEnVideo = mifps
		self.ventana = 5

		self.dicts_by_name = defaultdict(list)


	def inicializarEnCarpeta(self,carpetaReporte):
		self.carpetaDeReporteActual = carpetaReporte

	def generarReporteInfraccion(self,informacionTotal, infraccion = True):
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


			if frameInferior > len(informacionTotal):
				final = len(informacionTotal)
			else:
				final = frameSuperior


			print('Generada infr de: ',inicio,final,' len: ',final-inicio,' total lista: ',len(informacionTotal))
			
			for indiceVideo in range(inicio, final):

				time.sleep(0.01)
				prueba.write(informacionTotal[indiceVideo]['frame'])
				#cv2.imwrite(self.carpetaDeReporteActual+'/'+infraccion['name']+'_{}.jpg'.format(indiceVideo),informacionTotal[indiceVideo]['frame'])
				#cv2.imwrite('frame_{}_{}.jpg'.format(indiceVideo,final), informacionTotal[indiceVideo]['frame'])

			prueba.release()
			return 1
		
		
		except Exception as e:
			print('[...Ocurred this error:.... --->]: ',e)
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

class AgenteReportero():
	def __init__(self,imagenDeInicializacion,areaProtegida,areaDeConfirmacion,areaDeInteresPlacas=[[0,0],[2592,1944]],framesPorSegundo=10,nombreCarpetaAlmacenamiento = 'casosReportados',modoDebug = False):
		# REGISTROS AUTOMOVILES:
		self.numeroDePuntosASeguir = 3
		self.miReporte = MiReporte(levelLogging=logging.INFO,nombre=__name__)
		self.areaDeResguardo = AreaDeResguardo(imagenDeInicializacion,self.numeroDePuntosASeguir,areaProtegida,areaDeConfirmacion)
		self.areaDeConfirmacion = np.array(areaDeConfirmacion)
		self.poligonoProtegidoParaVisualizacion = np.array(areaProtegida)

		self.reporteVideo = [] # Minimo 9 frames Maximo 15 frames
		self.misInfracciones = []

		# Parametros auxiliares
		self.numeroDeFrame = 0
		self.framesPorSegundoEnVideo = framesPorSegundo
		self.ultimaVelocidad = 0
		self.widerVideo = 6		# aumenta el numero de frames al inicio y al final del video
		self.formaOndaDebug = []
		self.infraccionesConfirmadas = 0
		self.infraccionesDescartadasPorTiempo = 0
		self.infraccionesDescartadasPorEstacionario = 0
		self.infraccionesDescartadasGiro = 0
		self.numeroInfraccionesTotales = 0

		# Variables de reporte:
		self.reportarDebug = modoDebug
		# El directorio por defecto sera uno u otro en la memoria USB 
		# Estas variables son auxiliares para definir la variable que sera de reporte en cuanto se sepa si hay unidad flash introducida
		
		self.nombreDirectorioLocal = os.getenv('HOME')+'/trafficFlow/prototipo11'
		self.nombreDirectorioUSB = '/media/'+os.getenv('HOME').split('/')[-1]+'/usbName'

		if os.path.exists(self.nombreDirectorioUSB):
			self.carpetaDeReporte = self.nombreDirectorioUSB +'/'+ nombreCarpetaAlmacenamiento
			self.miReporte.info('Encontrada unidad USB, guardando informacionTotal en el medio: '+self.carpetaDeReporte)
			self.carpetaDeReporteDebug = self.nombreDirectorioUSB +'/debug'
		else:
			self.carpetaDeReporte = self.nombreDirectorioLocal +'/'+ nombreCarpetaAlmacenamiento
			self.miReporte.info('No se detectó unidad USB, guardando archivos de forma local:'+self.carpetaDeReporte)
			self.carpetaDeReporteDebug = self.nombreDirectorioLocal +'/casosDebug'

		if not os.path.exists(self.carpetaDeReporte):
			try:
				os.makedirs(self.carpetaDeReporte)
			except Exception as e:
				self.miReporte.error('ERROR, No pude crear el directorio '+self.carpetaDeReporteDebug+' por: '+ str(e))

		if not os.path.exists(self.carpetaDeReporteDebug):
			try:
				os.makedirs(self.carpetaDeReporteDebug)
			except Exception as e:
				self.miReporte.error('ERROR, No pude crear el directorio '+self.carpetaDeReporteDebug+' por: '+ str(e))

		# Si estoy en el raspberry creo la clase shooter
		self.miComputadora = os.uname()[1]
		if self.miComputadora == 'raspberrypi':
			#print('ESTOY TRABAJANDO EN LA PI, CREANDO SHOOTER SHOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOTER')
			self.miCamara = Shooter(cutPoly=areaDeInteresPlacas)
			self.miReporte.debug('Creada camara de alta resolucion')
		
		# Creo las carpetas de reporte actual y para el debug, por ahora la misma
		self.fechaReporte = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
		self.carpetaDeReporteActual = self.carpetaDeReporte+ '/' + self.fechaReporte
		self.carpetaDeReporteActualDebug = self.carpetaDeReporteDebug + '/' + self.fechaReporte

	def inicializarAgente(self,dateToUse=datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')):
		"""
		Devuelve a las condiciones iniciales, debera ser llamado en el primer Rojo
		"""
		del self.reporteVideo
		del self.misInfracciones
		del self.formaOndaDebug
		self.reporteVideo = []
		self.misInfracciones = []
		self.formaOndaDebug = []

		self.fechaReporte = dateToUse
		#Si introduzco fecha la uso, si no , empleo la actual
		self.carpetaDeReporteActual = self.carpetaDeReporte+'/'+self.fechaReporte
		self.carpetaDeReporteActualDebug = self.carpetaDeReporteDebug +'/'+self.fechaReporte
		#print(self.carpetaDeReporteActual)
		if not os.path.exists(self.carpetaDeReporteActual):
			try:
				os.makedirs(self.carpetaDeReporteActual)
			except Exception as e:
				self.miReporte.error('ERROR, No pude crear el directorio Actual por: '+ str(e))
		if not os.path.exists(self.carpetaDeReporteActualDebug):
			try:
				os.makedirs(self.carpetaDeReporteActualDebug)
			except Exception as e:
				self.miReporte.error('ERROR, No pude crear el directorio Debug por: '+ str(e))
		#print(self.fechaReporte)
		self.miReporte.moverRegistroACarpeta(self.fechaReporte)
		self.miReporte.info('Nuevo Directorio de reporte: '+self.carpetaDeReporteActual)
		return True

	def introducirImagen(self,frameActualFlujo):
		"""
		Introducir la forma de onda correspondiente a la imagen de prueba
		"""
		self.reporteVideo.append(frameActualFlujo)
		
		numeroDeFrameActual = len(self.reporteVideo)

		vectorRuidoso, self.ultimaVelocidad,indiceVideoFrameActual = self.areaDeResguardo.encontrarObjetosYCalcularFlujoYPaso(frameActualFlujo,self.misInfracciones)
		self.formaOndaDebug.append([vectorRuidoso,self.ultimaVelocidad])

		
			
		if indiceVideoFrameActual == -1:
			dateStamp = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S.%f')
			if self.miComputadora == 'raspberrypi':					
				self.miCamara.encenderCamaraEnSubDirectorio(self.fechaReporte,dateStamp)
				self.miReporte.info('Encendi Camara en '+dateStamp)
			caracteristicasASeguir = self.areaDeResguardo.obtenerUltimosPuntosASeguir()
			self.miReporte.debug('Detecte Flujo y encontre los puntos de interes: '+str(caracteristicasASeguir))
			# Si no encontre buenas características a seguir descarto esta infracción
			
			if len(caracteristicasASeguir.shape) > 1:
				self.miReporte.debug('GATILLADO DETECTADO')
				nuevaInfraccion = {'name':dateStamp,'momentum':indiceVideoFrameActual,'frameInicial':numeroDeFrameActual,'frameFinal':0,'desplazamiento':np.array(caracteristicasASeguir),'estado':'Candidato','foto':False}
				self.miReporte.debug('Guardando Imagen en: '+self.carpetaDeReporteActual+'/'+datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S.%f')+'.jpg')
				cv2.imwrite(self.carpetaDeReporteActual+'/'+dateStamp+'.jpg',frameActualFlujo)
				self.misInfracciones.append(nuevaInfraccion)
			else:
				self.miReporte.warning('No pude encontrar puntos de interes en el objeto >>>>>>>>>>>>>>>>>>>>>>')

		for infraction in self.misInfracciones:
			if (indiceVideoFrameActual == -10) & (self.miComputadora == 'raspberrypi') & (infraction['foto']==False):
				self.miCamara.encenderCamara()
				tomeFoto = {'foto':True}
				infraction.update(tomeFoto)
				self.miReporte.info('Encendi Camara con parametros anteriores')
			if infraction['estado'] == 'Confirmando':
				cerrarInfraccion = {'estado':'Confirmado','frameFinal':numeroDeFrameActual}
				infraction.update(cerrarInfraccion)
		
		numeroDeInfracciones = 0
		for infraction in self.misInfracciones:
			if infraction['estado'] == 'Confirmado':
				numeroDeInfracciones+=1
		self.reporteInfracciones()

		return numeroDeFrameActual

	def reporteInfracciones(self):
		sumaInfracciones = 0
		for infraction in self.misInfracciones:
			if infraction['estado'] == 'Confirmado':
				sumaInfracciones+=1
		self.infraccionesConfirmadas = sumaInfracciones
		sumaInfracciones = 0
		for infraction in self.misInfracciones:
			if infraction['estado'] == 'Timeout':
				sumaInfracciones+=1
		self.infraccionesDescartadasPorTiempo = sumaInfracciones
		sumaInfracciones = 0
		for infraction in self.misInfracciones:
			if infraction['estado'] == 'Giro':
				sumaInfracciones+=1
		self.infraccionesDescartadasGiro = sumaInfracciones

		self.infraccionesDescartadasPorEstacionario = 0
		self.numeroInfraccionesTotales = len(self.misInfracciones)

		return [self.infraccionesConfirmadas, self.numeroInfraccionesTotales, self.infraccionesDescartadasPorTiempo, self.infraccionesDescartadasPorEstacionario, self.infraccionesDescartadasGiro]

	def guardarReportes(self):
		"""
		Guarda los archivos de Debug, y casos, de existir, debera ser llamado en el primer Verde
		"""
		reportadosCasos = len(self.misInfracciones)
		if reportadosCasos==0:
			self.miReporte.info('Nada que reportar')
			return reportadosCasos
		self.miReporte.info('Reportando: '+str(len(self.misInfracciones))+' casos')
		numeroDeInfraccion = 0
		for infraccionActual in self.misInfracciones:
			if infraccionActual['estado'] == 'Confirmado':
				self.miReporte.info('Generando: '+str(infraccionActual['desplazamiento'].shape))
				self.generarReporteInfraccion(infraccionActual['name'],[infraccionActual['frameInicial']-self.widerVideo,infraccionActual['frameFinal']+self.widerVideo])
			else:
				archivosEliminados = 0
				for filename in glob.glob(self.carpetaDeReporteActual+'/'+infraccionActual['name']+'*'):
					os.remove(filename)
					archivosEliminados+=1
					os.system('touch '+filename+'.txt')
				self.miReporte.warning('ERASE WARNING!!!! Elimine {} archivos correspondientes a: '.format(archivosEliminados)+infraccionActual['name']+' con estado: '+infraccionActual['estado']+' ERASE WARNING!!!! ')

		if self.reportarDebug:
			np.save(self.carpetaDeReporteActualDebug+'/onda.npy',self.formaOndaDebug)
			self.generarReporteDebug()
			self.miReporte.debug('Guardado debug')
			with open(self.carpetaDeReporteActualDebug+'/infracciones.pkl', 'wb') as f:
				pickle.dump(self.misInfracciones, f, pickle.HIGHEST_PROTOCOL)
		self.miReporte.info('Casos guardados')

		return reportadosCasos

	def generarReporteDebug(self):
		"""
		Se crea un reporte en video con las imagenes de baja calidad con el fin de realizar mejoras futuras
		"""

		# Variables para la creacion de video:
		height, width, layers = self.reporteVideo[0].shape
		fourcc = cv2.VideoWriter_fourcc(*'XVID')
		prueba = cv2.VideoWriter(self.carpetaDeReporteActualDebug+'/'+self.fechaReporte+'-debug.avi',fourcc, self.framesPorSegundoEnVideo,(width,height))

		for indiceVideo in range(len(self.reporteVideo)):
			prueba.write(self.reporteVideo[indiceVideo])
		prueba.release()
	
		self.miReporte.info('Reportado: '+self.fechaReporte+' len: '+str(len(self.reporteVideo)))
		return True

	def generarReporteInfraccion(self,nombreInfraccion,indiceVideosParaVideo):
		"""
		Se crea un reporte para una infraccion comprendida entre indiceVideosParaVideo[0] y indiceVideosParaVideo[1] con gray scale en todos los frames que indique el indiceVideo para videos
		"""
		height, width, layers = self.reporteVideo[0].shape
		fourcc = cv2.VideoWriter_fourcc(*'XVID')
		prueba = cv2.VideoWriter(self.carpetaDeReporteActual+'/'+nombreInfraccion+'.avi',fourcc, self.framesPorSegundoEnVideo,(width,height))
		self.miReporte.info('Archivo guardado: '+self.carpetaDeReporteActual+'/'+nombreInfraccion+'.avi')
		if indiceVideosParaVideo[0]<0: inicio = 0
		else: inicio = indiceVideosParaVideo[0]
		if indiceVideosParaVideo[1]> len(self.reporteVideo): final = len(self.reporteVideo)
		else: final = indiceVideosParaVideo[1]
		for indiceVideo in range(inicio,final):
			imagenAVideo=self.reporteVideo[indiceVideo]
			prueba.write(imagenAVideo)
		prueba.release()
	
		self.miReporte.info('Reportado: '+self.fechaReporte+' len: '+str(indiceVideosParaVideo[1]-indiceVideosParaVideo[0]))
