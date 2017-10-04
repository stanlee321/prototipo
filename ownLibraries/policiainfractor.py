import os
import cv2
import time
import math
import numpy as np
from analisisonda import AnalisisOnda

import matplotlib.pyplot as graficaActual

directorioDeTrabajo = os.getenv('HOME')+'/trafficFlow/prototipo11'
directorioDeVideos = os.getenv('HOME')+'/trafficFlow/trialVideos'
directorioDeLibreriasPropias = directorioDeTrabajo +'/ownLibraries'
nombreCarpetaDeReporte = 'casosReportados'
myReportingDirectory = directorioDeTrabajo+'/'+nombreCarpetaDeReporte
folderDeInstalacion = directorioDeTrabajo+'/installationFiles'


class PoliciaInfractor():
	"""
	Esta clase recibe una imagen, el estado del semaforo y determina flujo vehicular e infracciones
	"""
	def __init__(self,imagenParaInicializar,poligonoPartida,poligonoLlegada):
		# Tomo la imagen de inicialización y obtengo algunas caracteristicas de la misma
		self.imagenAuxiliar = cv2.cvtColor(imagenParaInicializar, cv2.COLOR_BGR2GRAY)
		try:
			height,width = self.imagenAuxiliar.shape
		except:
			print('No pude obtener data, es una imagen el objeto de inicializacion?')
		
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
		self.numeroAutosCruzando = 0
		self.restablecerLineaLK()
		self.seguimientoEncendido = False
		self.aApagar = False
		self.listaDeInfracciones = []

	def inicializar(self,):
		"""
		Resets the starting line to get ready to the next frame
		"""
		self.restablecerLineaLK()

	def restablecerLineaLK(self,):
		self.lineaDeResguardoDelantera = np.array([[self.lineaDePintadoLK[0]]])
		for numeroDePunto in range(1,self.numeroDePuntos+1):
			self.lineaDeResguardoDelantera = np.append(self.lineaDeResguardoDelantera,[[self.lineaDePintadoLK[0]+numeroDePunto*np.array([self.stepX,self.stepY])]],axis=0)
		self.lineaFijaDelantera = self.lineaDeResguardoDelantera

	def evolucionarLineaVigilancia(self,numeroDeFrame,imagenActual):
		"""
		Get into the new frame, updates the flow and follows the item as required
		"""
		# la imagen introducida esta en RGB, 240,320,3
		variacionIntegral = 0
		imagenActualEnGris = cv2.cvtColor(imagenActual, cv2.COLOR_BGR2GRAY)
		#lineaAcondicionada = []
		#for array in self.lineaDeResguardoDelantera:
		#	lineaAcondicionada.append([list(array[0]*1.0)])
		self.lineaDeResguardoDelantera = np.array(self.lineaDeResguardoDelantera,dtype = np.float32)	# This solved the problem although the array seemed to ve  in float32, adding this specification to this line solved the problem
		self.lineaFijaDelantera = np.array(self.lineaFijaDelantera,dtype = np.float32)
		tiempoParaLK = time.time()
		
		
		# Se compara las lineas anterior y nueva para obtener el flujo en dirección deseada
		
		#variacionIntegral = self.obtenerMagnitudMovimiento(self.lineaDeResguardoDelantera,nuevoArrayAActualizar)

		arrayAuxiliarParaVelocidad, activo, err = cv2.calcOpticalFlowPyrLK(self.imagenAuxiliar, imagenActualEnGris, self.lineaFijaDelantera, None, **self.lk_params)
		self.lineaEmpuje = arrayAuxiliarParaVelocidad
		flujoTotal = self.obtenerMagnitudMovimiento(self.lineaFijaDelantera,arrayAuxiliarParaVelocidad)
		ondaFiltrada, flanco = self.miFiltro.obtenerOndaFiltrada(flujoTotal)
		if flanco == 1:
			puntosMasMoviles = self.obtenerPuntosMoviles(self.lineaFijaDelantera,arrayAuxiliarParaVelocidad)
			nuevaInfraccion = {'name':'fechaActual','momentum':numeroDeFrame,'frameInicial':numeroDeFrame,'frameFinal':0,'desplazamiento':puntosMasMoviles,'estado':'Candidato','foto':False}
			self.listaDeInfracciones.append(nuevaInfraccion)
			self.seguimientoEncendido = True
		
		for infraccion in self.listaDeInfracciones:
			if infraccion['estado'] == 'Candidato':
				nuevoArrayAActualizar, activo, err = cv2.calcOpticalFlowPyrLK(self.imagenAuxiliar, imagenActualEnGris, infraccion['desplazamiento'], None, **self.lk_params)	
				actualizacion = {'desplazamiento':nuevoArrayAActualizar}
				infraccion.update(actualizacion)
				for vector in nuevoArrayAActualizar:
					xTest, yTest = vector[0][0], vector[0][1]
					if cv2.pointPolygonTest(self.areaDeConfirmacion,(xTest, yTest ),True)>=0:
						self.numeroAutosCruzando+=1
						actualizacion = {'estado':'Confirmado'}
						infraccion.update(actualizacion)

		tiempoParaLK = time.time() - tiempoParaLK
		print('LK demoro:', tiempoParaLK)
		#self.lineaDeResguardoDelantera = nuevoArrayAActualizar
		self.imagenAuxiliar = imagenActualEnGris
		
		return ondaFiltrada,flanco,flujoTotal

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

	def obtenerPuntosMoviles(self,vectorAntiguo, nuevoVector):
		"""
		Gets center of movement as a tuple of three vectors
		"""
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
	"""
	This small trial is a proff of work for the current class
	"""
	try:
		nombreDeVideo = directorioDeVideos+'/'+sys.arg[1]
		camaraParaFlujo = cv2.VideoCapture(nombreDeVideo)
		archivoParametrosACargar = nombreDeVideo[:-4]+'.npy'
	except:
		nombreDeVideo = directorioDeVideos+'/mySquare.mp4'
		camaraParaFlujo = cv2.VideoCapture(directorioDeVideos+'/mySquare.mp4')
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
		filtrado,flancoRes,magnitud = miPolicia.evolucionarLineaVigilancia(frame,frameActual)
		print('Tiempo de evolución de linea: ', time.time()-tiempoAuxiliar)
		toPlot = miPolicia.obtenerLinea()
	
		for punto in toPlot:
			frameActual = cv2.circle(frameActual,punto, 4, (0,0,0), -1)# tuple(map(tuple,toPlot))
		font = cv2.FONT_HERSHEY_SIMPLEX
		cv2.putText(frameActual, str(int(magnitud)), (20,20), font, 0.4,(255,255,255),1,cv2.LINE_AA)
		cv2.putText(frameActual, str(miPolicia.numeroAutosCruzando), (20,40), font, 0.4,(255,255,255),1,cv2.LINE_AA)
		cv2.imshow('Visual',frameActual)
		
		
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
		#print(time.time()-tiempoAuxiliar)
		
		while time.time()-tiempoAuxiliar<1/mifps:
			True
		frame += 1
		tiempoAuxiliar = time.time()