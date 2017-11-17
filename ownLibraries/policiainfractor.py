import os
import sys
import cv2
import time
import math
import shutil
import logging
import datetime
import numpy as np

import matplotlib.pyplot as graficaActual
from ownLibraries.shooterv3 import Shooter
from ownLibraries.mireporte import MiReporte
from ownLibraries.analisisonda import AnalisisOnda

directorioDeReporte = os.getenv('HOME')+'/casosReportados'
directorioDeTrabajo = os.getenv('HOME')+'/trafficFlow/prototipo'
directorioDeVideos = os.getenv('HOME')+'/trafficFlow/trialVideos'

class PoliciaInfractor():
	"""
	Esta clase recibe una imagen, el estado del semaforo y determina flujo vehicular e infracciones
	"""
	def __init__(self,imagenParaInicializar,poligonoPartida,poligonoLlegada,segundaCamara = False):
		# Tomo la imagen de inicialización y obtengo algunas caracteristicas de la misma
		self.miReporte = MiReporte(levelLogging=logging.DEBUG,nombre=__name__)
		self.imagenAuxiliar = cv2.cvtColor(imagenParaInicializar, cv2.COLOR_BGR2GRAY)
		try:
			height,width = self.imagenAuxiliar.shape
		except:
			self.miReporte.error('No pude obtener data, es una imagen el objeto de inicializacion?')
		
		self.areaDeResguardo = np.array(poligonoPartida)
		self.areaDeConfirmacion = np.array(poligonoLlegada)
		self.lineaDePintadoLK =  np.array([poligonoPartida[0],poligonoPartida[3]])
		self.lineaTraseraLK =  np.array([poligonoPartida[1],poligonoPartida[2]])

		self.miFiltro = AnalisisOnda()

		ditanciaEnX = self.lineaDePintadoLK[1][0] - self.lineaDePintadoLK[0][0]
		ditanciaEnY = self.lineaDePintadoLK[1][1] - self.lineaDePintadoLK[0][1]
		vectorParalelo = self.lineaDePintadoLK[1] - self.lineaDePintadoLK[0]
		self.vectorParaleloUnitario = (vectorParalelo)/math.sqrt(vectorParalelo[0]**2+vectorParalelo[1]**2)
		self.vectorPerpendicularUnitario = np.array([self.vectorParaleloUnitario[1],-self.vectorParaleloUnitario[0]])
		self.numeroDePuntos = 9
		self.stepX = ditanciaEnX//self.numeroDePuntos
		self.stepY = ditanciaEnY//self.numeroDePuntos
		self.lk_params = dict(  winSize  = (15,15),
								maxLevel = 7,
								criteria = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03))
		# erase 4 lines featureparams
		self.lineaDeResguardoDelantera = np.array([self.lineaDePintadoLK[0]])
		self.lineaFijaDelantera = np.zeros((self.numeroDePuntos+1,1,2))
		self.lineaEmpuje = np.zeros((self.numeroDePuntos+1,1,2))
		self.infraccionesConfirmadas = 0
		self.restablecerLineaLK()
		self.listaDeInfracciones = []
		self.maximoNumeroFramesParaDescarte = 100
		self.ultimaVelocidad = 0
		self.segundaCamara = segundaCamara
		eightMP = (3240,2464)
		piCamSource  = 1
		if self.segundaCamara:
			self.camaraAlta = Shooter(video_source = piCamSource, width = eightMP[0], height = eightMP[1], capturas = 2)

	def establecerRegionInteresAlta(self,cutPoly):
		self.camaraAlta.establecerRegionInteres(cutPoly)

	def inicializarAgente(self,):
		"""
		Resets the starting line to get ready to the next frame
		"""
		self.infraccionesConfirmadas = 0
		self.restablecerLineaLK()
		del self.listaDeInfracciones
		self.listaDeInfracciones = []
		self.ultimaVelocidad = 0

	def restablecerLineaLK(self,):
		self.lineaDeResguardoDelantera = np.array([[self.lineaDePintadoLK[0]]])
		for numeroDePunto in range(1,self.numeroDePuntos+1):
			self.lineaDeResguardoDelantera = np.append(self.lineaDeResguardoDelantera,[[self.lineaDePintadoLK[0]+numeroDePunto*np.array([self.stepX,self.stepY])]],axis=0)
		self.lineaFijaDelantera = self.lineaDeResguardoDelantera

	def seguirObjeto(self,numeroDeFrame,informacion):
		"""
		Se organiza la información acorde al algoritmo de seguimiento
		"""
		# la imagen introducida esta en RGB, 240,320,3
		imagenActual = informacion['frame']
		cambiosImportantes, ondaFiltrada, flanco, flujoTotal = self.seguirImagen(numeroDeFrame,imagenActual,informacion)

		for rectangulo in informacion['rectangulos']:			# Para todos los rectangulos
			estado = 2
			x,y,w,h = rectangulo[0]
			centroid  = rectangulo[1]
			for infraccion in self.listaDeInfracciones:
				for punto in infraccion['desplazamiento']:
					if self.puntoEstaEnPoligono((punto[0][0],punto[0][1]),(x,y,w,h)):
						estado = 0
						break
					else:
						estado = 1
			if estado != 0:
				try:
					informacion['recortados'][informacion['rectangulos'].index(rectangulo)] = np.zeros((0))
				except Exception as e:
					#self.miReporte.error('No pude eliminar imagen en frame'+str(informacion['rectangulos']))
					print('this error:, ', e)
			rectangulo[2] = estado

		return cambiosImportantes

	def puntoEstaEnPoligono(self,punto,rectangulo):
		estadoARetornar = False
		if (punto[0]>rectangulo[0])&(punto[0]<rectangulo[0]+rectangulo[2])&(punto[1]>rectangulo[1])&(punto[1]<rectangulo[1]+rectangulo[3]):
			estadoARetornar = True
		return estadoARetornar, ondaFiltrada, flanco, flujoTotal

	def seguirImagen(self,numeroDeFrame,imagenActual,informacion = False,colorSemaforo = 1):
		"""
		Get into the new frame, updates the flow and follows the item as required
		"""
		# la imagen introducida esta en RGB, 240,320,3
		cambiosImportantes = False
		imagenActualEnGris = cv2.cvtColor(imagenActual, cv2.COLOR_BGR2GRAY)
		
		self.lineaDeResguardoDelantera = np.array(self.lineaDeResguardoDelantera,dtype = np.float32)	# This solved the problem although the array seemed to ve  in float32, adding this specification to this line solved the problem
		self.lineaFijaDelantera = np.array(self.lineaFijaDelantera,dtype = np.float32)
		# Se compara las lineas anterior y nueva para obtener el flujo en dirección deseada
		
		arrayAuxiliarParaVelocidad, activo, err = cv2.calcOpticalFlowPyrLK(self.imagenAuxiliar, imagenActualEnGris, self.lineaFijaDelantera, None, **self.lk_params)

		self.lineaEmpuje = arrayAuxiliarParaVelocidad
		flujoTotal = self.obtenerMagnitudMovimiento(self.lineaFijaDelantera,arrayAuxiliarParaVelocidad)

		ondaFiltrada, flanco = self.miFiltro.obtenerOndaFiltrada(flujoTotal)
		if colorSemaforo >=1:
			if flanco == 1:
				puntosMasMoviles = self.obtenerPuntosMoviles(self.lineaFijaDelantera,arrayAuxiliarParaVelocidad,informacion)
				nombreInfraccionYFolder = datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S')
				nuevaInfraccion = {'name':nombreInfraccionYFolder,'momentum':numeroDeFrame,'frameInicial':numeroDeFrame,'frameFinal':0,'desplazamiento':puntosMasMoviles,'estado':'Candidato','foto':False}
				if self.segundaCamara:
					self.camaraAlta.encenderCamaraEnSubDirectorio(nombreInfraccionYFolder, nombreInfraccionYFolder)
				cambiosImportantes = True
				self.listaDeInfracciones.append(nuevaInfraccion)
				
			for infraccion in self.listaDeInfracciones:
				# Si es candidato evoluciona:
				if infraccion['estado'] == 'Candidato':
					nuevoArrayAActualizar, activo, err = cv2.calcOpticalFlowPyrLK(self.imagenAuxiliar, imagenActualEnGris, infraccion['desplazamiento'], None, **self.lk_params)	
					infraccion['desplazamiento'] = nuevoArrayAActualizar
					# Si es candidato y duro demasiado se descarta
					if (numeroDeFrame - infraccion['frameInicial']) > self.maximoNumeroFramesParaDescarte:
						infraccion['estado']='Descartado'
					# Si es candidato y algun punto llego al final se confirma
					for vector in nuevoArrayAActualizar:
						xTest, yTest = vector[0][0], vector[0][1]
						if cv2.pointPolygonTest(self.areaDeConfirmacion,(xTest, yTest ),True)>=0:
							infraccion['estado'] = 'Confirmado'
							cambiosImportantes = True
							infraccion['frameFinal'] = numeroDeFrame
							self.miReporte.info('Conf: '+infraccion['name']+' de '+str(infraccion['frameInicial'])+' a '+str(infraccion['frameFinal'])+' es '+infraccion['estado'])
							break
			infraccionesConfirmadas = self.numeroInfraccionesConfirmadas()

		self.imagenAuxiliar = imagenActualEnGris
		return cambiosImportantes, ondaFiltrada, flanco, flujoTotal

	def numeroInfraccionesConfirmadas(self):
		contadorInfraccionesConfirmadas = 0
		for infraccion in self.listaDeInfracciones:
			if infraccion['estado'] == 'Confirmado':
				contadorInfraccionesConfirmadas += 1
		return contadorInfraccionesConfirmadas

	def numeroInfraccionesTotales(self):
		contadorInfracciones = 0
		for infraccion in self.listaDeInfracciones:
			contadorInfracciones += 1
		return contadorInfracciones

	def purgeInfractions(self):
		for infraccion in self.listaDeInfracciones:
			if infraccion['estado'] != 'Confirmado':
				self.eliminoCarpetaDeSerNecesario(infraccion)

	def eliminoCarpetaDeSerNecesario(self,infraccion):
		try: 
			carpetaABorrar = directorioDeReporte+'/'+infraccion['name']
			print('>>>>> Borrando: ',carpetaABorrar)
			shutil.rmtree(carpetaABorrar)
		except:
			self.miReporte.warning('No pude borrar posible carpeta fantasma: '+infraccion['name'])

	def popInfraccion(self):
		if self.numeroInfraccionesConfirmadas() != 0:
			variableARetornar = self.listaDeInfracciones.pop()
			while variableARetornar['estado'] != 'Confirmado':
				variableARetornar = self.listaDeInfracciones.pop()
			return variableARetornar
		else:
			return {}
		return variableARetornar

	def reporteActual(self):
		self.miReporte.info('Infracciones Sospechosas:')
		for infraccion in self.listaDeInfracciones:
			self.miReporte.info(infraccion['frameInicial']+' a '+str(infraccion['frameFinal'])+' con estado: '+infraccion['estado'])
		self.miReporte.info('Infracciones Confirmadas:')
		for infraccion in self.listaDeInfracciones:
			self.miReporte.info(infraccion['name']+' de '+str(infraccion['frameInicial'])+' a '+str(infraccion['frameFinal'])+' con estado: '+infraccion['estado'])

	def obtenerLinea(self):
		"""
		Returns the starting line in tuple format, ready to read or plot with opencv
		"""
		aDevolver = []
		for infraccion in self.listaDeInfracciones:
			if infraccion['estado']=='Candidato':
				for punto in infraccion['desplazamiento']:
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
		puntosOptimizados = False
		try:
			misRectangulos = informacion['rectangulos']
			puntosOptimizados = True
		except:
			puntosOptimizados = False
		if puntosOptimizados:
			lineaInterna = []
			for punto in self.lineaFijaDelantera:
				lineaInterna.append(punto[0].tolist())
			
			contadorDeRectangulos = 0
			lineaParaRectangulo = {}
			for rectangulo in misRectangulos:
				lineaParaRectangulo[contadorDeRectangulos] = lineaInterna.copy()
				for punto in lineaParaRectangulo[contadorDeRectangulos]:
					if (punto[0]<rectangulo[0][0])|(punto[0]>rectangulo[0][0]+rectangulo[0][1])|(punto[1]<rectangulo[0][1])|(punto[1]>rectangulo[0][1]+rectangulo[0][2]):
						lineaParaRectangulo[contadorDeRectangulos].pop(lineaParaRectangulo[contadorDeRectangulos].index(punto))
				lineaParaRectangulo[contadorDeRectangulos].pop()
				lineaParaRectangulo[contadorDeRectangulos].pop(0)
				contadorDeRectangulos+=1
			
			maximaLongitud = 0
			lineaRespuesta = []
			for index,linea in lineaParaRectangulo.items():
				if len(linea)>maximaLongitud:
					maximaLongitud = len(linea)
					lineaRespuesta = linea
			try:
				extremoInferior = lineaRespuesta[0]
			except:
				extremoInferior = lineaInterna[self.numeroDePuntos//2]
				self.miReporte.error('No pude detectar puntos a seguir en el rectangulo')
			extremoSuperior = extremoInferior
			if len(lineaRespuesta)>2:
				extremoInferior = lineaRespuesta.pop(0)
				extremoSuperior = lineaRespuesta.pop()
			if len(lineaRespuesta)>2:
				extremoInferior = lineaRespuesta.pop(0)
				extremoSuperior = lineaRespuesta.pop()
			extremoMedio = (np.array(extremoInferior)+np.array(extremoSuperior))//2
			extremoMedio = extremoMedio.tolist()
			
			return np.array([[np.array(extremoInferior,dtype = np.float32)],[np.array(extremoMedio,dtype = np.float32)],[np.array(extremoSuperior,dtype = np.float32)]])
		else:
			dif2 = []
			for numeroDePunto in range(1,self.numeroDePuntos+1):
				x = nuevoVector[numeroDePunto][0][0] - vectorAntiguo[numeroDePunto][0][0]
				y = nuevoVector[numeroDePunto][0][1] - vectorAntiguo[numeroDePunto][0][1]
				dif2.append(x**2+y**2)
			indiceDeMayores = []
			
			indice = dif2.index(max(dif2))
			indiceDeMayores.append(indice)
			dif2.pop(indice)
			indice = dif2.index(max(dif2))
			indiceDeMayores.append(indice)
			dif2.pop(indice)
			indice = dif2.index(max(dif2))
			indiceDeMayores.append(indice)
			dif2.pop(indice)
			
			return np.array([[nuevoVector[indiceDeMayores[0]][0]],[nuevoVector[indiceDeMayores[1]][0]],[nuevoVector[indiceDeMayores[2]][0]]])
			

	def obtenerMagnitudMovimiento(self,vectorAntiguo, nuevoVector):
		"""
		Gets the real magnitud of movement perpendicular to the starting point
		"""
		(x,y) = self.obtenerVectorMovimiento(vectorAntiguo, nuevoVector)
		moduloPerpendicular = self.vectorPerpendicularUnitario[0]*x+self.vectorPerpendicularUnitario[1]*y
		return moduloPerpendicular


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
	flanco = []
	frame = 0
	mifps = 8

	while True:
		for inciceDescarte in range(30//mifps):
			ret, frameActual = camaraParaFlujo.read()

		frameActual = cv2.resize(frameActual,(320,240))
		tiempoAuxiliar = time.time()
		filtrado,flancoRes,magnitud = miPolicia.seguirImagen(frame,frameActual)
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
		flanco.append(flancoRes)

		ch = 0xFF & cv2.waitKey(5)
		if ch == ord('q'):
			break

		if ch == ord('p'):
			x = range(len(velocidades))
			graficaActual.title('Velocidad Y objetos')
			graficaActual.plot(x,velocidades,label='vel')
			graficaActual.plot(x,velocidadesFiltradas,label='Fil')
			graficaActual.plot(x,flanco,label='Fla')
			graficaActual.legend(loc='upper center', bbox_to_anchor=(0.5, 1.05),ncol=4, fancybox=True, shadow=True)
			graficaActual.show()

		if ch == ord('r'):
			miPolicia.restablecerLineaLK()
		
		print('Ciclo',time.time()-tiempoAuxiliar)
		while time.time()-tiempoAuxiliar<1/mifps:
			True
		frame += 1
		tiempoAuxiliar = time.time()