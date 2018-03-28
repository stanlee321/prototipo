"""
This file allows us to keep track of the traffic flow
"""

import os
import sys
import cv2
import time
import math
import shutil
import logging
import datetime
import numpy as np
import multiprocessing

import matplotlib.pyplot as graficaActual
from ownLibraries.mireporte import MiReporte
from ownLibraries.perspectiva import Perspective
from ownLibraries.analisisonda import AnalisisOnda
from ownLibraries.generadorevidencia import GeneradorEvidencia
if os.uname()[1] == 'raspberrypi':
	from ownLibraries.shutterControllerv5 import ControladorCamara # Downgraded for tests

directorioDeTrabajo = os.getenv('HOME')+'/trafficFlow/prototipo'
directorioDeVideos = os.getenv('HOME')+'/trafficFlow/trialVideos'

class PoliciaInfractor():
	"""
	Entre las principales funciones de esta clase esta traducir la información de los frames entrantes a información mas manipulable y valiosa para un ser humano o para una inteligencia artificial
	Tambien se encarga de crear los objetos Vehiculos que pueden estar en estado cruce o infraccion
	También se encarga de proveer el estado actual del infractor
	"""
	def __init__(self,imagenParaInicializar,poligonoPartida,poligonoLlegada,poligonoDerecha,poligonoIzquierda,mifps = 8,directorioDeReporte=os.getenv('HOME')+'/'+datetime.datetime.now().strftime('%Y-%m-%d')+'_reporte',debug = False,flujoAntiguo = False, anguloCarril = 0):
		# Tomo la imagen de inicialización y obtengo algunas caracteristicas de la misma
		self.directorioDeReporte = directorioDeReporte
		self.miReporte = MiReporte(levelLogging=logging.DEBUG,nombre=__name__)
		self.miGrabadora = GeneradorEvidencia(self.directorioDeReporte,mifps,False)
		self.reportarDebug = debug
		self.minimosFramesVideoNormalDebug = 1*mifps # minimo 1 segundos de debug

		# Se cargan las variables de creación de la clase
		self.imagenAuxiliar = cv2.cvtColor(imagenParaInicializar, cv2.COLOR_BGR2GRAY)
		self.areaDeResguardo = np.array(poligonoPartida)
		self.areaDeConfirmacion = np.array(poligonoLlegada)
		self.areaDeGiroDerecha = np.array(poligonoDerecha)
		self.areaDeGiroIzquierda = np.array(poligonoIzquierda)
		self.anguloCarril = -anguloCarril
		self.desplazamiento = np.array([8*math.cos(self.anguloCarril),8*math.sin(self.anguloCarril)])

		# CONDICIONES DE DESCARTE
		# En si un punto sale del carril valido (ensanchado debidamente) se descarta el punto individual
		
		self.carrilValido = self.generarCarrilValido(poligonoPartida,poligonoLlegada,poligonoDerecha,poligonoIzquierda)
		self.maximoNumeroFramesParaDescarte = 80
		self.numeroDePuntosASeguirDeInicializacion = 4

		# la linea de referencia para tamanio sera del largo del paso de cebra, su longitud servira para descartar puntos que se alejen del resto
		self.maximaDistanciaEntrePuntos = self.tamanoVector(np.array(poligonoPartida[0])-np.array(poligonoPartida[1]))

		# Se crea la clase correspondiente
		self.miFiltro = AnalisisOnda()
		self.angulo = 18

		# La linea de pintado LK y trasera son los puntos del paso de cebra
		self.lineaDePintadoLK =  np.array([poligonoPartida[0],poligonoPartida[3]])
		self.lineaTraseraLK =  np.array([poligonoPartida[1],poligonoPartida[2]])

		ditanciaEnX = self.lineaDePintadoLK[1][0] - self.lineaDePintadoLK[0][0]
		ditanciaEnY = self.lineaDePintadoLK[1][1] - self.lineaDePintadoLK[0][1]
		vectorParalelo = self.lineaDePintadoLK[1] - self.lineaDePintadoLK[0]
		self.vectorParaleloUnitario = (vectorParalelo)/self.tamanoVector(vectorParalelo)
		self.vectorPerpendicularUnitario = np.array([self.vectorParaleloUnitario[1],-self.vectorParaleloUnitario[0]])
		self.numeroDePuntos = 15
		self.flujoAntiguo = False
		if flujoAntiguo == True:
			self.flujoAntiguo = True
			self.numeroDePuntos = 9
		self.stepX = ditanciaEnX/self.numeroDePuntos
		self.stepY = ditanciaEnY/self.numeroDePuntos
		self.lk_params = dict(  winSize  = (15,15),
								maxLevel = 7,
								criteria = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03))

		self.lineaFijaDelantera = np.zeros((self.numeroDePuntos+1,1,2))
		self.lineaDeResguardoDelantera = self.crearLineaDeResguardo()
		self.lineaDeResguardoAlteradaDelantera = self.lineaDeResguardoDelantera

		# Se inicializa la perspectiva con 1/9 del largo del paso de cebra como ancho

		self.areaFlujo = self.obtenerRegionFlujo(self.areaDeResguardo)
		self.miPerspectiva = Perspective(self.areaFlujo)
		self.anteriorFranja = self.miPerspectiva.transformarAMitad(self.imagenAuxiliar)
		self.optimalStep = 2

		self.listaVehiculos = []
		self.matrizDeterminacion = [['VERDE','-verdeEnRojo','-verdeEnAmarillo'],['rojoEnVerde','ROJO','-rojoEnAmarillo'],['-amarilloEnVerde','rojo','amarillo']]
		"""
		Estados de vehiculos
		1. Previo
		2. Cruce
		3. Giro
		4. Ruido
		"""
		self.reestablecerEstado()

		if os.uname()[1] == 'raspberrypi':
			self.camaraAlta = ControladorCamara()

	def obtenerRegionFlujo(self,npArrayDePartida):
		punto01 = npArrayDePartida[0]
		punto02 = npArrayDePartida[1]
		punto03 = npArrayDePartida[2]
		punto04 = npArrayDePartida[3]
		unitario12 = (punto02 - punto01)/self.tamanoVector(punto02 - punto01)
		unitario43 = (punto03 - punto04)/self.tamanoVector(punto03 - punto04)
		largoPasoCebra = self.tamanoVector(punto04-punto01)
		punto02 = punto01+largoPasoCebra/3*unitario12
		punto03 = punto04+largoPasoCebra/3*unitario43

		return np.array([punto01,punto02,punto03,punto04]).astype(int)

	def nuevoDia(self,directorioDeReporte):
		self.directorioDeReporte = directorioDeReporte
		self.miReporte.setDirectory(directorioDeReporte)
		self.miGrabadora.nuevoDia()
		self.reestablecerEstado()

	def generarCarrilValido(self, poligonoPartida,poligonoLlegada,poligonoDerecha,poligonoIzquierda):
		# Input type: self.carrilValido = np.array([poligonoPartida[0],poligonoPartida[1],poligonoPartida[2],poligonoPartida[3],poligonoLlegada[2],poligonoLlegada[3],poligonoLlegada[0],poligonoLlegada[1]])
		# Se modifican los puntos
		# partida: 0-,3+
		# llegada: 1+,2-
		# La matriz de rotacion por un angulo de 15 grados
		carrilValido = np.array([poligonoPartida[0],poligonoPartida[1],poligonoPartida[2],poligonoPartida[3],poligonoLlegada[2],poligonoLlegada[3],poligonoLlegada[0],poligonoLlegada[1]])
		self.angulo = 14
		cos15 = math.cos(self.angulo*math.pi/180)
		sin15 = math.sin(self.angulo*math.pi/180)
		rotacionNegativa = np.array([[cos15,sin15],[-sin15,cos15]])
		rotacionPositiva = np.array([[cos15,-sin15],[sin15,cos15]])
		llegada1_p7 = carrilValido[6]+rotacionPositiva.dot(carrilValido[7]-carrilValido[6])
		llegada1_p4 = carrilValido[5]+rotacionNegativa.dot(carrilValido[4]-carrilValido[5])

		llegada1_p0 = carrilValido[1]+rotacionNegativa.dot(carrilValido[0]-carrilValido[1])
		llegada1_p3 = carrilValido[2]+rotacionPositiva.dot(carrilValido[3]-carrilValido[2])

		carrilValido[0]=llegada1_p0
		carrilValido[3]=llegada1_p3
		carrilValido[4]=llegada1_p4
		carrilValido[7]=llegada1_p7

		# Hasta este punto se obtiene el carril valido simplemente ensanchado
		# Ahora concatenamos con los puntos de llegada a Derecha e Izquierda

		carrilValido = np.array([	carrilValido[0],
									carrilValido[1],
									carrilValido[2],
									carrilValido[3],
									poligonoDerecha[2],
									poligonoDerecha[3],
									poligonoDerecha[0],
									poligonoDerecha[1],
									carrilValido[4],
									carrilValido[5],
									carrilValido[6],
									carrilValido[7],
									poligonoIzquierda[2],
									poligonoIzquierda[3],
									poligonoIzquierda[0],
									poligonoIzquierda[1]])

		return carrilValido

	def tamanoVector(self,vector):
		# Metodo auxiliar por la recurencia de esta aplicacion
		return math.sqrt(vector[0]**2+vector[1]**2)

	def puntoEstaEnRectangulo(self,punto,rectangulo):
		# Metodo auxiliar por la recurencia de esta aplicacion
		estadoARetornar = False
		if (punto[0]>rectangulo[0])&(punto[0]<rectangulo[0]+rectangulo[2])&(punto[1]>rectangulo[1])&(punto[1]<rectangulo[1]+rectangulo[3]):
			estadoARetornar = True
		return estadoARetornar

	# No longer needed
	def inicializarAgente(self,):
		"""
		Resets the starting line to get ready to the next frame
		"""
		del self.listaVehiculos
		self.listaVehiculos = []

	def crearLineaDeResguardo(self):
		"""
		La linea de resguardo es una linea preparada para entrar en el algoritmo de lucas Kanade y controlar el flujo o seguir objetos que crucen la zona de partida
		"""
		lineaAuxiliar = np.array([[self.lineaDePintadoLK[0]]])
		for numeroDePunto in range(1,self.numeroDePuntos+1):
			lineaAuxiliar = np.append(lineaAuxiliar,[[self.lineaDePintadoLK[0]+numeroDePunto*np.array([self.stepX,self.stepY])]],axis=0)
		self.lineaFijaDelantera = lineaAuxiliar
		self.lineaFijaDelantera = np.array(self.lineaFijaDelantera,dtype = np.float32)
		return lineaAuxiliar

	def seguirImagen(self,numeroDeFrame,imagenActual,informacion = False,colorSemaforo = 1):
		"""
		Metodo mas importante del infractor: Se encarga de:
		1. Crear vehiculos de ser necesario
		2. Seguir vehiculos
		3. Confirmar o descartar vehículos
		"""
		#print('>> 01 Inicio Seguir')
		if colorSemaforo == 1:
			self.estadoActual['colorSemaforo'] = 'Rojo'
		elif colorSemaforo == 0:
			self.estadoActual['colorSemaforo'] = 'Verde'
		elif colorSemaforo == 2:
			self.estadoActual['colorSemaforo'] = 'Amarillo'
		else:
			self.estadoActual['colorSemaforo'] = 'No hay semaforo'

		imagenActualEnGris = cv2.cvtColor(imagenActual, cv2.COLOR_BGR2GRAY)

		arrayAuxiliarParaVelocidad, activo, err = cv2.calcOpticalFlowPyrLK(self.imagenAuxiliar, imagenActualEnGris, self.lineaFijaDelantera, None, **self.lk_params)
		self.lineaDeResguardoAlteradaDelantera = arrayAuxiliarParaVelocidad
		
		if self.flujoAntiguo:
			velocidadEnBruto = self.obtenerMagnitudMovimientoEnRegion(self.miPerspectiva.transformarAMitad(imagenActualEnGris))
		else:
			velocidadEnBruto = self.obtenerMagnitudMovimiento(self.lineaFijaDelantera,self.lineaDeResguardoAlteradaDelantera)
		velocidadFiltrada, pulsoVehiculos = self.miFiltro.obtenerOndaFiltrada(velocidadEnBruto)

		# Se evoluciona el resto de vehiculos solo si son 'Previo'
		for infraccion in self.listaVehiculos:
			# Si es candidato evoluciona:
			if infraccion['estado'] == 'Previo':
				if (infraccion['infraccion'] == 'candidato')&(colorSemaforo==0):
					#infraccion['observacion'] = 'LlegoEnVerde'
					self.miReporte.info('Infraccion Descartada Por Llegar En Verde')
					infraccion['infraccion'] = ''
				# Al principio descarto los puntos negativos o en los bordes (0,0), -(x,y)
				nuevaPosicionVehiculo, activo, err = cv2.calcOpticalFlowPyrLK(self.imagenAuxiliar, imagenActualEnGris, infraccion['desplazamiento'], None, **self.lk_params)	
				
				# DESCARTE POR DISPERSIÓN DE PUNTOS Y POR TIMEOUT
				NoneType = type(None)

				dispersion = type(nuevaPosicionVehiculo) == NoneType
				timeout = (numeroDeFrame - infraccion['frameInicial']) > self.maximoNumeroFramesParaDescarte
				if  dispersion or timeout:
					infraccion['estado'] = 'Salio'
					if timeout:
						infraccion['estado'] = 'TimeOut'
					
					if infraccion['infraccion'] == 'candidato':
						infraccion['infraccion'] = ''
						self.eliminoCarpetaDeSerNecesario(infraccion)
						# VALIDO SOLO PARA GIRO CONTROLADO POR SEMAFORO A PARTE
					self.estadoActual['ruido'] += 1
					break
				# DESCARTE INDIVIDUAL POR PUNTO
				# Se descarta puntos individualmente, si un punto esta en el borde del frame o fuera de el entonces se lo mantiene congelado
				# PELIGRO, los frames congelados estan ingresando al calcOpticalFlow arriba, revisar
				# for otroIndice in range(len(infraccion['desplazamiento'])):
				#	controlVector = infraccion['desplazamiento'][otroIndice]
				#	if not self.puntoEstaEnRectangulo((controlVector[0][0],controlVector[0][1]),(0,0,320,240)):
				#		nuevaPosicionVehiculo[otroIndice] = infraccion['desplazamiento'][otroIndice]
				# DESCARTE POR TIEMPO, POR VEHICULO

				# Si es candidato y algun punto llego al final se confirma
				indicesValidos = []
				puntosQueLlegaron = 0
				puntosQueGiraronDerecha = 0
				puntosQueGiraronIzquierda = 0

				for indiceVector in range(len(nuevaPosicionVehiculo)):
					# Para cada indice
					vector = nuevaPosicionVehiculo[indiceVector]
					
					xTest, yTest = vector[0][0], vector[0][1]
					# hago una lista de los indices que aun son validos
					if cv2.pointPolygonTest(self.carrilValido,(xTest, yTest),True)>=0:	# Si esta dentro del carril valido se mantiene el punto
						indicesValidos.append(indiceVector)
					# Confirmo la llegada de uno
					if cv2.pointPolygonTest(self.areaDeConfirmacion,(xTest, yTest ),True)>=0:	# Si esta dentro del espacio de llegada se confirma
						puntosQueLlegaron += 1
					if cv2.pointPolygonTest(self.areaDeGiroDerecha,(xTest, yTest ),True)>=0:	# Si esta dentro del espacio de llegada se confirma
						puntosQueGiraronDerecha += 1
					if cv2.pointPolygonTest(self.areaDeGiroIzquierda,(xTest, yTest ),True)>=0:	# Si esta dentro del espacio de llegada se confirma
						puntosQueGiraronIzquierda += 1
					
					if puntosQueLlegaron >= 2:
						# Si llego al otro extremo, entonces cruzo:
						infraccion['estado'] = 'Cruzo'
						self.estadoActual['cruzo'] += 1
						# Si era candidato y esta llegando en rojo o amarillo
						# ESTO DESCARTA LAS LLEGADAS EN VERDE # Anulado por mala intensión
						if (infraccion['infraccion'] == 'candidato'):
							infraccion['infraccion'] = 'CAPTURADO'
							infraccion['colorFinal'] = colorSemaforo
							infraccion['colorReporte'] = self.matrizDeterminacion[infraccion['colorInicial']][infraccion['colorFinal']]
							infraccion['frameFinal'] = numeroDeFrame
							self.estadoActual['infraccion'] += 1
						
						self.miReporte.info(infraccion['infraccion']+'\t'+infraccion['estado']+' a horas '+infraccion['hora']+' ('+str(infraccion['frameInicial'])+'-'+str(infraccion['frameFinal'])+')')
						break

					if puntosQueGiraronDerecha >= 2:
						# Si llego al otro extremo, entonces cruzo:
						infraccion['estado'] = 'GiroDerecha'
						self.estadoActual['derecha'] += 1
						# Si era candidato y esta llegando en rojo o amarillo
						# ESTO DESCARTA LAS LLEGADAS EN VERDE # Anulado por mala intensión
						if (infraccion['infraccion'] == 'candidato'):
							infraccion['infraccion'] = 'CAPTURADO_DERECHA'
							infraccion['colorFinal'] = colorSemaforo
							infraccion['colorReporte'] = self.matrizDeterminacion[infraccion['colorInicial']][infraccion['colorFinal']]
							infraccion['frameFinal'] = numeroDeFrame
							self.estadoActual['infraccion'] += 1
						
						self.miReporte.info(infraccion['infraccion']+'\t'+infraccion['estado']+' a horas '+infraccion['hora']+' ('+str(infraccion['frameInicial'])+'-'+str(infraccion['frameFinal'])+')')
						break

					if puntosQueGiraronIzquierda >= 2:
						# Si llego al otro extremo, entonces cruzo:
						infraccion['estado'] = 'GiroIzquierda'
						self.estadoActual['izquierda'] += 1
						# Si era candidato y esta llegando en rojo o amarillo
						# ESTO DESCARTA LAS LLEGADAS EN VERDE # Anulado por mala intensión
						if (infraccion['infraccion'] == 'candidato'):
							infraccion['infraccion'] = 'CAPTURADO_IZQUIERDA'
							infraccion['colorFinal'] = colorSemaforo
							infraccion['colorReporte'] = self.matrizDeterminacion[infraccion['colorInicial']][infraccion['colorFinal']]
							infraccion['frameFinal'] = numeroDeFrame
							self.estadoActual['infraccion'] += 1
						
						self.miReporte.info(infraccion['infraccion']+'\t'+infraccion['estado']+' a horas '+infraccion['hora']+' ('+str(infraccion['frameInicial'])+'-'+str(infraccion['frameFinal'])+')')
						break
				# Se continuara solamente con los puntos validos
				infraccion['desplazamiento'] = nuevaPosicionVehiculo[indicesValidos]

		if pulsoVehiculos == 1:
			# Se determina los mejores puntos para seguir para ser parte del objeto Vehiculo
			puntosMasMoviles = self.obtenerPuntosMoviles(self.lineaFijaDelantera,self.lineaDeResguardoAlteradaDelantera,informacion)
			
			# Cada vehiculo tiene un numbre que biene a xer ela fecja y hora de la infracción en cuestion
			fechaNueva = datetime.datetime.now().strftime('%Y%m%d')
			horaNueva = datetime.datetime.now().strftime('%H%M%S')
			nombreInicialParaInfraccionYFolder = fechaNueva+'_'+horaNueva

			# CREACION NUEVO VEHICULO
			nuevoVehiculo = {	'name':nombreInicialParaInfraccionYFolder,
								'fecha':fechaNueva,
								'hora':horaNueva,
								'colorReporte':'none',
								'frameInicial':numeroDeFrame,
								'colorInicial':colorSemaforo,
								'frameFinal':0,
								'colorFinal':-1,
								'multiplicidad':1,
								'desplazamiento':puntosMasMoviles,
								'numeroDeVehiculos':1,
								'estado':'Previo',
								'infraccion':'',
								'observacion':''}

			# CREACION NUEVO CANDIDATO
			direccionDeGuardadoFotos = 'None'
			if colorSemaforo >=1:
				nuevoVehiculo['infraccion'] = 'candidato'
				direccionDeGuardadoFotos = self.directorioDeReporte + '/' + nombreInicialParaInfraccionYFolder
				if not os.path.exists(direccionDeGuardadoFotos):
					os.makedirs(direccionDeGuardadoFotos)

				if os.uname()[1] == 'raspberrypi':
					# AQUI!
					self.camaraAlta.encenderCamaraEnSubDirectorio(direccionDeGuardadoFotos)
			
			self.listaVehiculos.append(nuevoVehiculo)
			self.miReporte.info('\t\tCreado vehiculo '+nuevoVehiculo['hora']+' en frame '+str(nuevoVehiculo['frameInicial'])+' con nivel '+nuevoVehiculo['infraccion']+' guardado en '+direccionDeGuardadoFotos[19:])

		infraccionesConfirmadas = self.numeroInfraccionesConfirmadas()

		self.imagenAuxiliar = imagenActualEnGris
		#print(self.estadoActual)
		#sys.stdout.write("\033[F") # Cursor up one line
		return velocidadEnBruto, velocidadFiltrada, pulsoVehiculos, 0

	def reestablecerEstado(self):
		self.estadoActual =   { 'previo':0,
								'cruzo':0,
								'salio':0,
								'derecha':0,
								'izquierda':0,
								'ruido':0,
								'infraccion':0,
								'infraccionAmarillo':0,
								'colorSemaforo':'Verde'}


	def numeroInfraccionesConfirmadas(self):
		contadorInfraccionesConfirmadas = 0
		for infraccion in self.listaVehiculos:
			if infraccion['estado'] == 'Cruzo':	
				contadorInfraccionesConfirmadas += 1
		return contadorInfraccionesConfirmadas

	def numeroInfraccionesTotales(self):
		contadorInfracciones = 0
		for infraccion in self.listaVehiculos:
			contadorInfracciones += 1
		return contadorInfracciones

	def reportarPasoAPaso(self,historial):
		"""
		Este metodo reporta un caso a la vez de existir el mismo en la base de datos de infracciones
		"""
		self.listaVehiculos = [vehiculosPendientes for vehiculosPendientes in self.listaVehiculos if vehiculosPendientes['estado']=='Previo' or vehiculosPendientes['infraccion']=='CAPTURADO' or vehiculosPendientes['infraccion']=='CAPTURADO_DERECHA' or vehiculosPendientes['infraccion']=='CAPTURADO_IZQUIERDA']
		listaInfracciones = [infraccion for infraccion in self.listaVehiculos if infraccion['infraccion']=='CAPTURADO']
		# Los cruces siguen evolucionando
		# Las infracciones en calidad de 'CAPTURADO' son generadas en video
		# Los cruces en ruido son eliminados	
		if len(listaInfracciones)>0:
			# Como python optimiza el copiado de listas de diccionarios la siguiente figura modifica la lista originalself.es
			infraccionActual = listaInfracciones[0]
			#infraccionActual = self.listaVehiculos[self.listaVehiculos.index(listaInfracciones[0])]
			infraccionActual['infraccion'] = 'REPORTADO'
			#self.miGrabadora.generarReporteInfraccion(historial, infraccionActual,debug = self.reportarDebug)
			self.miGrabadora.generarReporteEnVideoDe(historial,infraccionActual,debug = self.reportarDebug)

	def generarVideoMuestra(self,historial):
		if len(historial) > self.minimosFramesVideoNormalDebug:
			#self.miGrabadora.generarReporteInfraccion(historial, True,debug = self.reportarDebug)
			self.miGrabadora.generarVideoDebugParaPruebas(historial)
		else:
			self.miReporte.info('\t\t-Infraccion Descartada por longitud')

	def eliminoCarpetaDeSerNecesario(self,infraccion):
		carpetaABorrar = self.directorioDeReporte+'/'+infraccion['name']
		self.miReporte.info('\t\t> Borrando: '+carpetaABorrar+' con estado '+infraccion['estado'])
		try:
			os.system('rm -rf '+carpetaABorrar)
		except Exception as rmException:
			self.miReporte.warning('\t\t\tFALLO rm -rf '+infraccion['name']+' por '+str(rmException))
			try:
				shutil.rmtree(carpetaABorrar, ignore_errors=True)
			except Exception as rmTreeException:
				self.miReporte.error('\t\t\tFALLO RMTREE '+infraccion['name']+' por '+str(rmTreeException))

	def popInfraccion(self):
		if self.numeroInfraccionesConfirmadas() != 0:
			variableARetornar = self.listaVehiculos.pop()
			while variableARetornar['estado'] != 'Cruzo':
				variableARetornar = self.listaVehiculos.pop()
			return variableARetornar
		else:
			return {}
		return variableARetornar

	def reporteActual(self):
		self.miReporte.info('Infracciones Sospechosas:')
		for infraccion in self.listaVehiculos:
			self.miReporte.info(infraccion['frameInicial']+' a '+str(infraccion['frameFinal'])+' con estado: '+infraccion['estado'])
		self.miReporte.info('Infracciones Confirmadas:')
		for infraccion in self.listaVehiculos:
			self.miReporte.info('\t-> '+infraccion['hora']+' de '+str(infraccion['frameInicial'])+' a '+str(infraccion['frameFinal'])+' con estado: '+infraccion['estado'])

	def obtenerLinea(self):
		"""
		Returns the starting line in tuple format, ready to read or plot with opencv
		"""
		aDevolver = []
		for infraccion in self.listaVehiculos:
			if infraccion['estado']=='Previo':
				for punto in infraccion['desplazamiento']:
					aDevolver.append(tuple(punto[0]))
		return aDevolver

	def obtenerLineasDeResguardo(self,alterada=False):
		aDevolver = []
		if alterada:
			for punto in self.lineaDeResguardoAlteradaDelantera:
				aDevolver.append(tuple(punto[0]))
		else:
			for punto in self.lineaDeResguardoDelantera:
				aDevolver.append(tuple(punto[0]))
		return aDevolver

	def obtenerVectorMovimiento(self,vectorAntiguo, nuevoVector):
		"""
		Gets the movement vector of all points in the starting line, this is used more like an internal method
		"""
		x = 0
		y = 0
		for numeroDePunto in range(1,self.numeroDePuntos+1):
			x += nuevoVector[numeroDePunto][0][0] - vectorAntiguo[numeroDePunto][0][0]
			y += nuevoVector[numeroDePunto][0][1] - vectorAntiguo[numeroDePunto][0][1]
		x = 10*x/(self.numeroDePuntos+1)
		y = 10*y/(self.numeroDePuntos+1)
		return (x,y)

	def obtenerPuntosMoviles(self,vectorAntiguo, nuevoVector,informacion = False):
		"""
		Gets center of movement as a tuple of three vectors
		"""
		##### OJO AQUI TAMBIEN PUEDO FILTRAR RUIDO???
		dif2 = []	# Para todos los puntos de resguardo veo los que tienen mayor movimiento
		for numeroDePunto in range(1,self.numeroDePuntos+1):
			x = nuevoVector[numeroDePunto][0][0] - vectorAntiguo[numeroDePunto][0][0]
			y = nuevoVector[numeroDePunto][0][1] - vectorAntiguo[numeroDePunto][0][1]
			dif2.append(x**2+y**2)
		indiceDeMayores = []
		for numeroDePuntoASeguir in range(self.numeroDePuntosASeguirDeInicializacion):
			indice = dif2.index(max(dif2))
			indiceDeMayores.append(indice)
			dif2.pop(indice)

		listaNuevosPuntos = np.array(nuevoVector[indiceDeMayores])
		
		for indice in range(len(listaNuevosPuntos)):
			listaNuevosPuntos[indice][0] = listaNuevosPuntos[indice][0] + self.desplazamiento

		return listaNuevosPuntos #np.array([[nuevoVector[indiceDeMayores[0]][0]],[nuevoVector[indiceDeMayores[1]][0]],[nuevoVector[indiceDeMayores[2]][0]]])
			

	def obtenerMagnitudMovimiento(self,vectorAntiguo, nuevoVector):
		"""
		Gets the real magnitud of movement perpendicular to the starting point
		"""
		(x,y) = self.obtenerVectorMovimiento(vectorAntiguo, nuevoVector)
		moduloPerpendicular = self.vectorPerpendicularUnitario[0]*x+self.vectorPerpendicularUnitario[1]*y
		return moduloPerpendicular

	def obtenerMagnitudMovimientoEnRegion(self,nuevaFranja):
		flow = cv2.calcOpticalFlowFarneback(self.anteriorFranja, nuevaFranja, None, 0.5, 3, 15, 3, 5, 1.2, 0) #(self.auxiliar_image, current_image, None, 0.7, 3, 9, 3, 5, 1.2, 0)

		#y, x = np.mgrid[self.optimalStep//2:nuevaFranja.shape[0]:self.optimalStep, self.optimalStep//2:nuevaFranja.shape[1]:self.optimalStep].reshape(2,-1)
		#y = np.int32(y)
		#x = np.int32(x)
		#fx, fy = flow[y,x].T
		#flowX = sum(fx)
		#flowY = sum(fy)

		flowX = 0
		flowY = 0

		for row in flow:
			for data in row:
				flowX += data[0]
				flowY += data[1]

		self.anteriorFranja = nuevaFranja
		# Se retorna el flujo en X invertido
		flujoPerpendicular = -10*flowX/((flow.shape[0]*flow.shape[1])+1)
		
		return flujoPerpendicular


	def apagarCamara(self):
		self.camaraAlta.apagarControlador()



if __name__ == '__main__':

	#This small trial is a proff of work for the current class

	try:
		nombreDeVideo = directorioDeVideos+'/{}.mp4'.format(sys.argv[1])
		camaraParaFlujo = cv2.VideoCapture(nombreDeVideo)
		archivoParametrosACargar = nombreDeVideo[:-4]+'.npy'
	except:
		nombreDeVideo = directorioDeVideos+'/mySquare.mp4'
		camaraParaFlujo = cv2.VideoCapture(nombreDeVideo)
		archivoParametrosACargar = nombreDeVideo[:-4]+'.npy'

	parametrosInstalacion = np.load(archivoParametrosACargar)
	poligonoSemaforo = parametrosInstalacion[0]
	verticesPartida = parametrosInstalacion[1]
	verticesLlegada = parametrosInstalacion[2]
	
	ret, capturaDeFlujoInicial = camaraParaFlujo.read()
	framePrueba = cv2.resize(capturaDeFlujoInicial,(320,240))
	## Creo los objetos:
	miPolicia = PoliciaInfractor(framePrueba,verticesPartida,verticesLlegada)
	tiempoAuxiliar = time.time()
	velocidades = []
	velocidadesFiltradas = []
	pulsoVehiculos = []
	frame = 0
	mifps = 8

	while True:
		for inciceDescarte in range(30//mifps):
			ret, frameActual = camaraParaFlujo.read()

		frameActual = cv2.resize(frameActual,(320,240))
		tiempoAuxiliar = time.time()
		filtrado,pulsoVehiculosRes,magnitud = miPolicia.seguirImagen(frame,frameActual)
		toPlot = miPolicia.obtenerLinea()
	
		for punto in toPlot:
			frameActual = cv2.circle(frameActual,punto, 4, (0,0,0), -1)# tuple(map(tuple,toPlot))
		font = cv2.FONT_HERSHEY_SIMPLEX
		cv2.putText(frameActual, str(int(magnitud)), (20,20), font, 0.4,(255,255,255),1,cv2.LINE_AA)
		cv2.putText(frameActual, str(miPolicia.infraccionesConfirmadas), (20,40), font, 0.4,(255,255,255),1,cv2.LINE_AA)
		cv2.imshow('Visual',frameActual)
		miPolicia.reporteActual()
		
		velocidades.append(magnitud)
		velocidadesFiltradas.append(filtrado)
		pulsoVehiculos.append(pulsoVehiculosRes)

		ch = 0xFF & cv2.waitKey(5)
		if ch == ord('q'):
			break

		if ch == ord('p'):
			x = range(len(velocidades))
			graficaActual.title('Velocidad Y objetos')
			graficaActual.plot(x,velocidades,label='vel')
			graficaActual.plot(x,velocidadesFiltradas,label='Fil')
			graficaActual.plot(x,pulsoVehiculos,label='Fla')
			graficaActual.legend(loc='upper center', bbox_to_anchor=(0.5, 1.05),ncol=4, fancybox=True, shadow=True)
			graficaActual.show()

		print('Ciclo',time.time()-tiempoAuxiliar)
		while time.time()-tiempoAuxiliar<1/mifps:
			True
		frame += 1
		tiempoAuxiliar = time.time()
