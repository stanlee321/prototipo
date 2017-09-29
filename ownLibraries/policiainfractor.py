import os
import cv2
import time
import math
import numpy as np

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
		self.numeroAutosCruzando = 0
		self.restablecerLineaLK()

	def inicializar(self,):
		self.restablecerLineaLK()

	def restablecerLineaLK(self,):
		self.lineaDeResguardoDelantera = np.array([[self.lineaDePintadoLK[0]]])
		for numeroDePunto in range(1,self.numeroDePuntos+1):
			self.lineaDeResguardoDelantera = np.append(self.lineaDeResguardoDelantera,[[self.lineaDePintadoLK[0]+numeroDePunto*np.array([self.stepX,self.stepY])]],axis=0)

	def evolucionarLineaVigilancia(self,imagenActual):
		# la imagen introducida esta en RGB, 240,320,3
		variacionIntegral = 0
		imagenActualEnGris = cv2.cvtColor(imagenActual, cv2.COLOR_BGR2GRAY)
		#lineaAcondicionada = []
		#for array in self.lineaDeResguardoDelantera:
		#	lineaAcondicionada.append([list(array[0]*1.0)])
		lineaAcondicionada = np.array(self.lineaDeResguardoDelantera,dtype = np.float32)	# This solved the problem although the array seemed to ve  in float32, adding this specification to this line solved the problem
		arrayAuxiliar, activo, err = cv2.calcOpticalFlowPyrLK(self.imagenAuxiliar, imagenActualEnGris, lineaAcondicionada, None, **self.lk_params)
		# Se compara las lineas anterior y nueva para obtener el flujo en dirección deseada
		variacionIntegral = self.obtenerMagnitudFlujoPerpendicularALinea(self.lineaDeResguardoDelantera,arrayAuxiliar)

		self.lineaDeResguardoDelantera = arrayAuxiliar
		self.imagenAuxiliar = imagenActualEnGris
		for vector in arrayAuxiliar:
			xTest, yTest = vector[0][0], vector[0][1]
			if cv2.pointPolygonTest(self.areaDeConfirmacion,(xTest, yTest ),True)>=0:
				self.numeroAutosCruzando+=1
				self.restablecerLineaLK()
		return variacionIntegral

	def obtenerLinea(self):
		return self.lineaDeResguardoDelantera

	def obtenerVectorFlujoEnLinea(self,vectorAntiguo, nuevoVector):
		x = 0
		y = 0
		for numeroDePunto in range(1,self.numeroDePuntos+1):
			x += nuevoVector[numeroDePunto][0][0] - vectorAntiguo[numeroDePunto][0][0]
			y += nuevoVector[numeroDePunto][0][1] - vectorAntiguo[numeroDePunto][0][1]
		x = 10*x/(self.numeroDePuntos+1)
		y = 10*y/(self.numeroDePuntos+1)
		return (x,y)

	def obtenerMagnitudFlujoPerpendicularALinea(self,vectorAntiguo, nuevoVector):
		(x,y) = self.obtenerVectorFlujoEnLinea(vectorAntiguo, nuevoVector)
		moduloPerpendicular = self.vectorPerpendicularUnitario[0]*x+self.vectorPerpendicularUnitario[1]*y

		return moduloPerpendicular

if __name__ == '__main__':
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
	numeroAutosCruzando = 0
	tiempoAuxiliar = time.time()

	while True:
		ret, frameActual = camaraParaFlujo.read()

		frameActual = cv2.resize(frameActual,(320,240))
		tiempoAuxiliar = time.time()
		magnitud = miPolicia.evolucionarLineaVigilancia(frameActual)
		print('Tiempo de evolución de linea: ', time.time()-tiempoAuxiliar)
		toPlot = miPolicia.obtenerLinea()
	
		for punto in toPlot:
			frameActual = cv2.circle(frameActual,tuple(punto[0]), 4, (0,0,0), -1)# tuple(map(tuple,toPlot))
		font = cv2.FONT_HERSHEY_SIMPLEX
		cv2.putText(frameActual, str(int(magnitud)), (20,20), font, 0.4,(255,255,255),1,cv2.LINE_AA)
		cv2.putText(frameActual, str(miPolicia.numeroAutosCruzando), (20,40), font, 0.4,(255,255,255),1,cv2.LINE_AA)
		cv2.imshow('Visual',frameActual)
		
		ch = 0xFF & cv2.waitKey(5)
		if ch == ord('q'):
			break

		if ch == ord('r'):
			miPolicia.restablecerLineaLK()
		#print(time.time()-tiempoAuxiliar)
		tiempoAuxiliar = time.time()
		while time.time()-tiempoAuxiliar<0.05:
			True